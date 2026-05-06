"""BA 12.0 — Master Asset Manifest."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from app.production_assembly.schema import AssemblyAssetType, ManifestAsset, MasterAssetManifestResult

EXPECTED_ASSET_TYPES: List[AssemblyAssetType] = ["image", "video", "audio", "thumbnail", "render"]


def _asset_id(seed: str) -> str:
    return f"asset_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _provider_type_to_asset_type(provider_type: str) -> AssemblyAssetType:
    p = (provider_type or "").lower()
    if p == "voice":
        return "audio"
    if p in ("image", "video", "thumbnail", "render", "audio"):
        return p  # type: ignore[return-value]
    return "image"


def _append_live_asset(out: List[ManifestAsset], res: object, fallback_type: AssemblyAssetType) -> None:
    if res is None:
        return
    norm = getattr(res, "normalized_asset", None)
    if norm is None:
        return
    provider_name = getattr(res, "provider_name", "") or getattr(norm, "provider_name", "")
    asset_type = getattr(norm, "asset_type", None) or fallback_type
    if asset_type == "voice":
        asset_type = "audio"
    source_status = getattr(res, "execution_mode", "") or getattr(norm, "normalization_status", "")
    seed = f"live:{provider_name}:{asset_type}:{getattr(norm, 'asset_url', '')}:{getattr(norm, 'local_path', '')}"
    out.append(
        ManifestAsset(
            asset_id=_asset_id(seed),
            provider_name=provider_name,
            asset_type=asset_type,
            source_status=source_status,
            asset_url=getattr(norm, "asset_url", None),
            local_path=getattr(norm, "local_path", None),
            chapter_index=None,
            scene_index=0 if asset_type in ("image", "video", "audio", "render") else None,
            metadata=dict(getattr(norm, "metadata", {}) or {}),
        )
    )


def _append_mock_assets(out: List[ManifestAsset], plan: object) -> None:
    runner = getattr(plan, "provider_job_runner_mock_result", None)
    if runner is None:
        return
    present = {a.asset_type for a in out}
    for outcome in runner.job_outcomes:
        asset_type = _provider_type_to_asset_type(outcome.provider_type)
        if asset_type in present or outcome.final_status != "simulated_success":
            continue
        seed = f"mock:{outcome.job_id}:{outcome.provider_name}:{asset_type}"
        out.append(
            ManifestAsset(
                asset_id=_asset_id(seed),
                provider_name=outcome.provider_name,
                asset_type=asset_type,
                source_status=outcome.final_status,
                scene_index=0 if asset_type in ("image", "video", "audio", "render") else None,
                metadata={"job_id": outcome.job_id, "notes": outcome.notes, "mock": True},
            )
        )
        present.add(asset_type)


def _append_persistence_assets(out: List[ManifestAsset], plan: object) -> None:
    persistence = getattr(plan, "asset_persistence_result", None)
    if persistence is None:
        return
    present_keys = {(a.provider_name, a.asset_type, a.asset_url, a.local_path) for a in out}
    for idx, row in enumerate(persistence.downloadable_assets):
        if not isinstance(row, dict):
            continue
        asset_type = row.get("asset_type") or "image"
        if asset_type == "voice":
            asset_type = "audio"
        key = (row.get("provider") or "", asset_type, row.get("asset_url"), row.get("local_path"))
        if key in present_keys:
            continue
        seed = f"persist:{idx}:{key}"
        out.append(
            ManifestAsset(
                asset_id=_asset_id(seed),
                provider_name=str(row.get("provider") or ""),
                asset_type=asset_type,
                source_status=str(row.get("normalization_status") or "metadata"),
                asset_url=row.get("asset_url"),
                local_path=row.get("local_path"),
                scene_index=0 if asset_type in ("image", "video", "audio", "render") else None,
                metadata={"from_asset_persistence": True},
            )
        )
        present_keys.add(key)


def build_master_asset_manifest(plan: object) -> MasterAssetManifestResult:
    warnings: List[str] = []
    assets: List[ManifestAsset] = []

    _append_live_asset(assets, getattr(plan, "leonardo_live_result", None), "image")
    _append_live_asset(assets, getattr(plan, "voice_live_result", None), "audio")
    _append_persistence_assets(assets, plan)
    _append_mock_assets(assets, plan)

    present = {a.asset_type for a in assets}
    missing = [t for t in EXPECTED_ASSET_TYPES if t not in present]
    if missing:
        warnings.append("missing_asset_types:" + ",".join(missing))

    if not assets:
        status = "blocked"
        warnings.append("no_assets_available_for_manifest")
    elif missing:
        status = "partial"
    else:
        status = "complete"

    return MasterAssetManifestResult(
        manifest_status=status,
        total_assets=len(assets),
        assets=assets,
        missing_asset_types=missing,
        warnings=list(dict.fromkeys(warnings)),
    )
