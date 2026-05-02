"""BA 13.6 — Founder Publishing Summary."""

from __future__ import annotations

from app.publishing.schema import FounderPublishingSummaryResult


def build_founder_publishing_summary(plan: object) -> FounderPublishingSummaryResult:
    meta = getattr(plan, "metadata_master_package_result", None)
    opt = getattr(plan, "metadata_optimizer_result", None)
    thumbs = getattr(plan, "thumbnail_variant_pack_result", None)
    readiness = getattr(plan, "publishing_readiness_gate_result", None)
    schedule = getattr(plan, "schedule_plan_result", None)
    bundle = getattr(plan, "downloadable_production_bundle_result", None)

    title = getattr(meta, "canonical_title", "") if meta else ""
    content_summary = f"Publishing package for '{title or 'untitled production'}'."
    marketability_summary = (
        f"{len(getattr(thumbs, 'variants', []) or [])} thumbnail variants; "
        f"primary={getattr(thumbs, 'recommended_primary', '') or 'n/a'}."
    )
    seo_summary = (
        f"SEO score {getattr(opt, 'seo_score', 0)}/100, "
        f"click potential {getattr(opt, 'click_potential_score', 0)}/100."
    )
    status = getattr(readiness, "publishing_status", "not_ready") if readiness else "not_ready"
    rec = getattr(readiness, "release_recommendation", "hold") if readiness else "hold"
    risks = len(getattr(readiness, "blockers", []) or []) + len(getattr(readiness, "warnings", []) or [])
    risk_summary = f"Publishing status {status}; {risks} risk signals."
    mode = getattr(schedule, "suggested_publish_mode", "hold") if schedule else "hold"
    release_strategy = f"Recommendation: {rec}; schedule mode: {mode}."
    note = (
        "Publish-ready package prepared; human approval still required before external upload."
        if rec == "publish"
        else "Hold or review before publishing; no upload has been triggered."
    )

    return FounderPublishingSummaryResult(
        content_summary=content_summary,
        marketability_summary=marketability_summary,
        seo_summary=seo_summary,
        publishing_risk_summary=risk_summary,
        release_strategy=release_strategy,
        final_founder_note=note,
        supporting_signals={
            "bundle_id": getattr(bundle, "bundle_id", "") if bundle else "",
            "publishing_status": status,
            "release_recommendation": rec,
            "suggested_publish_mode": mode,
        },
    )
