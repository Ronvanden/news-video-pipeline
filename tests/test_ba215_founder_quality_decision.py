"""BA 21.5 — Founder Quality Decision Layer."""

from __future__ import annotations

import importlib.util
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


def test_block_on_blocking_reason(preview_mod):
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": [],
        "blocking_reasons": ["ffmpeg_missing"],
        "steps": {
            "build_subtitles": {"ok": True, "subtitle_manifest_path": "/m", "warnings": []},
            "render_clean": {"video_created": True, "output_path": "/c", "warnings": []},
            "burnin_preview": {"ok": True, "skipped": False, "output_video_path": "/p", "warnings": []},
        },
        "quality_checklist": {"status": "pass", "items": []},
        "subtitle_quality_check": {"status": "pass", "items": [], "warnings": [], "summary": ""},
        "sync_guard": {"status": "pass", "items": [], "warnings": [], "summary": ""},
        "warning_classification": {"highest": "INFO", "counts": {}, "items": [], "summary": ""},
    }
    d = preview_mod.build_founder_quality_decision(r)
    assert d["decision_code"] == "BLOCK"
    assert "Blocking" in d["top_issue"] or "ffmpeg" in d["top_issue"].lower()


def test_block_on_quality_checklist_fail(preview_mod):
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": [],
        "blocking_reasons": [],
        "steps": {
            "build_subtitles": {"ok": True, "subtitle_manifest_path": "/m", "warnings": []},
            "render_clean": {"video_created": True, "output_path": "/c", "warnings": []},
            "burnin_preview": {"ok": True, "skipped": False, "output_video_path": "/p", "warnings": []},
        },
        "quality_checklist": {
            "status": "fail",
            "items": [{"id": "x", "label": "Preview fehlt", "status": "fail", "detail": "x", "path": ""}],
        },
        "subtitle_quality_check": {"status": "pass", "items": [], "warnings": [], "summary": ""},
        "sync_guard": {"status": "pass", "items": [], "warnings": [], "summary": ""},
        "warning_classification": {"highest": "INFO", "counts": {}, "items": [], "summary": ""},
    }
    d = preview_mod.build_founder_quality_decision(r)
    assert d["decision_code"] == "BLOCK"
    assert "Preview fehlt" in d["top_issue"] or "Quality" in d["top_issue"]


def test_review_when_verdict_warning(preview_mod):
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": ["build_warn"],
        "blocking_reasons": [],
        "steps": {
            "build_subtitles": {"ok": True, "subtitle_manifest_path": "/m", "warnings": []},
            "render_clean": {"video_created": True, "output_path": "/c", "warnings": []},
            "burnin_preview": {"ok": True, "skipped": False, "output_video_path": "/p", "warnings": []},
        },
        "quality_checklist": {"status": "pass", "items": []},
        "subtitle_quality_check": {"status": "pass", "items": [], "warnings": [], "summary": ""},
        "sync_guard": {"status": "pass", "items": [], "warnings": [], "summary": ""},
        "warning_classification": {"highest": "INFO", "counts": {}, "items": [], "summary": ""},
    }
    d = preview_mod.build_founder_quality_decision(r)
    assert d["decision_code"] == "REVIEW_REQUIRED"


def test_review_when_warning_class_check(preview_mod):
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": [],
        "blocking_reasons": [],
        "steps": {
            "build_subtitles": {"ok": True, "subtitle_manifest_path": "/m", "warnings": []},
            "render_clean": {"video_created": True, "output_path": "/c", "warnings": []},
            "burnin_preview": {"ok": True, "skipped": False, "output_video_path": "/p", "warnings": []},
        },
        "quality_checklist": {"status": "pass", "items": []},
        "subtitle_quality_check": {"status": "pass", "items": [], "warnings": [], "summary": ""},
        "sync_guard": {"status": "pass", "items": [], "warnings": [], "summary": ""},
        "warning_classification": {
            "highest": "CHECK",
            "counts": {},
            "items": [{"code": "sync_guard_timeline_missing", "level": "CHECK"}],
            "summary": "1 CHECK",
        },
    }
    d = preview_mod.build_founder_quality_decision(r)
    assert d["decision_code"] == "REVIEW_REQUIRED"
    assert d["signals"]["warning_level_highest"] == "CHECK"


