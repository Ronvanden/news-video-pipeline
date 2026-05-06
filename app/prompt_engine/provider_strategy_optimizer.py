"""BA 9.28 — Provider-Strategie aus Plan, Kosten und Packaging (keine APIs)."""

from __future__ import annotations

from typing import List

from app.prompt_engine.schema import (
    CostPriorityLevel,
    ProductionPromptPlan,
    ProviderStrategyOptimizationStatus,
    ProviderStrategyOptimizerResult,
)


def optimize_provider_strategy(plan: ProductionPromptPlan) -> ProviderStrategyOptimizerResult:
    reasoning: List[str] = []
    cost = plan.cost_projection_result
    tl = plan.production_timeline_result
    pkg = plan.provider_packaging_result
    bundle = plan.provider_export_bundle_result

    status: ProviderStrategyOptimizationStatus = "ready"
    if bundle is None or bundle.bundle_status == "blocked":
        status = "blocked"
        reasoning.append("Export-Bundle blockiert oder fehlt — Strategie nur Platzhalter.")
    elif bundle.bundle_status == "partial" or (pkg and pkg.packaging_status == "partial"):
        status = "partial"
        reasoning.append("Packaging partial — konservative Standard-Provider beibehalten.")

    total = float(cost.total_estimated_cost_eur) if cost else 0.0
    minutes = 0.0
    if tl and tl.total_estimated_duration_seconds > 0:
        minutes = tl.total_estimated_duration_seconds / 60.0
    per_min = float(cost.estimated_cost_per_minute) if cost else 0.0

    cost_priority: CostPriorityLevel = "balanced"
    if total > 0 and (per_min > 25 or total > 80):
        cost_priority = "premium"
        reasoning.append("Höhere EUR/Minute oder Gesamtkosten — Premium-Priorität (V1-Heuristik).")
    elif total > 0 and per_min < 8 and total < 35:
        cost_priority = "low_cost"
        reasoning.append("Niedrige geschätzte Kosten pro Minute — low_cost priorisieren.")
    else:
        reasoning.append("Kosten im mittleren Korridor — balanced Strategie.")

    tt = (plan.template_type or "").lower()
    if "mystery" in tt:
        reasoning.append("Mystery-Template: visuelle Ruhe priorisieren (Stub-Hinweis).")

    if minutes > 8:
        reasoning.append("Längeres Video — Render-/Voice-Blöcke im Auge behalten.")

    image_p = "Leonardo"
    video_p = "Kling"
    voice_p = "OpenAI / ElevenLabs (stub)"
    thumb_p = "Thumbnail (stub)"

    if cost_priority == "premium":
        reasoning.append("V1: Rolle image/video formal unverändert; später echte Premium-Routing-Regeln.")

    return ProviderStrategyOptimizerResult(
        optimization_status=status,
        recommended_image_provider=image_p,
        recommended_video_provider=video_p,
        recommended_voice_provider=voice_p,
        recommended_thumbnail_provider=thumb_p,
        cost_priority=cost_priority,
        reasoning=reasoning,
    )
