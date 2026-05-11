"""Local storyboard render execution using the existing ffmpeg renderer."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.storyboard.schema import (
    StoryboardLocalRenderExecutionRequest,
    StoryboardLocalRenderExecutionResult,
    StoryboardLocalRenderPackageResult,
)


ROOT = Path(__file__).resolve().parents[2]
_RENDER_SCRIPT = ROOT / "scripts" / "render_final_story_video.py"
_AUDIO_GAP_TOLERANCE_SECONDS = 3.0
_AUDIO_GAP_TOLERANCE_RATIO = 0.05
_AUDIO_GAP_BLOCK_SECONDS = 8.0
_AUDIO_GAP_BLOCK_RATIO = 0.12


def _safe_run_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(value or "").strip())
    return cleaned.strip("._-") or "storyboard_local_render_execute_v1"


def _dedupe(items: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for item in items:
        value = " ".join(str(item or "").split()).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _file_info(path: Path) -> Tuple[bool, Optional[int]]:
    try:
        if not path.is_file():
            return False, None
        return True, path.stat().st_size
    except OSError:
        return False, None


def _probe_audio_duration_seconds(path: Path) -> Tuple[Optional[float], List[str]]:
    warns: List[str] = []
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None, ["audio_duration_probe_unavailable"]
    try:
        cp = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        raw = (cp.stdout or "").strip()
        if not raw or raw == "N/A":
            return None, ["audio_duration_probe_empty"]
        return float(raw), warns
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None, ["audio_duration_probe_failed"]


def _timeline_seconds_from_manifest(timeline_manifest: Dict[str, Any]) -> Optional[float]:
    try:
        estimated = timeline_manifest.get("estimated_duration_seconds")
        if estimated is not None:
            return float(estimated)
        scenes = timeline_manifest.get("scenes") or []
        if not isinstance(scenes, list):
            return None
        return float(sum(float(scene.get("duration_seconds") or 0) for scene in scenes))
    except (TypeError, ValueError, AttributeError):
        return None


def _audio_gap_status(
    timeline_seconds: Optional[float],
    audio_seconds: Optional[float],
) -> Tuple[Optional[float], Optional[float], List[str], List[str]]:
    warnings: List[str] = []
    blocking: List[str] = []
    if timeline_seconds is None or timeline_seconds <= 0:
        warnings.append("timeline_duration_unavailable")
        return None, None, warnings, blocking
    if audio_seconds is None:
        warnings.append("audio_duration_unavailable")
        return None, None, warnings, blocking
    gap = max(0.0, float(timeline_seconds) - float(audio_seconds))
    ratio = gap / float(timeline_seconds) if float(timeline_seconds) > 0 else None
    if ratio is None:
        warnings.append("audio_gap_ratio_unavailable")
        return gap, None, warnings, blocking
    if gap <= _AUDIO_GAP_TOLERANCE_SECONDS or ratio <= _AUDIO_GAP_TOLERANCE_RATIO:
        return gap, ratio, warnings, blocking
    warning_tag = f"audio_gap_exceeds_tolerance:{gap:.3f}"
    if gap > _AUDIO_GAP_BLOCK_SECONDS and ratio > _AUDIO_GAP_BLOCK_RATIO:
        blocking.append(warning_tag)
        blocking.append("audio_shorter_than_timeline_blocking_gap")
    else:
        warnings.append(warning_tag)
    return gap, ratio, warnings, blocking


def _write_json(path: Path, body: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_render_fn() -> Callable[..., Dict[str, Any]]:
    spec = importlib.util.spec_from_file_location("storyboard_render_final_story_video", _RENDER_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("render_script_load_failed")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, "render_final_story_video", None)
    if not callable(fn):
        raise RuntimeError("render_final_story_video_missing")
    return fn


def execute_storyboard_local_render(
    local_render_package: StoryboardLocalRenderPackageResult,
    *,
    run_id: str = "storyboard_local_render_execute_v1",
    output_root: str = "output",
    dry_run: bool = False,
    motion_mode: str = "basic",
    render_fn: Optional[Callable[..., Dict[str, Any]]] = None,
) -> StoryboardLocalRenderExecutionResult:
    """Write manifests and optionally invoke the existing local renderer."""

    safe_run_id = _safe_run_id(run_id)
    warnings: List[str] = list(local_render_package.warnings or [])
    blocking_issues: List[str] = list(local_render_package.blocking_issues or [])

    asset_manifest_path = Path(local_render_package.asset_manifest_path or "")
    timeline_manifest_path = Path(local_render_package.timeline_manifest_path or "")
    final_video_path = Path(local_render_package.final_video_path or "")

    if local_render_package.overall_status == "blocked":
        blocking_issues.append("storyboard_local_render_package_blocked")
    if not local_render_package.asset_manifest:
        blocking_issues.append("storyboard_local_render_asset_manifest_missing")
    if not local_render_package.timeline_manifest:
        blocking_issues.append("storyboard_local_render_timeline_manifest_missing")
    if not str(asset_manifest_path).strip():
        blocking_issues.append("storyboard_local_render_asset_manifest_path_missing")
    if not str(timeline_manifest_path).strip():
        blocking_issues.append("storyboard_local_render_timeline_manifest_path_missing")
    if not str(final_video_path).strip():
        blocking_issues.append("storyboard_local_render_output_path_missing")

    if blocking_issues:
        return StoryboardLocalRenderExecutionResult(
            execution_status="failed",
            dry_run=dry_run,
            run_id=safe_run_id,
            asset_manifest_path=str(asset_manifest_path.as_posix()) if str(asset_manifest_path) else "",
            timeline_manifest_path=str(timeline_manifest_path.as_posix()) if str(timeline_manifest_path) else "",
            final_video_path=str(final_video_path.as_posix()) if str(final_video_path) else "",
            warnings=_dedupe(warnings),
            blocking_issues=_dedupe(blocking_issues),
            render_recommendation="Lokales Render Package zuerst in einen nicht-blockierten Zustand bringen.",
        )

    try:
        _write_json(asset_manifest_path, local_render_package.asset_manifest)
        _write_json(timeline_manifest_path, local_render_package.timeline_manifest)
    except OSError as exc:
        return StoryboardLocalRenderExecutionResult(
            execution_status="failed",
            dry_run=dry_run,
            run_id=safe_run_id,
            asset_manifest_path=asset_manifest_path.as_posix(),
            timeline_manifest_path=timeline_manifest_path.as_posix(),
            final_video_path=final_video_path.as_posix(),
            warnings=_dedupe(warnings + [f"storyboard_local_render_manifest_write_failed:{type(exc).__name__}"]),
            blocking_issues=["storyboard_local_render_manifest_write_failed"],
            render_recommendation="Manifest-Pfade pr?fen und lokalen Render erneut starten.",
        )

    timeline_seconds = _timeline_seconds_from_manifest(local_render_package.timeline_manifest)
    audio_seconds: Optional[float] = None
    metric_warnings: List[str] = []
    metric_blocking: List[str] = []
    audio_path_raw = str(local_render_package.timeline_manifest.get("audio_path") or "").strip()
    audio_path = Path(audio_path_raw) if audio_path_raw else None
    if audio_path and audio_path.is_file():
        audio_seconds, probe_warnings = _probe_audio_duration_seconds(audio_path)
        metric_warnings.extend(probe_warnings)
    elif audio_path_raw:
        metric_warnings.append("audio_path_set_but_file_missing_for_duration_probe")
    gap_seconds, gap_ratio, gap_warnings, gap_blocking = _audio_gap_status(timeline_seconds, audio_seconds)
    metric_warnings.extend(gap_warnings)
    metric_blocking.extend(gap_blocking)

    if dry_run:
        return StoryboardLocalRenderExecutionResult(
            execution_status="dry_run",
            dry_run=True,
            run_id=safe_run_id,
            asset_manifest_path=asset_manifest_path.as_posix(),
            timeline_manifest_path=timeline_manifest_path.as_posix(),
            final_video_path=final_video_path.as_posix(),
            manifest_written=True,
            timeline_seconds=timeline_seconds,
            audio_duration_seconds=audio_seconds,
            audio_gap_seconds=gap_seconds,
            audio_gap_ratio=gap_ratio,
            warnings=_dedupe(warnings + metric_warnings),
            blocking_issues=_dedupe(metric_blocking),
            render_recommendation="Dry-Run fertig. F?r MP4-Erzeugung den lokalen Render ohne dry_run starten.",
        )

    try:
        render = render_fn or _load_render_fn()
        meta = render(
            timeline_manifest_path,
            output_video=final_video_path,
            motion_mode=(motion_mode or "basic"),
            run_id=safe_run_id,
            write_output_manifest=True,
            manifest_root=Path(output_root or "output"),
        )
    except Exception as exc:
        return StoryboardLocalRenderExecutionResult(
            execution_status="failed",
            dry_run=False,
            run_id=safe_run_id,
            asset_manifest_path=asset_manifest_path.as_posix(),
            timeline_manifest_path=timeline_manifest_path.as_posix(),
            final_video_path=final_video_path.as_posix(),
            manifest_written=True,
            warnings=_dedupe(warnings + [f"storyboard_local_render_execution_exception:{type(exc).__name__}"]),
            blocking_issues=["storyboard_local_render_execution_exception"],
            render_recommendation="Renderer-Fehler beheben und lokalen Render erneut starten.",
        )

    render_warnings = [str(x) for x in (meta.get("warnings") or []) if str(x).strip()]
    render_blockers = [str(x) for x in (meta.get("blocking_reasons") or []) if str(x).strip()]
    output_exists, file_size_bytes = _file_info(final_video_path)
    video_created = bool(meta.get("video_created")) and output_exists
    all_warnings = _dedupe(warnings + metric_warnings + render_warnings)
    all_blocking = _dedupe(blocking_issues + metric_blocking + render_blockers)
    status = "completed" if video_created else "failed"
    recommendation = "Lokaler Storyboard-Render erfolgreich. Final Video kann jetzt im Dashboard gepr?ft werden."
    if status == "failed":
        recommendation = "Renderer-Blocker pr?fen und den lokalen Render erneut starten."
    elif metric_blocking:
        recommendation = "Audio-Dauer weicht deutlich von der Timeline ab; Review vor Production-Greenlight pr?fen."

    return StoryboardLocalRenderExecutionResult(
        execution_status=status,
        dry_run=False,
        run_id=safe_run_id,
        asset_manifest_path=asset_manifest_path.as_posix(),
        timeline_manifest_path=timeline_manifest_path.as_posix(),
        final_video_path=final_video_path.as_posix(),
        render_output_manifest_path=str(meta.get("render_output_manifest_path") or ""),
        timeline_seconds=timeline_seconds,
        audio_duration_seconds=audio_seconds,
        audio_gap_seconds=gap_seconds,
        audio_gap_ratio=gap_ratio,
        manifest_written=True,
        video_created=video_created,
        output_exists=output_exists,
        file_size_bytes=file_size_bytes,
        warnings=all_warnings,
        blocking_issues=all_blocking,
        render_recommendation=recommendation,
    )


def execute_storyboard_local_render_request(

    req: StoryboardLocalRenderExecutionRequest,
) -> StoryboardLocalRenderExecutionResult:
    """Request wrapper for local storyboard render execution."""

    return execute_storyboard_local_render(
        req.local_render_package,
        run_id=req.run_id,
        output_root=req.output_root,
        dry_run=req.dry_run,
        motion_mode=req.motion_mode,
    )