def test_go_preview_all_green(preview_mod):
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": [],
        "blocking_reasons": [],
        "steps": {
            "build_subtitles": {"ok": True, "subtitle_manifest_path": "/m", "warnings": []},
            "render_clean": {"video_created": True, "output_path": "/c", "warnings": []},
            "burnin_preview": {"ok": True, "skipped": False, "output_video_path": "/p", "warnings": []},
        },
        "quality_checklist": {"status": "pass", "items": []},
        "subtitle_quality_check": {"status": "pass", "items": [], "warnings": [], "summary": ""},
        "sync_guard": {"status": "pass", "items": [], "warnings": [], "summary": ""},
        "warning_classification": {"highest": "INFO", "counts": {}, "items": [], "summary": ""},
    }
    d = preview_mod.build_founder_quality_decision(r)
    assert d["decision_code"] == "GO_PREVIEW"


def test_founder_report_section(preview_mod):
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": [],
        "blocking_reasons": [],
        "paths": {"preview_with_subtitles": "/p.mp4", "clean_video": "/c.mp4"},
        "steps": {
            "build_subtitles": {"ok": True, "subtitle_manifest_path": "/m", "warnings": []},
            "render_clean": {"video_created": True, "output_path": "/c", "warnings": []},
            "burnin_preview": {"ok": True, "skipped": False, "output_video_path": "/p", "warnings": []},
        },
        "founder_quality_decision": preview_mod.build_founder_quality_decision(
            {
                "ok": True,
                "warnings": [],
                "blocking_reasons": [],
                "steps": {
                    "build_subtitles": {"ok": True, "subtitle_manifest_path": "/m", "warnings": []},
                    "render_clean": {"video_created": True, "output_path": "/c", "warnings": []},
                    "burnin_preview": {"ok": True, "skipped": False, "output_video_path": "/p", "warnings": []},
                },
                "quality_checklist": {"status": "pass", "items": []},
                "subtitle_quality_check": {"status": "pass", "items": [], "warnings": [], "summary": ""},
                "sync_guard": {"status": "pass", "items": [], "warnings": [], "summary": ""},
                "warning_classification": {"highest": "INFO", "items": [], "summary": ""},
            }
        ),
    }
    md = preview_mod.build_local_preview_founder_report(r)
    assert "## Founder Decision (BA 21.5)" in md
    assert "GO_PREVIEW" in md


def test_finalize_attaches_founder_decision(preview_mod, tmp_path):
    pd = tmp_path / "local_preview_ba215"
    pd.mkdir()
    (pd / "clean_video.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42")
    (pd / "pv.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42")
    r: dict = {
        "ok": True,
        "run_id": "ba215",
        "pipeline_dir": str(pd),
        "warnings": [],
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
    assert "founder_quality_decision" in out
    fd = out["founder_quality_decision"]
    assert isinstance(fd, dict)
    assert fd.get("decision_code") in ("BLOCK", "REVIEW_REQUIRED", "GO_PREVIEW")
    assert fd.get("top_issue")
    om = (pd / "OPEN_ME.md").read_text(encoding="utf-8")
    assert "## Founder Decision (BA 21.5)" in om


def test_smoke_shows_founder_decision(smoke_mod, preview_mod):
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": [],
        "blocking_reasons": [],
        "paths": {"preview_with_subtitles": "/p.mp4"},
        "report_path": "/r.md",
        "steps": {
            "build_subtitles": {"ok": True, "subtitle_manifest_path": "/m", "warnings": []},
            "render_clean": {"video_created": True, "output_path": "/c", "warnings": []},
            "burnin_preview": {"ok": True, "skipped": False, "output_video_path": "/p", "warnings": []},
        },
        "founder_quality_decision": preview_mod.build_founder_quality_decision(
            {
                "ok": True,
                "warnings": [],
                "blocking_reasons": [],
                "steps": {
                    "build_subtitles": {"ok": True, "subtitle_manifest_path": "/m", "warnings": []},
                    "render_clean": {"video_created": True, "output_path": "/c", "warnings": []},
                    "burnin_preview": {"ok": True, "skipped": False, "output_video_path": "/p", "warnings": []},
                },
                "quality_checklist": {"status": "pass", "items": []},
                "subtitle_quality_check": {"status": "pass", "items": [], "warnings": [], "summary": ""},
                "sync_guard": {"status": "pass", "items": [], "warnings": [], "summary": ""},
                "warning_classification": {"highest": "INFO", "items": [], "summary": ""},
            }
        ),
    }
    s = smoke_mod.build_local_preview_smoke_summary(r)
    assert "Founder decision: GO_PREVIEW" in s
