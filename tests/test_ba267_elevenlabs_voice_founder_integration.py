"""BA 26.7 — ElevenLabs Voice Founder Integration: voice-mode none/existing/elevenlabs/dummy."""

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
def ba267_mod():
    spec = importlib.util.spec_from_file_location("run_url_to_final_mp4_ba267", _SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _ffmpeg_ok() -> bool:
    return shutil.which("ffmpeg") is not None


def _ffprobe_ok() -> bool:
    return shutil.which("ffprobe") is not None


def _write_min_mp4(target: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=teal:s=320x240:r=25",
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
        "title": "BA 26.7 Test",
        "hook": "Dies ist ein kurzer Hook für den Voice-Test.",
        "chapters": chapters,
        "full_script": "",
        "sources": [],
        "warnings": [],
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


def _has_audio_stream(mp4: Path) -> bool:
    if not _ffprobe_ok():
        return False
    out = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "csv=p=0",
            str(mp4),
        ],
        capture_output=True,
        text=True,
    )
    return "audio" in (out.stdout or "")


# ---------------------------------------------------------------------------
# 1. voiceover_text wird aus Szenen erzeugt — ohne Szene-Labels
# ---------------------------------------------------------------------------


def test_voiceover_text_collects_narration_without_scene_labels(ba267_mod):
    rows = [
        {"title": "Hook", "narration": "Erster Satz für die Stimme."},
        {"title": "Kapitel 1: Einstieg", "narration": "Zweiter Absatz fließend."},
        {"title": "Kapitel 2", "narration": "Dritter Absatz."},
    ]
    text = ba267_mod._collect_voiceover_text(rows)
    assert "Erster Satz" in text
    assert "Zweiter Absatz" in text
    assert "Dritter Absatz" in text
    forbidden = ("Hook:", "Kapitel 1:", "Kapitel 2:", "Szene 1", "Scene 001", "DRAFT PLACEHOLDER")
    for token in forbidden:
        assert token not in text, f"voiceover-Text darf {token!r} nicht enthalten"


# ---------------------------------------------------------------------------
# 2. --voice-mode existing mit gültiger Audiodatei → voice_used=true + Audio in Video
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_voice_mode_existing_with_valid_audio(ba267_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=2)
    assets = tmp_path / "assets"
    assets.mkdir()
    _write_min_mp4(assets / "clip.mp4")
    audio = tmp_path / "voice.mp3"
    _write_min_mp3(audio, seconds=3)
    out = tmp_path / "out267_existing"
    doc = ba267_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=2,
        duration_seconds=20,
        asset_dir=assets,
        run_id="t267_existing",
        motion_mode="static",
        voice_mode="existing",
        voice_file=audio,
    )
    assert doc.get("ok") is True
    assert doc.get("voice_used") is True
    assert doc.get("voice_mode") == "existing"
    assert doc.get("audio_stream_expected") is True
    assert (out / "voiceover_text.txt").is_file()
    final = Path(doc["final_video_path"])
    assert final.is_file()
    assert _has_audio_stream(final), "final_video.mp4 muss bei voice_used=true einen Audio-Stream enthalten"
    rsum = json.loads((out / "run_summary.json").read_text(encoding="utf-8"))
    assert "audio_missing_silent_render" not in (rsum.get("warnings") or [])


# ---------------------------------------------------------------------------
# 3. fehlende voice_file → blocking_reason, kein Crash
# ---------------------------------------------------------------------------


def test_voice_mode_existing_missing_file_blocks_clean(ba267_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=2)
    out = tmp_path / "out267_missing"
    doc = ba267_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=2,
        duration_seconds=20,
        asset_dir=None,
        run_id="t267_missing",
        motion_mode="static",
        voice_mode="existing",
        voice_file=tmp_path / "does_not_exist.mp3",
    )
    assert (out / "run_summary.json").is_file()
    assert doc.get("voice_used") is False
    blockers = doc.get("voice_blocking_reasons") or []
    assert "voice_file_missing" in blockers
    assert "voice_text_path" in doc
    assert "voice_warnings" in doc


# ---------------------------------------------------------------------------
# 4. --voice-mode dummy erzeugt MP3 + final_video.mp4 mit Audio
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_voice_mode_dummy_produces_audio_track(ba267_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=2)
    out = tmp_path / "out267_dummy"
    doc = ba267_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=2,
        duration_seconds=20,
        asset_dir=None,
        run_id="t267_dummy",
        motion_mode="static",
        voice_mode="dummy",
        dummy_voice_seconds=3,
    )
    assert doc.get("ok") is True
    assert doc.get("voice_used") is True
    assert doc.get("voice_mode") == "dummy"
    warns = " ".join(doc.get("voice_warnings") or [])
    assert "dummy_voice_used_not_real_tts" in warns
    voice_file = Path(doc["voice_file_path"])
    assert voice_file.is_file()
    assert voice_file.stat().st_size > 0
    final = Path(doc["final_video_path"])
    assert final.is_file()
    if _ffprobe_ok():
        assert _has_audio_stream(final)


