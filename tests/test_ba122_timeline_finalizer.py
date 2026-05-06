"""BA 12.2 — Timeline Finalizer."""

from app.production_assembly.timeline_finalizer import build_final_timeline
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_final_timeline_links_assets_and_duration():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    final = plan.final_timeline_result
    assert final is not None
    assert final.timeline_status == "complete"
    assert final.final_duration_seconds == plan.production_timeline_result.total_estimated_duration_seconds
    assert final.scenes
    assert all(scene.linked_assets for scene in final.scenes)
    assert all(scene.narration_asset for scene in final.scenes)


def test_final_timeline_partial_without_audio():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    no_audio_manifest = plan.master_asset_manifest_result.model_copy(
        update={
            "assets": [a for a in plan.master_asset_manifest_result.assets if a.asset_type != "audio"],
            "missing_asset_types": ["audio"],
            "manifest_status": "partial",
        }
    )
    final = build_final_timeline(plan.model_copy(update={"master_asset_manifest_result": no_audio_manifest}))
    assert final.timeline_status == "partial"
    assert any(scene.narration_asset is None for scene in final.scenes)
