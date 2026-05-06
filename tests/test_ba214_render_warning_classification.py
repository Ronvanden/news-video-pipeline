"""BA 21.4 — Render Warning Classification (INFO / CHECK / WARNING / BLOCKING)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

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


def test_classify_known_levels(preview_mod):
    assert preview_mod.classify_local_preview_warning("quality_checklist_build_failed") == "BLOCKING"
    assert preview_mod.classify_local_preview_warning("ffmpeg_missing") == "BLOCKING"
    assert preview_mod.classify_local_preview_warning("build_warn") == "WARNING"
    assert preview_mod.classify_local_preview_warning("sync_guard_fail") == "WARNING"
    assert preview_mod.classify_local_preview_warning("sync_guard_clean_probe_failed") == "CHECK"
    assert preview_mod.classify_local_preview_warning("sync_guard_no_audio_file") == "INFO"
    assert preview_mod.classify_local_preview_warning("preview_with_subtitles_already_exists") == "INFO"
    assert preview_mod.classify_local_preview_warning("subtitle_mode_unknown_defaulting_simple:x") == "INFO"


def test_classify_unknown_default_warning(preview_mod):
    assert preview_mod.classify_local_preview_warning("totally_unknown_operator_code") == "WARNING"


def test_classify_sync_guard_unknown_prefix_check(preview_mod):
    assert preview_mod.classify_local_preview_warning("sync_guard_future_hypothetical_code") == "CHECK"


def test_gather_merges_without_duplicates(preview_mod):
    r = {
        "warnings": ["build_warn"],
        "steps": {
            "build_subtitles": {"warnings": ["burn_warn"]},
        },
        "sync_guard": {"warnings": ["sync_guard_fail", "build_warn"]},
        "subtitle_quality_check": {"warnings": ["subtitle_quality_warning"]},
        "quality_checklist": {"warnings": ["sync_guard_fail"]},
    }
    g = preview_mod._gather_local_preview_warnings_for_classification(r)
    assert g == ["build_warn", "burn_warn", "sync_guard_fail", "subtitle_quality_warning"]


def test_build_highest_is_worst_present(preview_mod):
    r = {
        "warnings": ["preview_with_subtitles_already_exists", "quality_checklist_build_failed"],
        "steps": {},
    }
    bc = preview_mod.build_local_preview_warning_classification(r)
    assert bc["highest"] == "BLOCKING"
    assert bc["counts"]["BLOCKING"] == 1
    assert bc["counts"]["INFO"] == 1
    assert len(bc["items"]) == 2


def test_build_empty_result_info(preview_mod):
    bc = preview_mod.build_local_preview_warning_classification({})
    assert bc["highest"] == "INFO"
    assert bc["summary"] == "keine Warnungen"
    assert bc["items"] == []


def test_founder_report_contains_classification_section(preview_mod):
    r = {
        "ok": True,
        "run_id": "r214",
        "pipeline_dir": "/tmp",
        "warnings": ["build_warn"],
        "blocking_reasons": [],
        "paths": {"preview_with_subtitles": "/p.mp4", "clean_video": "/c.mp4"},
        "steps": {},
        "warning_classification": preview_mod.build_local_preview_warning_classification(
            {"warnings": ["build_warn"], "steps": {}}
        ),
    }
    md = preview_mod.build_local_preview_founder_report(r)
    assert "## Warning Classification (BA 21.4)" in md
    assert "[WARNING] `build_warn`" in md


def test_open_me_contains_warning_levels(preview_mod):
    r = {
        "ok": True,
        "run_id": "r214b",
        "pipeline_dir": "/tmp",
        "warnings": [],
        "blocking_reasons": [],
        "paths": {"preview_with_subtitles": "/p.mp4", "clean_video": "/c.mp4"},
        "warning_classification": preview_mod.build_local_preview_warning_classification({}),
    }
    om = preview_mod.build_local_preview_open_me(r)
    assert "## Warning Levels (BA 21.4)" in om


def test_finalize_attaches_warning_classification(preview_mod, tmp_path):
    pd = tmp_path / "local_preview_ba214"
    pd.mkdir()
    (pd / "clean_video.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42")
    (pd / "pv.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42")
    r: dict = {
        "ok": True,
        "run_id": "ba214",
        "pipeline_dir": str(pd),
        "warnings": ["sync_guard_clean_probe_failed"],
        "blocking_reasons": [],
        "steps": {
            "build_subtitles": {"ok": True, "subtitle_manifest_path": "/m.json", "warnings": []},
            "render_clean": {"video_created": True, "output_path": str(pd / "clean_video.mp4"), "warnings": []},
            "burnin_preview": {"ok": True, "skipped": False, "output_video_path": str(pd / "pv.mp4"), "warnings": []},
        },
        "paths": {
            "clean_video": str(pd / "clean_video.mp4"),
            "preview_with_subtitles": str(pd / "pv.mp4"),
        },
    }
    out = preview_mod.finalize_local_preview_operator_artifacts(r)
    assert "warning_classification" in out
    wc = out["warning_classification"]
    assert isinstance(wc, dict)
    # Checkliste zieht Subtitle-Quality/Sync mit; CHECK (Top-Warnung) kann durch WARNING aus SQ überstimmt werden.
    assert wc.get("highest") in ("CHECK", "WARNING")
    codes = {it.get("code") for it in wc.get("items", []) if isinstance(it, dict)}
    assert "sync_guard_clean_probe_failed" in codes


def test_smoke_shows_warning_level_when_present(smoke_mod, preview_mod):
    r = {
        "ok": True,
        "warnings": [],
        "blocking_reasons": [],
        "paths": {"preview_with_subtitles": "/p.mp4"},
        "report_path": "/r.md",
        "steps": {},
        "quality_checklist": {"status": "pass"},
        "warning_classification": preview_mod.build_local_preview_warning_classification(
            {"warnings": ["build_warn"], "steps": {}}
        ),
    }
    s = smoke_mod.build_local_preview_smoke_summary(r)
    assert "Warning level: WARNING" in s
