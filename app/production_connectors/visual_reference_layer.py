"""BA 32.73 — Visual Reference Layer V1 (CLI-first, 1 Master Reference Image).

Ziele:
- Ein konsistenter visueller Referenzanker pro Video (Master Reference Image + strukturierter Brief)
- Kein Auto-Fallback, keine Secrets/Response-Bodies in Logs/Outputs
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.production_connectors.openai_images_adapter import generate_openai_image_from_prompt


_VR_VERSION = "ba32_73_v1"

_SUBJECT_LOCK_ADULT_MAN = "adult_man"
_SUBJECT_LOCK_ADULT_WOMAN = "adult_woman"
_SUBJECT_LOCK_NEUTRAL = "neutral"


def _clean(s: Optional[str]) -> str:
    return (s or "").strip()


def _sanitize_warning(w: str) -> str:
    s = str(w or "").strip()
    if not s:
        return ""
    low = s.lower()
    # Never allow likely secret fragments into outputs.
    if "bearer " in low or "authorization" in low:
        return "visual_reference_warning_sanitized"
    if "sk-" in low:
        return "visual_reference_warning_sanitized"
    # Also avoid dumping huge payload-y strings
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


def _topic_or_summary(*, title: str, topic: str, hook_or_summary: str) -> str:
    t = _clean(topic)
    hs = _clean(hook_or_summary)
    if hs:
        return hs
    if t:
        return t
    return _clean(title)


def _infer_subject_lock_v1(*, title: str, topic_or_summary: str) -> tuple[str, str]:
    """
    BA 32.73a — Simple subject inference for the central character.
    Returns (subject_lock, reason).
    """
    blob = f"{title}\n{topic_or_summary}".lower()

    male_patterns = (
        r"\bmann\b",
        r"\bman\b",
        r"\bmale\b",
        r"\bhe\b",
        r"\bhim\b",
        r"\bhis\b",
        r"\bfather\b",
        r"\bhusband\b",
        r"\bson\b",
        r"\bboy\b",
        r"\bgentleman\b",
    )
    female_patterns = (
        r"\bfrau\b",
        r"\bwoman\b",
        r"\bfemale\b",
        r"\bshe\b",
        r"\bher\b",
        r"\bhers\b",
        r"\bmother\b",
        r"\bwife\b",
        r"\bdaughter\b",
        r"\bgirl\b",
        r"\blady\b",
    )

    def _has_any(patterns: tuple[str, ...]) -> bool:
        return any(re.search(p, blob, flags=re.IGNORECASE) is not None for p in patterns)

    m = _has_any(male_patterns)
    f = _has_any(female_patterns)
    if m and not f:
        return (_SUBJECT_LOCK_ADULT_MAN, "token_match_male")
    if f and not m:
        return (_SUBJECT_LOCK_ADULT_WOMAN, "token_match_female")
    if m and f:
        return (_SUBJECT_LOCK_NEUTRAL, "conflict_male_and_female_tokens")
    return (_SUBJECT_LOCK_NEUTRAL, "no_gender_tokens_detected")


def build_visual_reference_brief_v1(
    *,
    title: Optional[str] = None,
    topic: Optional[str] = None,
    hook_or_summary: Optional[str] = None,
    video_template: Optional[str] = None,
    scene_asset_pack: Optional[Dict[str, Any]] = None,
    visual_style: Optional[str] = None,
    target_platform: str = "youtube",
) -> Dict[str, Any]:
    """
    Baut einen strukturierten Visual Brief + Master Reference Prompt.
    Kein Provider-Call.
    """
    warns: List[str] = []
    t = _clean(title)
    tp = _clean(topic)
    hs = _clean(hook_or_summary)
    tpl = _clean(video_template)
    vs = _clean(visual_style) or "cinematic_editorial_documentary"
    plat = _clean(target_platform) or "youtube"

    tos = _topic_or_summary(title=t, topic=tp, hook_or_summary=hs)
    if not t and not tos:
        warns.append("visual_reference_missing_title_or_summary")

    # Extremely light-weight signal from scene_asset_pack (optional).
    sap_hint = ""
    try:
        if isinstance(scene_asset_pack, dict):
            exp = scene_asset_pack.get("scene_expansion") or {}
            beats = exp.get("expanded_scene_assets") or []
            if isinstance(beats, list) and beats:
                b0 = beats[0] if isinstance(beats[0], dict) else {}
                vp = _clean(str(b0.get("visual_prompt") or b0.get("visual_prompt_effective") or ""))
                if vp:
                    sap_hint = vp
    except Exception:
        sap_hint = ""

    # Safety: strip celebrity-like tokens (best-effort, do not overreach).
    def _strip_risky_names(s: str) -> str:
        # remove @handles and #hashtags; keep editorial.
        s2 = re.sub(r"[@#][A-Za-z0-9_]{2,64}", "", s)
        return re.sub(r"\s{2,}", " ", s2).strip()

    tos_safe = _strip_risky_names(tos)
    sap_safe = _strip_risky_names(sap_hint)

    subject_lock, subject_lock_reason = _infer_subject_lock_v1(title=t, topic_or_summary=tos_safe)

    # Prompt architecture: cinematic/editorial cover image, space for text overlay, no text in image.
    # 16:9 intent even if model outputs square.
    master_prompt_parts = [
        "High-end cinematic editorial cover image for a YouTube documentary/storytelling video.",
        "A single clear hero scene with strong subject focus and readable composition.",
        (
            "Central subject must be an adult man (male). No female main character."
            if subject_lock == _SUBJECT_LOCK_ADULT_MAN
            else (
                "Central subject must be an adult woman (female). No male main character."
                if subject_lock == _SUBJECT_LOCK_ADULT_WOMAN
                else "Central subject: one adult human protagonist (gender-neutral unless specified)."
            )
        ),
        "Lighting: natural cinematic key light with gentle contrast, realistic shadows, filmic highlight rolloff.",
        "Camera: 35mm or 50mm equivalent, shallow depth of field, crisp subject, subtle background bokeh.",
        "Color: cohesive palette, modern documentary grade, controlled saturation, no neon look.",
        "Composition: leave clean negative space for later thumbnail text overlay (do NOT render text).",
        "Mood: realistic, serious, engaging, trustworthy newsroom/editorial tone.",
        "Framing intent: suitable for 16:9 YouTube thumbnail (even if output is square).",
        "No logos, no watermarks, no brand marks, no copyrighted characters, no real celebrity likeness.",
    ]
    if t:
        master_prompt_parts.append(f"Video title context: {tos_safe}.")
    elif tos_safe:
        master_prompt_parts.append(f"Topic/summary: {tos_safe}.")
    if tpl:
        master_prompt_parts.append(f"Template hint: {tpl}.")
    if sap_safe:
        master_prompt_parts.append(f"Scene pack hint (first beat): {sap_safe}.")
    master_prompt_parts.append(f"Style lock: {vs}. Platform: {plat}.")
    master_reference_prompt = " ".join(p.strip() for p in master_prompt_parts if p.strip())

    negative_prompt = (
        "text, captions, subtitles, watermark, logo, brand, signature, UI overlays, "
        "copyrighted characters, celebrities, political campaign materials, gore, explicit content"
    )
    if subject_lock == _SUBJECT_LOCK_ADULT_MAN:
        negative_prompt = negative_prompt + ", female main character, woman as central subject"
    elif subject_lock == _SUBJECT_LOCK_ADULT_WOMAN:
        negative_prompt = negative_prompt + ", male main character, man as central subject"

    brief = {
        "visual_reference_version": _VR_VERSION,
        "title": t,
        "topic_or_summary": tos_safe,
        "visual_style": vs,
        "subject_lock": subject_lock,
        "subject_lock_reason": subject_lock_reason,
        "master_reference_prompt": master_reference_prompt,
        "negative_prompt": negative_prompt,
        "thumbnail_direction": (
            "One strong hero subject, high contrast silhouette separation, clean background space for headline, "
            "documentary/editorial realism, no text rendered."
        ),
        "scene_style_lock": (
            "Keep consistent lens/lighting/palette with the master reference. "
            "Avoid style drift; keep newsroom/editorial realism; no text-in-image."
        ),
        "provider_handoff_notes": (
            "Use master reference image as visual anchor for later thumbnail candidates and scene generation. "
            "Do not introduce new brands or recognizable IP. Keep overlays separate from image generation."
        ),
        "warnings": sanitize_warnings(warns),
    }
    return brief


@dataclass(frozen=True)
class VisualReferenceImageResult:
    ok: bool
    model: str
    size: str
    output_path: str
    bytes_written: int
    visual_reference_brief: Dict[str, Any]
    warnings: List[str]
    result_path: str
    visual_reference_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": bool(self.ok),
            "model": self.model,
            "size": self.size,
            "output_path": self.output_path,
            "bytes_written": int(self.bytes_written),
            "visual_reference_brief": dict(self.visual_reference_brief or {}),
            "warnings": list(self.warnings or []),
            "result_path": self.result_path,
            "visual_reference_version": self.visual_reference_version,
        }


def run_visual_reference_image_v1(
    *,
    output_dir: str | Path,
    title: Optional[str] = None,
    summary: Optional[str] = None,
    topic: Optional[str] = None,
    video_template: Optional[str] = None,
    scene_asset_pack: Optional[Dict[str, Any]] = None,
    visual_style: Optional[str] = None,
    target_platform: str = "youtube",
    model: Optional[str] = None,
    size: str = "1024x1024",
    timeout_seconds: float = 120.0,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Erzeugt genau 1 Master Reference PNG + JSON-Report.

    - Re-uses OpenAI adapter (BA 26.5) for image generation.
    - model: Parameter → OPENAI_IMAGE_MODEL → Default gpt-image-2
    - No auto-fallback (the adapter has controlled error codes, but we do not switch models).
    """
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    eff_model = _clean(model) or _clean(os.environ.get("OPENAI_IMAGE_MODEL")) or "gpt-image-2"
    eff_size = _clean(size) or "1024x1024"

    brief = build_visual_reference_brief_v1(
        title=title,
        topic=topic,
        hook_or_summary=summary,
        video_template=video_template,
        scene_asset_pack=scene_asset_pack,
        visual_style=visual_style,
        target_platform=target_platform,
    )

    png_path = out_dir / "master_reference.png"
    gen = generate_openai_image_from_prompt(
        brief.get("master_reference_prompt") or "",
        png_path,
        dry_run=bool(dry_run),
        size=eff_size,
        model=eff_model,
        timeout_seconds=float(timeout_seconds),
    )

    warnings = sanitize_warnings(list(gen.warnings or []) + list(brief.get("warnings") or []))
    result = VisualReferenceImageResult(
        ok=bool(gen.ok),
        model=str(gen.model or eff_model),
        size=str(gen.size or eff_size),
        output_path=str(Path(gen.output_path).resolve()),
        bytes_written=int(gen.bytes_written or 0),
        visual_reference_brief=brief,
        warnings=warnings,
        result_path=str((out_dir / "visual_reference_result.json").resolve()),
        visual_reference_version=_VR_VERSION,
    )
    rp = Path(result.result_path)
    rp.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result.to_dict()

