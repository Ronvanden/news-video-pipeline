"""BA 12.6 — Human Final Review Package."""

from __future__ import annotations

from typing import List

from app.production_assembly.schema import HumanFinalReviewPackageResult


def build_human_final_review_package(plan: object) -> HumanFinalReviewPackageResult:
    checklist = [
        "Asset manifest reviewed",
        "Timeline continuity reviewed",
        "Voice/scene alignment reviewed",
        "Render instructions reviewed",
        "Cost projection reviewed",
        "Execution safety reviewed",
    ]
    risks: List[str] = []
    strengths: List[str] = []

    manifest = getattr(plan, "master_asset_manifest_result", None)
    assembly = getattr(plan, "multi_asset_assembly_result", None)
    timeline = getattr(plan, "final_timeline_result", None)
    alignment = getattr(plan, "voice_scene_alignment_result", None)
    render = getattr(plan, "render_instruction_package_result", None)
    bundle = getattr(plan, "downloadable_production_bundle_result", None)
    cost = getattr(plan, "cost_projection_result", None)
    safety = getattr(plan, "live_provider_safety_result", None)

    if manifest is None or manifest.manifest_status == "blocked":
        risks.append("asset_manifest_blocked_or_missing")
    elif manifest.manifest_status == "complete":
        strengths.append("asset_manifest_complete")
    else:
        risks.append("asset_manifest_partial")

    if assembly is None or assembly.coverage_score < 100:
        risks.append("asset_coverage_incomplete")
    else:
        strengths.append("asset_coverage_complete")

    if timeline is None or timeline.timeline_status == "blocked":
        risks.append("final_timeline_blocked_or_missing")
    elif timeline.timeline_status == "complete":
        strengths.append("final_timeline_complete")
    else:
        risks.append("final_timeline_partial")

    if alignment is None or alignment.alignment_status == "blocked":
        risks.append("voice_alignment_blocked_or_missing")
    elif alignment.missing_voice_scenes:
        risks.append("voice_alignment_missing_scenes")
    else:
        strengths.append("voice_alignment_ready")

    if render is None or render.render_status == "blocked":
        risks.append("render_package_blocked_or_missing")
    elif render.render_status == "complete":
        strengths.append("render_package_complete")
    else:
        risks.append("render_package_partial")

    if bundle is None or bundle.bundle_status == "blocked":
        risks.append("download_bundle_blocked_or_missing")
    elif bundle.bundle_id:
        strengths.append("download_bundle_id_available")

    if cost is None or cost.cost_status == "insufficient_data":
        risks.append("cost_projection_missing_or_insufficient")
    else:
        strengths.append("cost_projection_available")

    if safety is None:
        risks.append("live_provider_safety_missing")
    elif safety.live_provider_mode == "blocked":
        risks.append("live_provider_safety_not_live_ready")
    else:
        strengths.append("live_provider_safety_evaluated")

    if any(r.endswith("_blocked_or_missing") or r.endswith("_blocked") for r in risks):
        status = "blocked"
        recommendation = "hold"
    elif risks:
        status = "needs_revision"
        recommendation = "revise_before_render"
    else:
        status = "ready_for_human_review"
        recommendation = "approve_for_render"

    summary = (
        f"Final Review: {len(strengths)} Stärken, {len(risks)} Risiken. "
        f"Empfehlung: {recommendation}."
    )

    return HumanFinalReviewPackageResult(
        review_status=status,
        final_checklist=checklist,
        critical_risks=list(dict.fromkeys(risks)),
        strengths=list(dict.fromkeys(strengths)),
        final_summary=summary,
        release_recommendation=recommendation,
    )
