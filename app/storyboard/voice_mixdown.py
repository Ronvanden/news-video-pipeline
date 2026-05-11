"""Local voice mixdown for storyboard render timelines."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

from app.storyboard.schema import (
    StoryboardRenderTimelineResult,
    StoryboardVoiceMixdownRequest,
    StoryboardVoiceMixdownResult,
)


def _dedupe(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for item in items:
        value = " ".join(str(item or "").split()).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _safe_run_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(value or "").strip())
    return cleaned.strip("._-") or "storyboard_voice_mixdown_v1"


def _voice_paths(render_timeline: StoryboardRenderTimelineResult) -> List[str]:
    return sorted({str(seg.voice_path or "").strip() for seg in (render_timeline.segments or []) if str(seg.voice_path or "").strip()})


def _output_path(*, run_id: str, output_root: str) -> Path:
    return Path(output_root or "output") / "storyboard_runs" / _safe_run_id(run_id) / "audio" / "storyboard_voice_mixdown.mp3"


def _file_info(path: Path) -> Tuple[bool, Optional[int]]:
    try:
        if not path.is_file():
            return False, None
        return True, path.stat().st_size
    except OSError:
        return False, None


def _escape_concat_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace("'", "'\\''")


def _concat_mp3_segments_ffmpeg(
    segment_paths: Sequence[Path],
    out_mp3: Path,
    *,
    ffmpeg_bin: str,
    run_fn: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> Tuple[bool, List[str]]:
    if not segment_paths:
        return False, ["storyboard_voice_mixdown_inputs_empty"]
    if len(segment_paths) == 1:
        try:
            shutil.copyfile(segment_paths[0], out_mp3)
            return True, []
        except OSError as exc:
            return False, [f"storyboard_voice_mixdown_copy_failed:{type(exc).__name__}"]
    if not ffmpeg_bin:
        return False, ["ffmpeg_missing"]
    list_txt = out_mp3.parent / f"_concat_{out_mp3.stem}.txt"
    lines = [f"file '{_escape_concat_path(path)}'" for path in segment_paths]
    try:
        list_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
        cmd = [
            ffmpeg_bin,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_txt),
            "-c",
            "copy",
            str(out_mp3),
        ]
        run_fn(cmd, check=True, capture_output=True, text=True)
        return True, []
    except FileNotFoundError:
        return False, ["ffmpeg_missing"]
    except subprocess.CalledProcessError:
        return False, ["storyboard_voice_mixdown_ffmpeg_failed"]
    except OSError as exc:
        return False, [f"storyboard_voice_mixdown_write_failed:{type(exc).__name__}"]
    finally:
        try:
            list_txt.unlink(missing_ok=True)
        except OSError:
            pass


def execute_storyboard_voice_mixdown(
    render_timeline: StoryboardRenderTimelineResult,
    *,
    run_id: str = "storyboard_voice_mixdown_v1",
    output_root: str = "output",
    dry_run: bool = False,
    ffmpeg_bin: Optional[str] = None,
    which_fn: Callable[[str], Optional[str]] = shutil.which,
    run_fn: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> StoryboardVoiceMixdownResult:
    """Mix scene-level voice files into one renderer-ready MP3."""

    input_voice_paths = _voice_paths(render_timeline)
    mixed_audio_path = _output_path(run_id=run_id, output_root=output_root)
    warnings: List[str] = []
    blocking_issues: List[str] = []

    if render_timeline.overall_status == "blocked":
        blocking_issues.append("storyboard_render_timeline_blocked")
    if not input_voice_paths:
        return StoryboardVoiceMixdownResult(
            execution_status="skipped",
            dry_run=dry_run,
            run_id=_safe_run_id(run_id),
            mixed_audio_path=str(mixed_audio_path.as_posix()),
            input_voice_paths=[],
            warnings=["storyboard_voice_mixdown_no_voice_paths"],
            render_recommendation="Zuerst echte Voice-Dateien erzeugen, dann Mixdown erneut starten.",
        )
    if dry_run:
        if len(input_voice_paths) == 1:
            warnings.append("storyboard_voice_mixdown_single_voice_passthrough")
        return StoryboardVoiceMixdownResult(
            execution_status="dry_run",
            dry_run=True,
            run_id=_safe_run_id(run_id),
            mixed_audio_path=str(mixed_audio_path.as_posix()),
            input_voice_paths=input_voice_paths,
            warnings=_dedupe(warnings),
            blocking_issues=blocking_issues,
            render_recommendation="Lokalen Voice Mixdown ausführen, damit das Render-Paket einen globalen audio_path bekommt.",
        )

    resolved_inputs = [Path(path) for path in input_voice_paths]
    missing_inputs = [str(path.as_posix()) for path in resolved_inputs if not path.is_file()]
    if missing_inputs:
        return StoryboardVoiceMixdownResult(
            execution_status="failed",
            dry_run=False,
            run_id=_safe_run_id(run_id),
            mixed_audio_path=str(mixed_audio_path.as_posix()),
            input_voice_paths=input_voice_paths,
            warnings=[f"storyboard_voice_mixdown_input_missing:{path}" for path in missing_inputs],
            blocking_issues=["storyboard_voice_mixdown_inputs_missing"],
            render_recommendation="Fehlende Voice-Dateien erneut erzeugen, dann Mixdown wiederholen.",
        )

    try:
        mixed_audio_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return StoryboardVoiceMixdownResult(
            execution_status="failed",
            dry_run=False,
            run_id=_safe_run_id(run_id),
            mixed_audio_path=str(mixed_audio_path.as_posix()),
            input_voice_paths=input_voice_paths,
            warnings=[f"storyboard_voice_mixdown_output_dir_failed:{type(exc).__name__}:path={mixed_audio_path.parent.as_posix()}"],
            blocking_issues=["storyboard_voice_mixdown_output_dir_failed"],
            render_recommendation="Output-Pfad prüfen und Mixdown erneut starten.",
        )

    ffmpeg = ffmpeg_bin if ffmpeg_bin is not None else (which_fn("ffmpeg") or "")
    ok, mix_warnings = _concat_mp3_segments_ffmpeg(resolved_inputs, mixed_audio_path, ffmpeg_bin=ffmpeg, run_fn=run_fn)
    warnings.extend(mix_warnings)
    output_exists, file_size_bytes = _file_info(mixed_audio_path)
    if ok and output_exists:
        if len(input_voice_paths) == 1:
            warnings.append("storyboard_voice_mixdown_single_voice_passthrough")
        return StoryboardVoiceMixdownResult(
            execution_status="completed",
            dry_run=False,
            run_id=_safe_run_id(run_id),
            mixed_audio_path=str(mixed_audio_path.as_posix()),
            output_exists=True,
            file_size_bytes=file_size_bytes,
            input_voice_paths=input_voice_paths,
            warnings=_dedupe(warnings),
            blocking_issues=blocking_issues,
            render_recommendation="Local Render Package neu bauen, damit audio_path auf die Mixdown-Datei zeigt.",
        )

    warnings.append(f"storyboard_voice_mixdown_output_missing:path={mixed_audio_path.as_posix()}")
    return StoryboardVoiceMixdownResult(
        execution_status="failed",
        dry_run=False,
        run_id=_safe_run_id(run_id),
        mixed_audio_path=str(mixed_audio_path.as_posix()),
        input_voice_paths=input_voice_paths,
        warnings=_dedupe(warnings),
        blocking_issues=_dedupe(blocking_issues + ["storyboard_voice_mixdown_failed"]),
        render_recommendation="ffmpeg/Mixdown-Fehler beheben und den lokalen Voice-Mixdown erneut starten.",
    )


def execute_storyboard_voice_mixdown_request(
    req: StoryboardVoiceMixdownRequest,
) -> StoryboardVoiceMixdownResult:
    """Request wrapper for local storyboard voice mixdown."""

    return execute_storyboard_voice_mixdown(
        req.render_timeline,
        run_id=req.run_id,
        output_root=req.output_root,
        dry_run=req.dry_run,
    )
