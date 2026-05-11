from app.visual_plan.engine_v1 import VisualPromptEngineContext, build_visual_prompt_v1
from app.visual_plan.presets import VISUAL_PROMPT_CONTROL_DEFAULTS


def test_hook_title_is_sanitized_in_visual_prompts():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Hook",
            narration="A quiet opening line introduces the investigation without showing text.",
            beat_role="opening hook",
        )
    )
    prompt_blob = f"{result.visual_prompt_raw}\n{result.visual_prompt_effective}"
    assert "Hook" not in prompt_blob
    assert "hook" not in prompt_blob.lower()
    assert "cinematic opening beat" in result.visual_prompt_raw
    assert "internal_term_sanitized:hook" in result.visual_policy_warnings
    anatomy = result.visual_prompt_anatomy
    assert anatomy["subject_description"] == "cinematic opening beat"
    assert "Hook" not in anatomy["subject_description"]
    assert "internal_term_sanitized:hook" in anatomy["sanitized_terms"]


def test_hook_negative_prompt_contains_fishing_hook_guard():
    result = build_visual_prompt_v1(VisualPromptEngineContext(scene_title="Aufhänger", narration="Intro."))
    neg = result.negative_prompt.lower()
    assert "no fishing hook" in neg
    assert "no metal hook" in neg
    assert "no literal hook object" in neg
    assert "no hook-shaped object" in neg
    constraints = [x.lower() for x in result.visual_prompt_anatomy["negative_constraints"]]
    assert "no fishing hook" in constraints
    assert "no literal hook object" in constraints


def test_normalized_controls_use_defaults_when_unset():
    result = build_visual_prompt_v1(VisualPromptEngineContext(scene_title="Scene One", narration="A city at dawn."))
    assert result.normalized_controls == VISUAL_PROMPT_CONTROL_DEFAULTS
    assert result.visual_style_profile == "documentary_realism"


def test_visual_prompt_anatomy_contains_core_fields():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Chapter One",
            narration="A grounded documentary scene follows workers entering a public building at sunrise.",
        )
    )
    anatomy = result.visual_prompt_anatomy
    assert anatomy["subject_description"] == "Chapter One"
    assert anatomy["environment"]
    assert anatomy["camera"]
    assert anatomy["lighting"]
    assert anatomy["composition"]
    assert anatomy["source_summary"]
    assert "grounded_realism" in anatomy["style_tags"]


def test_unknown_controls_warn_and_fall_back_to_defaults():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Scene One",
            narration="A city at dawn.",
            visual_preset="unknown_style",
            prompt_detail_level="maximum",
            provider_target="openai_image",
        )
    )
    assert result.normalized_controls["visual_preset"] == "documentary_realism"
    assert result.normalized_controls["prompt_detail_level"] == "enhanced"
    assert result.normalized_controls["provider_target"] == "openai_image"
    assert "visual_prompt_control_unknown:visual_preset:unknown_style" in result.visual_policy_warnings
    assert "visual_prompt_control_unknown:prompt_detail_level:maximum" in result.visual_policy_warnings


def test_visual_prompt_effective_contains_no_text_guard():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(scene_title="Documents", narration="Files are reviewed on a desk.")
    )
    assert "[visual_no_text_guard_v26_4]" in result.visual_prompt_effective
    assert "No readable text" in result.visual_prompt_effective


def test_strict_no_text_sets_anatomy_text_safety_and_composition():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(scene_title="Documents", narration="Files are reviewed on a desk.")
    )
    anatomy = result.visual_prompt_anatomy
    assert "no readable text" in anatomy["text_safety"]
    assert "no generated text" in anatomy["composition"]


def test_overlay_friendly_sets_anatomy_overlay_space():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Explainer",
            narration="A clear explainer scene.",
            text_safety_mode="overlay_friendly",
        )
    )
    anatomy = result.visual_prompt_anatomy
    assert "overlay" in anatomy["text_safety"]
    assert "clean negative space" in anatomy["composition"]


def test_sparse_narration_sets_risk_flag_without_crash():
    result = build_visual_prompt_v1(VisualPromptEngineContext(scene_title="Scene One"))
    assert result.visual_prompt_raw
    assert result.visual_prompt_effective
    assert "sparse_narration" in result.prompt_risk_flags


def test_prompt_quality_score_is_present_and_bounded():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Chapter One",
            narration="A grounded documentary scene follows workers entering a public building at sunrise.",
        )
    )
    assert isinstance(result.prompt_quality_score, int)
    assert 0 <= result.prompt_quality_score <= 100
