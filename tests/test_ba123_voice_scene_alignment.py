"""BA 12.3 — Voice / Scene Alignment."""

from app.production_assembly.timeline_finalizer import build_final_timeline
from app.production_assembly.voice_scene_alignment import build_voice_scene_alignment
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_voice_alignment_complete_when_narration_linked():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    alignment = plan.voice_scene_alignment_result
    assert alignment is not None
    assert alignment.alignment_status == "complete"
    assert not alignment.missing_voice_scenes
    assert alignment.aligned_scenes


def test_voice_alignment_detects_missing_voice_scenes():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    no_audio_manifest = plan.master_asset_manifest_result.model_copy(
        update={
            "assets": [a for a in plan.master_asset_manifest_result.assets if a.asset_type != "audio"],
            "missing_asset_types": ["audio"],
            "manifest_status": "partial",
        }
    )
    final = build_final_timeline(plan.model_copy(update={"master_asset_manifest_result": no_audio_manifest}))
    alignment = build_voice_scene_alignment(plan.model_copy(update={"final_timeline_result": final}))
    assert alignment.alignment_status == "partial"
    assert alignment.missing_voice_scenes
    assert alignment.recommendations
