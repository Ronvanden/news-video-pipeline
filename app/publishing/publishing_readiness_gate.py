"""BA 13.5 — Publishing Readiness Gate."""

from __future__ import annotations

from typing import List

from app.publishing.schema import PublishingReadinessGateResult


def evaluate_publishing_readiness(plan: object) -> PublishingReadinessGateResult:
    blockers: List[str] = []
    warnings: List[str] = []
    strengths: List[str] = []

    meta = getattr(plan, "metadata_master_package_result", None)
    opt = getattr(plan, "metadata_optimizer_result", None)
    thumbs = getattr(plan, "thumbnail_variant_pack_result", None)
    checklist = getattr(plan, "upload_checklist_result", None)
    schedule = getattr(plan, "schedule_plan_result", None)
    review = getattr(plan, "human_final_review_package_result", None)

    score = 0
    if meta and meta.metadata_status != "blocked":
        score += 20
        strengths.append("metadata_available")
        warnings.extend(meta.compliance_warnings)
    else:
        blockers.append("metadata_missing_or_blocked")

    if opt and opt.seo_score >= 60:
        score += 20
        strengths.append("seo_variants_available")
    elif opt:
        score += 10
        warnings.append("seo_score_low")
    else:
        blockers.append("metadata_optimizer_missing")

    if thumbs and thumbs.variant_status != "blocked" and thumbs.variants:
        score += 15
        strengths.append("thumbnail_variants_available")
    else:
        blockers.append("thumbnail_variants_missing")

    if checklist and checklist.checklist_status == "complete":
        score += 20
        strengths.append("upload_checklist_complete")
    elif checklist and checklist.checklist_status == "partial":
        score += 10
        warnings.extend(checklist.missing_items)
    else:
        blockers.extend(list(getattr(checklist, "blockers", []) or ["upload_checklist_blocked_or_missing"]))

    if schedule and schedule.suggested_publish_mode != "hold":
        score += 10
        strengths.append("schedule_plan_available")
    else:
        warnings.append("schedule_hold_or_missing")

    review_revision_pending = False
    if review and review.review_status == "ready_for_human_review":
        score += 15
        strengths.append("human_final_review_ready")
    elif review and review.review_status == "needs_revision":
        score += 8
        review_revision_pending = True
        warnings.append("human_final_review_needs_revision")
        warnings.extend(review.critical_risks)
    else:
        blockers.append("human_final_review_blocked_or_missing")

    score = max(0, min(100, score))
    if blockers:
        status = "not_ready"
        recommendation = "hold"
    elif score >= 85 and not review_revision_pending:
        status = "ready_to_publish"
        recommendation = "publish"
    else:
        status = "ready_for_review"
        recommendation = "review"

    return PublishingReadinessGateResult(
        publishing_status=status,
        publishing_score=score,
        blockers=list(dict.fromkeys(blockers)),
        warnings=list(dict.fromkeys(warnings)),
        strengths=list(dict.fromkeys(strengths)),
        release_recommendation=recommendation,
    )
