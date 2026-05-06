"""BA 20.6b — Typewriter-ASS-Renderer (burn_in_subtitles_preview)."""

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
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return m


def test_parse_srt_cues_and_ass_sections(burn_mod, tmp_path):
    srt = tmp_path / "p.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nHello world.\n\n"
        "2\n00:00:02,500 --> 00:00:04,000\nSecond cue.\n",
        encoding="utf-8",
    )
    cues = burn_mod._parse_srt_cues(srt)
    assert len(cues) == 2
    assert cues[0].text == "Hello world."
    ass = tmp_path / "out.ass"
    res = burn_mod._build_typewriter_ass_file(
        cues, ass, font_size=22, margin_v=45, max_chars_per_line=34, min_frame_duration=0.035
    )
    assert res["ok"] is True
    body = ass.read_text(encoding="utf-8")
    assert "[Script Info]" in body
    assert "[V4+ Styles]" in body
    assert "[Events]" in body
    assert "Format: Layer, Start, End" in body


def test_typewriter_dialogue_progressive_not_full_cue_immediately(burn_mod, tmp_path):
    long_text = "Word " * 15 + "end."
    srt = tmp_path / "long.srt"
    srt.write_text(
        f"1\n00:00:00,000 --> 00:00:05,000\n{long_text}\n",
        encoding="utf-8",
    )
    cues = burn_mod._parse_srt_cues(srt)
    ass = tmp_path / "tw.ass"
    burn_mod._build_typewriter_ass_file(
        cues, ass, font_size=22, margin_v=45, max_chars_per_line=34, min_frame_duration=0.035
    )
    lines = [ln for ln in ass.read_text(encoding="utf-8").splitlines() if ln.startswith("Dialogue:")]
    assert len(lines) >= 3
    first = lines[0]
    assert long_text not in first
    assert "Dialogue:" in first and "{\\an2}" in first
    last = lines[-1]
    assert "end." in last or "Word" in last


def test_format_ass_timestamp(burn_mod):
    assert burn_mod._format_ass_timestamp(0.0) == "0:00:00.00"
    assert burn_mod._format_ass_timestamp(61.23).startswith("0:01:01")


def test_escape_ass_text_braces(burn_mod):
    assert burn_mod._escape_ass_text("a{b}c") == r"a\{b\}c"


def test_build_ffmpeg_ass_filter_escapes_path(burn_mod, tmp_path):
    p = tmp_path / "d" / "f.ass"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x", encoding="utf-8")
    vf = burn_mod._build_ffmpeg_ass_filter(p)
    assert vf.startswith("ass='")
    esc = burn_mod._ffmpeg_escape_subtitle_file_path(p)
    assert esc in vf


def test_typewriter_burn_uses_ass_renderer(burn_mod, tmp_path):
    vid = tmp_path / "v.mp4"
    vid.write_bytes(b"x")
    srt = tmp_path / "s.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,500\nHi there.\n", encoding="utf-8")
    man = _manifest(tmp_path, style="typewriter", srt_path=srt)
    calls: list[list[str]] = []

    def fake_run(cmd, check=True, capture_output=True, text=True):
        calls.append(list(cmd))
        Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
        Path(cmd[-1]).write_bytes(b"")
        return CompletedProcess(cmd, 0, "", "")

    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "or",
        run_id="ba206b_tw",
        force=True,
        subprocess_run=fake_run,
        shutil_which=lambda n: "fm" if n == "ffmpeg" else None,
    )
    assert meta["ok"] is True
    assert meta["renderer_used"] == "ass_typewriter"
    assert meta["fallback_used"] is False
    assert "subtitle_typewriter_ass_renderer_used" in meta["warnings"]
    assert "subtitle_style_typewriter_fallback_to_srt_burnin" not in meta["warnings"]
    assert meta["ass_subtitle_path"].endswith("preview_typewriter.ass")
    assert meta["subtitle_delivery_mode"] == "burn_in"
    assert meta["clean_video_required"] is True
    assert meta["input_video_role"] == "clean_candidate"
    vf = calls[0][calls[0].index("-vf") + 1]
    assert "ass='" in vf
    assert "subtitles=" not in vf


def test_typewriter_fallback_when_ass_build_fails(burn_mod, tmp_path, monkeypatch):
    def fail_build(*_a, **_k):
        return {"ok": False, "error": "no_events", "warnings": [], "dialogue_count": 0}

    monkeypatch.setattr(burn_mod, "_build_typewriter_ass_file", fail_build)

    vid = tmp_path / "v2.mp4"
    vid.write_bytes(b"x")
    srt = tmp_path / "s2.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nXy\n", encoding="utf-8")
    man = _manifest(tmp_path, style="typewriter", srt_path=srt)
    calls: list[list[str]] = []

    def fake_run(cmd, check=True, capture_output=True, text=True):
        calls.append(list(cmd))
        Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
        Path(cmd[-1]).write_bytes(b"")
        return CompletedProcess(cmd, 0, "", "")

    meta = burn_mod.burn_in_subtitles_preview(
        vid,
        man,
        out_root=tmp_path / "or2",
        run_id="ba206b_fb",
        force=True,
        subprocess_run=fake_run,
        shutil_which=lambda n: "fm" if n == "ffmpeg" else None,
    )
    assert meta["ok"] is True
    assert meta["fallback_used"] is True
    assert meta["renderer_used"] == "srt_burnin"
    assert "subtitle_typewriter_ass_failed_fallback_srt" in meta["warnings"]
    vf = calls[0][calls[0].index("-vf") + 1]
    assert "subtitles=" in vf
