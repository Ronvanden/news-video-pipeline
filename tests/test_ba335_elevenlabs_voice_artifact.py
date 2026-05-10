"""BA 32.35 — Voice-Artefakt / ElevenLabs-Pfad: keine echten Provider-Calls."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.founder_dashboard.ba323_video_generate import build_voice_artifact

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_url_to_final_mp4.py"


@pytest.fixture(scope="module")
def ba265_mod():
    spec = importlib.util.spec_from_file_location("run_url_to_final_mp4_ba335", _SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _ffmpeg_ok() -> bool:
    return shutil.which("ffmpeg") is not None


def _write_min_mp4(target: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=320x240:r=25",
            "-t",
            "1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(target),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _minimal_script(path: Path) -> None:
    chapters = [{"title": "K1", "content": "Text für Voiceover-Test. " * 6}]
    doc = {
        "title": "T",
        "hook": "H",
        "chapters": chapters,
        "full_script": "",
        "sources": ["https://example.com/a"],
        "warnings": [],
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_voice_artifact_includes_summary_blocking_and_warnings(tmp_path: Path) -> None:
    (tmp_path / "run_summary.json").write_text(
        json.dumps(
            {
                "voice_mode": "elevenlabs",
                "voice_file_path": None,
                "voice_blocking_reasons": ["elevenlabs_mid_run_failed"],
                "voice_warnings": ["elevenlabs_chunk_failed:0:empty_body"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    va = build_voice_artifact(
        output_dir=tmp_path,
        requested_voice_mode="elevenlabs",
        effective_voice_mode="elevenlabs",
    )
    w = va.get("warnings") or []
    assert "voice_file_path_missing" in w
    assert any(x.startswith("voice_summary_blocking:") for x in w)
    assert any("elevenlabs_chunk_failed" in x for x in w)
    assert va.get("voice_ready") is False


def test_build_voice_artifact_elevenlabs_with_file_ready(tmp_path: Path) -> None:
    mp3 = tmp_path / "voiceover.mp3"
    mp3.write_bytes(b"\xff\xfb\x90\x00")  # minimal junk; exists as file
    (tmp_path / "run_summary.json").write_text(
        json.dumps(
            {
                "voice_mode": "elevenlabs",
                "voice_file_path": str(mp3),
                "voice_duration_seconds": 1.2,
                "voice_blocking_reasons": [],
                "voice_warnings": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    va = build_voice_artifact(
        output_dir=tmp_path,
        requested_voice_mode="elevenlabs",
        effective_voice_mode="elevenlabs",
    )
    assert va.get("voice_ready") is True
    assert va.get("is_dummy") is False
    assert va.get("voice_file_path") == str(mp3)
    assert "voice_file_path_missing" not in (va.get("warnings") or [])


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_ba265_surfaces_elevenlabs_synthesis_failure_in_warnings(ba265_mod, tmp_path, monkeypatch) -> None:
    """Stub-TTS scheitert: Haupt-warnings + run_summary müssen Codes tragen (BA 32.35)."""

    def _fake_synthesize(*_a, **_kw):
        return {
            "voice_used": False,
            "voice_mode": "elevenlabs",
            "voice_file_path": None,
            "voice_duration_seconds": None,
            "voice_warnings": ["elevenlabs_chunk_failed:0:stub"],
            "voice_blocking_reasons": ["elevenlabs_mid_run_failed"],
        }

    monkeypatch.setattr(ba265_mod, "_synthesize_voice", _fake_synthesize)

    script_p = tmp_path / "in.json"
    _minimal_script(script_p)
    assets = tmp_path / "assets"
    assets.mkdir()
    clip = assets / "smoke.mp4"
    _write_min_mp4(clip)
    out = tmp_path / "out335"
    doc = ba265_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=2,
        duration_seconds=24,
        asset_dir=assets,
        run_id="t335",
        motion_mode="static",
        voice_mode="elevenlabs",
    )
    wjoin = " ".join(doc.get("warnings") or [])
    assert "elevenlabs_voice_synthesis_failed" in wjoin
    assert "voice_synthesis_blocked:" in wjoin
    assert "elevenlabs_chunk_failed" in wjoin

    summ = json.loads((out / "run_summary.json").read_text(encoding="utf-8"))
    sw = " ".join(summ.get("warnings") or [])
    assert "elevenlabs_voice_synthesis_failed" in sw
