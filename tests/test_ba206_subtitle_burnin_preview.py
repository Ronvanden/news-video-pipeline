"""BA 20.6 — burn_in_subtitles_preview.py (mocks, kein schwerer ffmpeg-Lauf)."""

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


def _manifest(tmp: Path, *, style: str, srt_path: Path) -> Path:
    m = tmp / "subtitle_manifest.json"
    m.write_text(
        json.dumps(
            {
                "subtitle_style": style,
                "subtitles_srt_path": str(srt_path),
                "subtitle_render_contract": {"style": style},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return m


def test_classic_ok_with_mocked_ffmpeg(burn_mod, tmp_path):
    vid = tmp_path / "in.mp4"
    vid.write_bytes(b"not-real-mp4")
    srt = tmp_path / "sub.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n", encoding="utf-8")
    man = _manifest(tmp_path, style="classic", srt_path=srt)

    calls: list[list[str]] = []

    def fake_run(cmd, check=True, capture_output=True, text=True):
        calls.append(list(cmd))
        Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
        Path(cmd[-1]).write_bytes(b"")
        return CompletedProcess(cmd, 0, "", "")

    def fake_which(name: str):
        if name == "ffmpeg":
            return "ffmpeg_mock"
        if name == "ffprobe":
            return None
        return None

    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "outroot",
        run_id="ba206classic",
        force=True,
        subprocess_run=fake_run,
        shutil_which=fake_which,
    )
    assert meta["ok"] is True
    assert meta["skipped"] is False
    assert meta["fallback_used"] is False
    assert meta["subtitle_style"] == "classic"
    assert len(calls) == 1
    vf = calls[0][calls[0].index("-vf") + 1]
    assert "subtitles=" in vf
    assert "Alignment=2" in vf
    assert "MarginV=45" in vf
    assert "subtitle_burnin_safe_style_applied" in meta["warnings"]
    assert meta["output_video_path"].endswith("preview_with_subtitles.mp4")
    assert meta.get("renderer_used") == "srt_burnin"
    assert meta.get("ass_subtitle_path") == ""
    assert meta.get("input_video_role") == "clean_candidate"
    assert meta.get("subtitle_delivery_mode") == "burn_in"
    assert meta.get("clean_video_required") is True
    assert meta.get("output_video_role") == "subtitle_burnin_preview"


def test_typewriter_uses_ass_not_srt_filter(burn_mod, tmp_path):
    vid = tmp_path / "in2.mp4"
    vid.write_bytes(b"x")
    srt = tmp_path / "sub2.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n", encoding="utf-8")
    man = _manifest(tmp_path, style="typewriter", srt_path=srt)
    calls: list[list[str]] = []

    def fake_run(cmd, check=True, capture_output=True, text=True):
        calls.append(list(cmd))
        Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
        Path(cmd[-1]).write_bytes(b"")
        return CompletedProcess(cmd, 0, "", "")

    def fake_which(name: str):
        return "ffmpeg_mock" if name == "ffmpeg" else None

    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "o2",
        run_id="ba206tw",
        force=True,
        subprocess_run=fake_run,
        shutil_which=fake_which,
    )
    assert meta["ok"] is True
    assert meta["fallback_used"] is False
    assert meta.get("renderer_used") == "ass_typewriter"
    assert "subtitle_typewriter_ass_renderer_used" in meta["warnings"]
    vf = calls[0][calls[0].index("-vf") + 1]
    assert "ass='" in vf and "subtitles=" not in vf


def test_none_skipped_no_subprocess(burn_mod, tmp_path):
    vid = tmp_path / "in3.mp4"
    vid.write_bytes(b"x")
    srt = tmp_path / "sub3.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nX\n", encoding="utf-8")
    man = _manifest(tmp_path, style="none", srt_path=srt)

    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return CompletedProcess(cmd, 0, "", "")

    def fake_which(name: str):
        return "ffmpeg_mock" if name == "ffmpeg" else None

    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "o3",
        run_id="ba206none",
        force=True,
        subprocess_run=fake_run,
        shutil_which=fake_which,
    )
    assert meta["ok"] is True
    assert meta["skipped"] is True
    assert meta["output_video_path"] == ""
    assert "subtitle_style_none_skipped" in meta["warnings"]
    assert calls == []
    assert meta.get("renderer_used") == "none"
    assert meta.get("ass_subtitle_path") == ""
    assert meta.get("subtitle_delivery_mode") == "none"
    assert meta.get("clean_video_required") is False
    assert meta.get("output_video_role") == ""


