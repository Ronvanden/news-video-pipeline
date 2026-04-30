"""BA 9.x — Video-Template / Story Engine (Skript-JSON-Vertrag unverändert)."""

from app.story_engine.conformance import (
    conformance_warnings_for_template,
    template_conformance_warning,
)
from app.story_engine.hook_engine import (
    HookEngineResult,
    generate_hook_v1,
    hook_meta_for_persist,
    infer_hook_type_from_blob,
)
from app.story_engine.templates import (
    STORY_TEMPLATE_IDS,
    chapter_band_for_template_duration,
    chapter_title_style_hint_de,
    min_hook_words_for_template,
    normalize_story_template_id,
    public_story_template_catalog,
    story_template_blueprint_prompt_de,
    story_template_prompt_addon_de,
    style_profile_for_template,
    voice_profile_for_template,
)

__all__ = [
    "STORY_TEMPLATE_IDS",
    "HookEngineResult",
    "chapter_band_for_template_duration",
    "chapter_title_style_hint_de",
    "conformance_warnings_for_template",
    "generate_hook_v1",
    "hook_meta_for_persist",
    "infer_hook_type_from_blob",
    "min_hook_words_for_template",
    "normalize_story_template_id",
    "public_story_template_catalog",
    "story_template_blueprint_prompt_de",
    "story_template_prompt_addon_de",
    "style_profile_for_template",
    "template_conformance_warning",
    "voice_profile_for_template",
]
