"""BA 29.2 — Local preview MP4 from render_input_bundle (optional FFmpeg)."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

_PREVIEW_VERSION = "ba29_2_v1"
_DEFAULT_SCENE_SECONDS = 5.0
_VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _s(v: Any) -> str:
    return str(v or "").strip()


def _float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def check_ffmpeg_available(
    *,
    _which: Optional[Callable[[str], Optional[str]]] = None,
    _run: Optional[Callable[..., Any]] = None,
    _timeout_sec: float = 8.0,
) -> Tuple[bool, str]:
    """Return (available, ffmpeg_path_or_empty). Injectable for tests."""
    which_fn = _which or shutil.which
    run_fn = _run or subprocess.run
    path = which_fn("ffmpeg") or ""
    if not path:
        return False, ""
    try:
        proc = run_fn([path, "-version"], capture_output=True, text=True, timeout=_timeout_sec)
    except (OSError, subprocess.TimeoutExpired):
        return False, str(path)
    if getattr(proc, "returncode", 1) != 0:
        return False, str(path)
    return True, str(path)


def _is_placeholder_clip(path: Path) -> bool:
    if not path or not _s(str(path)):
        return True
    if path.suffix.lower() == ".json":
        return True
    return False


def _is_video_media(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in _VIDEO_EXT and not _is_placeholder_clip(path)


def _is_image_media(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in _IMAGE_EXT


def _resolve_media_path(raw: str, bases: Sequence[Path]) -> Path:
    p = Path(raw)
    if p.is_file():
        return p.resolve()
    for b in bases:
        if not b:
            continue
        cand = (b / raw).resolve()
        if cand.is_file():
            return cand
    return p.resolve()


def load_json_path(path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not _s(path):
        return None
    p = Path(path)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def build_preview_scenes(
    *,
    bundle: Dict[str, Any],
    bundle_path: Optional[str],
    timeline: Optional[Dict[str, Any]],
    default_duration_seconds: float = _DEFAULT_SCENE_SECONDS,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Build ordered scene list with resolved paths and durations.
    Each item: duration_seconds, image_path (Path or empty), clip_path (Path or empty), use_video (bool)
    """
    warns: List[str] = []
    bases: List[Path] = []
    if _s(bundle_path):
        bases.append(Path(bundle_path).resolve().parent)
    if timeline and _s(bundle.get("motion_timeline_manifest_path")):
        bases.append(Path(str(bundle.get("motion_timeline_manifest_path"))).resolve().parent)

    scenes_out: List[Dict[str, Any]] = []

    if isinstance(timeline, dict) and isinstance(timeline.get("scenes"), list):
        for sc in timeline.get("scenes") or []:
            if not isinstance(sc, dict):
                continue
            dur = _float(sc.get("duration_seconds"), default_duration_seconds)
            if dur <= 0:
                dur = default_duration_seconds
            ip = _s(sc.get("image_path"))
            cp = _s(sc.get("clip_path"))
            img_p = _resolve_media_path(ip, bases) if ip else Path()
            clip_p = _resolve_media_path(cp, bases) if cp else Path()
            use_video = bool(cp) and _is_video_media(clip_p) and not _is_placeholder_clip(clip_p)
            if cp and not use_video and not _is_placeholder_clip(Path(cp)):
                if clip_p.suffix.lower() == ".json":
                    warns.append(f"scene_{sc.get('scene_number')}:placeholder_clip_json")
                elif not clip_p.is_file():
                    warns.append(f"scene_{sc.get('scene_number')}:clip_not_found")
            scenes_out.append(
                {
                    "scene_number": sc.get("scene_number"),
                    "duration_seconds": float(dur),
                    "image_path": img_p,
                    "clip_path": clip_p,
                    "use_video": use_video,
                }
            )
        return scenes_out, warns

    imgs = [_resolve_media_path(_s(x), bases) for x in (bundle.get("image_paths") or []) if _s(x)]
    clips_raw = [_s(x) for x in (bundle.get("clip_paths") or []) if _s(x)]
    clips = [_resolve_media_path(x, bases) for x in clips_raw]
    n = max(len(imgs), len(clips), 0)
    if n == 0:
        return [], warns
    for i in range(n):
        img_p = imgs[i] if i < len(imgs) else Path()
        clip_p = clips[i] if i < len(clips) else Path()
        use_video = i < len(clips) and _is_video_media(clip_p) and not _is_placeholder_clip(clip_p)
        scenes_out.append(
            {
                "scene_number": i + 1,
                "duration_seconds": float(default_duration_seconds),
                "image_path": img_p,
                "clip_path": clip_p,
                "use_video": use_video,
            }
        )
    return scenes_out, warns


