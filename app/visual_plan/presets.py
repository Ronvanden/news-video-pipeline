"""Visual prompt operator controls and preset catalog.

This module is intentionally provider-neutral: it defines dropdown values and
normalization only. It does not build prompts, call providers, or touch renders.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple


VISUAL_PROMPT_CONTROL_DEFAULTS: Dict[str, str] = {
    "visual_preset": "documentary_realism",
    "prompt_detail_level": "enhanced",
    "provider_target": "generic",
    "text_safety_mode": "strict_no_text",
    "visual_consistency_mode": "one_style_per_video",
}


_VISUAL_PRESETS: List[Dict[str, Any]] = [
    {
        "id": "documentary_realism",
        "label": "Documentary Realism",
        "description": "Grounded, realistic documentary visuals with natural light and real-world settings.",
        "style_tags": ["grounded_realism", "natural_light", "real_world_locations"],
        "negative_tags": ["no_fantasy", "no_surreal", "no_cartoonish"],
        "recommended_detail_level": "enhanced",
        "recommended_text_safety_mode": "strict_no_text",
    },
    {
        "id": "cinematic_story",
        "label": "Cinematic Story",
        "description": "Polished cinematic story frames with controlled drama and clear visual focus.",
        "style_tags": ["cinematic_framing", "controlled_contrast", "story_driven_composition"],
        "negative_tags": ["no_overbusy_background", "no_fake_text", "no_excessive_hdr"],
        "recommended_detail_level": "enhanced",
        "recommended_text_safety_mode": "strict_no_text",
    },
    {
        "id": "dark_mystery",
        "label": "Dark Mystery",
        "description": "Low-key mystery visuals with restrained tension and atmospheric but factual framing.",
        "style_tags": ["low_key_lighting", "muted_palette", "restrained_tension"],
        "negative_tags": ["no_gore", "no_horror_monster", "no_exaggerated_blood"],
        "recommended_detail_level": "deep",
        "recommended_text_safety_mode": "strict_no_text",
    },
    {
        "id": "clean_news_explainer",
        "label": "Clean News Explainer",
        "description": "Clear editorial visuals for explainers, with simple composition and overlay-friendly space.",
        "style_tags": ["clean_editorial", "balanced_composition", "overlay_friendly_space"],
        "negative_tags": ["no_fake_news_tabloid_aesthetic", "no_cluttered_frame", "no_legible_trademarks"],
        "recommended_detail_level": "enhanced",
        "recommended_text_safety_mode": "overlay_friendly",
    },
    {
        "id": "emotional_human_story",
        "label": "Emotional Human Story",
        "description": "Human-centered visuals with empathetic tone, natural environments, and restrained emotion.",
        "style_tags": ["human_centered", "natural_environment", "empathetic_tone"],
        "negative_tags": ["no_exploitative_emotion", "no_identifiable_real_person_likeness_claims", "no_gore"],
        "recommended_detail_level": "deep",
        "recommended_text_safety_mode": "strict_no_text",
    },
    {
        "id": "minimal_symbolic",
        "label": "Minimal Symbolic",
        "description": "Sparse symbolic visuals with simple objects, negative space, and reduced visual noise.",
        "style_tags": ["minimal_composition", "symbolic_visual", "negative_space"],
        "negative_tags": ["no_literal_internal_terms", "no_cluttered_frame", "no_readable_text"],
        "recommended_detail_level": "basic",
        "recommended_text_safety_mode": "overlay_friendly",
    },
]


_PROMPT_DETAIL_LEVELS: List[Dict[str, str]] = [
    {"id": "basic", "label": "Basic", "description": "Short, simple visual prompts with minimal enrichment."},
    {"id": "enhanced", "label": "Enhanced", "description": "Balanced prompt detail for concrete scenes and stable outputs."},
    {"id": "deep", "label": "Deep", "description": "Richer scene detail, style guidance, and risk-aware prompt structure."},
]


_PROVIDER_TARGETS: List[Dict[str, str]] = [
    {"id": "generic", "label": "Generic", "description": "Provider-neutral prompt preparation."},
    {"id": "openai_image", "label": "OpenAI Image", "description": "Prompt preparation for OpenAI image generation."},
    {"id": "runway", "label": "Runway", "description": "Prompt preparation for future Runway motion workflows."},
    {"id": "kling", "label": "Kling", "description": "Prompt preparation for future Kling motion workflows."},
]


_TEXT_SAFETY_MODES: List[Dict[str, str]] = [
    {"id": "normal", "label": "Normal", "description": "Standard visual text safety guidance."},
    {"id": "strict_no_text", "label": "Strict No Text", "description": "Strongly avoids generated readable text, logos, and typography."},
    {"id": "overlay_friendly", "label": "Overlay Friendly", "description": "Keeps clean negative space for later editorial overlays."},
]


_VISUAL_CONSISTENCY_MODES: List[Dict[str, str]] = [
    {"id": "one_style_per_video", "label": "One Style Per Video", "description": "Keeps one consistent style anchor across the video."},
    {"id": "scene_specific", "label": "Scene Specific", "description": "Allows style adjustments per scene while staying coherent."},
    {"id": "experimental", "label": "Experimental", "description": "Allows broader visual variation for exploration."},
]


_CONTROL_SPECS: Tuple[Tuple[str, str, List[Dict[str, Any]]], ...] = (
    ("visual_preset", "visual_presets", _VISUAL_PRESETS),
    ("prompt_detail_level", "prompt_detail_levels", _PROMPT_DETAIL_LEVELS),
    ("provider_target", "provider_targets", _PROVIDER_TARGETS),
    ("text_safety_mode", "text_safety_modes", _TEXT_SAFETY_MODES),
    ("visual_consistency_mode", "visual_consistency_modes", _VISUAL_CONSISTENCY_MODES),
)


def _valid_ids(entries: List[Dict[str, Any]]) -> set[str]:
    return {str(e.get("id") or "").strip() for e in entries if str(e.get("id") or "").strip()}


def get_visual_prompt_control_options() -> Dict[str, Any]:
    """Return UI/API-friendly visual prompt control options."""
    return {
        "defaults": deepcopy(VISUAL_PROMPT_CONTROL_DEFAULTS),
        "controls": {
            "visual_presets": deepcopy(_VISUAL_PRESETS),
            "prompt_detail_levels": deepcopy(_PROMPT_DETAIL_LEVELS),
            "provider_targets": deepcopy(_PROVIDER_TARGETS),
            "text_safety_modes": deepcopy(_TEXT_SAFETY_MODES),
            "visual_consistency_modes": deepcopy(_VISUAL_CONSISTENCY_MODES),
        },
    }


def normalize_visual_prompt_controls(raw: dict | None) -> Dict[str, Any]:
    """Normalize optional operator controls against the stable dropdown catalog."""
    data = raw if isinstance(raw, dict) else {}
    normalized: Dict[str, str] = {}
    warnings: List[str] = []

    for field_name, _control_name, entries in _CONTROL_SPECS:
        default = VISUAL_PROMPT_CONTROL_DEFAULTS[field_name]
        value = str(data.get(field_name) or "").strip()
        if not value:
            normalized[field_name] = default
            continue
        if value not in _valid_ids(entries):
            normalized[field_name] = default
            warnings.append(f"visual_prompt_control_unknown:{field_name}:{value}")
            continue
        normalized[field_name] = value

    return {"normalized": normalized, "warnings": warnings}
