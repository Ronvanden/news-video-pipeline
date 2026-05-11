"""Structured prompt anatomy for Visual Prompt Engine V1.

This module is deterministic and provider-neutral. It prepares structured
prompt parts that can later be formatted for different image or motion targets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List


@dataclass(frozen=True)
class VisualPromptAnatomy:
    subject_description: str = ""
    action: str = ""
    environment: str = ""
    camera: str = ""
    lighting: str = ""
    mood: str = ""
    composition: str = ""
    style_tags: List[str] = field(default_factory=list)
    continuity: str = ""
    text_safety: str = ""
    negative_constraints: List[str] = field(default_factory=list)
    sanitized_terms: List[str] = field(default_factory=list)
    source_summary: str = ""


@dataclass(frozen=True)
class MotionPromptAnatomy:
    motion_intent: str = ""
    camera_motion: str = ""
    subject_motion: str = ""
    pacing: str = ""
    transition_hint: str = ""
    duration_hint: str = ""
    stability_constraints: List[str] = field(default_factory=list)
    motion_negative_constraints: List[str] = field(default_factory=list)


def _norm_space(value: str) -> str:
    return " ".join(str(value or "").split())


def _dedupe(items: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for item in items:
        value = _norm_space(item)
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _split_negative_segments(value: str) -> List[str]:
    parts: List[str] = []
    for piece in re.split(r"[;,]", value or ""):
        part = _norm_space(piece)
        if part:
            parts.append(part)
    return parts


def _source_summary(narration: str, detail_level: str) -> str:
    text = _norm_space(narration)
    if not text:
        return ""
    cap = {"basic": 120, "enhanced": 260, "deep": 420}.get(detail_level, 260)
    if len(text) <= cap:
        return text
    return text[: max(1, cap - 3)].rsplit(" ", 1)[0].strip() + "..."


def _camera_for(preset_id: str, detail_level: str) -> str:
    if preset_id == "clean_news_explainer":
        return "clean editorial medium-wide frame"
    if preset_id == "dark_mystery":
        return "controlled cinematic frame with restrained slow tension"
    if preset_id == "minimal_symbolic":
        return "static minimal composition with one clear focal object"
    if detail_level == "basic":
        return "clear editorial frame"
    if detail_level == "deep":
        return "grounded documentary frame with deliberate focal hierarchy"
    return "natural editorial frame with clear focal subject"


def _lighting_for(preset_id: str) -> str:
    if preset_id == "dark_mystery":
        return "low-key muted lighting"
    if preset_id == "cinematic_story":
        return "cinematic naturalistic lighting with controlled contrast"
    if preset_id == "clean_news_explainer":
        return "bright neutral newsroom-style lighting"
    if preset_id == "emotional_human_story":
        return "soft natural light"
    if preset_id == "minimal_symbolic":
        return "simple soft studio-like light"
    return "natural light"


def _mood_for(preset_id: str, video_template: str) -> str:
    template = _norm_space(video_template).lower()
    if preset_id == "dark_mystery" or "mystery" in template:
        return "restrained tension"
    if preset_id == "emotional_human_story":
        return "empathetic and grounded"
    if preset_id == "clean_news_explainer":
        return "clear and neutral"
    if preset_id == "minimal_symbolic":
        return "quiet and symbolic"
    return "grounded documentary realism"


def _composition_for(text_safety_mode: str) -> str:
    if text_safety_mode == "overlay_friendly":
        return "concrete editorial image, clear focal subject, believable environment, clean negative space for later overlay"
    if text_safety_mode == "strict_no_text":
        return "concrete editorial image, clear focal subject, believable environment, natural framing, no generated text"
    return "concrete editorial image, clear focal subject, believable environment, natural framing"


def _text_safety_for(text_safety_mode: str) -> str:
    if text_safety_mode == "overlay_friendly":
        return "leave clean empty space for later editorial text overlay"
    if text_safety_mode == "strict_no_text":
        return "no readable text, no letters, no fake UI, no logo, no typography"
    return "avoid readable generated text"


def build_visual_prompt_anatomy(
    *,
    context: Any,
    normalized_controls: Dict[str, str],
    sanitized_title_or_label: str,
    sanitizer_guards: List[str],
    sanitizer_warnings: List[str] | None = None,
    preset: Dict[str, Any] | None = None,
) -> VisualPromptAnatomy:
    """Build structured prompt anatomy from context and normalized operator controls."""
    controls = dict(normalized_controls or {})
    preset_data = dict(preset or {})
    preset_id = controls.get("visual_preset", "")
    detail_level = controls.get("prompt_detail_level", "enhanced")
    text_safety_mode = controls.get("text_safety_mode", "strict_no_text")
    consistency_mode = controls.get("visual_consistency_mode", "one_style_per_video")

    title = _norm_space(sanitized_title_or_label)
    narration = _norm_space(getattr(context, "narration", "") or "")
    source = _source_summary(narration, detail_level)
    style_tags = [str(t) for t in (preset_data.get("style_tags") or []) if str(t).strip()]

    negative_constraints: List[str] = []
    negative_constraints.extend(str(t) for t in (preset_data.get("negative_tags") or []) if str(t).strip())
    negative_constraints.extend(sanitizer_guards or [])
    negative_constraints.extend(_split_negative_segments(getattr(context, "existing_negative_prompt", "") or ""))
    if text_safety_mode == "strict_no_text":
        negative_constraints.extend(["no readable text", "no letters", "no fake UI", "no logo", "no typography"])
    elif text_safety_mode == "overlay_friendly":
        negative_constraints.extend(["no rendered text", "no cluttered frame", "preserve clean negative space"])
    elif text_safety_mode == "normal":
        negative_constraints.append("avoid readable generated text")

    sanitized_terms = [w for w in (sanitizer_warnings or []) if str(w).strip()]

    return VisualPromptAnatomy(
        subject_description=title or "grounded editorial scene based on the scene title",
        action=source,
        environment="grounded documentary environment / editorial real-world setting",
        camera=_camera_for(preset_id, detail_level),
        lighting=_lighting_for(preset_id),
        mood=_mood_for(preset_id, getattr(context, "video_template", "") or ""),
        composition=_composition_for(text_safety_mode),
        style_tags=_dedupe(style_tags),
        continuity=(
            "use one consistent visual style across the video"
            if consistency_mode == "one_style_per_video"
            else ("allow scene-specific visual emphasis" if consistency_mode == "scene_specific" else "allow experimental variation")
        ),
        text_safety=_text_safety_for(text_safety_mode),
        negative_constraints=_dedupe(negative_constraints),
        sanitized_terms=_dedupe(sanitized_terms),
        source_summary=source,
    )
