"""BA 32.51 — Auto Fit-to-Voice für static image + echte Voice (max_motion_clips=0), ohne Provider."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_url_to_final_mp4.py"


@pytest.fixture(scope="module")
def ba351_mod():
    spec = importlib.util.spec_from_file_location("run_url_to_final_mp4_ba351", _SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _ffmpeg_ok() -> bool:
    return shutil.which("ffmpeg") is not None


def _ffprobe_ok() -> bool:
    return shutil.which("ffprobe") is not None


def _write_min_mp3(target: Path, seconds: float = 6.0) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=stereo",
            "-t",
            str(float(seconds)),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "128k",
            str(target),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _minimal_script(path: Path, *, n_chapters: int = 3) -> None:
    chapters = [
        {"title": f"Kapitel {i+1}", "content": f"Inhaltlicher Absatz Nummer {i+1}. " * 4}
        for i in range(n_chapters)
    ]
    doc = {
        "title": "BA 32.51 Test",
        "hook": "Hook.",
        "chapters": chapters,
        "full_script": "",
        "sources": [],
        "warnings": [],
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
@pytest.mark.skipif(not _ffprobe_ok(), reason="ffprobe not available")
def test_auto_fit_static_voice_max_motion_zero_no_explicit_flag(ba351_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=3)
    audio = tmp_path / "voice.mp3"
    _write_min_mp3(audio, seconds=12.0)
    out = tmp_path / "out351_auto"
    doc = ba351_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=3,
        duration_seconds=60,
        asset_dir=None,
        run_id="t351_auto",
        motion_mode="static",
        voice_mode="existing",
        voice_file=audio,
        fit_video_to_voice=False,
        voice_fit_padding_seconds=1.0,
        fit_min_seconds_per_scene=2,
        max_motion_clips=0,
    )
    assert doc.get("ok") is True
    warns = list(doc.get("warnings") or [])
    assert "timeline_fit_to_voice_applied" in warns
    assert doc.get("fit_video_to_voice") is True
    ta = doc.get("timing_audit") or {}
    assert ta.get("fit_strategy") == "fit_to_voice"
    assert "audio_shorter_than_timeline_padded_or_continued" not in " ".join(str(w) for w in warns).lower()
    assert ta.get("timing_gap_status") in ("ok", "minor_gap")
    fitted = float(doc.get("fitted_video_duration_seconds") or 0)
    assert 12.0 <= fitted <= 15.0


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_no_auto_fit_when_max_motion_clips_positive(ba351_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=3)
    audio = tmp_path / "voice.mp3"
    _write_min_mp3(audio, seconds=8.0)
    out = tmp_path / "out351_nom"
    doc = ba351_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=3,
        duration_seconds=60,
        asset_dir=None,
        run_id="t351_nom",
        motion_mode="static",
        voice_mode="existing",
        voice_file=audio,
        fit_video_to_voice=False,
        max_motion_clips=10,
    )
    assert doc.get("ok") is True
    warns = list(doc.get("warnings") or [])
    assert "timeline_fit_to_voice_applied" not in warns
    assert doc.get("fit_video_to_voice") is False


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_auto_fit_applies_for_motion_basic_when_max_motion_clips_zero(ba351_mod, tmp_path):
    """Dashboard-Default motion_mode=basic gilt als Bildläufe; mit max_motion_clips=0 wird gefittet."""
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=3)
    audio = tmp_path / "voice.mp3"
    _write_min_mp3(audio, seconds=10.0)
    out = tmp_path / "out351_basic"
    doc = ba351_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=3,
        duration_seconds=60,
        asset_dir=None,
        run_id="t351_basic",
        motion_mode="basic",
        voice_mode="existing",
        voice_file=audio,
        fit_video_to_voice=False,
        max_motion_clips=0,
    )
    assert doc.get("ok") is True
    warns = list(doc.get("warnings") or [])
    assert "timeline_fit_to_voice_applied" in warns
    assert doc.get("fit_video_to_voice") is True
