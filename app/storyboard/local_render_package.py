"""Local render package handoff for storyboard render timelines.

This module only builds deterministic JSON-ready manifest shapes. It does not
write files, start ffmpeg, call providers, or persist anything remotely.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from app.storyboard.schema import (
    StoryboardLocalRenderPackageRequest,
    StoryboardLocalRenderPackageResult,
    StoryboardRenderTimelineResult,
)


def _safe_run_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", (value or "").strip())
    return cleaned.strip("._-") or "storyboard_local_render_v1"


def _as_posix_path(path: Path) -> str:
    return path.as_posix()


def build_storyboard_local_render_package(
    render_timeline: StoryboardRenderTimelineResult,
    *,
    run_id: str = "storyboard_local_render_v1",
    output_root: str = "output",
) -> StoryboardLocalRenderPackageResult:
    """Build a renderer-compatible handoff package from a storyboard timeline."""

    safe_run_id = _safe_run_id(run_id)
    root = Path(output_root or "output")
    render_dir = root / "storyboard_runs" / safe_run_id / "render"
    asset_manifest_path = render_dir / "asset_manifest.json"
    timeline_manifest_path = render_dir / "timeline_manifest.json"
    final_video_path = render_dir / "final_video.mp4"

    warnings: List[str] = list(render_timeline.warnings or [])
    blocking_issues: List[str] = list(render_timeline.blocking_issues or [])

    if render_timeline.overall_status == "blocked":
        blocking_issues.append("render_timeline_blocked")
    if not render_timeline.segments:
        blocking_issues.append("render_timeline_has_no_segments")

    assets: List[Dict[str, Any]] = []
    scenes: List[Dict[str, Any]] = []
    voice_paths = sorted({(seg.voice_path or "").strip() for seg in render_timeline.segments if (seg.voice_path or "").strip()})

    for seg in render_timeline.segments:
        scene_warnings = list(seg.warnings or [])
        scene_blockers = list(seg.blocking_issues or [])
        image_path = (seg.image_path or "").strip()
        video_path = (seg.video_path or "").strip()
        voice_path = (seg.voice_path or "").strip()
        media_type = "video" if seg.render_mode == "video_clip" and video_path else "image"

        if media_type == "image" and not image_path:
            issue = f"scene_{seg.scene_number}_local_render_image_missing"
            scene_blockers.append(issue)
            blocking_issues.append(issue)
        if media_type == "video" and not video_path:
            issue = f"scene_{seg.scene_number}_local_render_video_missing"
            scene_blockers.append(issue)
            blocking_issues.append(issue)

        asset: Dict[str, Any] = {
            "scene_number": seg.scene_number,
            "scene_id": seg.scene_id,
            "title": seg.title,
            "duration_seconds": int(round(seg.duration_seconds or 0)),
            "estimated_duration_seconds": int(round(seg.duration_seconds or 0)),
            "transition": seg.transition,
            "camera_motion_hint": "static",
            "render_mode": seg.render_mode,
            "motion_status": seg.motion_status,
            "voice_path": voice_path,
            "warnings": scene_warnings,
            "blocking_issues": scene_blockers,
        }
        if image_path:
            asset["image_path"] = image_path
        if video_path:
            asset["video_path"] = video_path
        assets.append(asset)

        scene: Dict[str, Any] = {
            "scene_number": seg.scene_number,
            "scene_id": seg.scene_id,
            "title": seg.title,
            "start_time": round(seg.start_seconds or 0, 3),
            "end_time": round(seg.end_seconds or 0, 3),
            "duration_seconds": int(round(seg.duration_seconds or 0)),
            "transition": "fade" if seg.transition == "dissolve" else seg.transition,
            "media_type": media_type,
            "camera_motion_hint": "static",
            "zoom_type": "static",
            "pan_direction": "none",
            "voice_path": voice_path,
            "warnings": scene_warnings,
            "blocking_issues": scene_blockers,
        }
        if media_type == "video":
            scene["video_path"] = video_path
            if image_path:
                scene["image_path"] = image_path
        else:
            scene["image_path"] = image_path
        scenes.append(scene)

    audio_path = ""
    if len(voice_paths) == 1:
        audio_path = voice_paths[0]
    elif len(voice_paths) > 1:
        warnings.append("storyboard_render_voice_mixdown_required")

    asset_manifest = {
        "run_id": safe_run_id,
        "generation_mode": "storyboard_local_render_handoff_v1",
        "assets": assets,
    }
    timeline_manifest = {
        "run_id": safe_run_id,
        "asset_manifest_path": _as_posix_path(asset_manifest_path),
        "assets_directory": _as_posix_path(asset_manifest_path.parent),
        "audio_path": audio_path,
        "total_scenes": len(scenes),
        "estimated_duration_seconds": int(round(render_timeline.total_duration_seconds or 0)),
        "scene_duration_default_seconds": 6,
        "scenes": scenes,
    }

    unique_warnings = list(dict.fromkeys(warnings))
    unique_blockers = list(dict.fromkeys(blocking_issues))
    status = "blocked" if unique_blockers else ("warning" if unique_warnings else "ready")
    recommendation = "Lokales timeline_manifest.json und asset_manifest.json schreiben, dann Renderer starten."
    if "storyboard_render_voice_mixdown_required" in unique_warnings:
        recommendation = "Mehrere Voice-Dateien zuerst zu einem Audio-Track mixen, dann lokalen Renderer starten."
    if status == "blocked":
        recommendation = "Render Timeline Blocker beheben, bevor ein lokales Render-Paket genutzt wird."

    return StoryboardLocalRenderPackageResult(
        overall_status=status,
        run_id=safe_run_id,
        timeline_manifest_path=_as_posix_path(timeline_manifest_path),
        asset_manifest_path=_as_posix_path(asset_manifest_path),
        final_video_path=_as_posix_path(final_video_path),
        timeline_manifest=timeline_manifest,
        asset_manifest=asset_manifest,
        render_command_hint=[
            "python",
            "scripts/render_final_story_video.py",
            "--timeline-manifest",
            _as_posix_path(timeline_manifest_path),
            "--output",
            _as_posix_path(final_video_path),
        ],
        warnings=unique_warnings,
        blocking_issues=unique_blockers,
        render_recommendation=recommendation,
    )


def build_storyboard_local_render_package_request(
    req: StoryboardLocalRenderPackageRequest,
) -> StoryboardLocalRenderPackageResult:
    """Request wrapper for the local render package endpoint."""

    return build_storyboard_local_render_package(
        req.render_timeline,
        run_id=req.run_id,
        output_root=req.output_root,
    )
