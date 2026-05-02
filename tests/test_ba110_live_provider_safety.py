"""BA 11.0 — Live Provider Safety."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest
from app.production_connectors.live_provider_safety import evaluate_live_provider_safety


def test_default_plan_is_dry_run_only_not_live_allowed():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    s = evaluate_live_provider_safety(plan)
    assert s.live_provider_allowed is False
    assert not s.approved_providers
    assert s.live_provider_mode in ("dry_run_only", "blocked")


def test_blocked_when_live_execution_guard_blocked():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    g = plan.live_execution_guard_result
    assert g is not None
    blocked_guard = g.model_copy(update={"live_execution_status": "blocked", "blockers": ["x"]})
    p2 = plan.model_copy(update={"live_execution_guard_result": blocked_guard})
    s = evaluate_live_provider_safety(p2)
    assert s.live_provider_mode == "blocked"
    assert "live_execution_guard_blocked" in s.violations
