"""BA 12.5 — Downloadable Production Bundle."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from app.production_assembly.master_asset_manifest import build_master_asset_manifest
from app.production_assembly.schema import DownloadableProductionBundleResult


def _bundle_id(plan: object) -> str:
    seed = "|".join(
        [
            getattr(plan, "template_type", ""),
            getattr(plan, "video_template", ""),
            getattr(plan, "hook", "")[:80],
        ]
    )
    return f"prod_bundle_{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def build_downloadable_production_bundle(plan: object) -> DownloadableProductionBundleResult:
    warnings: List[str] = []
    manifest = getattr(plan, "master_asset_manifest_result", None) or build_master_asset_manifest(plan)
    assembly = getattr(plan, "multi_asset_assembly_result", None)
    final_timeline = getattr(plan, "final_timeline_result", None)
    render = getattr(plan, "render_instruction_package_result", None)
    persistence = getattr(plan, "asset_persistence_result", None)

    bid = _bundle_id(plan)
    included = ["master_asset_manifest"]
    if assembly:
        included.append("multi_asset_assembly")
    if final_timeline:
        included.append("final_timeline")
    if render:
        included.append("render_instruction_package")
    if persistence:
        included.append("asset_persistence_contract")

    local_targets = [f"exports/{bid}/manifest.json", f"exports/{bid}/render_instructions.json"]
    if persistence:
        local_targets.extend(list(persistence.local_storage_targets or []))

    downloadable_manifest: Dict[str, Any] = {
        "bundle_id": bid,
        "manifest_version": manifest.manifest_version,
        "asset_count": manifest.total_assets,
        "assets": [a.model_dump() for a in manifest.assets],
        "components": included,
    }

    if manifest.manifest_status == "blocked":
        status = "blocked"
        warnings.append("manifest_blocked_bundle_not_export_ready")
    elif render and render.render_status == "complete" and manifest.manifest_status == "complete":
        status = "complete"
    else:
        status = "partial"
        warnings.append("bundle_partial_until_render_package_and_assets_complete")

    return DownloadableProductionBundleResult(
        bundle_status=status,
        bundle_id=bid,
        included_components=list(dict.fromkeys(included)),
        downloadable_manifest=downloadable_manifest,
        local_export_targets=list(dict.fromkeys(local_targets)),
        warnings=list(dict.fromkeys(warnings + list(manifest.warnings))),
    )
