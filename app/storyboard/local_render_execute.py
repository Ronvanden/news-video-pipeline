"""Local storyboard render execution using the existing ffmpeg renderer."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.storyboard.schema import (
    StoryboardLocalRenderExecutionRequest,
    StoryboardLocalRenderExecutionResult,
    StoryboardLocalRenderPackageResult,
)


ROOT = Path(__file__).resolve().parents[2]
_RENDER_SCRIPT = ROOT / "scripts" / "render_final_story_video.py"


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
            render_recommendation="Manifest-Pfade prüfen und lokalen Render erneut starten.",
        )

    if dry_run:
        return StoryboardLocalRenderExecutionResult(
            execution_status="dry_run",
            dry_run=True,
            run_id=safe_run_id,
            asset_manifest_path=asset_manifest_path.as_posix(),
            timeline_manifest_path=timeline_manifest_path.as_posix(),
            final_video_path=final_video_path.as_posix(),
            manifest_written=True,
            warnings=_dedupe(warnings),
            blocking_issues=[],
            render_recommendation="Dry-Run fertig. Für MP4-Erzeugung den lokalen Render ohne dry_run starten.",
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
    status = "completed" if video_created else "failed"
    recommendation = "Lokaler Storyboard-Render erfolgreich. Final Video kann jetzt im Dashboard geprüft werden."
    if status == "failed":
        recommendation = "Renderer-Blocker prüfen und den lokalen Render erneut starten."

    return StoryboardLocalRenderExecutionResult(
        execution_status=status,
        dry_run=False,
        run_id=safe_run_id,
        asset_manifest_path=asset_manifest_path.as_posix(),
        timeline_manifest_path=timeline_manifest_path.as_posix(),
        final_video_path=final_video_path.as_posix(),
        render_output_manifest_path=str(meta.get("render_output_manifest_path") or ""),
        manifest_written=True,
        video_created=video_created,
        output_exists=output_exists,
        file_size_bytes=file_size_bytes,
        warnings=_dedupe(warnings + render_warnings),
        blocking_issues=_dedupe(blocking_issues + render_blockers),
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
