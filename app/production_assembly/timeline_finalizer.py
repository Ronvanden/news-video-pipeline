"""BA 12.2 — Timeline Finalizer."""

from __future__ import annotations

from typing import List, Optional

from app.production_assembly.master_asset_manifest import build_master_asset_manifest
from app.production_assembly.schema import FinalTimelineResult, FinalTimelineScene, ManifestAsset


def _first_asset_id(assets: List[ManifestAsset], asset_type: str) -> Optional[str]:
    for asset in assets:
        if asset.asset_type == asset_type:
            return asset.asset_id
    return None


def _scene_link_ids(assets: List[ManifestAsset], scene_index: int) -> List[str]:
    visual_types = {"image", "video", "render"}
    linked: List[str] = []
    for asset in assets:
        if asset.asset_type not in visual_types:
            continue
        if asset.scene_index in (None, scene_index, 0):
            linked.append(asset.asset_id)
    return list(dict.fromkeys(linked))


def build_final_timeline(plan: object) -> FinalTimelineResult:
    warnings: List[str] = []
    timeline = getattr(plan, "production_timeline_result", None)
    manifest = getattr(plan, "master_asset_manifest_result", None) or build_master_asset_manifest(plan)
    assets = list(manifest.assets)
    audio_id = _first_asset_id(assets, "audio")

    if timeline is None or not timeline.scenes:
        return FinalTimelineResult(
            timeline_status="blocked",
            final_duration_seconds=0,
            scenes=[],
            warnings=["production_timeline_missing_or_empty"],
        )

    final_scenes: List[FinalTimelineScene] = []
    cursor = 0
    for idx, scene in enumerate(timeline.scenes):
        duration = int(getattr(scene, "estimated_duration_seconds", 0) or 0)
        linked = _scene_link_ids(assets, scene.scene_index)
        if not linked:
            warnings.append(f"scene_{scene.scene_index}_missing_visual_assets")
        if audio_id is None:
            warnings.append(f"scene_{scene.scene_index}_missing_narration_asset")
        final_scenes.append(
            FinalTimelineScene(
                scene_index=scene.scene_index,
                start_time=cursor,
                end_time=cursor + duration,
                linked_assets=linked,
                narration_asset=audio_id,
                render_priority=idx,
            )
        )
        cursor += duration

    if not final_scenes:
        status = "blocked"
    elif warnings or manifest.manifest_status != "complete":
        status = "partial"
    else:
        status = "complete"

    return FinalTimelineResult(
        timeline_status=status,
        final_duration_seconds=cursor,
        scenes=final_scenes,
        warnings=list(dict.fromkeys(warnings + list(manifest.warnings))),
    )
