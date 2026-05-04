"""BA 20.11 — Local Preview Smoke (Summary, Exit Codes, Pfade)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SMOKE = _ROOT / "scripts" / "run_local_preview_smoke.py"
_PIPELINE = _ROOT / "scripts" / "run_local_preview_pipeline.py"


@pytest.fixture
def smoke_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_smoke", _SMOKE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._pipeline_mod = None
    yield mod
    mod._pipeline_mod = None


@pytest.fixture(scope="module")
def pipeline_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_pipeline", _PIPELINE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_exit_codes(pipeline_mod, smoke_mod):
    assert smoke_mod.local_preview_exit_code("PASS") == 0
    assert smoke_mod.local_preview_exit_code("WARNING") == 2
    assert smoke_mod.local_preview_exit_code("FAIL") == 1
    assert smoke_mod.local_preview_exit_code("") == 1
    assert smoke_mod.local_preview_exit_code("unknown") == 1


def test_resolve_preview_prefers_extended_keys_then_ba209_then_clean(smoke_mod):
    assert smoke_mod.resolve_local_preview_smoke_video_path(
        {"preview_video": "/a.mp4", "clean_video": "/c.mp4"}
    ) == "/a.mp4"
    assert smoke_mod.resolve_local_preview_smoke_video_path(
        {"clean_video": "/c.mp4", "preview_with_subtitles": "/p.mp4"}
    ) == "/p.mp4"
    assert smoke_mod.resolve_local_preview_smoke_video_path({"clean_video": "/c.mp4"}) == "/c.mp4"
    assert smoke_mod.resolve_local_preview_smoke_video_path({}) == ""
    assert smoke_mod.resolve_local_preview_smoke_video_path(None) == ""


def test_resolve_report_path(smoke_mod):
    assert smoke_mod.resolve_local_preview_smoke_report_path({"report_path": "/r.md"}) == "/r.md"
    assert smoke_mod.resolve_local_preview_smoke_report_path(
        {"paths": {"founder_report": "/f.md"}}
    ) == "/f.md"
    assert smoke_mod.resolve_local_preview_smoke_report_path({}) == ""
    assert smoke_mod.resolve_local_preview_smoke_report_path(None) == ""


def test_summary_pass_contains_fields(smoke_mod, pipeline_mod):
    r: Dict[str, Any] = {
        "ok": True,
        "run_id": "x",
        "pipeline_dir": "/out/l",
        "warnings": [],
        "blocking_reasons": [],
        "report_path": "/out/l/local_preview_report.md",
        "paths": {
            "preview_with_subtitles": "/out/p.mp4",
            "clean_video": "/out/c.mp4",
        },
        "steps": {
            "build_subtitles": {"ok": True, "subtitle_manifest_path": "/m.json", "warnings": []},
            "render_clean": {"video_created": True, "output_path": "/out/c.mp4", "warnings": []},
            "burnin_preview": {"ok": True, "skipped": False, "output_video_path": "/out/p.mp4", "warnings": []},
        },
        "quality_checklist": {"status": "pass"},
        "subtitle_quality_check": {"status": "pass"},
        "sync_guard": {"status": "pass"},
    }
    s = smoke_mod.build_local_preview_smoke_summary(r)
    assert "Local Preview Smoke" in s
    assert "Status: PASS" in s
    assert "Quality: PASS" in s
    assert "Subtitle Quality: PASS" in s
    assert "Sync Guard: PASS" in s
    assert "Preview öffnen: /out/p.mp4" in s
    assert "Report öffnen: /out/l/local_preview_report.md" in s
    assert "Open-Me Datei:" in s
    assert "Open-Me Datei: nicht verfügbar" in s
    assert "Untertitel-Timing" in s
    r["open_me_path"] = "/out/l/OPEN_ME.md"
    s2 = smoke_mod.build_local_preview_smoke_summary(r)
    assert "Open-Me Datei: /out/l/OPEN_ME.md" in s2


def test_summary_warning_next_step(smoke_mod):
    r = {
        "ok": True,
        "warnings": ["w1"],
        "blocking_reasons": [],
        "paths": {"preview_with_subtitles": "/p.mp4"},
        "report_path": "/r.md",
        "steps": {
            "build_subtitles": {"ok": True, "subtitle_manifest_path": "/m", "warnings": []},
            "render_clean": {"video_created": True, "output_path": "/c", "warnings": []},
            "burnin_preview": {"ok": True, "skipped": False, "output_video_path": "/p.mp4", "warnings": []},
        },
    }
    s = smoke_mod.build_local_preview_smoke_summary(r)
    assert "Status: WARNING" in s
    assert "Repair" in s or "Warnungen" in s


def test_summary_fail(smoke_mod):
    r = {
        "ok": False,
        "warnings": [],
        "blocking_reasons": ["build_subtitles_failed"],
        "paths": {},
        "steps": {},
    }
    s = smoke_mod.build_local_preview_smoke_summary(r)
    assert "Status: FAIL" in s
    assert "nicht verfügbar" in s
    assert "Behebe zuerst die Blocking Reasons" in s


def test_summary_missing_keys_no_crash(smoke_mod):
    s = smoke_mod.build_local_preview_smoke_summary({})
    assert "Status: FAIL" in s
    assert "nicht verfügbar" in s


def test_main_exit_codes_with_fake_pipeline(smoke_mod, tmp_path, monkeypatch, pipeline_mod):
    tl = tmp_path / "tl.json"
    nar = tmp_path / "n.txt"
    tl.write_text("{}", encoding="utf-8")
    nar.write_text("b", encoding="utf-8")

    class FakePl:
        resolve_local_preview_video_path = staticmethod(pipeline_mod.resolve_local_preview_video_path)
        resolve_local_preview_report_path = staticmethod(pipeline_mod.resolve_local_preview_report_path)
        resolve_local_preview_open_me_path = staticmethod(pipeline_mod.resolve_local_preview_open_me_path)

        def compute_local_preview_verdict(self, r):
            return self.verdict

        def local_preview_next_step_for_verdict(self, v):
            return pipeline_mod.local_preview_next_step_for_verdict(v)

        def run_local_preview_pipeline(self, *a, **k):
            rid = k.get("run_id", "rid")
            base = tmp_path / f"local_preview_{rid}"
            return {
                "ok": self.run_ok,
                "run_id": rid,
                "pipeline_dir": str(base),
                "warnings": list(self.warnings),
                "blocking_reasons": list(self.blocking),
                "report_path": str(base / "local_preview_report.md"),
                "paths": {
                    "preview_with_subtitles": str(tmp_path / "pv.mp4"),
                    "clean_video": str(tmp_path / "cv.mp4"),
                },
                "steps": {},
                "report_markdown": "# x",
            }

    fake = FakePl()
    fake.verdict = "PASS"
    fake.run_ok = True
    fake.warnings = []
    fake.blocking = []
    smoke_mod._pipeline_mod = fake
    assert smoke_mod.main(["--timeline-manifest", str(tl), "--narration-script", str(nar), "--out-root", str(tmp_path), "--run-id", "e0"]) == 0

    fake.verdict = "WARNING"
    fake.warnings = ["x"]
    assert smoke_mod.main(["--timeline-manifest", str(tl), "--narration-script", str(nar), "--out-root", str(tmp_path), "--run-id", "e1"]) == 2

    fake.verdict = "FAIL"
    fake.blocking = ["b"]
    assert smoke_mod.main(["--timeline-manifest", str(tl), "--narration-script", str(nar), "--out-root", str(tmp_path), "--run-id", "e2"]) == 1


def test_main_print_json_contains_meta(smoke_mod, tmp_path, monkeypatch, pipeline_mod, capsys):
    tl = tmp_path / "t.json"
    nar = tmp_path / "n.txt"
    tl.write_text("{}", encoding="utf-8")
    nar.write_text("b", encoding="utf-8")

    class FakePl:
        verdict = "PASS"

        resolve_local_preview_video_path = staticmethod(pipeline_mod.resolve_local_preview_video_path)
        resolve_local_preview_report_path = staticmethod(pipeline_mod.resolve_local_preview_report_path)
        resolve_local_preview_open_me_path = staticmethod(pipeline_mod.resolve_local_preview_open_me_path)

        def compute_local_preview_verdict(self, r):
            return self.verdict

        def local_preview_next_step_for_verdict(self, v):
            return pipeline_mod.local_preview_next_step_for_verdict(v)

        def run_local_preview_pipeline(self, *a, **k):
            return {"ok": True, "run_id": "j1", "paths": {}, "warnings": [], "blocking_reasons": []}

    smoke_mod._pipeline_mod = FakePl()
    rc = smoke_mod.main(
        [
            "--timeline-manifest",
            str(tl),
            "--narration-script",
            str(nar),
            "--out-root",
            str(tmp_path),
            "--print-json",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "---" in out
    assert '"run_id": "j1"' in out
    json.loads(out.split("---", 1)[1].strip())


def test_module_import_smoke():
    spec = importlib.util.spec_from_file_location("smoke2", _SMOKE)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert callable(m.main)
    assert callable(m.build_local_preview_smoke_summary)
