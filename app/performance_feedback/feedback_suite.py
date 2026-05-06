"""BA 14.0–14.7 — Performance Feedback Loop Suite."""

from __future__ import annotations

from app.performance_feedback.auto_recommendation_upgrade import build_auto_recommendation_upgrade
from app.performance_feedback.cost_revenue_analysis import build_cost_revenue_analysis
from app.performance_feedback.founder_growth_intelligence import build_founder_growth_intelligence
from app.performance_feedback.hook_performance import analyze_hook_performance
from app.performance_feedback.kpi_ingest_contract import build_kpi_ingest_contract
from app.performance_feedback.kpi_normalization import normalize_kpi_metrics
from app.performance_feedback.master_feedback_orchestrator import build_master_feedback_orchestrator
from app.performance_feedback.template_evolution import build_template_evolution


def apply_performance_feedback_suite(plan: object) -> object:
    """KPI ingest → normalization → analysis → recommendations → growth summary."""
    ingest = build_kpi_ingest_contract(plan)
    p = plan.model_copy(update={"kpi_ingest_contract_result": ingest})
    norm = normalize_kpi_metrics(ingest.imported_metrics)
    p = p.model_copy(update={"kpi_normalization_result": norm})
    p = p.model_copy(update={"hook_performance_result": analyze_hook_performance(p, norm)})
    p = p.model_copy(update={"template_evolution_result": build_template_evolution(p, norm)})
    p = p.model_copy(update={"cost_revenue_analysis_result": build_cost_revenue_analysis(p, norm)})
    p = p.model_copy(update={"auto_recommendation_upgrade_result": build_auto_recommendation_upgrade(p)})
    p = p.model_copy(update={"founder_growth_intelligence_result": build_founder_growth_intelligence(p)})
    p = p.model_copy(update={"master_feedback_orchestrator_result": build_master_feedback_orchestrator(p)})
    return p
