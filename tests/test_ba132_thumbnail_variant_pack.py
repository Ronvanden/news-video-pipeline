"""BA 13.2 — Thumbnail Variant Pack."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest
from app.publishing.thumbnail_variant_pack import build_thumbnail_variant_pack


def test_thumbnail_variant_pack_has_core_angles():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    pack = plan.thumbnail_variant_pack_result
    assert pack is not None
    assert pack.variant_status == "complete"
    assert len(pack.variants) == 4
    assert pack.recommended_primary
    assert {"curiosity", "urgency", "authority", "emotional"} <= {v.emotional_trigger for v in pack.variants}


def test_thumbnail_variant_warns_without_base_angle():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    pack = build_thumbnail_variant_pack(plan.model_copy(update={"thumbnail_angle": ""}))
    assert pack.variants
    assert "thumbnail_angle_missing_using_generic_variants" in pack.warnings
