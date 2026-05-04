"""BA 20.6c — Clean Render Contract (burn_in_subtitles_preview)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from subprocess import CompletedProcess

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "burn_in_subtitles_preview.py"


@pytest.fixture(scope="module")
def burn_mod():
    spec = importlib.util.spec_from_file_location("burn_in_subtitles_preview", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_classify_clean_candidate(burn_mod, tmp_path):
    p = tmp_path / "final_story_video.mp4"
    p.write_bytes(b"x")
    role, w = burn_mod._classify_input_video_role(p)
    assert role == "clean_candidate"
    assert w == []


def test_classify_preview_with_subtitles_name(burn_mod, tmp_path):
    p = tmp_path / "preview_with_subtitles.mp4"
    p.write_bytes(b"x")
    role, w = burn_mod._classify_input_video_role(p)
    assert role == "possibly_burned"
    assert "input_video_may_already_have_burned_subtitles" in w


def test_classify_subtitle_burnin_in_parent_path(burn_mod, tmp_path):
    d = tmp_path / "output" / "subtitle_burnin_test"
    d.mkdir(parents=True)
    p = d / "clean_name.mp4"
    p.write_bytes(b"x")
    role, w = burn_mod._classify_input_video_role(p)
    assert role == "possibly_burned"
    assert "input_video_may_already_have_burned_subtitles" in w


def test_suspected_burned_input_blocks_without_force(burn_mod, tmp_path):
    vid = tmp_path / "preview_with_subtitles.mp4"
    vid.write_bytes(b"x")
    srt = tmp_path / "s.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n", encoding="utf-8")
    man = tmp_path / "m.json"
    man.write_text(
        json.dumps({"subtitle_style": "classic", "subtitles_srt_path": str(srt)}),
        encoding="utf-8",
    )
    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "o",
        run_id="blk206c",
        force=False,
        ffmpeg_bin="fm",
        subprocess_run=lambda *a, **k: CompletedProcess([], 0, "", ""),
        shutil_which=lambda _n: "x",
    )
    assert meta["ok"] is False
    assert "input_video_possibly_burned_subtitles_use_clean_or_force" in meta["blocking_reasons"]
    assert meta["input_video_role"] == "possibly_burned"
    assert meta["subtitle_delivery_mode"] == "burn_in"
    assert meta["clean_video_required"] is True


def test_suspected_burned_allowed_with_force(burn_mod, tmp_path):
    vid = tmp_path / "with_subtitles_copy.mp4"
    vid.write_bytes(b"x")
    srt = tmp_path / "s2.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n", encoding="utf-8")
    man = tmp_path / "m2.json"
    man.write_text(
        json.dumps({"subtitle_style": "classic", "subtitles_srt_path": str(srt)}),
        encoding="utf-8",
    )
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
        Path(cmd[-1]).write_bytes(b"")
        return CompletedProcess(cmd, 0, "", "")

    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "o2",
        run_id="f206c",
        force=True,
        subprocess_run=fake_run,
        shutil_which=lambda n: "fm" if n == "ffmpeg" else None,
    )
    assert meta["ok"] is True
    assert meta["input_video_role"] == "possibly_burned"
    assert meta["subtitle_delivery_mode"] == "burn_in"
    assert meta["clean_video_required"] is True
    assert meta["output_video_role"] == "subtitle_burnin_preview"
    assert len(calls) == 1


def test_typewriter_contract_burn_in(burn_mod, tmp_path):
    vid = tmp_path / "clean.mp4"
    vid.write_bytes(b"x")
    srt = tmp_path / "st.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nAb\n", encoding="utf-8")
    man = tmp_path / "mt.json"
    man.write_text(
        json.dumps({"subtitle_style": "typewriter", "subtitles_srt_path": str(srt)}),
        encoding="utf-8",
    )

    def fake_run(cmd, **kwargs):
        Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
        Path(cmd[-1]).write_bytes(b"")
        return CompletedProcess(cmd, 0, "", "")

    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "otw",
        run_id="tw206c",
        force=True,
        subprocess_run=fake_run,
        shutil_which=lambda n: "fm" if n == "ffmpeg" else None,
    )
    assert meta["ok"] is True
    assert meta["subtitle_delivery_mode"] == "burn_in"
    assert meta["clean_video_required"] is True
    assert meta["input_video_role"] == "clean_candidate"


def test_none_contract_delivery_none(burn_mod, tmp_path):
    vid = tmp_path / "v.mp4"
    vid.write_bytes(b"x")
    srt = tmp_path / "sn.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nX\n", encoding="utf-8")
    man = tmp_path / "mn.json"
    man.write_text(
        json.dumps({"subtitle_style": "none", "subtitles_srt_path": str(srt)}),
        encoding="utf-8",
    )
    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "on",
        run_id="n206c",
        force=True,
        ffmpeg_bin="fm",
        subprocess_run=lambda *a, **k: CompletedProcess([], 0, "", ""),
        shutil_which=lambda _n: "x",
    )
    assert meta["subtitle_delivery_mode"] == "none"
    assert meta["clean_video_required"] is False
    assert meta["renderer_used"] == "none"
    assert meta["output_video_role"] == ""
