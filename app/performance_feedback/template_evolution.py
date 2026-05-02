"""BA 14.3 — Template Performance Evolution."""

from __future__ import annotations

from app.performance_feedback.schema import KpiNormalizationResult, TemplateEvolutionResult


def build_template_evolution(plan: object, metrics: KpiNormalizationResult) -> TemplateEvolutionResult:
    template = getattr(plan, "template_type", "") or "generic"
    archetype = getattr(plan, "narrative_archetype_id", "") or "unknown"
    if metrics.normalized_status == "insufficient_data":
        return TemplateEvolutionResult(
            template_evolution_status="insufficient_data",
            template_scalability="unknown_without_kpis",
            best_use_cases=[template],
            avoid_cases=[],
            optimization_notes=["Import CTR, retention and growth metrics to evaluate template evolution."],
        )

    score = int(round((metrics.normalized_ctr * 550) + (metrics.normalized_retention * 35) + min(metrics.normalized_growth * 5000, 15)))
    score = max(0, min(100, score))

    if score >= 75:
        status = "scalable"
        scalability = "repeat_for_similar_topics"
    elif score >= 50:
        status = "promising"
        scalability = "use_with_packaging_tests"
    else:
        status = "needs_iteration"
        scalability = "limit_until_hook_and_retention_improve"

    notes = [f"template:{template}", f"archetype:{archetype}"]
    if metrics.normalized_retention < 0.25:
        notes.append("improve_pacing_or_scene_retention")
    if metrics.normalized_ctr < 0.04:
        notes.append("improve_title_thumbnail_fit")

    return TemplateEvolutionResult(
        template_evolution_status=status,
        template_real_world_score=score,
        template_scalability=scalability,
        best_use_cases=[template, archetype],
        avoid_cases=["low_source_confidence"] if metrics.normalized_retention < 0.2 else [],
        optimization_notes=list(dict.fromkeys(notes)),
    )
