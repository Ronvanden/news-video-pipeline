"""Provider-neutral prompt formatters for Visual Prompt Engine V1."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from app.visual_plan.prompt_anatomy import MotionPromptAnatomy, VisualPromptAnatomy


def _norm_space(value: str) -> str:
    return " ".join(str(value or "").split())


def _append_part(parts: List[str], label: str, value: str) -> None:
    clean = _norm_space(value)
    if clean:
        parts.append(f"{label}: {clean}")


def _join_sentence(parts: Iterable[str]) -> str:
    clean_parts = [_norm_space(part) for part in parts if _norm_space(part)]
    if not clean_parts:
        return ""
    text = ". ".join(part.rstrip(".") for part in clean_parts)
    return f"{text}."


def _preset_label(controls: Dict[str, Any]) -> str:
    label = _norm_space(str(controls.get("visual_preset_label") or ""))
    if label:
        return label
    preset_id = _norm_space(str(controls.get("visual_preset") or ""))
    if not preset_id:
        return ""
    return preset_id.replace("_", " ").title()


def anatomy_to_generic_prompt(anatomy: VisualPromptAnatomy, controls: dict | None = None) -> str:
    """Format a VisualPromptAnatomy into the generic V1 prompt string.

    This intentionally stays provider-neutral. Provider-specific prompt routing
    can be added later without changing the engine's public result contract.
    """
    controls_payload: Dict[str, Any] = dict(controls or {})
    detail_level = str(controls_payload.get("prompt_detail_level") or "enhanced")

    parts: List[str] = []
    style_label = _preset_label(controls_payload)
    style_tags = [str(tag) for tag in (anatomy.style_tags or []) if str(tag).strip()]

    if detail_level != "basic" and style_label:
        style_value = style_label
        if style_tags:
            style_value = f"{style_value}; style tags: {', '.join(style_tags[:5])}"
        parts.append(style_value)

    _append_part(parts, "Scene", anatomy.subject_description or "untitled scene")

    if detail_level in {"enhanced", "deep"}:
        _append_part(parts, "Action", anatomy.action)

    _append_part(parts, "Environment", anatomy.environment)

    if detail_level in {"enhanced", "deep"}:
        _append_part(parts, "Camera", anatomy.camera)
        _append_part(parts, "Lighting", anatomy.lighting)
        _append_part(parts, "Mood", anatomy.mood)

    _append_part(parts, "Composition", anatomy.composition)

    if detail_level == "deep":
        _append_part(parts, "Continuity", anatomy.continuity)
        if style_tags and not style_label:
            _append_part(parts, "Style tags", ", ".join(style_tags[:8]))
        _append_part(parts, "Source summary", anatomy.source_summary)
        constraints = [str(item) for item in (anatomy.negative_constraints or []) if str(item).strip()]
        if constraints:
            _append_part(parts, "Constraints", ", ".join(constraints[:8]))

    provider_target = _norm_space(str(controls_payload.get("provider_target") or ""))
    consistency_mode = _norm_space(str(controls_payload.get("visual_consistency_mode") or ""))
    if detail_level == "deep":
        _append_part(parts, "Provider target", provider_target)
        _append_part(parts, "Consistency mode", consistency_mode)

    return _norm_space(_join_sentence(parts))


def anatomy_to_openai_image_prompt(anatomy: VisualPromptAnatomy, controls: dict | None = None) -> str:
    """Format a VisualPromptAnatomy for OpenAI Image prompt input.

    This only changes prompt wording. It does not select or call a provider.
    """
    controls_payload: Dict[str, Any] = dict(controls or {})
    detail_level = str(controls_payload.get("prompt_detail_level") or "enhanced")

    parts: List[str] = ["Create a realistic documentary-style image"]
    style_label = _preset_label(controls_payload)
    style_tags = [str(tag) for tag in (anatomy.style_tags or []) if str(tag).strip()]
    constraints = [
        str(item)
        for item in (anatomy.negative_constraints or [])
        if str(item).strip() and "hook" not in str(item).lower()
    ]

    _append_part(parts, "Subject", anatomy.subject_description or "grounded editorial scene")

    if detail_level in {"enhanced", "deep"}:
        _append_part(parts, "Visual moment", anatomy.action)

    _append_part(parts, "Environment", anatomy.environment)
    _append_part(parts, "Composition", anatomy.composition)

    if detail_level in {"enhanced", "deep"}:
        _append_part(parts, "Framing", anatomy.camera)
        lighting_color = anatomy.lighting
        if style_tags:
            lighting_color = f"{lighting_color}; natural color treatment" if lighting_color else "natural color treatment"
        _append_part(parts, "Lighting and color", lighting_color)
        _append_part(parts, "Mood", anatomy.mood)

    if style_label and detail_level != "basic":
        style_value = style_label
        if style_tags:
            style_value = f"{style_value}; style tags: {', '.join(style_tags[:8])}"
        _append_part(parts, "Style consistency", style_value)

    if detail_level == "deep":
        _append_part(parts, "Continuity", anatomy.continuity)
        _append_part(parts, "Source context", anatomy.source_summary)

    if constraints:
        limit = 5 if detail_level == "basic" else (8 if detail_level == "enhanced" else 12)
        _append_part(parts, "Important constraints", "; ".join(constraints[:limit]))

    return _norm_space(_join_sentence(parts))


def anatomy_to_runway_motion_prompt(
    visual_anatomy: VisualPromptAnatomy,
    motion_anatomy: MotionPromptAnatomy,
    controls: dict | None = None,
) -> str:
    """Format a motion-focused prompt for future Runway image-to-video use."""
    controls_payload: Dict[str, Any] = dict(controls or {})
    detail_level = str(controls_payload.get("prompt_detail_level") or "enhanced")

    parts: List[str] = [
        "Animate the provided image as a realistic short documentary clip"
    ]

    _append_part(parts, "Camera movement", motion_anatomy.camera_motion)
    _append_part(parts, "Scene evolution", motion_anatomy.scene_evolution)
    _append_part(parts, "Subject motion", motion_anatomy.subject_motion)
    _append_part(parts, "Background motion", motion_anatomy.background_motion)
    _append_part(parts, "Pacing", f"{motion_anatomy.pacing}; {motion_anatomy.duration_hint}".strip("; "))

    if detail_level == "deep":
        continuity_parts = [visual_anatomy.continuity, motion_anatomy.transition_hint]
        continuity_text = "; ".join(_norm_space(part) for part in continuity_parts if _norm_space(part))
        _append_part(parts, "Continuity", continuity_text)

    stability = [str(item) for item in (motion_anatomy.stability_constraints or []) if str(item).strip()]
    if stability:
        _append_part(parts, "Stability constraints", "; ".join(stability))

    avoid = [str(item) for item in (motion_anatomy.motion_negative_constraints or []) if str(item).strip()]
    if avoid:
        _append_part(parts, "Avoid", "; ".join(avoid))

    return _norm_space(_join_sentence(parts))
