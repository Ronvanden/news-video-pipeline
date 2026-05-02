"""BA 14.3 — Template Evolution."""

from app.performance_feedback.kpi_normalization import normalize_kpi_metrics
from app.performance_feedback.template_evolution import build_template_evolution
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_template_evolution_scores_real_world_fit():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord"))
    metrics = normalize_kpi_metrics({"views": 10000, "impressions": 100000, "ctr": 0.08, "avg_view_duration": 260, "subscribers_gained": 80})
    res = build_template_evolution(plan, metrics)
    assert res.template_evolution_status in ("scalable", "promising", "needs_iteration")
    assert res.template_real_world_score > 0
    assert plan.template_type in res.best_use_cases


def test_template_evolution_handles_missing_data():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord"))
    res = build_template_evolution(plan, normalize_kpi_metrics({}))
    assert res.template_evolution_status == "insufficient_data"
    assert res.optimization_notes
