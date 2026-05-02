"""BA 10.3 — Asset-Rückgabe-Normalisierung (Stub, keine Downloads)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.production_connectors.registry import get_connector
from app.production_connectors.schema import AssetNormalizationStatus, NormalizedAssetResult, NormalizedAssetType


def _infer_asset_type(provider_name: str) -> NormalizedAssetType:
    key = (provider_name or "").lower()
    if "thumbnail" in key:
        return "thumbnail"
    if "render" in key or "timeline" in key:
        return "render"
    if "kling" in key or "video" in key:
        return "video"
    if "voice" in key or "elevenlabs" in key or "openai" in key:
        return "audio"
    if "leonardo" in key or "image" in key:
        return "image"
    return "image"


def normalize_provider_asset_result(provider_name: str, raw_result: Any) -> NormalizedAssetResult:
    """Mappt rohe Provider-Antworten auf ein einheitliches Schema (ohne Netzwerk)."""
    ptype = ""
    conn = get_connector(provider_name)
    if conn is not None:
        ptype = conn.provider_type
    else:
        ptype = _infer_asset_type(provider_name)

    atype = _infer_asset_type(provider_name)
    warns: list[str] = []

    if raw_result is None:
        return NormalizedAssetResult(
            provider_name=provider_name,
            provider_type=ptype,
            normalization_status="invalid",
            asset_type=atype,
            metadata={},
            warnings=["raw_result_none"],
        )

    if not isinstance(raw_result, dict):
        return NormalizedAssetResult(
            provider_name=provider_name,
            provider_type=ptype,
            normalization_status="invalid",
            asset_type=atype,
            metadata={"non_dict": True},
            warnings=["raw_result_not_object"],
        )

    data: Dict[str, Any] = dict(raw_result)
    url: Optional[str] = None
    for k in ("asset_url", "url", "signed_url", "download_url"):
        v = data.get(k)
        if isinstance(v, str) and v.strip().startswith(("http://", "https://")):
            url = v.strip()
            break

    local: Optional[str] = None
    lp = data.get("local_path") or data.get("path")
    if isinstance(lp, str) and lp.strip():
        local = lp.strip()

    meta = {k: data[k] for k in sorted(data.keys()) if k not in ("asset_url", "url", "signed_url", "download_url")}

    if not url and not local and not meta:
        return NormalizedAssetResult(
            provider_name=provider_name,
            provider_type=ptype,
            normalization_status="invalid",
            asset_type=atype,
            metadata={},
            warnings=["empty_payload_after_strip"],
        )

    status: AssetNormalizationStatus = "normalized"
    if not url and not local:
        status = "partial"
        warns.append("no_url_or_local_path")
    if not url and local:
        warns.append("local_path_only")

    return NormalizedAssetResult(
        provider_name=provider_name,
        provider_type=ptype,
        normalization_status=status,
        asset_type=atype,
        asset_url=url,
        local_path=local,
        metadata=meta,
        warnings=warns,
    )
