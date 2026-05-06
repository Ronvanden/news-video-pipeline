"""BA 9.18 — Production-Handoff-Paket aus Prompt-Plan (ohne Produktionsstart)."""

from __future__ import annotations

from typing import List

from app.prompt_engine.schema import (
    ProductionHandoffPackage,
    ProductionHandoffResult,
    ProductionPromptPlan,
)

WARN_HUMAN_MISSING = "Human approval state missing."

SUMMARY_PENDING_REVIEW = (
    "Prompt plan is technically ready but still requires human approval."
)
SUMMARY_APPROVED = "Prompt plan is approved and ready for production handoff."
SUMMARY_NEEDS_REVISION = "Prompt plan requires revision before production handoff."
SUMMARY_BLOCKED = "Prompt plan blocked from production handoff."
SUMMARY_HUMAN_LAYER_MISSING = (
    "Human approval state missing; cannot assess production handoff."
)


def _collect_checked_sources(plan: ProductionPromptPlan) -> List[str]:
    out = ["production_prompt_plan"]
    if plan.quality_result is not None:
        out.append("quality_result")
    if plan.narrative_score_result is not None:
        out.append("narrative_score_result")
    if plan.review_gate_result is not None:
        out.append("review_gate_result")
    if plan.repair_suggestions_result is not None:
        out.append("repair_suggestions_result")
    if plan.human_approval_state is not None:
        out.append("human_approval_state")
    return out


def _build_package(plan: ProductionPromptPlan) -> ProductionHandoffPackage:
    q = plan.quality_result
    n = plan.narrative_score_result
    rg = plan.review_gate_result
    ha = plan.human_approval_state
    return ProductionHandoffPackage(
        template_type=plan.template_type,
        video_template=plan.video_template,
        narrative_archetype_id=plan.narrative_archetype_id,
        hook_type=plan.hook_type,
        hook_score=plan.hook_score,
        quality_status=q.status if q else "",
        quality_score=q.score if q else 0,
        narrative_status=n.status if n else "",
        narrative_score=n.score if n else 0,
        review_decision=rg.decision if rg else "",
        approval_status=ha.status if ha else "",
        hook=plan.hook,
        chapter_outline=list(plan.chapter_outline or []),
        scene_prompts=list(plan.scene_prompts or []),
        voice_style=plan.voice_style,
        thumbnail_angle=plan.thumbnail_angle,
    )


def _revision_blocking_reasons(plan: ProductionPromptPlan) -> List[str]:
    out: List[str] = []
    rg = plan.review_gate_result
    if rg is not None:
        out.extend(rg.reasons or [])
        out.extend(rg.required_actions or [])
    rs = plan.repair_suggestions_result
    if rs is not None:
        if (rs.summary or "").strip():
            out.append(rs.summary.strip())
        for s in (rs.suggestions or [])[:16]:
            out.append(f"[{s.category}] {s.issue}")
    ha = plan.human_approval_state
    if ha is not None:
        out.extend(ha.reasons or [])
    return list(dict.fromkeys(out))


def _rejected_blocking_reasons(plan: ProductionPromptPlan) -> List[str]:
    out: List[str] = []
    rg = plan.review_gate_result
    if rg is not None:
        out.extend(rg.reasons or [])
    q = plan.quality_result
    if q is not None:
        for bi in q.blocking_issues or []:
            out.append(f"Blocker: {bi}")
        if q.status == "fail":
            out.append("Quality status fail.")
    ha = plan.human_approval_state
    if ha is not None:
        if ha.rejected_reason:
            out.append(ha.rejected_reason)
        out.extend(ha.reasons or [])
    return list(dict.fromkeys(out))


def build_production_handoff(plan: ProductionPromptPlan) -> ProductionHandoffResult:
    package = _build_package(plan)
    checked_sources = _collect_checked_sources(plan)
    warnings: List[str] = []
    blocking_reasons: List[str] = []

    ha = plan.human_approval_state
    if ha is None:
        warnings.append(WARN_HUMAN_MISSING)
        return ProductionHandoffResult(
            handoff_status="needs_review",
            production_ready=False,
            summary=SUMMARY_HUMAN_LAYER_MISSING,
            package=package,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            checked_sources=checked_sources,
        )

    if ha.status == "pending_review":
        return ProductionHandoffResult(
            handoff_status="needs_review",
            production_ready=False,
            summary=SUMMARY_PENDING_REVIEW,
            package=package,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            checked_sources=checked_sources,
        )

    if ha.status == "approved":
        return ProductionHandoffResult(
            handoff_status="ready",
            production_ready=True,
            summary=SUMMARY_APPROVED,
            package=package,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            checked_sources=checked_sources,
        )

    if ha.status == "needs_revision":
        blocking_reasons = _revision_blocking_reasons(plan)
        return ProductionHandoffResult(
            handoff_status="needs_revision",
            production_ready=False,
            summary=SUMMARY_NEEDS_REVISION,
            package=package,
            warnings=warnings,
            blocking_reasons=blocking_reasons,
            checked_sources=checked_sources,
        )

    blocking_reasons = _rejected_blocking_reasons(plan)
    return ProductionHandoffResult(
        handoff_status="blocked",
        production_ready=False,
        summary=SUMMARY_BLOCKED,
        package=package,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        checked_sources=checked_sources,
    )
