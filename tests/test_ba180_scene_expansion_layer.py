"""BA 18.0 — Multi-Scene Asset Expansion (2–3 Beats pro Kapitel, plan-only)."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import ChapterOutlineItem, ProductionPromptPlan, PromptPlanRequest
from app.scene_expansion.layer import build_scene_expansion_layer


def test_prompt_plan_has_scene_expansion_result():
    plan = build_production_prompt_plan(
        PromptPlanRequest(topic="Polizei und Mord", title="", source_summary="")
    )
    assert plan.scene_expansion_result is not None
    r = plan.scene_expansion_result
    assert r.plan_only is True
    assert r.layer_version == "18.0-v1"
    assert len(r.expanded_scene_assets) >= 2
    first = r.expanded_scene_assets[0]
    assert first.chapter_index == 0
    assert first.beat_index == 0
    assert first.visual_prompt
    assert first.visual_prompt_raw
    assert first.visual_prompt_effective
    assert first.negative_prompt
    assert "[visual_no_text_guard_v26_4]" in first.visual_prompt_effective
    assert first.visual_prompt == first.visual_prompt_effective
    assert first.visual_style_profile == "documentary_realism"
    assert isinstance(first.prompt_quality_score, int)
    assert isinstance(first.prompt_risk_flags, list)
    assert isinstance(first.normalized_controls, dict)
    assert first.camera_motion_hint
    assert first.duration_seconds >= 1
    assert first.asset_type in ("image", "broll", "establishing", "detail")
    assert isinstance(first.safety_notes, list)


def test_two_beats_for_short_scene_text():
    plan = ProductionPromptPlan(
        template_type="documentary",
        tone="",
        hook="Kurz.",
        chapter_outline=[
            ChapterOutlineItem(title="A", summary="x"),
            ChapterOutlineItem(title="B", summary="y"),
        ],
        scene_prompts=["short", "tiny"],
        voice_style="",
        thumbnail_angle="",
        warnings=[],
    )
    r = build_scene_expansion_layer(plan)
    assert len(r.expanded_scene_assets) == 4
    for a in r.expanded_scene_assets:
        assert a.beat_index in (0, 1)


def test_three_beats_for_long_scene_text():
    long_scene = "word " * 40
    plan = ProductionPromptPlan(
        template_type="documentary",
        tone="",
        hook="H",
        chapter_outline=[ChapterOutlineItem(title="Titel", summary="Sum")],
        scene_prompts=[long_scene],
        voice_style="",
        thumbnail_angle="",
        warnings=[],
    )
    r = build_scene_expansion_layer(plan)
    assert len(r.expanded_scene_assets) == 3
    types = {x.asset_type for x in r.expanded_scene_assets}
    assert "establishing" in types


def test_internal_hook_title_is_sanitized_in_scene_expansion_visual_fields():
    plan = ProductionPromptPlan(
        template_type="documentary",
        tone="",
        hook="H",
        chapter_outline=[ChapterOutlineItem(title="Hook", summary="A tense opening beat introduces the story.")],
        scene_prompts=[],
        voice_style="",
        thumbnail_angle="",
        warnings=[],
    )
    r = build_scene_expansion_layer(plan)
    first = r.expanded_scene_assets[0]
    prompt_blob = "\n".join([first.visual_prompt, first.visual_prompt_raw, first.visual_prompt_effective])
    assert "Hook" not in prompt_blob
    assert "cinematic opening beat" in prompt_blob
    assert "no fishing hook" in first.negative_prompt.lower()
    assert "no literal hook object" in first.negative_prompt.lower()
    assert "internal_term_sanitized:hook" in first.visual_policy_warnings
    assert "[visual_no_text_guard_v26_4]" in first.visual_prompt_effective
