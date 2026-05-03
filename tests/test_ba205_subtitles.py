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


def test_escape_subtitle_path_colon(render_mod, tmp_path):
    p = tmp_path / "sub folder" / "f.srt"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("1\n00:00:00,000 --> 00:00:01,000\nok\n", encoding="utf-8")
    s = render_mod._ffmpeg_escape_subtitle_file_path(p)
    raw_posix = p.resolve().as_posix()
    if ":" in raw_posix:
        assert r"\:" in s
