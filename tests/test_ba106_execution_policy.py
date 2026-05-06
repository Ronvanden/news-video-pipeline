"""BA 10.6 — Execution policy / kill switch."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_kill_switch_active_by_default():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    pol = plan.execution_policy_result
    assert pol is not None
    assert pol.kill_switch_active is True
    assert pol.global_execution_mode in ("dry_run_only", "emergency_stop", "guarded_live")
