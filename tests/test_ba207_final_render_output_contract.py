"""BA 20.7 — Final Render Output Contract (render_final_story_video + burn_in_subtitles_preview)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from subprocess import CompletedProcess

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_RENDER = _ROOT / "scripts" / "render_final_story_video.py"
_BURN = _ROOT / "scripts" / "burn_in_subtitles_preview.py"


@pytest.fixture(scope="module")
def render_mod():
    spec = importlib.util.spec_from_file_location("render_final_story_video", _RENDER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def burn_mod():
    spec = importlib.util.spec_from_file_location("burn_in_subtitles_preview", _BURN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_render_clean_manifest_no_subtitles(render_mod, tmp_path, monkeypatch):
    assets = tmp_path / "a207"
    assets.mkdir()
    for n in ("scene_001.png", "scene_002.png"):
        (assets / n).write_bytes(b"\x89PNG\r\n\x1a\n")
    tl = tmp_path / "tl207.json"
    tl.write_text(
        json.dumps(
            {
                "assets_directory": str(assets),
                "audio_path": "",
                "scenes": [
                    {"image_path": "scene_001.png", "duration_seconds": 2},
                    {"image_path": "scene_002.png", "duration_seconds": 2},
                ],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "clean207.mp4"
    man_root = tmp_path / "manifests207"

    def fake_run(cmd, **kwargs):
        out.touch()
        return CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(render_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(render_mod, "_probe_video_duration", lambda _v, _f: (4.0, []))

    meta = render_mod.render_final_story_video(
        tl,
        output_video=out,
        motion_mode="static",
        subtitle_path=None,
        ffmpeg_bin="fm",
        ffprobe_bin="fp",
        run_id="ba207clean",
        write_output_manifest=True,
        manifest_root=man_root,
    )
    assert meta["video_created"] is True
    mp = Path(meta["render_output_manifest_path"])
    assert mp.is_file()
    disk = json.loads(mp.read_text(encoding="utf-8"))
    assert disk["subtitle_delivery_mode"] == "none"
    assert disk["renderer_used"] == "none"
    assert disk["clean_video_path"]
    assert "legacy_subtitle_path_burnin_used" not in meta["warnings"]


def test_render_legacy_subtitle_path_warning(render_mod, tmp_path, monkeypatch):
    assets = tmp_path / "a207b"
    assets.mkdir()
    for n in ("scene_001.png",):
        (assets / n).write_bytes(b"\x89PNG\r\n\x1a\n")
    tl = tmp_path / "tl207b.json"
    tl.write_text(
        json.dumps(
            {
                "assets_directory": str(assets),
                "audio_path": "",
                "scenes": [{"image_path": "scene_001.png", "duration_seconds": 2}],
            }
        ),
        encoding="utf-8",
    )
    srt = tmp_path / "leg.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nX\n", encoding="utf-8")
    out = tmp_path / "burn207.mp4"
    man_root = tmp_path / "manifests207b"

    def fake_run(cmd, **kwargs):
        out.touch()
        return CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(render_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(render_mod, "_probe_video_duration", lambda _v, _f: (2.0, []))

    meta = render_mod.render_final_story_video(
        tl,
        output_video=out,
        motion_mode="static",
        subtitle_path=srt,
        ffmpeg_bin="fm",
        ffprobe_bin="fp",
        run_id="ba207leg",
        write_output_manifest=True,
        manifest_root=man_root,
    )
    assert meta["video_created"] is True
    assert "legacy_subtitle_path_burnin_used" in meta["warnings"]
    disk = json.loads(Path(meta["render_output_manifest_path"]).read_text(encoding="utf-8"))
    assert disk["subtitle_delivery_mode"] in ("burn_in", "both")
    assert disk["renderer_used"] == "srt_burnin"


def test_burnin_writes_burnin_output_manifest(burn_mod, tmp_path):
    vid = tmp_path / "cin.mp4"
    vid.write_bytes(b"x")
    srt = tmp_path / "cs.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n", encoding="utf-8")
    man = tmp_path / "cm.json"
    man.write_text(
        json.dumps({"subtitle_style": "classic", "subtitles_srt_path": str(srt)}),
        encoding="utf-8",
    )

    def fake_run(cmd, **kwargs):
        Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
        Path(cmd[-1]).write_bytes(b"")
        return CompletedProcess(cmd, 0, "", "")

    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "or207",
        run_id="ba207burn",
        force=True,
        subprocess_run=fake_run,
        shutil_which=lambda n: "fm" if n == "ffmpeg" else None,
    )
    assert meta["ok"] is True
    assert "burnin_output_manifest_path" in meta
    bm = Path(meta["burnin_output_manifest_path"])
    assert bm.is_file()
    d = json.loads(bm.read_text(encoding="utf-8"))
    assert d["clean_input_video_path"] == str(vid.resolve())
    assert d["subtitle_burnin_video_path"].endswith("preview_with_subtitles.mp4")


def test_burnin_none_skips_video_but_writes_manifest(burn_mod, tmp_path):
    vid = tmp_path / "nv.mp4"
    vid.write_bytes(b"x")
    srt = tmp_path / "ns.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nZ\n", encoding="utf-8")
    man = tmp_path / "nm.json"
    man.write_text(
        json.dumps({"subtitle_style": "none", "subtitles_srt_path": str(srt)}),
        encoding="utf-8",
    )
    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "on207",
        run_id="ba207none",
        force=True,
        ffmpeg_bin="fm",
        subprocess_run=lambda *a, **k: CompletedProcess([], 0, "", ""),
        shutil_which=lambda _n: "x",
    )
    assert meta["ok"] is True
    assert meta["subtitle_delivery_mode"] == "none"
    assert Path(meta["burnin_output_manifest_path"]).is_file()
    d = json.loads(Path(meta["burnin_output_manifest_path"]).read_text(encoding="utf-8"))
    assert d["subtitle_delivery_mode"] == "none"
    assert d["subtitle_burnin_video_path"] == ""
