"""BA 20.5 — build_subtitle_file.py + render subtitle burn-in."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from subprocess import CompletedProcess

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SUB_SCRIPT = _ROOT / "scripts" / "build_subtitle_file.py"
_RENDER_SCRIPT = _ROOT / "scripts" / "render_final_story_video.py"


@pytest.fixture(scope="module")
def sub_mod():
    spec = importlib.util.spec_from_file_location("build_subtitle_file", _SUB_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def render_mod():
    spec = importlib.util.spec_from_file_location("render_final_story_video", _RENDER_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_build_subtitle_creates_srt_and_manifest(sub_mod, tmp_path):
    narr = tmp_path / "narration_script.txt"
    narr.write_text(
        "# header\n\n"
        "Dies ist der erste Satz. Hier folgt ein zweiter mit etwas Inhalt. "
        "Und ein dritter Satz für die Verteilung.\n",
        encoding="utf-8",
    )
    tl = tmp_path / "tl.json"
    tl.write_text(
        json.dumps(
            {
                "scenes": [
                    {"duration_seconds": 5, "image_path": "a.png"},
                    {"duration_seconds": 5, "image_path": "b.png"},
                ]
            }
        ),
        encoding="utf-8",
    )
    meta = sub_mod.build_subtitle_pack(
        narr,
        timeline_manifest_path=tl,
        out_root=tmp_path / "out",
        run_id="sub205",
        subtitle_mode="simple",
    )
    assert meta["ok"] is True
    assert meta["subtitle_count"] >= 1
    out_dir = Path(meta["output_dir"])
    srt = out_dir / "subtitles.srt"
    man = out_dir / "subtitle_manifest.json"
    assert srt.is_file() and man.is_file()
    body = srt.read_text(encoding="utf-8")
    assert "-->" in body
    assert "1\n" in body or body.startswith("1\n")
    disk = json.loads(man.read_text(encoding="utf-8"))
    assert disk["run_id"] == "sub205"
    assert disk["subtitle_mode"] == "simple"
    assert "source_narration_script" in disk
    assert "timeline_manifest" in disk
    assert disk["subtitle_count"] == meta["subtitle_count"]
    assert "warnings" in disk and "blocking_reasons" in disk
    assert float(disk["estimated_duration_seconds"]) == 10.0
    assert "subtitle_timeline_duration_used" in meta["warnings"]
    assert meta.get("subtitle_source") == "narration"
    assert meta.get("transcription_used") is False
    assert meta.get("fallback_used") is False
    assert meta.get("subtitle_style") == "classic"
    sc = meta.get("subtitle_render_contract") or {}
    assert sc.get("style") == "classic"
    assert sc.get("requires_word_timing") is False


def test_subtitle_manifest_shape_none_mode(sub_mod, tmp_path):
    narr = tmp_path / "n2.txt"
    narr.write_text("# x\n\nHallo Welt.", encoding="utf-8")
    meta = sub_mod.build_subtitle_pack(
        narr,
        timeline_manifest_path=None,
        out_root=tmp_path / "out2",
        run_id="none205",
        subtitle_mode="none",
    )
    assert meta["ok"] is True
    assert meta["subtitle_count"] == 0
    man = json.loads(Path(meta["subtitle_manifest_path"]).read_text(encoding="utf-8"))
    assert man["subtitle_count"] == 0


def test_render_static_includes_subtitles_in_vf(render_mod, tmp_path, monkeypatch):
    assets = tmp_path / "ga"
    assets.mkdir(parents=True)
    for n in ("scene_001.png", "scene_002.png"):
        (assets / n).write_bytes(b"\x89PNG\r\n\x1a\n")
    tl_path = tmp_path / "tl.json"
    tl_path.write_text(
        json.dumps(
            {
                "assets_directory": str(assets),
                "audio_path": "",
                "scenes": [
                    {"image_path": "scene_001.png", "duration_seconds": 4},
                    {"image_path": "scene_002.png", "duration_seconds": 4},
                ],
            }
        ),
        encoding="utf-8",
    )
    srt = tmp_path / "x.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nTest\n",
        encoding="utf-8",
    )
    out = tmp_path / "v.mp4"
    captured: list[list[str]] = []

    def fake_run(cmd, check=True, capture_output=True, text=True):
        captured.append(list(cmd))
        out.touch()
        return CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(render_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(render_mod, "_probe_video_duration", lambda _v, _f: (8.0, []))

    meta = render_mod.render_final_story_video(
        tl_path,
        output_video=out,
        motion_mode="static",
        subtitle_path=srt,
        ffmpeg_bin="ffmpeg_mock",
        ffprobe_bin="ffprobe_mock",
    )
    assert meta["video_created"] is True
    assert meta.get("subtitles_burned") is True
    cmd = captured[0]
    vf = cmd[cmd.index("-vf") + 1]
    assert "subtitles=" in vf
    assert "force_style=" in vf


def test_subtitle_burn_failure_falls_back_static(render_mod, tmp_path, monkeypatch):
    assets = tmp_path / "gb"
    assets.mkdir(parents=True)
    for n in ("scene_001.png", "scene_002.png"):
        (assets / n).write_bytes(b"\x89PNG\r\n\x1a\n")
    tl_path = tmp_path / "tlb.json"
    tl_path.write_text(
        json.dumps(
            {
                "assets_directory": str(assets),
                "audio_path": "",
                "scenes": [
                    {"image_path": "scene_001.png", "duration_seconds": 3},
                    {"image_path": "scene_002.png", "duration_seconds": 3},
                ],
            }
        ),
        encoding="utf-8",
    )
    srt = tmp_path / "burn.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nX\n", encoding="utf-8")
    out = tmp_path / "vb.mp4"
    calls: list[list[str]] = []

    def fake_run(cmd, check=True, capture_output=True, text=True):
        calls.append(list(cmd))
        if len(calls) == 1:
            raise subprocess.CalledProcessError(1, cmd, stderr="subtitles_filter_failed")
        out.touch()
        return CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(render_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(render_mod, "_probe_video_duration", lambda _v, _f: (6.0, []))

    meta = render_mod.render_final_story_video(
        tl_path,
        output_video=out,
        motion_mode="static",
        subtitle_path=srt,
        ffmpeg_bin="ffmpeg_mock",
        ffprobe_bin="ffprobe_mock",
    )
    assert meta["video_created"] is True
    assert "subtitle_burn_failed_fallback_no_subtitles" in meta["warnings"]
    assert meta.get("subtitles_burned") is False
    assert len(calls) == 2
    assert "subtitles=" in " ".join(calls[0])
    assert "subtitles=" not in " ".join(calls[1])


def test_audio_duration_preferred_when_probe_ok(sub_mod, tmp_path, monkeypatch):
    narr = tmp_path / "na.txt"
    narr.write_text(
        "# h\n\n" + " ".join(f"word{i}" for i in range(80)) + ".",
        encoding="utf-8",
    )
    mp3 = tmp_path / "voice.mp3"
    mp3.write_bytes(b"fake")
    tl = tmp_path / "tl_audio.json"
    tl.write_text(
        json.dumps(
            {
                "audio_path": str(mp3),
                "scenes": [{"duration_seconds": 5, "image_path": "a.png"}],
            }
        ),
        encoding="utf-8",
    )

    def fake_run(cmd, check=True, capture_output=True, text=True):
        return CompletedProcess(cmd, 0, "42.5\n", "")

    monkeypatch.setattr(sub_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(sub_mod.shutil, "which", lambda x: "ffprobe_bin" if x == "ffprobe" else None)

    meta = sub_mod.build_subtitle_pack(
        narr,
        timeline_manifest_path=tl,
        out_root=tmp_path / "outa",
        run_id="aud205b",
        subtitle_mode="simple",
    )
    assert meta["ok"] is True
    assert "subtitle_audio_duration_used" in meta["warnings"]
    assert abs(float(meta["estimated_duration_seconds"]) - 42.5) < 0.01


def test_shorter_cues_more_chunks_for_long_text(sub_mod, tmp_path):
    narr = tmp_path / "long.txt"
    narr.write_text(
        "# x\n\n"
        + " ".join(f"w{i}" for i in range(55))
        + ". Ende.",
        encoding="utf-8",
    )
    tl = tmp_path / "tl_long.json"
    tl.write_text(
        json.dumps({"scenes": [{"duration_seconds": 30, "image_path": "a.png"}]}),
        encoding="utf-8",
    )
    meta = sub_mod.build_subtitle_pack(
        narr,
        timeline_manifest_path=tl,
        out_root=tmp_path / "outl",
        run_id="chunk205b",
        subtitle_mode="simple",
    )
    assert meta["ok"] is True
    assert meta["subtitle_count"] >= 5


def test_cue_end_times_not_exceed_total_duration(sub_mod, tmp_path):
    narr = tmp_path / "t.txt"
    narr.write_text("#\n\nHallo hier. Zweiter Satz. Dritter Satz.\n", encoding="utf-8")
    tl = tmp_path / "tl_cap.json"
    tl.write_text(
        json.dumps(
            {
                "scenes": [
                    {"duration_seconds": 4, "image_path": "a.png"},
                    {"duration_seconds": 4, "image_path": "b.png"},
                ]
            }
        ),
        encoding="utf-8",
    )
    meta = sub_mod.build_subtitle_pack(
        narr,
        timeline_manifest_path=tl,
        out_root=tmp_path / "outc",
        run_id="cap205b",
        subtitle_mode="simple",
    )
    total = float(meta["estimated_duration_seconds"])
    text = Path(meta["subtitles_srt_path"]).read_text(encoding="utf-8")
    ends: list[float] = []
    for line in text.splitlines():
        if "-->" in line:
            _, right = line.split("-->", 1)
            h, m, rest = right.strip().split(":")
            sec, ms = rest.split(",")
            ends.append(int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000.0)
    assert ends
    assert max(ends) <= total + 0.06


def test_audio_mode_missing_openai_key_fallback_narration(sub_mod, tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    narr = tmp_path / "nar_a.txt"
    narr.write_text("#\n\nEins zwei drei vier fünf sechs.\n", encoding="utf-8")
    mp3 = tmp_path / "v.mp3"
    mp3.write_bytes(b"id3fake")
    meta = sub_mod.build_subtitle_pack(
        narr,
        timeline_manifest_path=None,
        out_root=tmp_path / "outa2",
        run_id="env205c",
        subtitle_mode="simple",
        subtitle_source="audio",
        audio_path=mp3,
    )
    assert meta["ok"] is True
    assert "subtitle_audio_transcription_env_missing_fallback_narration" in meta["warnings"]
    assert meta.get("fallback_used") is True
    assert meta.get("transcription_used") is False
    assert meta.get("subtitle_source") == "narration"


def test_audio_mode_mocked_segments_valid_srt(sub_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-not-real")
    narr = tmp_path / "nar_seg.txt"
    narr.write_text("#\n\nFallback text hier genug Wörter für den Notfall.\n", encoding="utf-8")
    mp3 = tmp_path / "voice_seg.mp3"
    mp3.write_bytes(b"x" * 200)

    def fake_tf(_p: Path, _k: str):
        return (
            {
                "text": "one two three four",
                "segments": [
                    {"start": 0.0, "end": 1.2, "text": "one two"},
                    {"start": 1.2, "end": 3.0, "text": "three four five six seven"},
                ],
            },
            [],
        )

    monkeypatch.setattr(sub_mod, "_probe_audio_file_duration", lambda _p: (3.0, []))

    meta = sub_mod.build_subtitle_pack(
        narr,
        timeline_manifest_path=None,
        out_root=tmp_path / "outs",
        run_id="seg205c",
        subtitle_mode="simple",
        subtitle_source="audio",
        audio_path=mp3,
        transcribe_fn=fake_tf,
    )
    assert meta["ok"] is True
    assert meta.get("transcription_used") is True
    assert meta.get("fallback_used") is False
    assert meta.get("subtitle_source") == "audio"
    srt = Path(meta["subtitles_srt_path"]).read_text(encoding="utf-8")
    assert "-->" in srt
    assert meta["subtitle_count"] >= 2


def test_audio_transcription_cues_short_word_count(sub_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    narr = tmp_path / "nar_w.txt"
    narr.write_text("#\n\nReserve Satz genug Wörter hier drin.\n", encoding="utf-8")
    mp3 = tmp_path / "v2.mp3"
    mp3.write_bytes(b"y" * 200)

    long_seg = " ".join(f"w{i}" for i in range(25))

    def fake_tf(_p: Path, _k: str):
        return (
            {
                "text": long_seg,
                "segments": [{"start": 0.0, "end": 8.0, "text": long_seg}],
            },
            [],
        )

    monkeypatch.setattr(sub_mod, "_probe_audio_file_duration", lambda _p: (8.0, []))

    meta = sub_mod.build_subtitle_pack(
        narr,
        timeline_manifest_path=None,
        out_root=tmp_path / "outw",
        run_id="short205c",
        subtitle_mode="simple",
        subtitle_source="audio",
        audio_path=mp3,
        transcribe_fn=fake_tf,
    )
    assert meta["ok"] is True
    assert meta["subtitle_count"] >= 4


def test_fallback_estimate_without_timeline(sub_mod, tmp_path):
    narr = tmp_path / "e.txt"
    narr.write_text("Ein zwei drei vier fünf sechs sieben acht.\n", encoding="utf-8")
    meta = sub_mod.build_subtitle_pack(
        narr,
        timeline_manifest_path=None,
        out_root=tmp_path / "oute",
        run_id="est205b",
        subtitle_mode="simple",
    )
    assert meta["ok"] is True
    assert "subtitle_duration_estimate_used" in meta["warnings"]


def test_escape_subtitle_path_colon(render_mod, tmp_path):
    p = tmp_path / "sub folder" / "f.srt"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("1\n00:00:00,000 --> 00:00:01,000\nok\n", encoding="utf-8")
    s = render_mod._ffmpeg_escape_subtitle_file_path(p)
    raw_posix = p.resolve().as_posix()
    if ":" in raw_posix:
        assert r"\:" in s


def test_typewriter_render_contract_fallback_word_by_word(sub_mod, tmp_path):
    narr = tmp_path / "tw.txt"
    narr.write_text("# h\n\n" + " ".join(f"w{i}" for i in range(20)) + ".\n", encoding="utf-8")
    meta = sub_mod.build_subtitle_pack(
        narr,
        timeline_manifest_path=None,
        out_root=tmp_path / "outtw",
        run_id="tw205d",
        subtitle_mode="simple",
        subtitle_style="typewriter",
    )
    assert meta["ok"] is True
    c = meta["subtitle_render_contract"]
    assert c["style"] == "typewriter"
    assert c["fallback_style"] == "word_by_word"
    assert c["requires_character_timing"] is True
    assert any("typewriter_v1_contract_only" in w for w in (c.get("warnings") or []))


def test_subtitle_style_none_suppresses_cues_no_hard_error(sub_mod, tmp_path):
    narr = tmp_path / "nonevis.txt"
    narr.write_text("# x\n\nBeliebiger Text.\n", encoding="utf-8")
    meta = sub_mod.build_subtitle_pack(
        narr,
        timeline_manifest_path=None,
        out_root=tmp_path / "outnv",
        run_id="nonvis205d",
        subtitle_mode="simple",
        subtitle_style="none",
    )
    assert meta["ok"] is True
    assert meta["subtitle_count"] == 0
    assert "subtitle_style_none_visual_suppressed" in meta["warnings"]
    c = meta["subtitle_render_contract"]
    assert c["style"] == "none"
    assert c["max_words_per_cue"] == 0
    srt = Path(meta["subtitles_srt_path"]).read_text(encoding="utf-8")
    assert srt.strip() == ""


def test_subtitle_style_invalid_programmatic_defaults_classic_warning(sub_mod, tmp_path):
    narr = tmp_path / "inv.txt"
    narr.write_text("# h\n\nEins zwei drei vier fünf sechs sieben.\n", encoding="utf-8")
    meta = sub_mod.build_subtitle_pack(
        narr,
        timeline_manifest_path=None,
        out_root=tmp_path / "outinv",
        run_id="inv205d",
        subtitle_mode="simple",
        subtitle_style="neon_glow_not_valid",
    )
    assert meta["ok"] is True
    assert meta.get("subtitle_style") == "classic"
    assert any("subtitle_style_unknown_defaulting_classic" in w for w in meta["warnings"])
