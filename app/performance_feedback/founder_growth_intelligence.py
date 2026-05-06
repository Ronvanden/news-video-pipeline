"""BA 14.6 — Founder Growth Intelligence."""

from __future__ import annotations

from app.performance_feedback.schema import FounderGrowthIntelligenceResult


def build_founder_growth_intelligence(plan: object) -> FounderGrowthIntelligenceResult:
    norm = getattr(plan, "kpi_normalization_result", None)
    hook = getattr(plan, "hook_performance_result", None)
    template = getattr(plan, "template_evolution_result", None)
    rec = getattr(plan, "auto_recommendation_upgrade_result", None)
    cost = getattr(plan, "cost_revenue_analysis_result", None)

    if norm is None or norm.normalized_status == "insufficient_data":
        return FounderGrowthIntelligenceResult(
            intelligence_status="needs_data",
            growth_summary="No reliable KPI baseline yet.",
            scaling_opportunities=["Import manual or CSV KPIs after publication."],
            major_risks=["decisions_without_performance_data"],
            content_strategy_shift="wait_for_kpi_baseline",
            founder_actions=["Collect views, impressions, CTR, retention and revenue if available."],
        )

    opportunities = []
    risks = []
    if norm.normalized_ctr >= 0.06:
        opportunities.append("scale_topic_packaging")
    else:
        risks.append("low_click_through")
    if norm.normalized_retention >= 0.35:
        opportunities.append("reuse_story_structure")
    else:
        risks.append("retention_needs_work")
    if cost and cost.analysis_status == "loss":
        risks.append("unit_economics_negative")

    confidence = getattr(rec, "confidence", 0) if rec else 0
    status = "growth_ready" if confidence >= 70 and not risks else "watch"
    strategy = "double_down_on_current_template" if status == "growth_ready" else "iterate_packaging_before_scaling"

    return FounderGrowthIntelligenceResult(
        intelligence_status=status,
        growth_summary=f"CTR {norm.normalized_ctr:.2%}, retention {norm.normalized_retention:.2%}, growth {norm.normalized_growth:.4f}.",
        scaling_opportunities=opportunities or ["controlled_follow_up_test"],
        major_risks=risks,
        content_strategy_shift=strategy,
        founder_actions=[
            "Review hook and thumbnail learnings before next production.",
            "Compare this result against future template cohorts.",
            "Do not automate monetization decisions from V1 signals.",
        ],
    )
