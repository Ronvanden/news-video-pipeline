"""BA 9.30 — Story-to-Production Master Summary (ohne Launch, ohne APIs)."""

from __future__ import annotations

from app.prompt_engine.schema import (
    LaunchRecommendation,
    MasterOrchestrationResult,
    MasterOrchestrationStatus,
    ProductionPromptPlan,
)


def build_master_orchestration_summary(plan: ProductionPromptPlan) -> MasterOrchestrationResult:
    topic_bits = [
        plan.template_type,
        plan.video_template,
        str(len(plan.chapter_outline)),
        str(len(plan.scene_prompts)),
    ]
    story_input_summary = (
        f"Topic-Pfad: template={plan.template_type}, video_template={plan.video_template}, "
        f"Kapitel={len(plan.chapter_outline)}, Szenen={len(plan.scene_prompts)}."
    )

    q = plan.quality_result
    rg = plan.review_gate_result
    prompt_planning_summary = (
        f"Quality {q.status if q else 'n/a'} ({q.score if q else 0}/100); "
        f"Review-Gate {rg.decision if rg else 'n/a'}."
    )

    tl = plan.production_timeline_result
    production_summary = "Timeline nicht gebaut."
    if tl:
        production_summary = (
            f"Timeline {tl.timeline_status}, ~{tl.total_estimated_duration_seconds}s, "
            f"Länge-Kategorie {tl.target_video_length_category}."
        )

    pkg = plan.provider_packaging_result
    bundle = plan.provider_export_bundle_result
    provider_summary = "Provider-Pakete fehlen."
    if pkg and bundle:
        provider_summary = (
            f"Packaging {pkg.packaging_status}; Bundle {bundle.bundle_status}; "
            f"Bundle-ID {bundle.bundle_id or 'n/a'}."
        )

    fr = plan.final_readiness_gate_result
    risk_summary = fr.summary if fr else "Keine Readiness-Daten."
    if plan.warnings:
        risk_summary += f" Plan-Warnungen: {len(plan.warnings)}."

    launch: LaunchRecommendation = "revise"
    orch: MasterOrchestrationStatus = "review"
    if fr:
        if fr.readiness_decision == "ready_for_production":
            launch = "proceed"
            orch = "ready"
        elif fr.readiness_decision == "not_ready":
            launch = "hold"
            orch = "blocked"

    founder = (
        f"Gesamtbild ({', '.join(topic_bits)}): {fr.readiness_decision if fr else 'unknown'} — "
        f"Launch-Empfehlung {launch}. Kein automatischer Produktionsstart (V1)."
    )

    return MasterOrchestrationResult(
        orchestration_status=orch,
        story_input_summary=story_input_summary,
        prompt_planning_summary=prompt_planning_summary,
        production_summary=production_summary,
        provider_summary=provider_summary,
        risk_summary=risk_summary[:500],
        launch_recommendation=launch,
        final_founder_note=founder[:800],
    )
