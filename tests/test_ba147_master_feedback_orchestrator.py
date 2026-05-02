"""BA 14.7 — Master Feedback Orchestrator."""

from app.performance_feedback.master_feedback_orchestrator import build_master_feedback_orchestrator
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_master_feedback_orchestrator_builds_growth_note():
    plan = build_production_prompt_plan(
        PromptPlanRequest(
            topic="Polizei und Mord",
            kpi_source_type="manual",
            external_kpi_metrics={
                "views": 10000,
                "impressions": 120000,
                "ctr": 0.083,
                "avg_view_duration": 260,
                "watch_time": 43000,
                "subscribers_gained": 100,
                "revenue_optional": 50,
            },
        )
    )
    orch = plan.master_feedback_orchestrator_result
    assert orch.orchestrator_status in ("growth_ready", "learning")
    assert orch.scaling_score > 0
    assert orch.strategic_direction
    assert orch.final_growth_note


def test_master_feedback_orchestrator_needs_data_without_metrics():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord"))
    orch = build_master_feedback_orchestrator(plan)
    assert orch.orchestrator_status == "needs_data"
    assert orch.scaling_score == 0