# ---------------------------------------------------------------------------
# 5. run_summary enthält die geforderten Voice-Felder
# ---------------------------------------------------------------------------


def test_run_summary_contains_voice_fields(ba267_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=2)
    out = tmp_path / "out267_fields"
    ba267_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=2,
        duration_seconds=18,
        asset_dir=None,
        run_id="t267_fields",
        motion_mode="static",
        voice_mode="none",
    )
    rs = json.loads((out / "run_summary.json").read_text(encoding="utf-8"))
    for key in (
        "voice_used",
        "voice_mode",
        "voice_text_path",
        "voice_file_path",
        "voice_duration_seconds",
        "audio_stream_expected",
        "voice_warnings",
        "voice_blocking_reasons",
        "fit_video_to_voice",
        "voice_fit_padding_seconds",
        "fitted_video_duration_seconds",
        "original_requested_duration_seconds",
    ):
        assert key in rs, f"run_summary muss {key!r} enthalten"
    assert rs["voice_used"] is False
    assert rs["voice_mode"] == "none"
    assert rs["audio_stream_expected"] is False
    assert rs["fit_video_to_voice"] is False
    assert rs["voice_fit_padding_seconds"] is None
    assert rs["fitted_video_duration_seconds"] is None
    assert rs["original_requested_duration_seconds"] == 18


# ---------------------------------------------------------------------------
# 6. --voice-mode elevenlabs ohne API-Key → blocking, KEIN Secret in Output
# ---------------------------------------------------------------------------


def test_voice_mode_elevenlabs_blocks_without_api_key(ba267_mod, tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=2)
    out = tmp_path / "out267_el_block"
    doc = ba267_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=2,
        duration_seconds=18,
        asset_dir=None,
        run_id="t267_el_block",
        motion_mode="static",
        voice_mode="elevenlabs",
    )
    assert doc.get("voice_used") is False
    blockers = doc.get("voice_blocking_reasons") or []
    assert "elevenlabs_missing_api_key" in blockers
    rendered = json.dumps(doc, ensure_ascii=False)
    assert "ELEVENLABS_API_KEY" not in rendered or "ELEVENLABS_API_KEY=" not in rendered
    for forbidden in ("xi-api-key:", "Authorization: Bearer "):
        assert forbidden not in rendered


# ---------------------------------------------------------------------------
# 7. ElevenLabs mit gemocktem Post-Override → erfolgreich, audio im Video
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_voice_mode_elevenlabs_with_post_override(ba267_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-fake-key-not-real")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "test-voice-id")

    sample_mp3 = tmp_path / "_sample.mp3"
    _write_min_mp3(sample_mp3, seconds=2)
    sample_bytes = sample_mp3.read_bytes()

    def fake_post(text, api_key, voice_id, body_json):
        assert api_key == "test-fake-key-not-real"
        assert voice_id == "test-voice-id"
        return sample_bytes

    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=2)
    out = tmp_path / "out267_el_ok"
    doc = ba267_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=2,
        duration_seconds=18,
        asset_dir=None,
        run_id="t267_el_ok",
        motion_mode="static",
        voice_mode="elevenlabs",
        elevenlabs_post_override=fake_post,
    )
    assert doc.get("ok") is True
    assert doc.get("voice_used") is True
    assert doc.get("voice_mode") == "elevenlabs"
    voice_path = Path(doc["voice_file_path"])
    assert voice_path.is_file()
    assert voice_path.stat().st_size > 0
    final = Path(doc["final_video_path"])
    assert final.is_file()
    if _ffprobe_ok():
        assert _has_audio_stream(final)
    rendered = json.dumps(doc, ensure_ascii=False)
    assert "test-fake-key-not-real" not in rendered, "API-Key darf nicht im Summary auftauchen"


# ---------------------------------------------------------------------------
# BA 26.7 Erweiterung — --fit-video-to-voice
# ---------------------------------------------------------------------------


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


