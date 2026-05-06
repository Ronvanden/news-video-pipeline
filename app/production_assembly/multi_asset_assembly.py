"""BA 12.1 — Multi-Asset Assembly."""

from __future__ import annotations

from typing import List

from app.production_assembly.master_asset_manifest import EXPECTED_ASSET_TYPES, build_master_asset_manifest
from app.production_assembly.schema import ManifestAsset, MultiAssetAssemblyResult


def _by_type(assets: List[ManifestAsset], asset_type: str) -> List[ManifestAsset]:
    return [a for a in assets if a.asset_type == asset_type]


def build_multi_asset_assembly(plan: object) -> MultiAssetAssemblyResult:
    manifest = getattr(plan, "master_asset_manifest_result", None) or build_master_asset_manifest(plan)
    assets = list(manifest.assets)
    images = _by_type(assets, "image")
    videos = _by_type(assets, "video")
    voices = _by_type(assets, "audio")
    thumbnails = _by_type(assets, "thumbnail")
    renders = _by_type(assets, "render")

    present_count = len({a.asset_type for a in assets if a.asset_type in EXPECTED_ASSET_TYPES})
    coverage = int(round((present_count / len(EXPECTED_ASSET_TYPES)) * 100)) if EXPECTED_ASSET_TYPES else 0

    warnings = list(manifest.warnings)
    if coverage < 100:
        warnings.append(f"asset_coverage_below_complete:{coverage}")

    if not assets:
        status = "blocked"
    elif coverage == 100:
        status = "complete"
    else:
        status = "partial"

    return MultiAssetAssemblyResult(
        assembly_status=status,
        image_assets=images,
        video_assets=videos,
        voice_assets=voices,
        thumbnail_assets=thumbnails,
        render_assets=renders,
        coverage_score=coverage,
        warnings=list(dict.fromkeys(warnings)),
    )
