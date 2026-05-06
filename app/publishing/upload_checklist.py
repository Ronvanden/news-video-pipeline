"""BA 13.3 — Upload Checklist."""

from __future__ import annotations

from typing import Dict, List

from app.publishing.schema import UploadChecklistResult


REQUIRED_ITEMS: Dict[str, str] = {
    "metadata_complete": "Metadata vollständig",
    "thumbnail_ready": "Thumbnail-Varianten vorhanden",
    "download_bundle_ready": "Download-Bundle vorhanden",
    "human_final_review_available": "Human Final Review vorhanden",
    "policy_compliance_reviewed": "Policy / Compliance geprüft",
    "copyright_risk_reviewed": "Copyright-/Risk-Hinweise geprüft",
}


def build_upload_checklist(plan: object) -> UploadChecklistResult:
    completed: List[str] = []
    blockers: List[str] = []
    meta = getattr(plan, "metadata_master_package_result", None)
    thumbs = getattr(plan, "thumbnail_variant_pack_result", None)
    bundle = getattr(plan, "downloadable_production_bundle_result", None)
    review = getattr(plan, "human_final_review_package_result", None)

    if meta and meta.metadata_status in ("complete", "partial") and meta.canonical_title and meta.canonical_description:
        completed.append("metadata_complete")
    else:
        blockers.append("metadata_missing_or_blocked")

    if thumbs and thumbs.variants and thumbs.recommended_primary:
        completed.append("thumbnail_ready")
    else:
        blockers.append("thumbnail_variants_missing")

    if bundle and bundle.bundle_id and bundle.bundle_status in ("complete", "partial"):
        completed.append("download_bundle_ready")
    else:
        blockers.append("download_bundle_missing_or_blocked")

    if review and review.review_status in ("ready_for_human_review", "needs_revision"):
        completed.append("human_final_review_available")
    else:
        blockers.append("human_final_review_missing_or_blocked")

    compliance_warnings = list(getattr(meta, "compliance_warnings", []) or []) if meta else []
    if meta and "human_review_required" in meta.audience_flags:
        completed.append("policy_compliance_reviewed")
    else:
        blockers.append("policy_compliance_not_reviewed")

    if compliance_warnings:
        completed.append("copyright_risk_reviewed")
    else:
        completed.append("copyright_risk_reviewed")

    missing = [key for key in REQUIRED_ITEMS if key not in completed]
    if blockers:
        status = "blocked"
    elif missing:
        status = "partial"
    else:
        status = "complete"

    return UploadChecklistResult(
        checklist_status=status,
        required_items=list(REQUIRED_ITEMS.keys()),
        completed_items=list(dict.fromkeys(completed)),
        missing_items=missing,
        blockers=list(dict.fromkeys(blockers)),
    )
