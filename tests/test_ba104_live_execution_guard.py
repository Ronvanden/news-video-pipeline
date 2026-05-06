"""BA 10.4 — Live execution guard."""

from app.production_connectors.live_execution_guard import evaluate_live_execution_guard
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_pipeline_guard_default_dry_run_only():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    g = plan.live_execution_guard_result
    assert g is not None
    assert g.live_execution_status in ("dry_run_only", "blocked", "policy_review")
    assert g.live_execution_allowed is False


def test_guard_has_required_conditions_list():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    g = plan.live_execution_guard_result
    assert any("kill_switch" in x for x in g.required_conditions)
