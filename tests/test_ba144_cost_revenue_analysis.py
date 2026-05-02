"""BA 14.4 — Cost vs Revenue."""

from app.performance_feedback.cost_revenue_analysis import build_cost_revenue_analysis
from app.performance_feedback.kpi_normalization import normalize_kpi_metrics
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_cost_revenue_analysis_computes_roi():
    plan = build_production_prompt_plan(
        PromptPlanRequest(
            topic="Polizei und Mord",
            kpi_source_type="manual",
            external_kpi_metrics={
                "views": 10000,
                "impressions": 120000,
                "ctr": 0.08,
                "avg_view_duration": 240,
                "watch_time": 40000,
                "subscribers_gained": 80,
                "revenue_optional": 1000,
            },
        )
    )
    res = plan.cost_revenue_analysis_result
    assert res.analysis_status in ("profitable", "break_even", "loss")
    assert res.production_cost >= 0
    assert res.revenue == 1000
    assert res.roi is not None or res.production_cost == 0


def test_cost_revenue_analysis_warns_without_revenue():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord"))
    res = build_cost_revenue_analysis(plan, normalize_kpi_metrics({}))
    assert "revenue_missing_or_zero" in res.warnings
