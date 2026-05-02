"""BA 14.5 — Auto Recommendation Upgrade."""

from app.performance_feedback.auto_recommendation_upgrade import build_auto_recommendation_upgrade
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_auto_recommendation_upgrade_uses_performance_signals():
    plan = build_production_prompt_plan(
        PromptPlanRequest(
            topic="Polizei und Mord",
            kpi_source_type="manual",
            external_kpi_metrics={
                "views": 10000,
                "impressions": 120000,
                "ctr": 0.083,
                "avg_view_duration": 240,
                "watch_time": 40000,
                "subscribers_gained": 80,
                "revenue_optional": 42,
            },
        )
    )
    rec = plan.auto_recommendation_upgrade_result
    assert rec.recommendation_status in ("ready", "partial")
    assert rec.next_best_template
    assert rec.next_best_hook_strategy
    assert rec.confidence > 0


def test_auto_recommendation_upgrade_handles_missing_signals():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord"))
    rec = build_auto_recommendation_upgrade(plan.model_copy(update={"hook_performance_result": None, "template_evolution_result": None}))
    assert rec.recommendation_status == "insufficient_data"
    assert rec.confidence == 10
