"""BA 9.24 — Heuristische Kostenschätzung (EUR, keine echten API-Preise)."""

from __future__ import annotations

from typing import List

from app.prompt_engine.schema import (
    CostProjectionResult,
    CostProjectionStatus,
    ProductionPromptPlan,
    ProviderCostEstimate,
)

# V1-Pauschalen / Einheiten (illustrativ, deterministisch)
EUR_LEONARDO_PER_SCENE = 0.18
EUR_KLING_PER_SCENE = 0.42
EUR_VOICE_PER_CHAPTER = 0.08
EUR_THUMBNAIL = 0.12
EUR_RENDER_FLAT = 18.0


def build_cost_projection(plan: ProductionPromptPlan) -> CostProjectionResult:
    warnings: List[str] = []
    assumptions = [
        "V1 Schätzung ohne API-Listenpreise; nur Planungsgrößen.",
        "Leonardo ≈ pro Timeline-Szene mit Bildbezug; Kling ≈ pro Video-Szene.",
        "Voice ≈ pro Kapitelblock; Thumbnail pauschal; Render pauschal.",
    ]
    tl = plan.production_timeline_result

    if tl is None or tl.timeline_status == "blocked":
        warnings.append("Timeline blocked or missing; cost projection insufficient.")
        return CostProjectionResult(
            cost_status="insufficient_data",
            total_estimated_cost_eur=0.0,
            estimated_cost_per_minute=0.0,
            provider_costs=[],
            assumptions=assumptions,
            warnings=warnings,
        )

    n_timeline_scenes = len(tl.scenes)
    n_chapters = len(plan.chapter_outline or [])
    n_scenes = len(plan.scene_prompts or [])

    leonardo_units = float(max(n_timeline_scenes, 1))
    kling_units = float(max(n_scenes, n_timeline_scenes - 1, 1))
    voice_units = float(max(n_chapters, 1))
    thumb_units = 1.0 if (plan.thumbnail_angle or "").strip() else 0.0
    if thumb_units == 0:
        warnings.append("No thumbnail_angle; thumbnail cost omitted.")

    c_leo = leonardo_units * EUR_LEONARDO_PER_SCENE
    c_kling = kling_units * EUR_KLING_PER_SCENE
    c_voice = voice_units * EUR_VOICE_PER_CHAPTER
    c_thumb = thumb_units * EUR_THUMBNAIL
    c_render = EUR_RENDER_FLAT

    provider_costs = [
        ProviderCostEstimate(
            provider_name="Leonardo (image)",
            estimated_units=leonardo_units,
            estimated_cost_eur=round(c_leo, 4),
            notes="Pro Szene / visueller Beat laut Timeline.",
        ),
        ProviderCostEstimate(
            provider_name="Kling (video)",
            estimated_units=kling_units,
            estimated_cost_eur=round(c_kling, 4),
            notes="Pro Szenen-Prompt / Motion-Unit.",
        ),
        ProviderCostEstimate(
            provider_name="Voice (OpenAI/ElevenLabs stub)",
            estimated_units=voice_units,
            estimated_cost_eur=round(c_voice, 4),
            notes="Pro Kapitel / Voice-Block.",
        ),
        ProviderCostEstimate(
            provider_name="Thumbnail",
            estimated_units=thumb_units,
            estimated_cost_eur=round(c_thumb, 4),
            notes="Pauschal ein Entwurf.",
        ),
        ProviderCostEstimate(
            provider_name="Render pipeline",
            estimated_units=1.0,
            estimated_cost_eur=round(c_render, 4),
            notes="Pauschal Schnitt/Timeline (Stub).",
        ),
    ]

    total = sum(p.estimated_cost_eur for p in provider_costs)
    minutes = tl.total_estimated_duration_seconds / 60.0 if tl.total_estimated_duration_seconds > 0 else 0.0
    per_min = round(total / minutes, 4) if minutes > 0 else 0.0

    cost_status: CostProjectionStatus
    if tl.timeline_status == "partial" or warnings:
        cost_status = "partial"
    else:
        cost_status = "estimated"

    return CostProjectionResult(
        cost_status=cost_status,
        total_estimated_cost_eur=round(total, 4),
        estimated_cost_per_minute=per_min,
        provider_costs=provider_costs,
        assumptions=assumptions,
        warnings=warnings,
    )
