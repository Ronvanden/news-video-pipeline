"""BA 26.7b — Fit Video Duration to Voice (--fit-video-to-voice, Padding, Summary-Felder)."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_url_to_final_mp4.py"


@pytest.fixture(scope="module")
def ba267b_mod():
    spec = importlib.util.spec_from_file_location("run_url_to_final_mp4_ba267b", _SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _ffmpeg_ok() -> bool:
    return shutil.which("ffmpeg") is not None


def _ffprobe_ok() -> bool:
    return shutil.which("ffprobe") is not None


def _write_min_mp3(target: Path, seconds: int = 2) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=stereo",
            "-t",
            str(int(seconds)),
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
        "title": "BA 26.7b Test",
        "hook": "Kurzer Hook für Fit-to-Voice.",
        "chapters": chapters,
        "full_script": "",
        "sources": [],
        "warnings": [],
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def _ffprobe_duration(mp4: Path) -> float:
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(mp4),
        ],
        capture_output=True,
        text=True,
    )
    s = (out.stdout or "").strip()
    return float(s) if s else 0.0


def test_cli_help_lists_fit_flags():
    r = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
    )
    assert r.returncode == 0, r.stderr
    assert "--fit-video-to-voice" in r.stdout
    assert "--voice-fit-padding-seconds" in r.stdout


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_voice_fit_padding_zero_matches_voice_only_seconds(ba267b_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=3)
    audio = tmp_path / "voice.mp3"
    _write_min_mp3(audio, seconds=9)
    out = tmp_path / "out267b_pad0"
    doc = ba267b_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=3,
        duration_seconds=60,
        asset_dir=None,
        run_id="t267b_pad0",
        motion_mode="static",
        voice_mode="existing",
        voice_file=audio,
        fit_video_to_voice=True,
        voice_fit_padding_seconds=0.0,
        fit_min_seconds_per_scene=2,
    )
    assert doc.get("ok") is True
    assert doc.get("fitted_video_duration_seconds") == 9.0
    assert doc.get("voice_fit_padding_seconds") == 0.0
    assert doc.get("original_requested_duration_seconds") == 60
    am = json.loads(Path(doc["asset_manifest_path"]).read_text(encoding="utf-8"))
    assert sum(int(a["duration_seconds"]) for a in am["assets"]) == 9


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_timeline_manifest_reflects_fitted_scene_durations(ba267b_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=3)
    audio = tmp_path / "voice.mp3"
    _write_min_mp3(audio, seconds=9)
    out = tmp_path / "out267b_tl"
    doc = ba267b_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=3,
        duration_seconds=60,
        asset_dir=None,
        run_id="t267b_tl",
        motion_mode="static",
        voice_mode="existing",
        voice_file=audio,
        fit_video_to_voice=True,
        voice_fit_padding_seconds=0.0,
        fit_min_seconds_per_scene=2,
    )
    tl_path = Path(doc["timeline_manifest_path"])
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    scenes = tl.get("scenes") or []
    total_tl = sum(float(s.get("duration_seconds", 0)) for s in scenes)
    assert int(round(total_tl)) == 9
    assert tl.get("estimated_duration_seconds") == 9


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_fit_requested_elevenlabs_blocked_emits_controlled_warning(ba267b_mod, tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=2)
    out = tmp_path / "out267b_el_fit"
    doc = ba267b_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=2,
        duration_seconds=30,
        asset_dir=None,
        run_id="t267b_el_fit",
        motion_mode="static",
        voice_mode="elevenlabs",
        fit_video_to_voice=True,
    )
    assert doc.get("voice_used") is False
    warns = doc.get("warnings") or []
    assert "fit_video_to_voice_requested_but_no_voice_duration" in warns
    rs = json.loads((out / "run_summary.json").read_text(encoding="utf-8"))
    assert rs["fit_video_to_voice"] is True
    assert rs["fitted_video_duration_seconds"] is None


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
@pytest.mark.skipif(not _ffprobe_ok(), reason="ffprobe not available")
def test_fit_shortens_final_mp4_vs_long_requested_timeline(ba267b_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=3)
    audio = tmp_path / "voice.mp3"
    _write_min_mp3(audio, seconds=6)
    out = tmp_path / "out267b_short"
    doc = ba267b_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=3,
        duration_seconds=30,
        asset_dir=None,
        run_id="t267b_short",
        motion_mode="static",
        voice_mode="existing",
        voice_file=audio,
        fit_video_to_voice=True,
        voice_fit_padding_seconds=0.75,
        fit_min_seconds_per_scene=2,
    )
    assert doc.get("ok") is True
    final = Path(doc["final_video_path"])
    dur = _ffprobe_duration(final)
    assert dur < 25.0, f"Fit-Run soll deutlich kürzer als ~30s sein, war {dur}s"
    warns = " ".join(doc.get("warnings") or [])
    assert "audio_shorter_than_timeline_padded_or_continued" not in warns
