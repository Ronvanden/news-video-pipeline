"""BA 12.4 — Render Instruction Package."""

from app.production_assembly.render_instruction_package import build_render_instruction_package
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_render_package_complete_for_default_assembled_plan():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    render = plan.render_instruction_package_result
    assert render is not None
    assert render.render_instruction_version == "12.4-v1"
    assert render.render_status == "complete"
    assert len(render.scene_render_map) == len(plan.final_timeline_result.scenes)
    assert len(render.voice_track_map) == len(plan.final_timeline_result.scenes)
    assert render.thumbnail_target


def test_render_package_partial_when_voice_missing():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    no_voice_timeline = plan.final_timeline_result.model_copy(
        update={
            "timeline_status": "partial",
            "scenes": [s.model_copy(update={"narration_asset": None}) for s in plan.final_timeline_result.scenes],
        }
    )
    render = build_render_instruction_package(plan.model_copy(update={"final_timeline_result": no_voice_timeline}))
    assert render.render_status == "partial"
    assert any("voice_track" in w for w in render.warnings)
