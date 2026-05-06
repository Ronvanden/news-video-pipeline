"""BA 12.4 — Render Instruction Package."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.production_assembly.multi_asset_assembly import build_multi_asset_assembly
from app.production_assembly.schema import RenderInstructionPackageResult
from app.production_assembly.timeline_finalizer import build_final_timeline


def _thumbnail_target(plan: object) -> Optional[str]:
    assembly = getattr(plan, "multi_asset_assembly_result", None) or build_multi_asset_assembly(plan)
    if assembly.thumbnail_assets:
        asset = assembly.thumbnail_assets[0]
        return asset.asset_url or asset.local_path or asset.asset_id
    thumb = (getattr(plan, "thumbnail_angle", "") or "").strip()
    return f"thumbnail_prompt:{thumb}" if thumb else None


def build_render_instruction_package(plan: object) -> RenderInstructionPackageResult:
    warnings: List[str] = []
    final_timeline = getattr(plan, "final_timeline_result", None) or build_final_timeline(plan)
    alignment = getattr(plan, "voice_scene_alignment_result", None)

    render_targets = ["timeline_video", "thumbnail", "metadata_manifest"]
    scene_map: List[Dict[str, Any]] = []
    voice_map: List[Dict[str, Any]] = []
    for scene in final_timeline.scenes:
        scene_map.append(
            {
                "scene_index": scene.scene_index,
                "start_time": scene.start_time,
                "end_time": scene.end_time,
                "linked_assets": list(scene.linked_assets),
                "render_priority": scene.render_priority,
            }
        )
        voice_map.append(
            {
                "scene_index": scene.scene_index,
                "narration_asset": scene.narration_asset,
            }
        )
        if not scene.linked_assets:
            warnings.append(f"scene_{scene.scene_index}_has_no_render_assets")
        if not scene.narration_asset:
            warnings.append(f"scene_{scene.scene_index}_has_no_voice_track")

    thumb_target = _thumbnail_target(plan)
    if not thumb_target:
        warnings.append("thumbnail_target_missing")

    if not scene_map:
        status = "blocked"
    elif final_timeline.timeline_status == "complete" and (alignment is None or alignment.alignment_status == "complete") and not warnings:
        status = "complete"
    else:
        status = "partial"

    return RenderInstructionPackageResult(
        render_status=status,
        render_targets=render_targets,
        scene_render_map=scene_map,
        voice_track_map=voice_map,
        thumbnail_target=thumb_target,
        warnings=list(dict.fromkeys(warnings + list(final_timeline.warnings))),
    )
