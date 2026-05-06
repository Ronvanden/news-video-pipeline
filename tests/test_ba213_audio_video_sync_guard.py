"""BA 21.3 — Audio/Video Sync Guard (heuristisch, ffprobe in Tests gemockt)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, Tuple

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_PIPELINE = _ROOT / "scripts" / "run_local_preview_pipeline.py"
_SMOKE = _ROOT / "scripts" / "run_local_preview_smoke.py"


@pytest.fixture(scope="module")
def preview_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_pipeline", _PIPELINE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def smoke_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_smoke", _SMOKE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._pipeline_mod = None
    yield mod
    mod._pipeline_mod = None


def _touch(p: Path, b: bytes = b"x") -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b)


def _tl(tmp_path: Path, sec: float) -> str:
    p = tmp_path / "tl213.json"
    p.write_text(json.dumps({"estimated_duration_seconds": sec}), encoding="utf-8")
    return str(p.resolve())


def _sub_manifest(tmp_path: Path, srt_body: str) -> str:
    d = tmp_path / "sub213"
    d.mkdir(parents=True, exist_ok=True)
    srt = d / "s.srt"
    srt.write_text(srt_body, encoding="utf-8")
    m = d / "m.json"
    m.write_text(json.dumps({"subtitles_srt_path": str(srt)}), encoding="utf-8")
    return str(m.resolve())


def _base_result(tmp_path: Path, tl_sec: float, srt_body: str, media_sec: float) -> Dict[str, Any]:
    pv = tmp_path / "pv.mp4"
    cv = tmp_path / "cv.mp4"
    rp = tmp_path / "r.md"
    om = tmp_path / "OPEN_ME.md"
    aud = tmp_path / "a.wav"
    for p in (pv, cv, rp, om, aud):
        _touch(p)
    sm = _sub_manifest(tmp_path, srt_body)
    return {
        "ok": True,
        "warnings": [],
        "blocking_reasons": [],
        "paths": {
            "preview_with_subtitles": str(pv),
            "clean_video": str(cv),
            "founder_report": str(rp),
            "open_me": str(om),
            "subtitle_manifest": sm,
            "timeline_manifest": _tl(tmp_path, tl_sec),
            "audio_path": str(aud),
        },
        "report_path": str(rp),
        "open_me_path": str(om),
        "steps": {},
    }, media_sec


def _probe_const(sec: float):
    return lambda _p: (sec, None)


def test_sync_pass_aligned(preview_mod, tmp_path):
    r, sec = _base_result(
        tmp_path,
        4.0,
        "1\n00:00:00,000 --> 00:00:02,000\nA.\n\n2\n00:00:02,100 --> 00:00:04,000\nB.\n",
        4.0,
    )
    sg = preview_mod.build_local_preview_sync_guard(r, _probe=_probe_const(sec))
    assert sg["status"] == "pass"
    assert sg["durations"]["timeline_seconds"] == 4.0


def test_sync_warning_audio_missing(preview_mod, tmp_path):
    r, sec = _base_result(
        tmp_path,
        4.0,
        "1\n00:00:00,000 --> 00:00:02,000\nA.\n\n2\n00:00:02,100 --> 00:00:04,000\nB.\n",
        4.0,
    )
    del r["paths"]["audio_path"]
    sg = preview_mod.build_local_preview_sync_guard(r, _probe=_probe_const(sec))
    assert any(it["id"] == "audio_duration_available" and it["status"] == "warning" for it in sg["items"])
    assert sg["status"] == "pass"


def test_sync_warning_preview_vs_clean(preview_mod, tmp_path):
    r, _ = _base_result(
        tmp_path,
        4.0,
        "1\n00:00:00,000 --> 00:00:02,000\nA.\n\n2\n00:00:02,100 --> 00:00:04,000\nB.\n",
        4.0,
    )

    def probe(p: Path) -> Tuple[float | None, str | None]:
        if "cv" in str(p).replace("\\", "/"):
            return (4.0, None)
        return (5.2, None)

    sg = preview_mod.build_local_preview_sync_guard(r, _probe=probe)
    assert any(it["id"] == "preview_vs_clean_video" and it["status"] == "warning" for it in sg["items"])
    assert sg["status"] == "warning"


def test_sync_fail_preview_vs_timeline(preview_mod, tmp_path):
    r, _ = _base_result(
        tmp_path,
        6.0,
        "1\n00:00:00,000 --> 00:00:02,000\nA.\n\n2\n00:00:02,100 --> 00:00:04,000\nB.\n",
        6.0,
    )

    def probe(_p: Path) -> Tuple[float | None, str | None]:
        return (60.0, None)

    sg = preview_mod.build_local_preview_sync_guard(r, _probe=probe)
    assert any(it["id"] == "preview_video_vs_timeline" and it["status"] == "fail" for it in sg["items"])
    assert sg["status"] == "fail"


def test_sync_subtitle_vs_timeline_fail_gt_35pct(preview_mod, tmp_path):
    r, _ = _base_result(
        tmp_path,
        10.0,
        "1\n00:00:00,000 --> 00:00:01,000\nX.\n",
        10.0,
    )

    sg = preview_mod.build_local_preview_sync_guard(r, _probe=_probe_const(10.0))
    assert any(it["id"] == "subtitle_vs_timeline" and it["status"] == "fail" for it in sg["items"])


def test_sync_ffprobe_error_warning_no_crash(preview_mod, tmp_path):
    r, _ = _base_result(
        tmp_path,
        4.0,
        "1\n00:00:00,000 --> 00:00:02,000\nA.\n\n2\n00:00:02,100 --> 00:00:04,000\nB.\n",
        4.0,
    )

    def bad_probe(_p: Path) -> Tuple[float | None, str | None]:
        return (None, "ffprobe_nonzero_exit")

    sg = preview_mod.build_local_preview_sync_guard(r, _probe=bad_probe)
    assert sg["status"] == "warning"
    assert sg["durations"]["clean_video_seconds"] is None


def test_quality_checklist_has_sync_item(preview_mod, tmp_path):
    r, sec = _base_result(
        tmp_path,
        4.0,
        "1\n00:00:00,000 --> 00:00:02,000\nA.\n\n2\n00:00:02,100 --> 00:00:04,000\nB.\n",
        4.0,
    )
    qc = preview_mod.build_local_preview_quality_checklist(r, _sync_guard_probe=_probe_const(sec))
    assert any(it.get("id") == "sync_guard" for it in qc["items"])
    assert isinstance(r.get("sync_guard"), dict)


def test_founder_and_open_me_have_sync_section(preview_mod, tmp_path):
    r, sec = _base_result(
        tmp_path,
        4.0,
        "1\n00:00:00,000 --> 00:00:02,000\nA.\n\n2\n00:00:02,100 --> 00:00:04,000\nB.\n",
        4.0,
    )
    preview_mod.build_local_preview_quality_checklist(r, _sync_guard_probe=_probe_const(sec))
    assert "## Sync Guard" in preview_mod.build_local_preview_founder_report(r)
    assert "## Sync Guard" in preview_mod.build_local_preview_open_me(r)


def test_smoke_has_sync_line(smoke_mod, preview_mod):
    smoke_mod._pipeline_mod = preview_mod
    s = smoke_mod.build_local_preview_smoke_summary(
        {
            "ok": True,
            "warnings": [],
            "blocking_reasons": [],
            "paths": {"preview_with_subtitles": "/p.mp4"},
            "quality_checklist": {"status": "pass"},
            "subtitle_quality_check": {"status": "pass"},
            "sync_guard": {"status": "pass"},
        }
    )
    assert "Sync Guard: PASS" in s
