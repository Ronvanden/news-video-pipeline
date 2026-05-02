"""BA 14.7 — Master Feedback Orchestrator."""

from __future__ import annotations

from app.performance_feedback.schema import MasterFeedbackOrchestratorResult


def build_master_feedback_orchestrator(plan: object) -> MasterFeedbackOrchestratorResult:
    norm = getattr(plan, "kpi_normalization_result", None)
    hook = getattr(plan, "hook_performance_result", None)
    template = getattr(plan, "template_evolution_result", None)
    growth = getattr(plan, "founder_growth_intelligence_result", None)
    cost = getattr(plan, "cost_revenue_analysis_result", None)

    if norm is None or norm.normalized_status == "insufficient_data":
        return MasterFeedbackOrchestratorResult(
            orchestrator_status="needs_data",
            production_vs_market_fit="unknown_without_kpis",
            hook_vs_market_fit="unknown_without_ctr",
            template_vs_market_fit="unknown_without_outcome",
            scaling_score=0,
            strategic_direction="collect_kpis_first",
            final_growth_note="Performance loop initialized; import KPIs after publication.",
        )

    hook_score = getattr(hook, "hook_effectiveness_score", 0) if hook else 0
    template_score = getattr(template, "template_real_world_score", 0) if template else 0
    roi_bonus = 10 if cost and cost.analysis_status in ("profitable", "break_even") else 0
    scaling_score = max(0, min(100, int(round((hook_score * 0.35) + (template_score * 0.45) + (norm.normalized_retention * 100 * 0.2) + roi_bonus))))

    if scaling_score >= 75:
        status = "growth_ready"
        direction = "scale_similar_topics_with_same_template"
    elif scaling_score >= 40:
        status = "learning"
        direction = "iterate_hook_thumbnail_and_template_before_scaling"
    else:
        status = "learning"
        direction = "rework_packaging_and_retention_strategy"

    return MasterFeedbackOrchestratorResult(
        orchestrator_status=status,
        production_vs_market_fit=f"retention={norm.normalized_retention:.2%}; rpm={norm.normalized_rpm:.2f}",
        hook_vs_market_fit=getattr(hook, "hook_ctr_alignment", "") if hook else "hook_not_evaluated",
        template_vs_market_fit=getattr(template, "template_scalability", "") if template else "template_not_evaluated",
        scaling_score=scaling_score,
        strategic_direction=direction,
        final_growth_note=getattr(growth, "growth_summary", "") if growth else "Growth intelligence pending.",
    )
