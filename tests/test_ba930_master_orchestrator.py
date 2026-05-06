"""BA 9.30 — Story-to-Production Master Orchestrator V1."""

from app.prompt_engine.master_orchestrator import build_master_orchestration_summary
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_master_summary_end_to_end_fields():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    m = build_master_orchestration_summary(plan)
    assert m.story_input_summary
    assert m.prompt_planning_summary
    assert m.production_summary
    assert m.provider_summary
    assert m.risk_summary
    assert m.launch_recommendation in ("proceed", "revise", "hold")
    assert m.final_founder_note
    assert m.orchestration_status in ("ready", "review", "blocked")
