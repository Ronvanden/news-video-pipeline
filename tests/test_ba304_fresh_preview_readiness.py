"""BA 30.4 — Fresh preview readiness gate."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.founder_dashboard.html import get_founder_dashboard_html
from app.main import app
from app.production_assembly.fresh_preview_snapshot import (
    build_latest_fresh_preview_snapshot,
    evaluate_fresh_preview_readiness,
)


def _minimal_script():
    return json.dumps({"title": "T", "hook": "H", "chapters": [{"title": "K", "content": "Text."}]})


def _minimal_pack():
    return json.dumps({"scene_expansion": {"expanded_scene_assets": [{"visual_prompt": "p", "narration": "n"}]}})


def _minimal_manifest_non_placeholder():
    return json.dumps(
        {
            "assets": [
                {"scene_number": 1, "image_path": "scene_001.png", "video_path": "delivered_clip.mp4"},
            ]
        }
    )


def test_readiness_not_available_blocked(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: Path(p).resolve(),
    )
    r = build_latest_fresh_preview_snapshot(tmp_path)
    assert r["readiness_status"] == "blocked"
    assert r["readiness_score"] == 0
    assert "fresh_preview_not_available" in r["blocking_reasons"]


def test_readiness_empty_run_dir_blocked(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "empty_run"
    run.mkdir(parents=True)
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["fresh_preview_available"] is True
    assert r["readiness_status"] == "blocked"
    assert "missing_script_json" in r["blocking_reasons"]


def test_readiness_core_only_warning_missing_open_me(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "w1"
    gen = run / "generated_assets_w1"
    gen.mkdir(parents=True)
    (run / "script.json").write_text(_minimal_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_minimal_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_minimal_manifest_non_placeholder(), encoding="utf-8")
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["readiness_status"] == "warning"
    assert "missing_open_preview_smoke_md" in r["readiness_reasons"]
    assert "missing_preview_smoke_auto_summary" in r["readiness_reasons"]


def test_readiness_ready_full_run(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "ok1"
    gen = run / "generated_assets_ok1"
    work = root / ".preview_smoke_work" / "ok1"
    gen.mkdir(parents=True)
    work.mkdir(parents=True)
    (run / "script.json").write_text(_minimal_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_minimal_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_minimal_manifest_non_placeholder(), encoding="utf-8")
    (work / "OPEN_PREVIEW_SMOKE.md").write_text("# ok\n", encoding="utf-8")
    (root / "preview_smoke_auto_summary_ok1.json").write_text(
        json.dumps({"ok": True, "open_preview_smoke_report_path": str((work / "OPEN_PREVIEW_SMOKE.md").resolve())}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["readiness_status"] == "ready"
    assert r["readiness_score"] >= 85
    assert r["blocking_reasons"] == []


def test_readiness_summary_ok_false_warning(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "badsum"
    gen = run / "generated_assets_badsum"
    work = root / ".preview_smoke_work" / "badsum"
    gen.mkdir(parents=True)
    work.mkdir(parents=True)
    (run / "script.json").write_text(_minimal_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_minimal_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_minimal_manifest_non_placeholder(), encoding="utf-8")
    (work / "OPEN_PREVIEW_SMOKE.md").write_text("# x\n", encoding="utf-8")
    (root / "preview_smoke_auto_summary_badsum.json").write_text(json.dumps({"ok": False}), encoding="utf-8")
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["readiness_status"] == "warning"
    assert "preview_smoke_summary_ok_false" in r["readiness_reasons"]


def test_readiness_invalid_script_json_blocked(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "badjs"
    gen = run / "generated_assets_badjs"
    gen.mkdir(parents=True)
    (run / "script.json").write_text("NOT JSON", encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_minimal_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_minimal_manifest_non_placeholder(), encoding="utf-8")
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["readiness_status"] == "blocked"
    assert "script_json_invalid_or_too_large" in r["blocking_reasons"]


def test_evaluate_fresh_preview_readiness_exported():
    m = evaluate_fresh_preview_readiness({"fresh_preview_available": False, "operator_next_step": "x"})
    assert m["readiness_status"] == "blocked"


def test_dashboard_html_readiness_marker():
    html = get_founder_dashboard_html()
    assert "data-ba304-readiness-marker" in html
    assert "readiness_status" in html or "fp-readiness-badge" in html
    assert "data-ba306-exec-strip" in html


def test_readiness_placeholder_manifest_hint(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "ph1"
    gen = run / "generated_assets_ph1"
    gen.mkdir(parents=True)
    (run / "script.json").write_text(_minimal_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_minimal_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(
        json.dumps({"assets": [{"scene_number": 1, "image_path": "scene_001.png"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["readiness_status"] == "warning"
    assert "manifest_assets_look_placeholder_only" in r["readiness_reasons"]


def test_api_includes_readiness_fields(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.routes.founder_dashboard.default_local_preview_out_root",
        lambda: tmp_path,
    )
    (tmp_path / "fresh_topic_preview").mkdir(parents=True)
    client = TestClient(app)
    r = client.get("/founder/dashboard/fresh-preview/snapshot")
    assert r.status_code == 200
    d = r.json()
    assert d.get("fresh_preview_snapshot_version") == "ba30_4_v1"
    assert "readiness_status" in d
    assert "readiness_score" in d
    assert "blocking_reasons" in d
    assert "readiness_reasons" in d
