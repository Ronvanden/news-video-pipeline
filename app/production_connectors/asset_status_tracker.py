"""BA 10.9 — Asset-Status aus Mock-Runner (ohne echte Assets)."""

from __future__ import annotations

from typing import List

from app.production_connectors.schema import (
    AssetMatrixEntry,
    AssetStatusTrackerResult,
    AssetTrackerSlotStatus,
    NormalizedAssetType,
    ProviderJobRunnerMockResult,
)


def _ptype_to_asset(provider_type: str) -> NormalizedAssetType:
    p = (provider_type or "").lower()
    if p == "thumbnail":
        return "thumbnail"
    if p == "render":
        return "render"
    if p == "video":
        return "video"
    if p == "voice":
        return "audio"
    return "image"


def _status_from_final(final_status: str) -> AssetTrackerSlotStatus:
    if final_status == "simulated_success":
        return "generated"
    if final_status == "skipped":
        return "skipped"
    if final_status == "blocked":
        return "failed"
    return "pending"


def build_asset_status_tracker(run_result: ProviderJobRunnerMockResult) -> AssetStatusTrackerResult:
    """Fünf Asset-Kanäle vs. Mock-Job-Outcomes."""
    expected: List[NormalizedAssetType] = ["thumbnail", "image", "audio", "video", "render"]
    matrix: List[AssetMatrixEntry] = []
    gen = pend = fail = skip = 0

    for et in expected:
        matched = next(
            (o for o in run_result.job_outcomes if _ptype_to_asset(o.provider_type) == et),
            None,
        )
        if matched is None:
            st: AssetTrackerSlotStatus = "pending"
            detail = "no_job_for_slot"
            pend += 1
        else:
            st = _status_from_final(matched.final_status)
            detail = matched.final_status
            if st == "generated":
                gen += 1
            elif st == "pending":
                pend += 1
            elif st == "failed":
                fail += 1
            else:
                skip += 1
        matrix.append(AssetMatrixEntry(asset_type=et, status=st, detail=detail))

    tstat = "ok"
    if fail:
        tstat = "degraded"
    elif pend or skip:
        tstat = "partial"

    return AssetStatusTrackerResult(
        tracker_status=tstat,
        total_expected_assets=len(expected),
        generated_assets=gen,
        pending_assets=pend,
        failed_assets=fail,
        asset_matrix=matrix,
    )