def _write_concat_list(segment_files: List[Path], concat_path: Path) -> None:
    """Segment files must live in the same directory as ``concat_path`` (relative names only)."""
    base = concat_path.parent.resolve()
    lines = []
    for p in segment_files:
        pr = p.resolve()
        if pr.parent != base:
            raise ValueError("concat segments must be colocated with concat list")
        lines.append(f"file '{pr.name}'")
    concat_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_ffmpeg(
    cmd: List[str],
    *,
    _run: Callable[..., Any],
) -> Tuple[bool, str]:
    try:
        proc = _run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        return False, "ffmpeg_timeout"
    except OSError as e:
        return False, f"ffmpeg_os_error:{e}"
    if getattr(proc, "returncode", 1) != 0:
        err = (getattr(proc, "stderr", None) or "")[:500]
        return False, err or "ffmpeg_failed"
    return True, ""


def build_local_preview_readme(*, output_video: Path, result: Dict[str, Any]) -> str:
    lines = [
        "# Lokale Vorschau (BA 29.2)",
        "",
        f"- Video: `{output_video.name}`",
        f"- Status ok: **{result.get('ok')}**",
        f"- Szenen: {result.get('scenes_rendered')}",
        f"- Dauer (s): {result.get('duration_seconds')}",
        "",
        "## Hinweis",
        "Dies ist eine vereinfachte Operator-Vorschau, kein finales YouTube-Master.",
        "",
    ]
    br = result.get("blocking_reasons") or []
    if br:
        lines.append("## Blockierende Gründe")
        for b in br:
            lines.append(f"- {b}")
    return "\n".join(lines)


