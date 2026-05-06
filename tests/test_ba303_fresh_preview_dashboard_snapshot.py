"""BA 30.3 — Fresh preview snapshot + Founder Dashboard wiring (BA 30.4 readiness ergänzt)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.founder_dashboard.html import get_founder_dashboard_html
from app.main import app
from app.production_assembly.fresh_preview_snapshot import build_latest_fresh_preview_snapshot


def _fp_script():
    return json.dumps({"title": "T", "hook": "H", "chapters": [{"title": "K", "content": "x"}]})


def _fp_pack():
    return json.dumps({"scene_expansion": {"expanded_scene_assets": [{"narration": "n"}]}})


def _fp_manifest():
    return json.dumps({"assets": [{"scene_number": 1, "video_path": "c.mp4"}]})


def test_snapshot_no_fresh_dir(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: Path(p).resolve(),
    )
    r = build_latest_fresh_preview_snapshot(tmp_path)
    assert r["ok"] is True
    assert r["fresh_preview_available"] is False
    assert "fresh_topic_preview_dir_absent" in r["warnings"]
    assert r["readiness_status"] == "blocked"


def test_snapshot_run_with_core_files(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "run_a"
    gen = run / "generated_assets_run_a"
    gen.mkdir(parents=True)
    (run / "script.json").write_text(_fp_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_fp_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_fp_manifest(), encoding="utf-8")

    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["ok"] is True
    assert r["fresh_preview_available"] is True
    assert r["latest_run_id"] == "run_a"
    assert r["script_json_present"] is True
    assert r["scene_asset_pack_present"] is True
    assert r["asset_manifest_present"] is True
    assert r["preview_smoke_summary_present"] is False
    assert r["readiness_status"] == "warning"


def test_snapshot_open_preview_from_work_dir(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "run_b"
    gen = run / "generated_assets_run_b"
    gen.mkdir(parents=True)
    (run / "script.json").write_text(_fp_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_fp_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_fp_manifest(), encoding="utf-8")
    work = root / ".preview_smoke_work" / "run_b"
    work.mkdir(parents=True)
    open_md = work / "OPEN_PREVIEW_SMOKE.md"
    open_md.write_text("# Preview Smoke Ergebnis\n", encoding="utf-8")

    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["open_preview_smoke_report_present"] is True
    assert r["open_preview_smoke_report_path"]
    assert "OPEN_PREVIEW_SMOKE.md" in r["open_preview_smoke_report_path"]


def test_snapshot_newest_run_by_mtime(tmp_path: Path, monkeypatch):
    import os
    import time

    root = tmp_path / "output"
    old = root / "fresh_topic_preview" / "old_run"
    new = root / "fresh_topic_preview" / "new_run"
    for d in (old, new):
        gen = d / f"generated_assets_{d.name}"
        gen.mkdir(parents=True)
        (d / "script.json").write_text(_fp_script(), encoding="utf-8")
        (d / "scene_asset_pack.json").write_text(_fp_pack(), encoding="utf-8")
        (gen / "asset_manifest.json").write_text(_fp_manifest(), encoding="utf-8")
    t0 = time.time() - 100
    os.utime(old, (t0, t0))
    os.utime(new, (t0 + 50, t0 + 50))

    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["latest_run_id"] == "new_run"


def test_dashboard_html_contains_fresh_preview_panel():
    html = get_founder_dashboard_html()
    assert "VideoPipe Founder Cockpit" in html
    assert "Preview Power" in html
    assert "fp-preview-power-gauge" in html
    assert "data-ba306c-preview-power" in html
    assert "fd-sidebar" in html
    assert "data-ba306c-sidebar" in html
    assert "fd-score-gauge" in html
    assert "data-ba306d-score-gauge" in html
    assert "Noch kein Score" in html
    assert "Fresh Preview" in html
    assert "Fresh Preview Smoke (BA 30.3–30.8)" in html
    assert "fdLoadFreshPreviewSnapshot" in html
    assert "out-fp-snapshot" in html
    assert "/founder/dashboard/fresh-preview/snapshot" in html
    assert "data-ba304-readiness-marker" in html
    assert "Fresh Preview aktualisieren" in html
    assert "data-ba305-refresh" in html
    assert "data-ba305-copy-markers" in html
    assert "data-ba305-copy-path" in html
    assert "operator_next_step" in html
    assert "Operator Review" in html
    assert "data-ba310-operator-review" in html
    assert "data-review-decision-marker" in html


def test_api_fresh_preview_snapshot_endpoint(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.routes.founder_dashboard.default_local_preview_out_root",
        lambda: tmp_path,
    )
    (tmp_path / "fresh_topic_preview").mkdir(parents=True)

    client = TestClient(app)
    r = client.get("/founder/dashboard/fresh-preview/snapshot")
    assert r.status_code == 200
    data = r.json()
    assert data.get("fresh_preview_snapshot_version") == "ba31_0_v1"
    assert data.get("ok") is True


def test_config_includes_fresh_preview_relative():
    client = TestClient(app)
    r = client.get("/founder/dashboard/config")
    assert r.status_code == 200
    cfg = r.json()
    assert "fresh_preview_snapshot_relative" in cfg
    assert cfg["fresh_preview_snapshot_relative"]["path"] == "/founder/dashboard/fresh-preview/snapshot"
