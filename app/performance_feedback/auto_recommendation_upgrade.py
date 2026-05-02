"""BA 14.5 — Auto Recommendation Upgrade."""

from __future__ import annotations

from app.performance_feedback.schema import AutoRecommendationUpgradeResult


def build_auto_recommendation_upgrade(plan: object) -> AutoRecommendationUpgradeResult:
    hook = getattr(plan, "hook_performance_result", None)
    template = getattr(plan, "template_evolution_result", None)
    cost = getattr(plan, "cost_revenue_analysis_result", None)
    publishing = getattr(plan, "publishing_readiness_gate_result", None)

    if hook is None or template is None:
        return AutoRecommendationUpgradeResult(
            recommendation_status="insufficient_data",
            next_best_template=getattr(plan, "template_type", "") or "generic",
            next_best_hook_strategy="import_performance_metrics_first",
            provider_adjustment="keep_current_until_metrics_available",
            publishing_adjustment="hold_major_changes",
            confidence=10,
        )

    next_template = getattr(plan, "template_type", "") or "generic"
    if template.template_evolution_status == "scalable":
        hook_strategy = "reuse_hook_pattern_with_new_angle"
        confidence = 80
    elif hook.hook_performance_status == "weak":
        hook_strategy = "test_stronger_curiosity_gap_and_title_thumbnail_fit"
        confidence = 55
    else:
        hook_strategy = "iterate_hook_opening_and_retention_pacing"
        confidence = 65

    provider_adjustment = "keep_provider_mix"
    if cost and cost.analysis_status == "loss":
        provider_adjustment = "reduce_cost_or_use_lower_cost_provider_path"
        confidence = min(confidence, 60)

    publishing_adjustment = "keep_scheduled_mode"
    if publishing and publishing.publishing_status != "ready_to_publish":
        publishing_adjustment = "resolve_review_warnings_before_next_release"
        confidence = min(confidence, 55)

    status = "ready" if confidence >= 70 else "partial"

    return AutoRecommendationUpgradeResult(
        recommendation_status=status,
        next_best_template=next_template,
        next_best_hook_strategy=hook_strategy,
        provider_adjustment=provider_adjustment,
        publishing_adjustment=publishing_adjustment,
        confidence=confidence,
    )
