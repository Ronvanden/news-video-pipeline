"""BA 32.58 — Renderer löst relative ``assets_directory`` / ``image_path`` gegen Timeline-Ordner auf."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from subprocess import CompletedProcess

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_RENDER = _ROOT / "scripts" / "render_final_story_video.py"


@pytest.fixture(scope="module")
def render_mod():
    spec = importlib.util.spec_from_file_location("render_final_story_video_ba358", _RENDER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_relative_assets_directory_uses_timeline_parent_not_cwd(render_mod, tmp_path, monkeypatch):
    """Medien liegen per ``../media`` relativ zur Timeline; CWD ist absichtlich falsch."""
    wrong_cwd = tmp_path / "wrong_cwd"
    wrong_cwd.mkdir()
    run = tmp_path / "run"
    media = run / "media"
    media.mkdir(parents=True)
    (media / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    tl_sub = run / "timeline_x"
    tl_sub.mkdir()
    tl = tl_sub / "timeline_manifest.json"
    tl.write_text(
        json.dumps(
            {
                "assets_directory": "../media",
                "audio_path": "",
                "scenes": [
                    {"scene_number": 1, "image_path": "scene_001.png", "duration_seconds": 2},
                ],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "ba358_ok.mp4"
    expected_png = (media / "scene_001.png").resolve()

    def fake_run(cmd, **kwargs):
        flat = [str(x) for x in cmd]
        if "-f" in flat and "concat" in flat and "-i" in flat:
            i_idx = flat.index("-i") + 1
            concat_body = Path(flat[i_idx]).read_text(encoding="utf-8")
            needle = expected_png.resolve().as_posix()
            assert needle in concat_body, (needle, concat_body)
        else:
            assert str(expected_png) in flat, flat
        out.touch()
        return CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(render_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(render_mod, "_probe_video_duration", lambda _v, _f: (2.0, []))

    old = os.getcwd()
    try:
        os.chdir(wrong_cwd)
        meta = render_mod.render_final_story_video(
            tl,
            output_video=out,
            motion_mode="static",
            ffmpeg_bin="fm",
            ffprobe_bin="fp",
        )
    finally:
        os.chdir(old)

    assert meta["video_created"] is True
    assert meta.get("render_image_segment_count") == 1


def test_missing_relative_image_emits_render_image_missing(render_mod, tmp_path):
    assets = tmp_path / "a358miss"
    assets.mkdir()
    tl = tmp_path / "tl358miss.json"
    tl.write_text(
        json.dumps(
            {
                "assets_directory": str(assets),
                "audio_path": "",
                "scenes": [
                    {"scene_number": 7, "image_path": "scene_001.png", "duration_seconds": 2},
                ],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "v358miss.mp4"
    meta = render_mod.render_final_story_video(
        tl,
        output_video=out,
        motion_mode="static",
        ffmpeg_bin="fm",
        ffprobe_bin="fp",
    )
    assert meta["video_created"] is False
    assert any("render_image_missing:7" in str(w) for w in (meta.get("warnings") or []))
    assert any(str(x).startswith("missing_scene_media:") for x in (meta.get("blocking_reasons") or []))


def test_absolute_image_path_still_works(render_mod, tmp_path, monkeypatch):
    root = tmp_path / "abs358"
    assets = root / "assets_marked"
    assets.mkdir(parents=True)
    png = root / "abs_scene.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n")
    tl = root / "timeline.json"
    tl.write_text(
        json.dumps(
            {
                "assets_directory": str(assets),
                "audio_path": "",
                "scenes": [
                    {
                        "scene_number": 1,
                        "image_path": str(png.resolve()),
                        "duration_seconds": 2,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    out = root / "out.mp4"

    def fake_run(cmd, **kwargs):
        out.touch()
        return CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(render_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(render_mod, "_probe_video_duration", lambda _v, _f: (2.0, []))

    meta = render_mod.render_final_story_video(
        tl,
        output_video=out,
        motion_mode="static",
        ffmpeg_bin="fm",
        ffprobe_bin="fp",
    )
    assert meta["video_created"] is True
