"""BA 9.25 — Finale Produktions-Readiness ohne Startbefehl."""

from __future__ import annotations

from typing import List

from app.prompt_engine.schema import (
    FinalProductionReadinessResult,
    FinalReadinessDecision,
    ProductionPromptPlan,
)


def evaluate_final_production_readiness(plan: ProductionPromptPlan) -> FinalProductionReadinessResult:
    blockers: List[str] = []
    review_flags: List[str] = []
    strengths: List[str] = []
    score = 100

    ex = plan.production_export_contract_result
    val = plan.package_validation_result
    tl = plan.production_timeline_result
    cost = plan.cost_projection_result
    ha = plan.human_approval_state
    bundle = plan.provider_export_bundle_result

    if ex is None:
        blockers.append("production_export_contract_result missing.")
        score -= 40
    elif not ex.export_ready:
        review_flags.append("Export contract not export_ready.")
        score -= 15
    if ex is not None and ex.export_status == "blocked":
        blockers.append("Export contract blocked.")
        score -= 35

    if val is None:
        blockers.append("package_validation_result missing.")
        score -= 30
    elif val.validation_status == "fail":
        blockers.append("Package validation failed.")
        score -= 35
    elif val.validation_status == "warning":
        review_flags.append("Package validation has warnings.")
        score -= 10
    else:
        strengths.append("Provider bundle validation passed.")

    if bundle is not None and bundle.bundle_status == "blocked":
        blockers.append("Provider export bundle blocked.")
        score -= 25

    if tl is None:
        blockers.append("production_timeline_result missing.")
        score -= 25
    elif tl.timeline_status == "blocked":
        blockers.append("Timeline blocked.")
        score -= 30
    elif tl.timeline_status == "partial":
        review_flags.append("Timeline partial (duration/structure warnings).")
        score -= 12
    else:
        strengths.append("Timeline ready.")

    if cost is None:
        blockers.append("cost_projection_result missing.")
        score -= 15
    elif cost.cost_status == "insufficient_data":
        blockers.append("Cost projection insufficient_data.")
        score -= 20
    elif cost.cost_status == "partial":
        review_flags.append("Cost projection partial.")
        score -= 8
    else:
        strengths.append("Cost projection estimated.")

    if ha is None:
        review_flags.append("Human approval state missing.")
        score -= 10
    elif ha.status == "rejected":
        blockers.append("Human approval rejected.")
        score -= 40
    elif ha.status == "needs_revision":
        blockers.append("Human approval needs_revision.")
        score -= 30
    elif ha.status == "pending_review":
        review_flags.append("Human approval pending_review (V1 default path).")
        score -= 12
    elif ha.status == "approved":
        strengths.append("Human approval approved.")

    score = max(0, min(100, score))

    decision: FinalReadinessDecision
    summary: str

    if blockers:
        decision = "not_ready"
        summary = "Not ready for production: resolve blockers before handoff."
    elif (
        ex
        and ex.export_ready
        and val
        and val.validation_status == "pass"
        and tl
        and tl.timeline_status == "ready"
        and cost
        and cost.cost_status == "estimated"
        and ha
        and ha.status == "approved"
        and not review_flags
        and score >= 88
    ):
        decision = "ready_for_production"
        summary = "All gates green with explicit approval; safe for production planning."
    elif not blockers:
        decision = "ready_for_review"
        summary = "No hard blockers; operational review recommended before production."
    else:
        decision = "not_ready"
        summary = "Readiness undetermined; treat as not ready."

    return FinalProductionReadinessResult(
        readiness_decision=decision,
        readiness_score=score,
        production_blockers=list(dict.fromkeys(blockers)),
        review_flags=list(dict.fromkeys(review_flags)),
        strengths=list(dict.fromkeys(strengths)),
        summary=summary,
    )
