"""BA 14.6 — Founder Growth Intelligence."""

from app.performance_feedback.founder_growth_intelligence import build_founder_growth_intelligence
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_founder_growth_intelligence_summarizes_growth():
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
    intel = plan.founder_growth_intelligence_result
    assert intel.intelligence_status in ("growth_ready", "watch")
    assert intel.growth_summary
    assert intel.founder_actions


def test_founder_growth_intelligence_needs_data_without_kpis():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord"))
    intel = build_founder_growth_intelligence(plan)
    assert intel.intelligence_status == "needs_data"
    assert intel.major_risks