def test_input_video_missing_blocking(burn_mod, tmp_path):
    vid = tmp_path / "missing.mp4"
    srt = tmp_path / "s.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nA\n", encoding="utf-8")
    man = _manifest(tmp_path, style="classic", srt_path=srt)

    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "o4",
        run_id="ba206miss",
        force=True,
        ffmpeg_bin="ffmpeg_mock",
        subprocess_run=lambda *a, **k: CompletedProcess([], 0, "", ""),
        shutil_which=lambda _n: "x",
    )
    assert meta["ok"] is False
    assert "input_video_missing" in meta["blocking_reasons"]


def test_subtitles_srt_missing_blocking(burn_mod, tmp_path):
    vid = tmp_path / "v.mp4"
    vid.write_bytes(b"x")
    man = tmp_path / "badman.json"
    man.write_text(
        json.dumps(
            {
                "subtitle_style": "classic",
                "subtitles_srt_path": str(tmp_path / "nope.srt"),
            }
        ),
        encoding="utf-8",
    )

    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "o5",
        run_id="ba206nosrt",
        force=True,
        ffmpeg_bin="ffmpeg_mock",
        subprocess_run=lambda *a, **k: CompletedProcess([], 0, "", ""),
        shutil_which=lambda _n: "x",
    )
    assert meta["ok"] is False
    assert "subtitles_srt_missing" in meta["blocking_reasons"]


def test_build_ffmpeg_subtitle_filter_contains_safe_style(burn_mod, tmp_path):
    p = tmp_path / "sty.srt"
    p.write_text("1\n00:00:00,000 --> 00:00:01,000\nok\n", encoding="utf-8")
    vf = burn_mod._build_ffmpeg_subtitle_filter(p)
    assert "Alignment=2" in vf
    assert "MarginV=45" in vf
    assert "MarginL=40" in vf
    assert "MarginR=40" in vf
    assert "BorderStyle=1" in vf
    assert "FontSize=22" in vf


def test_ffmpeg_escape_colon_in_path(burn_mod, tmp_path):
    p = tmp_path / "deep" / "sub_colon.srt"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x", encoding="utf-8")
    esc = burn_mod._ffmpeg_escape_subtitle_file_path(p)
    assert ":" not in esc or r"\:" in esc
    vf = burn_mod._build_ffmpeg_subtitle_filter(p)
    assert "subtitles='" in vf
    assert esc in vf


def test_wrap_long_cue_emits_wrapped_warning_and_file(burn_mod, tmp_path):
    long_line = "Wort " * 20
    srt = tmp_path / "long.srt"
    srt.write_text(
        f"1\n00:00:00,000 --> 00:00:10,000\n{long_line}\n",
        encoding="utf-8",
    )
    vid = tmp_path / "inv.mp4"
    vid.write_bytes(b"x")
    man = _manifest(tmp_path, style="classic", srt_path=srt)

    def fake_run(cmd, check=True, capture_output=True, text=True):
        Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
        Path(cmd[-1]).write_bytes(b"")
        return CompletedProcess(cmd, 0, "", "")

    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "wrapout",
        run_id="ba206wrap",
        force=True,
        subprocess_run=fake_run,
        shutil_which=lambda n: "ffm" if n == "ffmpeg" else None,
    )
    assert meta["ok"] is True
    assert "subtitle_srt_wrapped_for_burnin" in meta["warnings"]
    wrapped = Path(meta["output_dir"]) / "preview_subtitles_wrapped.srt"
    assert wrapped.is_file()
    body = wrapped.read_text(encoding="utf-8")
    assert body.count("\n") >= 3


def test_ffmpeg_missing_blocking(burn_mod, tmp_path):
    vid = tmp_path / "v2.mp4"
    vid.write_bytes(b"x")
    srt = tmp_path / "s2.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nB\n", encoding="utf-8")
    man = _manifest(tmp_path, style="classic", srt_path=srt)

    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "o6",
        run_id="ba206noff",
        force=True,
        ffmpeg_bin=None,
        subprocess_run=lambda *a, **k: CompletedProcess([], 0, "", ""),
        shutil_which=lambda _n: None,
    )
    assert meta["ok"] is False
    assert "ffmpeg_missing" in meta["blocking_reasons"]
