"""BA 19.2 — timeline_manifest + Bilder + Audio → MP4 (ffmpeg)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def which_ffmpeg() -> Optional[str]:
    return shutil.which("ffmpeg")


def which_ffprobe() -> Optional[str]:
    return shutil.which("ffprobe")


def load_timeline_manifest(path: Path) -> Dict[str, Any]:
    p = path.resolve()
    if not p.is_file():
        raise FileNotFoundError(f"timeline_manifest not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _escape_concat_path(p: Path) -> str:
    s = p.resolve().as_posix()
    return s.replace("'", "'\\''")


def _write_concat_list(scenes: List[Dict[str, Any]], assets_dir: Path, tmp_list: Path) -> None:
    lines: List[str] = []
    for i, sc in enumerate(scenes):
        img = assets_dir / str(sc.get("image_path") or "")
        dur = float(sc.get("duration_seconds") or 6)
        lines.append(f"file '{_escape_concat_path(img)}'")
        lines.append(f"duration {dur}")
    if scenes:
        last = assets_dir / str(scenes[-1].get("image_path") or "")
        lines.append(f"file '{_escape_concat_path(last)}'")
        lines.append("duration 0.04")
    tmp_list.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _probe_video_duration(video: Path, ffprobe: str) -> Tuple[Optional[float], List[str]]:
    warns: List[str] = []
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
                str(video),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return float((cp.stdout or "").strip()), warns
    except Exception:
        warns.append("output_duration_probe_failed")
        return None, warns


def render_final_story_video(
    timeline_path: Path,
    *,
    output_video: Path,
    ffmpeg_bin: Optional[str] = None,
    ffprobe_bin: Optional[str] = None,
) -> Dict[str, Any]:
    """
    MVP: concat demuxer → scale/pad 1920x1080 → H.264 + optional AAC.
    Ohne Audio: stumm (warnings audio_missing_silent_render).
    """
    warnings: List[str] = []
    blocking: List[str] = []
    ffprobe = ffprobe_bin or which_ffprobe()

    try:
        tl = load_timeline_manifest(timeline_path)
    except (OSError, json.JSONDecodeError, FileNotFoundError) as e:
        return {
            "video_created": False,
            "output_path": str(output_video),
            "duration_seconds": None,
            "scene_count": 0,
            "warnings": warnings + [f"timeline_load_failed:{type(e).__name__}"],
            "blocking_reasons": ["timeline_manifest_invalid_or_missing"],
        }

    scenes = tl.get("scenes") or []
    if not isinstance(scenes, list) or not scenes:
        return {
            "video_created": False,
            "output_path": str(output_video),
            "duration_seconds": None,
            "scene_count": 0,
            "warnings": warnings,
            "blocking_reasons": ["timeline_scenes_empty"],
        }

    n_scenes = len(scenes)
    ffmpeg = ffmpeg_bin if ffmpeg_bin is not None else which_ffmpeg()
    if not ffmpeg:
        return {
            "video_created": False,
            "output_path": str(output_video),
            "duration_seconds": None,
            "scene_count": n_scenes,
            "warnings": warnings,
            "blocking_reasons": ["ffmpeg_missing"],
        }

    assets_dir = Path(str(tl.get("assets_directory") or ""))
    if not assets_dir.is_dir():
        return {
            "video_created": False,
            "output_path": str(output_video),
            "duration_seconds": None,
            "scene_count": n_scenes,
            "warnings": warnings,
            "blocking_reasons": ["assets_directory_missing"],
        }

    for sc in scenes:
        ip = assets_dir / str(sc.get("image_path") or "")
        if not ip.is_file():
            return {
                "video_created": False,
                "output_path": str(output_video),
                "duration_seconds": None,
                "scene_count": n_scenes,
                "warnings": warnings,
                "blocking_reasons": [f"missing_image:{sc.get('image_path')}"],
            }

    audio_path = (tl.get("audio_path") or "").strip()
    audio_file: Optional[Path] = Path(audio_path) if audio_path else None
    if audio_file and not audio_file.is_file():
        warnings.append("audio_path_set_but_file_missing_silent_render")
        audio_file = None
    if not audio_file:
        warnings.append("audio_missing_silent_render")

    output_video.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(suffix="_concat.txt", text=True)
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        _write_concat_list(scenes, assets_dir, tmp_path)
        vf = (
            "format=yuv420p,scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black"
        )
        cmd: List[str] = [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(tmp_path),
        ]
        if audio_file:
            cmd.extend(["-i", str(audio_file)])
        cmd.extend(["-map", "0:v"])
        if audio_file:
            cmd.extend(
                [
                    "-map",
                    "1:a:0",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-shortest",
                ]
            )
        else:
            cmd.append("-an")
        cmd.extend(
            [
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-vf",
                vf,
                str(output_video),
            ]
        )
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "")[:800]
        return {
            "video_created": False,
            "output_path": str(output_video),
            "duration_seconds": None,
            "scene_count": n_scenes,
            "warnings": warnings + [f"ffmpeg_failed:{err}"],
            "blocking_reasons": ["ffmpeg_encode_failed"],
        }
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass

    dur: Optional[float] = None
    if ffprobe:
        dur, pw = _probe_video_duration(output_video, ffprobe)
        warnings.extend(pw)
    return {
        "video_created": True,
        "output_path": str(output_video.resolve()),
        "duration_seconds": dur,
        "scene_count": n_scenes,
        "warnings": warnings,
        "blocking_reasons": blocking,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="BA 19.2 — timeline_manifest → MP4 (ffmpeg)")
    parser.add_argument("--timeline-manifest", type=Path, required=True, dest="timeline_manifest")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "output" / "final_story_video.mp4",
        dest="output",
    )
    args = parser.parse_args()

    meta = render_final_story_video(args.timeline_manifest, output_video=args.output)
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0 if meta.get("video_created") else 4


if __name__ == "__main__":
    raise SystemExit(main())
