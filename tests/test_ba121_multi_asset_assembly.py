"""BA 12.1 — Multi-Asset Assembly."""

from app.production_assembly.multi_asset_assembly import build_multi_asset_assembly
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_asset_coverage_complete_for_default_plan():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    assembly = plan.multi_asset_assembly_result
    assert assembly is not None
    assert assembly.assembly_status == "complete"
    assert assembly.coverage_score == 100
    assert assembly.image_assets
    assert assembly.voice_assets


def test_asset_coverage_partial_when_manifest_partial():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    partial_manifest = plan.master_asset_manifest_result.model_copy(
        update={
            "assets": [a for a in plan.master_asset_manifest_result.assets if a.asset_type == "image"],
            "missing_asset_types": ["video", "audio", "thumbnail", "render"],
            "manifest_status": "partial",
            "total_assets": 1,
        }
    )
    assembly = build_multi_asset_assembly(plan.model_copy(update={"master_asset_manifest_result": partial_manifest}))
    assert assembly.assembly_status == "partial"
    assert assembly.coverage_score == 20
