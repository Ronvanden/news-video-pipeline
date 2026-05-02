"""Build the first local demo video from one image and one voice MP3."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

DEFAULT_AUDIO_PATH = Path("output") / "voice_smoke_test_output.mp3"
DEFAULT_VIDEO_OUTPUT_PATH = Path("output") / "first_demo_video.mp4"
DEFAULT_DOWNLOADED_IMAGE_PATH = Path("output") / "first_demo_image_input"


class FirstDemoVideoResult(BaseModel):
    """Safe CLI result for the first local image+voice MP4 proof."""

    video_created: bool = False
    output_path: str = str(DEFAULT_VIDEO_OUTPUT_PATH)
    duration_seconds: Optional[float] = None
    image_source: str = ""
    audio_source: str = str(DEFAULT_AUDIO_PATH)
    warnings: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _safe_url_source(value: str) -> str:
    parsed = urlparse(value)
    if not parsed.netloc:
        return value
    return f"{parsed.netloc}{parsed.path or ''}"


def _download_suffix(image_url: str) -> str:
    suffix = Path(urlparse(image_url).path).suffix.lower()
    if suffix in (".jpg", ".jpeg", ".png", ".webp"):
        return suffix
    return ".jpg"


def _download_image(image_url: str, target_base: Path) -> Path:
    target = target_base.with_suffix(_download_suffix(image_url))
    target.parent.mkdir(parents=True, exist_ok=True)
    request = Request(image_url, method="GET", headers={"User-Agent": "news-to-video-pipeline/first-demo"})
    with urlopen(request, timeout=30.0) as response:
        target.write_bytes(response.read())
    return target


def _probe_audio_duration(audio_path: Path, ffprobe_bin: str) -> tuple[Optional[float], List[str]]:
    try:
        completed = subprocess.run(
            [
                ffprobe_bin,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        value = float((completed.stdout or "").strip())
        return round(value, 3), []
    except Exception:
        return None, ["audio_duration_probe_failed"]


def build_first_demo_video(
    image_source: str,
    *,
    audio_path: Path | str = DEFAULT_AUDIO_PATH,
    output_path: Path | str = DEFAULT_VIDEO_OUTPUT_PATH,
    downloaded_image_path: Path | str = DEFAULT_DOWNLOADED_IMAGE_PATH,
) -> FirstDemoVideoResult:
    """Create a local MP4 from one static image and one MP3 voice file."""
    warnings: List[str] = []
    blocking: List[str] = []
    source = (image_source or "").strip()
    audio = Path(audio_path)
    output = Path(output_path)

    if not source:
        blocking.append("image_source_missing")
    if not audio.exists():
        blocking.append("audio_source_missing")

    ffmpeg_bin = shutil.which("ffmpeg")
    ffprobe_bin = shutil.which("ffprobe")
    if not ffmpeg_bin:
        blocking.append("ffmpeg_missing")
    if not ffprobe_bin:
        warnings.append("ffprobe_missing_duration_unknown")

    if blocking:
        return FirstDemoVideoResult(
            output_path=str(output),
            image_source=_safe_url_source(source),
            audio_source=str(audio),
            warnings=warnings,
            blocking_reasons=blocking,
        )

    image_path: Path
    reported_image_source = source
    if _is_url(source):
        try:
            image_path = _download_image(source, Path(downloaded_image_path))
            reported_image_source = str(image_path)
        except Exception:
            return FirstDemoVideoResult(
                output_path=str(output),
                image_source=_safe_url_source(source),
                audio_source=str(audio),
                warnings=warnings,
                blocking_reasons=["image_download_failed"],
            )
    else:
        image_path = Path(source)
        if not image_path.exists():
            return FirstDemoVideoResult(
                output_path=str(output),
                image_source=str(image_path),
                audio_source=str(audio),
                warnings=warnings,
                blocking_reasons=["image_source_missing"],
            )

    duration: Optional[float] = None
    if ffprobe_bin:
        duration, probe_warnings = _probe_audio_duration(audio, ffprobe_bin)
        warnings.extend(probe_warnings)

    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_bin,
        "-y",
        "-loop",
        "1",
        "-i",
        str(image_path),
        "-i",
        str(audio),
        "-c:v",
        "libx264",
        "-tune",
        "stillimage",
        "-vf",
        "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        str(output),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except Exception:
        return FirstDemoVideoResult(
            output_path=str(output),
            duration_seconds=duration,
            image_source=reported_image_source,
            audio_source=str(audio),
            warnings=warnings,
            blocking_reasons=["ffmpeg_render_failed"],
        )

    if not output.exists() or output.stat().st_size <= 0:
        return FirstDemoVideoResult(
            output_path=str(output),
            duration_seconds=duration,
            image_source=reported_image_source,
            audio_source=str(audio),
            warnings=warnings,
            blocking_reasons=["video_output_missing_or_empty"],
        )

    return FirstDemoVideoResult(
        video_created=True,
        output_path=str(output),
        duration_seconds=duration,
        image_source=reported_image_source,
        audio_source=str(audio),
        warnings=list(dict.fromkeys(warnings)),
        blocking_reasons=[],
    )
