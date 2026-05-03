"""BA 17.0 — Viral Upgrade Layer (advisory, vor Production Assembly)."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import ChapterOutlineItem, ProductionPromptPlan, PromptPlanRequest
from app.viral_upgrade.layer import build_viral_upgrade_layer


def test_prompt_plan_includes_viral_upgrade_layer_result():
    plan = build_production_prompt_plan(
        PromptPlanRequest(topic="Allgemeines Video ohne Treffer", title="", source_summary="")
    )
    assert plan.viral_upgrade_layer_result is not None
    v = plan.viral_upgrade_layer_result
    assert v.advisory_only is True
    assert v.layer_version == "17.0-v1"
    assert len(v.viral_title_variants) == 3
    assert len(v.thumbnail_angle_variants) == 3
    assert 0 <= v.hook_intensity_score <= 100
    assert v.emotional_driver in (
        "curiosity",
        "urgency",
        "hope",
        "concern",
        "surprise",
        "neutral",
    )


def test_viral_upgrade_detects_sensational_caution():
    plan = ProductionPromptPlan(
        template_type="documentary",
        tone="neutral",
        hook="Schock: Das musst du jetzt sehen!",
        chapter_outline=[
            ChapterOutlineItem(title="Skandal in Zahlen", summary="Kurz."),
        ],
        scene_prompts=["Szene 1"],
        voice_style="",
        thumbnail_angle="Kontrast",
        warnings=[],
    )
    v = build_viral_upgrade_layer(plan)
    assert "sensational_language_detected" in v.caution_flags


def test_true_crime_title_third_variant_pattern():
    plan = ProductionPromptPlan(
        template_type="true_crime",
        tone="",
        hook="Ein Fall bleibt offen.",
        chapter_outline=[ChapterOutlineItem(title="Der Prozess", summary="Fakten.")],
        scene_prompts=["x"],
        voice_style="",
        thumbnail_angle="",
        warnings=[],
    )
    v = build_viral_upgrade_layer(plan)
    assert "Fakten" in v.viral_title_variants[2] or "fakten" in v.viral_title_variants[2].lower()
