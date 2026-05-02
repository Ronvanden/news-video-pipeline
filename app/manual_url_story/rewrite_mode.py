"""BA 15.6 — Rewrite-Presets: Mapping auf Video-Template und Prompt-Template-Keys."""

from __future__ import annotations

from typing import Dict

# Video-Template-IDs für build_script_response_from_extracted_text / Hook-Engine (story_engine STORY_TEMPLATE_IDS)
REWRITE_MODE_TO_VIDEO_TEMPLATE: Dict[str, str] = {
    "documentary": "history_deep_dive",
    "emotional": "true_crime",
    "mystery": "mystery_explainer",
    "viral": "generic",
}

# Keys unter app/templates/prompt_planning/*.json
REWRITE_MODE_TO_PROMPT_TEMPLATE: Dict[str, str] = {
    "documentary": "mystery_history",
    "emotional": "true_crime",
    "mystery": "mystery_history",
    "viral": "true_crime",
}

PROMPT_TEMPLATE_KEY_TO_VIDEO_TEMPLATE: Dict[str, str] = {
    "true_crime": "true_crime",
    "mystery_history": "mystery_explainer",
}


def normalize_rewrite_mode(raw: str | None) -> str:
    return (raw or "").strip().lower()


def tune_hook_for_rewrite_mode(hook: str, mode: str) -> str:
    """Leichte Längenkorrektur für viral — keine inhaltlichen Zusätze (Faktenrisiko)."""
    h = (hook or "").strip()
    m = normalize_rewrite_mode(mode)
    if m == "viral" and len(h) > 140:
        cut = h[:137].rsplit(" ", 1)[0]
        return cut + "…"
    return h


def resolve_video_template_for_manual_url_script(req: object) -> str:
    """
    Priorität: template_override (Prompt-Key) → Video-ID gemappt;
    dann manual_url_rewrite_mode → Preset-Video;
    sonst manual_url_video_template.
    """
    o = getattr(req, "template_override", None)
    key = (o or "").strip()
    if key:
        return PROMPT_TEMPLATE_KEY_TO_VIDEO_TEMPLATE.get(key, key)
    mode = normalize_rewrite_mode(getattr(req, "manual_url_rewrite_mode", "") or "")
    if mode:
        return REWRITE_MODE_TO_VIDEO_TEMPLATE.get(
            mode,
            getattr(req, "manual_url_video_template", None) or "generic",
        )
    return getattr(req, "manual_url_video_template", None) or "generic"


def prompt_template_for_rewrite_mode(mode: str, templates: dict) -> str | None:
    """Prompt-Template-Key aus Modus, nur wenn Key geladen existiert."""
    m = normalize_rewrite_mode(mode)
    if not m:
        return None
    k = REWRITE_MODE_TO_PROMPT_TEMPLATE.get(m)
    if k and k in templates:
        return k
    return None
