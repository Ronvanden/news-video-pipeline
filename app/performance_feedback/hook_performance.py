"""BA 14.2 — Hook Performance Analyzer."""

from __future__ import annotations

from app.performance_feedback.schema import HookPerformanceResult, KpiNormalizationResult


def analyze_hook_performance(plan: object, normalized_metrics: KpiNormalizationResult) -> HookPerformanceResult:
    strengths: list[str] = []
    weaknesses: list[str] = []
    recommendations: list[str] = []
    hook_score = float(getattr(plan, "hook_score", 0.0) or 0.0)
    ctr = normalized_metrics.normalized_ctr
    ctr_score = min(100, int(round(ctr * 1000)))
    hook_component = min(100, int(round(hook_score * 10)))
    effectiveness = int(round((ctr_score * 0.65) + (hook_component * 0.35)))

    if normalized_metrics.normalized_status == "insufficient_data":
        return HookPerformanceResult(
            hook_performance_status="insufficient_data",
            hook_effectiveness_score=0,
            hook_ctr_alignment="no_kpi_data",
            recommendations=["Import CTR and retention before judging hook performance."],
        )

    if ctr >= 0.08:
        strengths.append("ctr_strong")
    elif ctr >= 0.04:
        strengths.append("ctr_acceptable")
    else:
        weaknesses.append("ctr_low")
        recommendations.append("Test a sharper curiosity gap in the opening line and thumbnail text.")

    if hook_score >= 7.0 and ctr < 0.04:
        alignment = "creative_hook_not_translating_to_clicks"
        recommendations.append("Rework title/thumbnail packaging before changing the story template.")
    elif hook_score < 5.0 and ctr >= 0.06:
        alignment = "market_interest_exceeds_hook_score"
        strengths.append("topic_market_pull")
    else:
        alignment = "hook_and_ctr_reasonably_aligned"

    if effectiveness >= 75:
        status = "strong"
    elif effectiveness >= 45:
        status = "mixed"
    else:
        status = "weak"

    return HookPerformanceResult(
        hook_performance_status=status,
        hook_effectiveness_score=effectiveness,
        hook_ctr_alignment=alignment,
        strengths=list(dict.fromkeys(strengths)),
        weaknesses=list(dict.fromkeys(weaknesses)),
        recommendations=list(dict.fromkeys(recommendations)),
    )
