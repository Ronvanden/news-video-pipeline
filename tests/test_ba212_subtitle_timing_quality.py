"""BA 21.2 — Subtitle Timing Quality Check (heuristisch, kein ffmpeg)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict

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


def _touch_artifacts(tmp_path: Path) -> Dict[str, str]:
    pv = tmp_path / "pv.mp4"
    rp = tmp_path / "r.md"
    om = tmp_path / "OPEN_ME.md"
    pv.write_bytes(b"x")
    rp.write_bytes(b"#")
    om.write_bytes(b"#")
    return {
        "preview_with_subtitles": str(pv.resolve()),
        "founder_report": str(rp.resolve()),
        "open_me": str(om.resolve()),
    }


def _write_srt_manifest(base: Path, srt_body: str) -> str:
    base.mkdir(parents=True, exist_ok=True)
    srt = base / "subtitles.srt"
    srt.write_text(srt_body, encoding="utf-8")
    man = base / "subtitle_manifest.json"
    man.write_text(json.dumps({"subtitles_srt_path": str(srt)}), encoding="utf-8")
    return str(man.resolve())


def _write_json_manifest(base: Path, doc: Dict[str, Any]) -> str:
    base.mkdir(parents=True, exist_ok=True)
    man = base / "subtitle_manifest.json"
    man.write_text(json.dumps(doc), encoding="utf-8")
    return str(man.resolve())


def test_subtitle_pass_srt_short_cues(preview_mod, tmp_path):
    sm = _write_srt_manifest(
        tmp_path / "sq_pass",
        "1\n00:00:00,000 --> 00:00:02,000\nShort one.\n\n2\n00:00:02,100 --> 00:00:04,000\nShort two.\n",
    )
    paths = _touch_artifacts(tmp_path)
    paths["subtitle_manifest"] = sm
    r: Dict[str, Any] = {"ok": True, "warnings": [], "blocking_reasons": [], "paths": paths, "steps": {}}
    sq = preview_mod.build_local_preview_subtitle_quality_check(r)
    assert sq["status"] == "pass"
    assert sq["cue_count"] == 2
    ids = {it["id"]: it["status"] for it in sq["items"]}
    assert ids["subtitle_manifest_exists"] == "pass"
    assert ids["subtitle_cues_present"] == "pass"


def test_subtitle_fail_manifest_missing(preview_mod, tmp_path):
    paths = _touch_artifacts(tmp_path)
    r: Dict[str, Any] = {"ok": True, "warnings": [], "blocking_reasons": [], "paths": paths, "steps": {}}
    sq = preview_mod.build_local_preview_subtitle_quality_check(r)
    assert sq["status"] == "fail"
    assert "subtitle_quality_manifest_missing" in sq["warnings"]


def test_subtitle_fail_invalid_json(preview_mod, tmp_path):
    base = tmp_path / "badjson"
    base.mkdir()
    mp = base / "subtitle_manifest.json"
    mp.write_text("{not json", encoding="utf-8")
    paths = _touch_artifacts(tmp_path)
    paths["subtitle_manifest"] = str(mp.resolve())
    r: Dict[str, Any] = {"ok": True, "warnings": [], "blocking_reasons": [], "paths": paths, "steps": {}}
    sq = preview_mod.build_local_preview_subtitle_quality_check(r)
    assert sq["status"] == "fail"
    assert "subtitle_quality_manifest_invalid_json" in sq["warnings"]


def test_subtitle_fail_no_cues(preview_mod, tmp_path):
    sm = _write_json_manifest(tmp_path / "nocues", {})
    paths = _touch_artifacts(tmp_path)
    paths["subtitle_manifest"] = sm
    r: Dict[str, Any] = {"ok": True, "warnings": [], "blocking_reasons": [], "paths": paths, "steps": {}}
    sq = preview_mod.build_local_preview_subtitle_quality_check(r)
    assert sq["status"] == "fail"
    assert "subtitle_quality_no_cues" in sq["warnings"]


def test_subtitle_fail_end_before_start_json(preview_mod, tmp_path):
    sm = _write_json_manifest(
        tmp_path / "inv",
        {"cues": [{"start": 2.0, "end": 1.0, "text": "bad"}]},
    )
    paths = _touch_artifacts(tmp_path)
    paths["subtitle_manifest"] = sm
    r: Dict[str, Any] = {"ok": True, "warnings": [], "blocking_reasons": [], "paths": paths, "steps": {}}
    sq = preview_mod.build_local_preview_subtitle_quality_check(r)
    assert sq["status"] == "fail"
    assert any(it["id"] == "subtitle_cue_duration_valid" and it["status"] == "fail" for it in sq["items"])


def test_subtitle_warning_too_many_words(preview_mod, tmp_path):
    long_words = " ".join([f"w{i}" for i in range(14)])
    sm = _write_json_manifest(
        tmp_path / "manyw",
        {"entries": [{"start": 0.0, "end": 3.0, "text": long_words}]},
    )
    paths = _touch_artifacts(tmp_path)
    paths["subtitle_manifest"] = sm
    r: Dict[str, Any] = {"ok": True, "warnings": [], "blocking_reasons": [], "paths": paths, "steps": {}}
    sq = preview_mod.build_local_preview_subtitle_quality_check(r)
    assert sq["status"] == "warning"
    assert any(it["id"] == "subtitle_cue_word_count_reasonable" and it["status"] == "warning" for it in sq["items"])


def test_subtitle_warning_too_many_chars(preview_mod, tmp_path):
    sm = _write_json_manifest(
        tmp_path / "manyc",
        {"items": [{"start": 0.0, "end": 4.0, "text": "x" * 81}]},
    )
    paths = _touch_artifacts(tmp_path)
    paths["subtitle_manifest"] = sm
    r: Dict[str, Any] = {"ok": True, "warnings": [], "blocking_reasons": [], "paths": paths, "steps": {}}
    sq = preview_mod.build_local_preview_subtitle_quality_check(r)
    assert sq["status"] == "warning"
    assert any(it["id"] == "subtitle_cue_text_length_reasonable" and it["status"] == "warning" for it in sq["items"])


def test_subtitle_warning_very_short_duration(preview_mod, tmp_path):
    sm = _write_srt_manifest(
        tmp_path / "shortd",
        "1\n00:00:00,000 --> 00:00:00,200\nBrief.\n",
    )
    paths = _touch_artifacts(tmp_path)
    paths["subtitle_manifest"] = sm
    r: Dict[str, Any] = {"ok": True, "warnings": [], "blocking_reasons": [], "paths": paths, "steps": {}}
    sq = preview_mod.build_local_preview_subtitle_quality_check(r)
    assert sq["status"] == "warning"
    assert any(it["id"] == "subtitle_cue_duration_valid" and it["status"] == "warning" for it in sq["items"])


def test_subtitle_warning_very_long_duration(preview_mod, tmp_path):
    sm = _write_srt_manifest(
        tmp_path / "longd",
        "1\n00:00:00,000 --> 00:00:09,000\nLong window.\n",
    )
    paths = _touch_artifacts(tmp_path)
    paths["subtitle_manifest"] = sm
    r: Dict[str, Any] = {"ok": True, "warnings": [], "blocking_reasons": [], "paths": paths, "steps": {}}
    sq = preview_mod.build_local_preview_subtitle_quality_check(r)
    assert sq["status"] == "warning"
    assert any(it["id"] == "subtitle_cue_duration_valid" and it["status"] == "warning" for it in sq["items"])


def test_subtitle_warning_overlap(preview_mod, tmp_path):
    sm = _write_srt_manifest(
        tmp_path / "ov",
        "1\n00:00:00,000 --> 00:00:03,000\nA.\n\n2\n00:00:02,000 --> 00:00:04,000\nB.\n",
    )
    paths = _touch_artifacts(tmp_path)
    paths["subtitle_manifest"] = sm
    r: Dict[str, Any] = {"ok": True, "warnings": [], "blocking_reasons": [], "paths": paths, "steps": {}}
    sq = preview_mod.build_local_preview_subtitle_quality_check(r)
    assert sq["status"] == "warning"
    assert any(it["id"] == "subtitle_cue_timing_order" and it["status"] == "warning" for it in sq["items"])


def test_quality_checklist_contains_subtitle_item(preview_mod, tmp_path):
    sm = _write_srt_manifest(
        tmp_path / "qcint",
        "1\n00:00:00,000 --> 00:00:01,500\nOk.\n",
    )
    paths = _touch_artifacts(tmp_path)
    paths["subtitle_manifest"] = sm
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": [],
        "blocking_reasons": [],
        "paths": paths,
        "report_path": paths["founder_report"],
        "open_me_path": paths["open_me"],
        "steps": {},
    }
    qc = preview_mod.build_local_preview_quality_checklist(r)
    assert any(it.get("id") == "subtitle_quality" for it in qc["items"])
    assert r.get("subtitle_quality_check") is not None


def test_founder_report_has_subtitle_section(preview_mod, tmp_path):
    sm = _write_srt_manifest(tmp_path / "fr", "1\n00:00:00,000 --> 00:00:02,000\nX.\n")
    paths = _touch_artifacts(tmp_path)
    paths["subtitle_manifest"] = sm
    r: Dict[str, Any] = {"ok": True, "warnings": [], "blocking_reasons": [], "paths": paths, "steps": {}}
    preview_mod.build_local_preview_quality_checklist(r)
    md = preview_mod.build_local_preview_founder_report(r)
    assert "## Subtitle Quality" in md


def test_open_me_has_subtitle_section(preview_mod, tmp_path):
    sm = _write_srt_manifest(tmp_path / "om", "1\n00:00:00,000 --> 00:00:02,000\nY.\n")
    paths = _touch_artifacts(tmp_path)
    paths["subtitle_manifest"] = sm
    r: Dict[str, Any] = {"ok": True, "warnings": [], "blocking_reasons": [], "paths": paths, "steps": {}}
    preview_mod.build_local_preview_quality_checklist(r)
    md = preview_mod.build_local_preview_open_me(r)
    assert "## Subtitle Quality" in md


def test_smoke_summary_subtitle_line(smoke_mod, preview_mod):
    smoke_mod._pipeline_mod = preview_mod
    s = smoke_mod.build_local_preview_smoke_summary(
        {
            "ok": True,
            "warnings": [],
            "blocking_reasons": [],
            "paths": {"preview_with_subtitles": "/p.mp4"},
            "report_path": "/r.md",
            "quality_checklist": {"status": "pass"},
            "subtitle_quality_check": {"status": "warning", "summary": "overlap"},
        }
    )
    assert "Subtitle Quality: WARNING" in s
