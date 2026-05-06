"""BA 9.17 — Human-Approval-Vorbereitung aus Review Gate und Repair-Signalen (ohne Persistenz)."""

from __future__ import annotations

from typing import List

from app.prompt_engine.schema import HumanApprovalState, ProductionPromptPlan

GO_CHECKLIST: List[str] = [
    "Hook prüfen",
    "Kapitelstruktur prüfen",
    "Szenen-Prompts prüfen",
    "Voice/Thumbnail prüfen",
    "Quellen-/Faktenrisiko prüfen",
    "Produktionskosten grob prüfen",
]

STOP_REJECT_REASON = "Plan failed automated review gate."
GATE_MISSING_REASON = "Review gate result missing."


def build_human_approval_state(plan: ProductionPromptPlan) -> HumanApprovalState:
    rg = plan.review_gate_result
    rs = plan.repair_suggestions_result

    if rg is None:
        return HumanApprovalState(
            status="pending_review",
            recommended_action="review",
            approval_required=True,
            reasons=[GATE_MISSING_REASON],
            checklist=[],
            approved_by=None,
            approved_at=None,
            rejected_reason=None,
        )

    if rg.decision == "go":
        return HumanApprovalState(
            status="pending_review",
            recommended_action="approve",
            approval_required=True,
            reasons=[],
            checklist=list(GO_CHECKLIST),
            approved_by=None,
            approved_at=None,
            rejected_reason=None,
        )

    if rg.decision == "revise":
        reasons: List[str] = list(rg.reasons or [])
        if rs is not None and (rs.summary or "").strip():
            reasons.append(rs.summary.strip())
        reasons = list(dict.fromkeys(reasons))
        return HumanApprovalState(
            status="needs_revision",
            recommended_action="revise",
            approval_required=True,
            reasons=reasons,
            checklist=[],
            approved_by=None,
            approved_at=None,
            rejected_reason=None,
        )

    # stop
    reasons = list(rg.reasons or [])
    q = plan.quality_result
    if q is not None:
        for bi in q.blocking_issues or []:
            reasons.append(f"Blocker: {bi}")
    reasons = list(dict.fromkeys(reasons))
    return HumanApprovalState(
        status="rejected",
        recommended_action="reject",
        approval_required=True,
        reasons=reasons,
        checklist=[],
        approved_by=None,
        approved_at=None,
        rejected_reason=STOP_REJECT_REASON,
    )
