"""BA 32.76 — Thumbnail Batch Overlay + Selection V1 (local only, heuristic).

No providers. No secrets. No uploads. No ML.
Takes existing candidate PNGs (A/B/C) and renders a controlled number of final thumbnails with text overlays.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.production_connectors.thumbnail_overlay import (
    build_thumbnail_text_variants_v1,
    render_thumbnail_overlay_v1,
    sanitize_warnings,
)


_BATCH_VERSION = "ba32_76_v1"


def _clean(s: Optional[str]) -> str:
    return (s or "").strip()


def _clamp_int(v: Any, lo: int, hi: int, default: int) -> int:
    try:
        n = int(v)
    except Exception:
        return default
    if n < lo:
        return lo
    if n > hi:
        return hi
    return n


def score_thumbnail_overlay_candidate_v1(
    *,
    source_candidate_path: str,
    text_lines: List[str],
    text_variant_id: str,
    style_preset: str,
) -> Tuple[int, List[str]]:
    """
    Returns (score 0..100, reasons[]).
    Simple heuristic:
    - short text better
    - impact_youtube / urgent_mystery slightly preferred
    - variant strength: SPURLOS/WEG and NIEMAND/FAND IHN are strong
    - candidate angle preference by filename thumb_a/thumb_b/thumb_c
    """
    reasons: List[str] = []
    score = 50

    sp = _clean(style_preset).lower()
    if sp == "impact_youtube":
        score += 10
        reasons.append("style:impact_youtube:+10")
    elif sp == "urgent_mystery":
        score += 8
        reasons.append("style:urgent_mystery:+8")
    elif sp == "documentary_poster":
        score += 4
        reasons.append("style:documentary_poster:+4")
    else:
        reasons.append("style:clean_bold:+0")

    p = _clean(source_candidate_path).lower()
    if "thumb_b" in p:
        score += 6
        reasons.append("angle:thumb_b(mystery_drama):+6")
    elif "thumb_a" in p:
        score += 5
        reasons.append("angle:thumb_a(emotional_closeup):+5")
    elif "thumb_c" in p:
        score -= 2
        reasons.append("angle:thumb_c(cinematic_wide):-2")

    # text strength
    joined = " ".join([_clean(x) for x in (text_lines or [])]).upper()
    if "SPURLOS" in joined and "WEG" in joined:
        score += 10
        reasons.append("text:SPURLOS_WEG:+10")
    if "NIEMAND" in joined and "FAND" in joined:
        score += 8
        reasons.append("text:NIEMAND_FAND_IHN:+8")
    if text_variant_id == "text_override":
        score += 2
        reasons.append("text:override:+2")

    # length penalty
    wc = len([w for w in joined.split() if w])
    if wc <= 3:
        score += 6
        reasons.append("text:length<=3:+6")
    elif wc <= 5:
        score += 2
        reasons.append("text:length<=5:+2")
    else:
        score -= min(12, (wc - 5) * 3)
        reasons.append("text:length>5:penalty")

    # line count
    lc = len([x for x in (text_lines or []) if _clean(x)])
    if lc == 1:
        score += 3
        reasons.append("lines:1:+3")
    elif lc == 2:
        score += 1
        reasons.append("lines:2:+1")
    else:
        score -= 5
        reasons.append("lines:invalid:-5")

    if score < 0:
        score = 0
    if score > 100:
        score = 100
    return score, reasons


@dataclass(frozen=True)
class BatchOverlayOutput:
    output_id: str
    source_candidate_path: str
    output_path: str
    text_variant_id: str
    text_lines: List[str]
    style_preset: str
    score: int
    score_reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "output_id": self.output_id,
            "source_candidate_path": self.source_candidate_path,
            "output_path": self.output_path,
            "text_variant_id": self.text_variant_id,
            "text_lines": list(self.text_lines or []),
            "style_preset": self.style_preset,
            "score": int(self.score),
            "score_reasons": list(self.score_reasons or []),
        }


def run_thumbnail_batch_overlay_v1(
    *,
    candidate_paths: List[str],
    title: str,
    summary: Optional[str],
    output_dir: str | Path,
    language: str = "de",
    max_outputs: int = 6,
    style_presets: Optional[List[str]] = None,
    text_variants: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    warns: List[str] = []

    cand = [str(Path(p).resolve()) for p in (candidate_paths or []) if _clean(p)]
    cand = [p for p in cand if Path(p).is_file()]
    if not cand:
        payload = {
            "ok": False,
            "thumbnail_batch_overlay_version": _BATCH_VERSION,
            "generated_count": 0,
            "outputs": [],
            "recommended_thumbnail": None,
            "warnings": ["thumbnail_batch_overlay_no_candidates"],
            "result_path": str((out_dir / "thumbnail_batch_overlay_result.json").resolve()),
        }
        Path(payload["result_path"]).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return payload

    mo = _clamp_int(max_outputs, 1, 12, 6)
    presets = style_presets if isinstance(style_presets, list) and style_presets else ["impact_youtube", "urgent_mystery"]
    presets = [str(x).strip() for x in presets if _clean(str(x))]
    if not presets:
        presets = ["impact_youtube"]
        warns.append("thumbnail_batch_overlay_style_presets_defaulted")

    if text_variants is None:
        tv = build_thumbnail_text_variants_v1(title=title, summary=summary, language=language, max_variants=3)
        text_variants = tv.get("text_variants") if isinstance(tv.get("text_variants"), list) else []
        warns.extend(list(tv.get("warnings") or []))
    variants = [v for v in (text_variants or []) if isinstance(v, dict)]
    if not variants:
        warns.append("thumbnail_batch_overlay_no_text_variants")

    # Controlled combination plan (ordered, then cut to max_outputs).
    # Prefer strong variant text_a on multiple candidates with impact_youtube.
    # Then add one mystery variant with urgent_mystery.
    plan: List[Tuple[str, str, str]] = []  # (candidate_path, variant_id, preset)

    # helper: pick candidate by kind
    def _pick_contains(substr: str) -> Optional[str]:
        for p in cand:
            if substr in p.lower():
                return p
        return None

    c_a = _pick_contains("thumb_a") or cand[0]
    c_b = _pick_contains("thumb_b") or (cand[1] if len(cand) > 1 else cand[0])
    c_c = _pick_contains("thumb_c") or (cand[2] if len(cand) > 2 else cand[-1])

    # pick variants
    v_by_id = {str(v.get("variant_id") or ""): v for v in variants}
    v_a = v_by_id.get("text_a") or (variants[0] if variants else {})
    v_b = v_by_id.get("text_b") or (variants[1] if len(variants) > 1 else v_a)

    pref0 = presets[0]
    pref1 = presets[1] if len(presets) > 1 else presets[0]
    pref_doc = "documentary_poster" if "documentary_poster" in [p.lower() for p in presets] else "documentary_poster"

    if v_a:
        plan.append((c_a, str(v_a.get("variant_id") or "text_a"), pref0))
        plan.append((c_b, str(v_a.get("variant_id") or "text_a"), pref0))
    if v_b:
        plan.append((c_b, str(v_b.get("variant_id") or "text_b"), pref1))
    if v_a:
        plan.append((c_c, str(v_a.get("variant_id") or "text_a"), pref_doc))

    # If still room, expand lightly: apply second preset to thumb_a and thumb_b with text_b.
    if len(plan) < mo and v_b:
        plan.append((c_a, str(v_b.get("variant_id") or "text_b"), pref1))
    if len(plan) < mo and v_b:
        plan.append((c_b, str(v_b.get("variant_id") or "text_b"), pref1))

    plan = plan[:mo]

    outputs: List[BatchOverlayOutput] = []
    idx = 0
    for (src, vid, preset) in plan:
        v = v_by_id.get(vid) or {}
        line1 = str(v.get("line_1") or "").strip()
        line2 = str(v.get("line_2") or "").strip() or None
        idx += 1
        out_name = f"thumbnail_batch_{idx:02d}.png"
        out_path = out_dir / out_name
        rr = render_thumbnail_overlay_v1(
            image_path=src,
            output_path=out_path,
            line_1=line1,
            line_2=line2,
            position="auto_right",
            canvas_size=(1280, 720),
            style_preset=str(preset),
        )
        warns.extend(list(rr.get("warnings") or []))
        if not rr.get("ok"):
            continue
        score, reasons = score_thumbnail_overlay_candidate_v1(
            source_candidate_path=src,
            text_lines=list(rr.get("text_lines") or []),
            text_variant_id=vid,
            style_preset=str(rr.get("style_preset") or preset),
        )
        outputs.append(
            BatchOverlayOutput(
                output_id=f"batch_{idx:02d}",
                source_candidate_path=str(src),
                output_path=str(Path(rr.get("output_path") or out_path).resolve()),
                text_variant_id=vid,
                text_lines=list(rr.get("text_lines") or []),
                style_preset=str(rr.get("style_preset") or preset),
                score=int(score),
                score_reasons=reasons,
            )
        )

    outputs_sorted = sorted(outputs, key=lambda o: int(o.score), reverse=True)
    recommended = outputs_sorted[0].to_dict() if outputs_sorted else None

    payload = {
        "ok": bool(outputs_sorted),
        "thumbnail_batch_overlay_version": _BATCH_VERSION,
        "generated_count": len(outputs_sorted),
        "outputs": [o.to_dict() for o in outputs_sorted],
        "recommended_thumbnail": recommended,
        "warnings": sanitize_warnings(warns),
        "result_path": str((out_dir / "thumbnail_batch_overlay_result.json").resolve()),
    }
    Path(payload["result_path"]).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload

