"""BA 20.9 — One Command Local Preview Pipeline (Orchestrierung ohne echtes ffmpeg)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_local_preview_pipeline.py"


@pytest.fixture(scope="module")
def preview_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_pipeline", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _min_subtitle_manifest(tmp_path: Path, tag: str) -> Path:
    d = tmp_path / f"sub209_{tag}"
    d.mkdir(parents=True, exist_ok=True)
    srt = d / "cues.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nA.\n\n2\n00:00:02,100 --> 00:00:04,000\nB.\n",
        encoding="utf-8",
    )
    m = d / "subtitle_manifest.json"
    m.write_text(json.dumps({"subtitles_srt_path": str(srt)}), encoding="utf-8")
    return m


def test_pipeline_calls_build_render_burn_in_order(preview_mod, tmp_path, monkeypatch):
    order: List[str] = []
    tl = tmp_path / "tl.json"
    nar = tmp_path / "nar.txt"
    tl.write_text(json.dumps({"estimated_duration_seconds": 4.0}), encoding="utf-8")
    nar.write_text("body", encoding="utf-8")
    sub_m = _min_subtitle_manifest(tmp_path, "order")
    aud_stub = tmp_path / "a209.wav"
    aud_stub.write_bytes(b"\0")

    def fake_build(
        narration_script_path: Path,
        *,
        timeline_manifest_path: Path,
        out_root: Path,
        run_id: str,
        subtitle_mode: str,
        subtitle_source: str = "narration",
        subtitle_style: str = "classic",
        audio_path=None,
        transcribe_fn=None,
    ) -> Dict[str, Any]:
        order.append("build")
        assert run_id == "ba209rid"
        assert narration_script_path.resolve() == nar.resolve()
        assert timeline_manifest_path.resolve() == tl.resolve()
        return {
            "ok": True,
            "subtitle_manifest_path": str(sub_m),
            "audio_path": str(aud_stub),
            "warnings": ["build_warn"],
            "blocking_reasons": [],
        }

    def fake_render(
        timeline_path: Path,
        *,
        output_video: Path,
        motion_mode=None,
        subtitle_path=None,
        ffmpeg_bin=None,
        ffprobe_bin=None,
        run_id=None,
        write_output_manifest=False,
        manifest_root=None,
    ) -> Dict[str, Any]:
        order.append("render")
        assert timeline_path.resolve() == tl.resolve()
        assert subtitle_path is None
        assert run_id == "ba209rid"
        assert "local_preview_ba209rid" in str(output_video)
        assert str(output_video).replace("\\", "/").endswith("clean_video.mp4")
        output_video.parent.mkdir(parents=True, exist_ok=True)
        output_video.write_bytes(b"cv")
        return {
            "video_created": True,
            "warnings": [],
            "blocking_reasons": [],
        }

    def fake_burn(
        input_video: Path,
        subtitle_manifest: Path,
        *,
        out_root: Path,
        run_id: str,
        force: bool,
        ffmpeg_bin=None,
        subprocess_run=None,
        shutil_which=None,
    ) -> Dict[str, Any]:
        order.append("burn")
        assert run_id == "ba209rid"
        assert subtitle_manifest.resolve() == sub_m.resolve()
        burn_out = tmp_path / "preview.mp4"
        burn_out.write_bytes(b"pv")
        return {
            "ok": True,
            "skipped": False,
            "output_video_path": str(burn_out),
            "warnings": ["burn_warn"],
            "blocking_reasons": [],
        }

    monkeypatch.setattr(preview_mod, "_probe_media_duration_seconds", lambda p, **kw: (4.0, None))

    meta = preview_mod.run_local_preview_pipeline(
        tl,
        nar,
        out_root=tmp_path,
        run_id="ba209rid",
        build_subtitle_pack_fn=fake_build,
        render_final_story_video_fn=fake_render,
        burn_in_subtitles_preview_fn=fake_burn,
    )
    assert order == ["build", "render", "burn"]
    assert meta["ok"] is True
    assert meta["run_id"] == "ba209rid"
    assert "build_warn" in meta["warnings"] and "burn_warn" in meta["warnings"]
    piped = Path(meta["pipeline_dir"])
    central = piped / "preview_with_subtitles.mp4"
    assert central.is_file()
    assert Path(meta["paths"]["preview_with_subtitles"]) == central.resolve()
    assert meta["paths"]["preview_video"] == meta["paths"]["preview_with_subtitles"]
    assert Path(meta["paths"]["burnin_preview_source"]) == (tmp_path / "preview.mp4").resolve()
    assert "local_preview_ba209rid" in meta["pipeline_dir"]


def test_stops_after_build_failure(preview_mod, tmp_path):
    order: List[str] = []

    def fake_build(*_a, **_k):
        order.append("build")
        return {"ok": False, "subtitle_manifest_path": "", "warnings": ["w"], "blocking_reasons": ["missing"]}

    def fake_render(*_a, **_k):
        order.append("render")
        raise AssertionError("render should not run")

    def fake_burn(*_a, **_k):
        order.append("burn")
        raise AssertionError("burn should not run")

    meta = preview_mod.run_local_preview_pipeline(
        tmp_path / "t.json",
        tmp_path / "n.txt",
        out_root=tmp_path,
        run_id="x",
        build_subtitle_pack_fn=fake_build,
        render_final_story_video_fn=fake_render,
        burn_in_subtitles_preview_fn=fake_burn,
    )
    assert order == ["build"]
    assert meta["ok"] is False
    assert "missing" in meta["blocking_reasons"]


def test_stops_after_render_failure(preview_mod, tmp_path, monkeypatch):
    order: List[str] = []
    sub_m = _min_subtitle_manifest(tmp_path, "rendfail")
    aud_stub = tmp_path / "a209rf.wav"
    aud_stub.write_bytes(b"\0")

    def fake_build(*_a, **_k):
        order.append("build")
        return {
            "ok": True,
            "subtitle_manifest_path": str(sub_m),
            "audio_path": str(aud_stub),
            "warnings": [],
            "blocking_reasons": [],
        }

    def fake_render(*_a, **_k):
        order.append("render")
        return {"video_created": False, "warnings": [], "blocking_reasons": ["ffmpeg_encode_failed"]}

    def fake_burn(*_a, **_k):
        order.append("burn")
        raise AssertionError("burn should not run")

    monkeypatch.setattr(preview_mod, "_probe_media_duration_seconds", lambda p, **kw: (4.0, None))
    tlf = tmp_path / "t_rf.json"
    tlf.write_text(json.dumps({"estimated_duration_seconds": 4.0}), encoding="utf-8")
    (tmp_path / "n.txt").write_text("n", encoding="utf-8")

    meta = preview_mod.run_local_preview_pipeline(
        tlf,
        tmp_path / "n.txt",
        out_root=tmp_path,
        run_id="y",
        build_subtitle_pack_fn=fake_build,
        render_final_story_video_fn=fake_render,
        burn_in_subtitles_preview_fn=fake_burn,
    )
    assert order == ["build", "render"]
    assert meta["ok"] is False
    assert meta["steps"]["burnin_preview"] is None


def test_burn_skipped_style_none_still_ok(preview_mod, tmp_path, monkeypatch):
    sub_m = _min_subtitle_manifest(tmp_path, "burnskip")
    aud_stub = tmp_path / "a209z.wav"
    aud_stub.write_bytes(b"\0")
    (tmp_path / "t.json").write_text(json.dumps({"estimated_duration_seconds": 4.0}), encoding="utf-8")
    (tmp_path / "n.txt").write_text("n", encoding="utf-8")

    def fake_build(*_a, **_k):
        return {
            "ok": True,
            "subtitle_manifest_path": str(sub_m),
            "audio_path": str(aud_stub),
            "warnings": [],
            "blocking_reasons": [],
        }

    def fake_render(*_a, **_k):
        return {"video_created": True, "warnings": [], "blocking_reasons": []}

    def fake_burn(*_a, **_k):
        return {
            "ok": True,
            "skipped": True,
            "output_video_path": "",
            "warnings": ["subtitle_style_none_skipped"],
            "blocking_reasons": [],
        }

    monkeypatch.setattr(preview_mod, "_probe_media_duration_seconds", lambda p, **kw: (4.0, None))

    meta = preview_mod.run_local_preview_pipeline(
        tmp_path / "t.json",
        tmp_path / "n.txt",
        out_root=tmp_path,
        run_id="z",
        build_subtitle_pack_fn=fake_build,
        render_final_story_video_fn=fake_render,
        burn_in_subtitles_preview_fn=fake_burn,
    )
    assert meta["ok"] is True
    assert meta["paths"]["preview_with_subtitles"] == ""


def test_main_prints_json_and_exit_zero_on_ok(preview_mod, tmp_path, capsys, monkeypatch):
    tl = tmp_path / "tl2.json"
    nar = tmp_path / "n2.txt"
    tl.write_text(json.dumps({"estimated_duration_seconds": 4.0}), encoding="utf-8")
    nar.write_text("x", encoding="utf-8")
    sub_m = _min_subtitle_manifest(tmp_path, "main209")
    aud_stub = tmp_path / "a209main.wav"
    aud_stub.write_bytes(b"\0")

    def fake_build(*_a, **_k):
        return {
            "ok": True,
            "subtitle_manifest_path": str(sub_m),
            "audio_path": str(aud_stub),
            "warnings": [],
            "blocking_reasons": [],
        }

    def fake_render(*_a, **kw):
        ov = kw.get("output_video")
        if ov is not None:
            Path(ov).parent.mkdir(parents=True, exist_ok=True)
            Path(ov).write_bytes(b"cv")
        return {"video_created": True, "warnings": [], "blocking_reasons": []}

    def fake_burn(*_a, **_k):
        outp = tmp_path / "out.mp4"
        outp.write_bytes(b"o")
        return {
            "ok": True,
            "skipped": False,
            "output_video_path": str(outp),
            "warnings": [],
            "blocking_reasons": [],
        }

    real_run = preview_mod.run_local_preview_pipeline

    def wrapped(timeline_manifest, narration_script, **kw):
        return real_run(
            timeline_manifest,
            narration_script,
            build_subtitle_pack_fn=fake_build,
            render_final_story_video_fn=fake_render,
            burn_in_subtitles_preview_fn=fake_burn,
            **kw,
        )

    monkeypatch.setattr(preview_mod, "run_local_preview_pipeline", wrapped)
    monkeypatch.setattr(preview_mod, "_probe_media_duration_seconds", lambda p, **kw: (4.0, None))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_local_preview_pipeline.py",
            "--timeline-manifest",
            str(tl),
            "--narration-script",
            str(nar),
            "--out-root",
            str(tmp_path),
            "--run-id",
            "cli209",
        ],
    )
    rc = preview_mod.main()
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["ok"] is True
    assert parsed["run_id"] == "cli209"
