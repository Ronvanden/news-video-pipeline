"""BA 10.10 — Production run summary."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_run_summary_present_and_launch_field():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    s = plan.production_run_summary_result
    assert s is not None
    assert s.launch_recommendation in ("hold", "dry_run_execute", "guarded_live_candidate")
    assert s.founder_summary
    assert s.projected_jobs >= 0
