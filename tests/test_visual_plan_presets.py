from app.visual_plan.presets import (
    VISUAL_PROMPT_CONTROL_DEFAULTS,
    get_visual_prompt_control_options,
    normalize_visual_prompt_controls,
)


EXPECTED_DEFAULTS = {
    "visual_preset": "documentary_realism",
    "prompt_detail_level": "enhanced",
    "provider_target": "generic",
    "text_safety_mode": "strict_no_text",
    "visual_consistency_mode": "one_style_per_video",
}


def _ids(entries):
    return {entry["id"] for entry in entries}


def test_visual_prompt_control_defaults_are_exact():
    assert VISUAL_PROMPT_CONTROL_DEFAULTS == EXPECTED_DEFAULTS


def test_visual_prompt_control_options_include_required_dropdown_values():
    controls = get_visual_prompt_control_options()["controls"]
    assert _ids(controls["visual_presets"]) == {
        "documentary_realism",
        "cinematic_story",
        "dark_mystery",
        "clean_news_explainer",
        "emotional_human_story",
        "minimal_symbolic",
    }
    assert _ids(controls["prompt_detail_levels"]) == {"basic", "enhanced", "deep"}
    assert _ids(controls["provider_targets"]) == {"generic", "openai_image", "runway", "kling"}
    assert _ids(controls["text_safety_modes"]) == {"normal", "strict_no_text", "overlay_friendly"}
    assert _ids(controls["visual_consistency_modes"]) == {
        "one_style_per_video",
        "scene_specific",
        "experimental",
    }


def test_visual_presets_have_minimum_dashboard_fields():
    presets = get_visual_prompt_control_options()["controls"]["visual_presets"]
    for preset in presets:
        assert preset["id"]
        assert preset["label"]
        assert preset["description"]
        assert isinstance(preset.get("style_tags"), list)
        assert isinstance(preset.get("negative_tags"), list)
        assert preset.get("recommended_detail_level")
        assert preset.get("recommended_text_safety_mode")


def test_missing_visual_prompt_controls_fall_back_to_defaults():
    result = normalize_visual_prompt_controls({"visual_preset": "dark_mystery"})
    assert result["normalized"] == {
        **EXPECTED_DEFAULTS,
        "visual_preset": "dark_mystery",
    }
    assert result["warnings"] == []

    none_result = normalize_visual_prompt_controls(None)
    assert none_result["normalized"] == EXPECTED_DEFAULTS
    assert none_result["warnings"] == []


def test_unknown_visual_prompt_controls_fall_back_and_warn():
    result = normalize_visual_prompt_controls(
        {
            "visual_preset": "literal_hook_art",
            "prompt_detail_level": "maximum",
            "provider_target": "openai_image",
            "text_safety_mode": "strict_no_text",
            "visual_consistency_mode": "wild",
        }
    )
    assert result["normalized"] == {
        **EXPECTED_DEFAULTS,
        "provider_target": "openai_image",
        "text_safety_mode": "strict_no_text",
    }
    assert "visual_prompt_control_unknown:visual_preset:literal_hook_art" in result["warnings"]
    assert "visual_prompt_control_unknown:prompt_detail_level:maximum" in result["warnings"]
    assert "visual_prompt_control_unknown:visual_consistency_mode:wild" in result["warnings"]


def test_get_visual_prompt_control_options_returns_stable_structure():
    options = get_visual_prompt_control_options()
    assert set(options.keys()) == {"defaults", "controls"}
    assert options["defaults"] == EXPECTED_DEFAULTS
    assert set(options["controls"].keys()) == {
        "visual_presets",
        "prompt_detail_levels",
        "provider_targets",
        "text_safety_modes",
        "visual_consistency_modes",
    }
