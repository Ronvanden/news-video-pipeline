"""BA 11.4 — Asset-Persistenz-/Download-Kontrakt (ohne Cloud-Pflicht)."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from app.production_connectors.schema import AssetPersistenceResult, AssetPersistenceStatus, LiveConnectorExecutionResult


def _slug(plan: object) -> str:
    raw = f"{getattr(plan, 'template_type', '')}:{getattr(plan, 'hook', '')[:48]}"
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:16]


def build_asset_persistence_contract(plan: object) -> AssetPersistenceResult:
    warns: List[str] = []
    slug = _slug(plan)
    base = f"tmp/production_assets/{slug}"

    downloadable: List[Dict[str, Any]] = []
    leo: LiveConnectorExecutionResult | None = getattr(plan, "leonardo_live_result", None)
    vo: LiveConnectorExecutionResult | None = getattr(plan, "voice_live_result", None)

    for res in (leo, vo):
        if res is None or res.normalized_asset is None:
            continue
        na = res.normalized_asset
        entry = {
            "provider": res.provider_name,
            "asset_type": na.asset_type,
            "asset_url": na.asset_url,
            "local_path": na.local_path,
            "normalization_status": na.normalization_status,
        }
        downloadable.append(entry)

    local_targets = [
        f"{base}/images/",
        f"{base}/audio/",
        f"{base}/manifest.json",
    ]

    manifest: Dict[str, Any] = {
        "run_key": slug,
        "assets": downloadable,
        "notes": "BA 11.4 V1 — keine automatischen Writes; nur Kontrakt.",
    }

    blocked_live = any(
        r is not None and r.execution_mode == "blocked" for r in (leo, vo)
    )
    has_binary_hint = any(
        d.get("asset_url") or d.get("local_path") for d in downloadable
    )

    status: AssetPersistenceStatus
    if blocked_live and not downloadable:
        status = "blocked"
        warns.append("live_connector_blocked_no_assets")
    elif has_binary_hint:
        status = "persist_ready"
    else:
        status = "metadata_only"
        warns.append("metadata_only_no_download_urls")

    return AssetPersistenceResult(
        persistence_status=status,
        downloadable_assets=downloadable,
        local_storage_targets=local_targets,
        metadata_manifest=manifest,
        warnings=list(dict.fromkeys(warns)),
    )
