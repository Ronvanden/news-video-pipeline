"""Ingest one existing Leonardo image URL into asset/manifest-compatible records."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.production_assembly.master_asset_manifest import _asset_id
from app.production_assembly.schema import ManifestAsset
from app.production_connectors.asset_normalization import normalize_provider_asset_result
from app.production_connectors.schema import NormalizedAssetResult


class LeonardoImageAssetIngestResult(BaseModel):
    """Safe local result for one existing Leonardo image asset."""

    normalized_asset: NormalizedAssetResult
    manifest_record: ManifestAsset
    manifest_status: str = "partial"
    warnings: List[str] = Field(default_factory=list)

    def safe_output(self) -> Dict[str, Any]:
        return {
            "asset_type": self.normalized_asset.asset_type,
            "provider_name": self.normalized_asset.provider_name,
            "asset_url": self.normalized_asset.asset_url,
            "manifest_asset_id": self.manifest_record.asset_id,
            "manifest_status": self.manifest_status,
            "warnings": self.warnings,
        }


def ingest_leonardo_image_asset(generation_id: str, image_url: str) -> LeonardoImageAssetIngestResult:
    """Normalize one already-created Leonardo image URL without network or persistence."""
    gid = (generation_id or "").strip()
    url = (image_url or "").strip()
    warnings: List[str] = []

    if not gid:
        warnings.append("generation_id_missing")
    if not url:
        warnings.append("image_url_missing")
    elif not url.startswith(("http://", "https://")):
        warnings.append("image_url_invalid")

    raw_result: Dict[str, Any] = {
        "asset_url": url if url.startswith(("http://", "https://")) else None,
        "generation_id": gid,
        "source": "manual_leonardo_generation_ingest",
    }
    normalized = normalize_provider_asset_result("Leonardo", raw_result)
    warnings.extend(normalized.warnings)

    manifest_status = "partial" if normalized.normalization_status == "normalized" else "blocked"
    source_status = "manual_ingested" if normalized.normalization_status == "normalized" else "invalid"
    seed = f"live:{normalized.provider_name}:{normalized.asset_type}:{normalized.asset_url or ''}:{normalized.local_path or ''}"
    record = ManifestAsset(
        asset_id=_asset_id(seed),
        provider_name=normalized.provider_name,
        asset_type=normalized.asset_type,
        source_status=source_status,
        asset_url=normalized.asset_url,
        local_path=normalized.local_path,
        scene_index=0 if normalized.asset_type in ("image", "video", "audio", "render") else None,
        metadata={
            "generation_id": gid,
            "source": "manual_leonardo_generation_ingest",
            "normalization_status": normalized.normalization_status,
        },
    )

    return LeonardoImageAssetIngestResult(
        normalized_asset=normalized,
        manifest_record=record,
        manifest_status=manifest_status,
        warnings=list(dict.fromkeys(warnings)),
    )
