"""BA 14.2 — Hook Performance."""

from app.performance_feedback.hook_performance import analyze_hook_performance
from app.performance_feedback.kpi_normalization import normalize_kpi_metrics
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_hook_performance_detects_strong_ctr():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord"))
    metrics = normalize_kpi_metrics({"views": 8000, "impressions": 90000, "ctr": 0.09, "avg_view_duration": 220})
    res = analyze_hook_performance(plan, metrics)
    assert res.hook_performance_status in ("strong", "mixed")
    assert res.hook_effectiveness_score > 0
    assert "ctr_strong" in res.strengths


def test_hook_performance_requires_kpis():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord"))
    res = analyze_hook_performance(plan, normalize_kpi_metrics({}))
    assert res.hook_performance_status == "insufficient_data"
    assert res.recommendations
