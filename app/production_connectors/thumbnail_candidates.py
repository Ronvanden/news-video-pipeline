"""BA 32.74 — Thumbnail Candidates V1 (CLI-first, 1–3 images).

Constraints:
- No auto-fallback, no secrets, no API bodies in outputs
- Subject lock is respected (from Visual Reference brief)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.production_connectors.openai_images_adapter import generate_openai_image_from_prompt
from app.production_connectors.visual_reference_layer import build_visual_reference_brief_v1


_TC_VERSION = "ba32_74_v1"


def _clean(s: Optional[str]) -> str:
    return (s or "").strip()


def _sanitize_warning(w: str) -> str:
    s = str(w or "").strip()
    if not s:
        return ""
    low = s.lower()
    if "bearer " in low or "authorization" in low or "sk-" in low:
        return "thumbnail_candidates_warning_sanitized"
    if len(s) > 260:
        return (s[:240] + "…").strip()
    return s


def sanitize_warnings(warnings: Any) -> List[str]:
    out: List[str] = []
    if not isinstance(warnings, list):
        return out
    for x in warnings:
        s = _sanitize_warning(str(x or ""))
        if s and s not in out:
            out.append(s)
    return out


def _subject_lock_snippet(subject_lock: str) -> str:
    sl = _clean(subject_lock).lower()
    if sl == "adult_man":
        return "Central subject must be an adult man (male). No female main character."
    if sl == "adult_woman":
        return "Central subject must be an adult woman (female). No male main character."
    return "Central subject: one adult human protagonist (gender-neutral unless specified)."


def _subject_negative(subject_lock: str) -> str:
    sl = _clean(subject_lock).lower()
    if sl == "adult_man":
        return "female main character, woman as central subject"
    if sl == "adult_woman":
        return "male main character, man as central subject"
    return ""


def _angle_defs() -> List[Dict[str, str]]:
    return [
        {
            "candidate_id": "thumb_a",
            "angle_type": "emotional_closeup",
            "rationale": "Testet maximale emotionale Spannung durch Close-up/Profil/Silhouette, klarer Fokus.",
            "intended_text_space": "Top-left or right third reserved as clean negative space (no text rendered).",
            "angle_prompt": "Emotional close-up: strong facial emotion or tense profile/silhouette, high contrast, crisp subject, click-stopping intensity.",
        },
        {
            "candidate_id": "thumb_b",
            "angle_type": "mystery_drama",
            "rationale": "Testet Mystery/Drama: Ort/Spur/Geheimnis als Bildfrage, dunklerer Ton, Spannung.",
            "intended_text_space": "Upper third reserved for headline space; keep background clean and readable.",
            "angle_prompt": "Mystery drama: darker cinematic scene, a clue/location element, strong visual question, suspenseful atmosphere, still realistic editorial tone.",
        },
        {
            "candidate_id": "thumb_c",
            "angle_type": "cinematic_wide",
            "rationale": "Testet breiten Doku-/Filmstill-Look: Ort + Atmosphäre + klare negative space Fläche.",
            "intended_text_space": "Wide negative space area for later text overlay; maintain strong silhouette separation.",
            "angle_prompt": "Cinematic wide: documentary film still, wide establishing shot with atmosphere, coherent palette, strong composition, clear negative space area.",
        },
    ]


def build_thumbnail_candidate_briefs_v1(
    *,
    visual_reference_brief: Optional[Dict[str, Any]] = None,
    title: Optional[str] = None,
    summary: Optional[str] = None,
    count: int = 3,
    target_platform: str = "youtube",
) -> Dict[str, Any]:
    """
    Builds 1–3 candidate briefs. No provider calls.
    """
    warns: List[str] = []
    t = _clean(title)
    s = _clean(summary)
    plat = _clean(target_platform) or "youtube"

    vr = visual_reference_brief if isinstance(visual_reference_brief, dict) else None
    if vr is None:
        # allowed V1 shortcut: build brief from title/summary only (no master image required)
        vr = build_visual_reference_brief_v1(title=t or None, hook_or_summary=s or None, target_platform=plat)

    subject_lock = _clean(str(vr.get("subject_lock") or "neutral")) or "neutral"
    visual_style = _clean(str(vr.get("visual_style") or "")) or "cinematic_editorial_documentary"
    base_dir = _clean(str(vr.get("thumbnail_direction") or "")) or ""
    base_lock = _clean(str(vr.get("scene_style_lock") or "")) or ""
    topic_or_summary = _clean(str(vr.get("topic_or_summary") or s or t))

    n = int(count or 0)
    if n <= 0:
        n = 3
        warns.append("thumbnail_candidates_count_defaulted")
    if n > 3:
        n = 3
        warns.append("thumbnail_candidates_count_capped_3")

    candidates: List[Dict[str, Any]] = []
    defs = _angle_defs()[:n]
    for d in defs:
        angle_prompt = d["angle_prompt"]
        prompt_parts = [
            "YouTube thumbnail image, high-end cinematic editorial realism.",
            _subject_lock_snippet(subject_lock),
            f"Angle: {angle_prompt}",
            "Composition: strong subject separation, readable silhouette, intentional framing for 16:9 thumbnail use (even if output is square).",
            "Leave clean negative space for later text overlay (do NOT render text, do NOT render typography).",
            "No logos, no watermarks, no brand marks, no copyrighted characters, no celebrities.",
            f"Style lock: {visual_style}. Platform: {plat}.",
        ]
        if topic_or_summary:
            prompt_parts.append(f"Topic/summary context: {topic_or_summary}.")
        if base_dir:
            prompt_parts.append(f"Direction: {base_dir}")
        if base_lock:
            prompt_parts.append(f"Scene style lock: {base_lock}")

        prompt = " ".join(p.strip() for p in prompt_parts if p.strip())
        neg = (
            "text, typography, captions, subtitles, watermark, logo, brand, signature, UI overlays, "
            "copyrighted characters, celebrities, political campaign materials, gore, explicit content"
        )
        sn = _subject_negative(subject_lock)
        if sn:
            neg = neg + ", " + sn

        candidates.append(
            {
                "candidate_id": d["candidate_id"],
                "angle_type": d["angle_type"],
                "prompt": prompt,
                "negative_prompt": neg,
                "rationale": d["rationale"],
                "intended_text_space": d["intended_text_space"],
                "subject_lock": subject_lock,
                "warnings": [],
            }
        )

    return {
        "thumbnail_candidates_version": _TC_VERSION,
        "title": t,
        "summary": s or None,
        "target_platform": plat,
        "subject_lock": subject_lock,
        "candidates": candidates,
        "warnings": sanitize_warnings(warns + list(vr.get("warnings") or [])),
    }


@dataclass(frozen=True)
class ThumbnailCandidatesResult:
    ok: bool
    model: str
    size: str
    generated_count: int
    failed_count: int
    candidate_paths: Dict[str, str]
    candidate_briefs: Dict[str, Any]
    warnings: List[str]
    result_path: str
    thumbnail_candidates_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": bool(self.ok),
            "model": self.model,
            "size": self.size,
            "generated_count": int(self.generated_count),
            "failed_count": int(self.failed_count),
            "candidate_paths": dict(self.candidate_paths or {}),
            "candidate_briefs": dict(self.candidate_briefs or {}),
            "warnings": list(self.warnings or []),
            "result_path": self.result_path,
            "thumbnail_candidates_version": self.thumbnail_candidates_version,
        }


def run_thumbnail_candidates_v1(
    *,
    output_dir: str | Path,
    title: Optional[str] = None,
    summary: Optional[str] = None,
    video_template: Optional[str] = None,
    visual_reference_brief: Optional[Dict[str, Any]] = None,
    count: int = 3,
    target_platform: str = "youtube",
    model: Optional[str] = None,
    size: str = "1024x1024",
    timeout_seconds: float = 120.0,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Generates 1–3 thumbnail candidate PNGs + JSON report.
    Uses OpenAI images adapter; no model auto-fallback.
    """
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    eff_model = _clean(model) or _clean(os.environ.get("OPENAI_IMAGE_MODEL")) or "gpt-image-2"
    eff_size = _clean(size) or "1024x1024"

    # Build or reuse brief (allowed: no master PNG required in V1)
    briefs = build_thumbnail_candidate_briefs_v1(
        visual_reference_brief=visual_reference_brief,
        title=title,
        summary=summary,
        count=int(count or 0),
        target_platform=target_platform,
    )
    cands = briefs.get("candidates") if isinstance(briefs.get("candidates"), list) else []

    paths: Dict[str, str] = {}
    warns: List[str] = list(briefs.get("warnings") or [])
    gen_ok = 0
    gen_fail = 0

    for c in cands:
        if not isinstance(c, dict):
            continue
        cid = _clean(str(c.get("candidate_id") or ""))
        prompt = _clean(str(c.get("prompt") or ""))
        if not cid or not prompt:
            gen_fail += 1
            continue
        out_name = f"thumbnail_candidate_{cid}.png"
        png_path = out_dir / out_name
        gen = generate_openai_image_from_prompt(
            prompt,
            png_path,
            dry_run=bool(dry_run),
            size=eff_size,
            model=eff_model,
            timeout_seconds=float(timeout_seconds),
        )
        warns.extend(list(gen.warnings or []))
        if bool(gen.ok):
            gen_ok += 1
            paths[cid] = str(Path(gen.output_path).resolve())
        else:
            gen_fail += 1

    warnings = sanitize_warnings(warns)
    result = ThumbnailCandidatesResult(
        ok=gen_ok > 0 and gen_fail == 0,
        model=str(eff_model),
        size=str(eff_size),
        generated_count=int(gen_ok),
        failed_count=int(gen_fail),
        candidate_paths=paths,
        candidate_briefs=briefs,
        warnings=warnings,
        result_path=str((out_dir / "thumbnail_candidates_result.json").resolve()),
        thumbnail_candidates_version=_TC_VERSION,
    )
    rp = Path(result.result_path)
    rp.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result.to_dict()