def test_distribute_durations_helper_floor_and_remainder(ba267_mod):
    assert ba267_mod._distribute_durations(0, 30) == []
    assert ba267_mod._distribute_durations(3, 9, min_per_scene=3) == [3, 3, 3]
    assert ba267_mod._distribute_durations(3, 10, min_per_scene=3) == [4, 3, 3]
    assert ba267_mod._distribute_durations(4, 5, min_per_scene=2) == [2, 2, 2, 2]
    assert sum(ba267_mod._distribute_durations(5, 30, min_per_scene=2)) == 30
    assert ba267_mod._distribute_durations(3, 9) == [5, 5, 5]
    assert ba267_mod._distribute_durations(3, 5, min_per_scene=2) == [2, 2, 2]


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
@pytest.mark.skipif(not _ffprobe_ok(), reason="ffprobe not available")
def test_fit_video_to_voice_aligns_video_duration_with_existing_audio(ba267_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=3)
    audio = tmp_path / "voice.mp3"
    _write_min_mp3(audio, seconds=6)
    out = tmp_path / "out267_fit_existing"
    doc = ba267_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=3,
        duration_seconds=45,
        asset_dir=None,
        run_id="t267_fit_existing",
        motion_mode="static",
        voice_mode="existing",
        voice_file=audio,
        fit_video_to_voice=True,
        fit_min_seconds_per_scene=2,
    )
    assert doc.get("ok") is True
    assert doc.get("voice_used") is True
    warns = " ".join(doc.get("warnings") or [])
    assert "ba267_video_fitted_to_voice:" in warns
    assert "target_total=7s" in warns
    assert doc.get("fitted_video_duration_seconds") == 7.0
    final = Path(doc["final_video_path"])
    assert final.is_file()
    final_duration = _ffprobe_duration(final)
    assert 6.0 <= final_duration <= 9.0, f"final_duration={final_duration} sollte ≈ voice+padding sein"


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_fit_video_to_voice_patches_asset_manifest_durations(ba267_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=3)
    audio = tmp_path / "voice.mp3"
    _write_min_mp3(audio, seconds=9)
    out = tmp_path / "out267_fit_patches"
    doc = ba267_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=3,
        duration_seconds=60,
        asset_dir=None,
        run_id="t267_fit_patches",
        motion_mode="static",
        voice_mode="existing",
        voice_file=audio,
        fit_video_to_voice=True,
        fit_min_seconds_per_scene=2,
    )
    assert doc.get("ok") is True
    am_path = Path(doc["asset_manifest_path"])
    am = json.loads(am_path.read_text(encoding="utf-8"))
    durations = [int(a["duration_seconds"]) for a in am["assets"]]
    assert sum(durations) == 10, f"Σ Szenen-Dauern muss ≈ voice+padding (Default 0.75) sein: {durations}"
    assert all(d >= 2 for d in durations)
    plan = json.loads((out / "scene_plan.json").read_text(encoding="utf-8"))
    plan_durs = [int(s["duration_seconds"]) for s in plan["scenes"]]
    assert sum(plan_durs) == 10
    pack = json.loads((out / "scene_asset_pack.json").read_text(encoding="utf-8"))
    beat_durs = [
        int(b["duration_seconds"])
        for b in (pack.get("scene_expansion") or {}).get("expanded_scene_assets") or []
    ]
    assert sum(beat_durs) == 10


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_fit_video_to_voice_skipped_when_no_voice(ba267_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=2)
    out = tmp_path / "out267_fit_noop"
    doc = ba267_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=2,
        duration_seconds=18,
        asset_dir=None,
        run_id="t267_fit_noop",
        motion_mode="static",
        voice_mode="none",
        fit_video_to_voice=True,
    )
    warns = " ".join(doc.get("warnings") or [])
    assert "fit_video_to_voice_requested_but_no_voice_duration" in warns
    assert doc.get("fit_video_to_voice") is True
    assert doc.get("fitted_video_duration_seconds") is None
    am_path = Path(doc["asset_manifest_path"])
    am = json.loads(am_path.read_text(encoding="utf-8"))
    durations = [int(a["duration_seconds"]) for a in am["assets"]]
    assert sum(durations) >= 18 - 2, "ohne Voice darf die Original-Dauer nicht durch fit verkürzt werden"


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_fit_video_to_voice_with_dummy_audio_aligns_to_dummy_seconds(ba267_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=3)
    out = tmp_path / "out267_fit_dummy"
    doc = ba267_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=3,
        duration_seconds=60,
        asset_dir=None,
        run_id="t267_fit_dummy",
        motion_mode="static",
        voice_mode="dummy",
        dummy_voice_seconds=12,
        fit_video_to_voice=True,
        fit_min_seconds_per_scene=2,
    )
    assert doc.get("ok") is True
    assert doc.get("voice_used") is True
    warns = " ".join(doc.get("warnings") or [])
    assert "ba267_video_fitted_to_voice:" in warns
    assert "target_total=13s" in warns
    am = json.loads(Path(doc["asset_manifest_path"]).read_text(encoding="utf-8"))
    durs = [int(a["duration_seconds"]) for a in am["assets"]]
    assert sum(durs) == 13, f"Σ Szenen-Dauern muss 12s+padding entsprechen: {durs}"