def run_local_preview_from_bundle(
    *,
    bundle: Dict[str, Any],
    bundle_path: str,
    output_dir: str | Path,
    output_video_name: str = "local_preview.mp4",
    timeline_override: Optional[Dict[str, Any]] = None,
    default_scene_seconds: float = _DEFAULT_SCENE_SECONDS,
    _which: Optional[Callable[[str], Optional[str]]] = None,
    _run: Optional[Callable[..., Any]] = None,
) -> Dict[str, Any]:
    """
    Build a simple MP4 preview from bundle + optional timeline. No secrets, no uploads.
    When FFmpeg is missing, returns ok=False and error_code ffmpeg_missing (no exception).
    """
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_video = (out_dir / output_video_name).resolve()

    base_result: Dict[str, Any] = {
        "ok": False,
        "preview_render_version": _PREVIEW_VERSION,
        "input_bundle_path": _s(bundle_path),
        "output_video_path": str(out_video),
        "duration_seconds": 0.0,
        "scenes_rendered": 0,
        "used_images_count": 0,
        "used_clips_count": 0,
        "used_audio": False,
        "ffmpeg_available": False,
        "blocking_reasons": [],
        "warnings": [],
        "error_code": None,
    }

    run_fn = _run or subprocess.run
    ff_ok, ff_path = check_ffmpeg_available(_which=_which, _run=run_fn)
    base_result["ffmpeg_available"] = bool(ff_ok)
    if not ff_ok:
        base_result["error_code"] = "ffmpeg_missing"
        base_result["blocking_reasons"] = ["ffmpeg_missing"]
        base_result["warnings"].append("install_ffmpeg_for_local_preview")
        readme = out_dir / "README_PREVIEW.md"
        readme.write_text(build_local_preview_readme(output_video=out_video, result=base_result), encoding="utf-8")
        return base_result

    timeline = timeline_override
    if timeline is None:
        tm_path = _s(bundle.get("motion_timeline_manifest_path"))
        timeline = load_json_path(tm_path) if tm_path else None

    scenes, swarns = build_preview_scenes(
        bundle=bundle,
        bundle_path=bundle_path,
        timeline=timeline,
        default_duration_seconds=default_scene_seconds,
    )
    base_result["warnings"].extend(swarns)

    segments: List[Path] = []
    used_img = 0
    used_clip = 0
    total_dur = 0.0

    if not scenes:
        base_result["blocking_reasons"] = ["no_preview_scenes_derived"]
        return base_result

    with tempfile.TemporaryDirectory(prefix="ba292_preview_") as tmp:
        tmp_path = Path(tmp)
        seg_idx = 0
        for sc in scenes:
            dur = float(sc.get("duration_seconds") or default_scene_seconds)
            total_dur += dur
            clip_p: Path = sc.get("clip_path") or Path()
            img_p: Path = sc.get("image_path") or Path()
            use_video = bool(sc.get("use_video"))

            if use_video and _is_video_media(clip_p):
                seg = tmp_path / f"seg_{seg_idx:04d}.mp4"
                cmd = [
                    ff_path,
                    "-y",
                    "-i",
                    str(clip_p.resolve()),
                    "-t",
                    str(dur),
                    "-an",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(seg),
                ]
                ok, err = _run_ffmpeg(cmd, _run=run_fn)
                if not ok:
                    base_result["warnings"].append(f"segment_video_failed:{err[:120]}")
                    use_video = False
                else:
                    segments.append(seg)
                    used_clip += 1
                    seg_idx += 1
                    continue

            if img_p and _is_image_media(img_p):
                seg = tmp_path / f"seg_{seg_idx:04d}.mp4"
                cmd = [
                    ff_path,
                    "-y",
                    "-loop",
                    "1",
                    "-t",
                    str(dur),
                    "-i",
                    str(img_p.resolve()),
                    "-an",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(seg),
                ]
                ok, err = _run_ffmpeg(cmd, _run=run_fn)
                if not ok:
                    base_result["blocking_reasons"].append(f"image_segment_failed:{err[:120]}")
                    base_result["warnings"].append("preview_partial_failure")
                    break
                segments.append(seg)
                used_img += 1
                seg_idx += 1
                continue

            base_result["warnings"].append(f"scene_{sc.get('scene_number')}:no_usable_media_skipped")

        if not segments:
            base_result["blocking_reasons"].append("no_media_segments_built")
            base_result["error_code"] = "no_media"
            return base_result

        if len(segments) == 1:
            shutil.copyfile(segments[0], out_video)
        else:
            concat_list = tmp_path / "concat.txt"
            _write_concat_list(segments, concat_list)
            cmd = [ff_path, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(out_video)]
            ok, err = _run_ffmpeg(cmd, _run=run_fn)
            if not ok:
                base_result["blocking_reasons"].append(f"concat_failed:{err[:200]}")
                base_result["error_code"] = "ffmpeg_concat_failed"
                return base_result

    base_result["ok"] = True
    base_result["scenes_rendered"] = int(len(segments))
    base_result["duration_seconds"] = float(round(total_dur, 3))
    base_result["used_images_count"] = int(used_img)
    base_result["used_clips_count"] = int(used_clip)
    base_result["used_audio"] = False
    base_result["blocking_reasons"] = []
    base_result["error_code"] = None
    base_result["warnings"] = list(dict.fromkeys([_s(w) for w in base_result["warnings"] if _s(w)]))

    readme = out_dir / "README_PREVIEW.md"
    readme.write_text(build_local_preview_readme(output_video=out_video, result=base_result), encoding="utf-8")
    open_txt = out_dir / "OPEN_PREVIEW.txt"
    open_txt.write_text(
        f"Local preview written by {_PREVIEW_VERSION}\nVideo: {out_video.name}\n",
        encoding="utf-8",
    )
    return base_result
