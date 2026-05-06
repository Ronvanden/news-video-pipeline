"""BA 29.6 — Safe final render execution (dry-run default, explicit --execute for local copy/render)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

_EXEC_VERSION = "ba29_6_v1"


def _s(v: Any) -> str:
    return str(v or "").strip()


def build_final_render_execution_result(
    *,
    production_summary: Dict[str, Any],
    output_dir: str | Path,
    execute: bool = False,
    preview_video_path: Optional[str] = None,
    _run: Optional[Callable[..., Any]] = None,
    _which: Optional[Callable[[str], Optional[str]]] = None,
) -> Dict[str, Any]:
    """
    Default dry-run: command preview only. With execute=True and readiness ready, copies preview to final
    via lightweight ffmpeg stream-copy when available, else shutil.copyfile.
    """
    ps = production_summary if isinstance(production_summary, dict) else {}
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    final_path = out_dir / "final_local_render.mp4"

    rr = ps.get("final_render_readiness_result") if isinstance(ps.get("final_render_readiness_result"), dict) else {}
    readiness = _s(rr.get("readiness_status")).lower()

    blocking: List[str] = []
    warns: List[str] = []
    executed = False

    if readiness != "ready":
        blocking.append("final_render_readiness_not_ready")
        return {
            "ok": False,
            "executed": False,
            "execution_version": _EXEC_VERSION,
            "output_video_path": str(final_path),
            "readiness_status": readiness or "unknown",
            "blocking_reasons": blocking,
            "warnings": warns,
            "ffmpeg_command_preview": None,
        }

    pv = _s(preview_video_path)
    if not pv:
        lp = ps.get("local_preview_video_path")
        pv = _s(lp) if lp else ""
    if not pv or not Path(pv).is_file():
        blocking.append("preview_video_missing_for_final_render")
        return {
            "ok": False,
            "executed": False,
            "execution_version": _EXEC_VERSION,
            "output_video_path": str(final_path),
            "readiness_status": readiness,
            "blocking_reasons": blocking,
            "warnings": warns + ["local_preview_video_missing"],
            "ffmpeg_command_preview": None,
        }

    cmd_preview = f"ffmpeg -y -i {pv} -c copy {final_path}"

    if not execute:
        return {
            "ok": True,
            "executed": False,
            "execution_version": _EXEC_VERSION,
            "output_video_path": str(final_path),
            "readiness_status": readiness,
            "blocking_reasons": [],
            "warnings": warns + ["dry_run_no_execution"],
            "ffmpeg_command_preview": cmd_preview,
        }

    run_fn = _run or subprocess.run
    which_fn = _which or shutil.which
    ffmpeg = which_fn("ffmpeg") or ""
    ok_run = False
    if ffmpeg:
        try:
            proc = run_fn(
                [str(ffmpeg), "-y", "-i", str(Path(pv).resolve()), "-c", "copy", str(final_path)],
                capture_output=True,
                text=True,
                timeout=600,
            )
            ok_run = getattr(proc, "returncode", 1) == 0
        except (OSError, subprocess.TimeoutExpired):
            ok_run = False
    if not ok_run:
        try:
            shutil.copyfile(Path(pv).resolve(), final_path)
            ok_run = final_path.is_file()
            if ok_run:
                warns.append("final_render_used_file_copy_fallback")
        except OSError:
            ok_run = False

    executed = bool(ok_run)
    if not executed:
        blocking.append("final_render_execution_failed")
    return {
        "ok": bool(executed),
        "executed": bool(executed),
        "execution_version": _EXEC_VERSION,
        "output_video_path": str(final_path.resolve()) if final_path.is_file() else str(final_path),
        "readiness_status": readiness,
        "blocking_reasons": blocking,
        "warnings": warns,
        "ffmpeg_command_preview": cmd_preview,
    }
