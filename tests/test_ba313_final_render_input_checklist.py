"""BA 31.3 — Final Render Input Checklist (Snapshot + Dashboard)."""

from __future__ import annotations

import json
from pathlib import Path

from app.founder_dashboard.html import get_founder_dashboard_html
from app.production_assembly.fresh_preview_snapshot import (
    build_final_render_input_checklist,
    build_latest_fresh_preview_snapshot,
)


def _script():
    return json.dumps({"title": "T", "hook": "H", "chapters": [{"title": "K", "content": "Text."}]})


def _pack():
    return json.dumps({"scene_expansion": {"expanded_scene_assets": [{"visual_prompt": "p", "narration": "n"}]}})


def _manifest_ok():
    return json.dumps(
        {
            "assets": [
                {"scene_number": 1, "image_path": "scene_001.png", "video_path": "clip.mp4"},
            ]
        }
    )


def test_checklist_blocked_incomplete_core(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "empty_run"
    run.mkdir(parents=True)
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["final_render_input_checklist_version"] == "ba31_3_v1"
    assert r["final_render_input_checklist_status"] == "blocked"
    assert "script_json" in r["final_render_input_missing"]


def test_checklist_pending_dry_run_only(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "dry1"
    gen = run / "generated_assets_dry1"
    gen.mkdir(parents=True)
    (run / "script.json").write_text(_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_manifest_ok(), encoding="utf-8")
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["final_render_gate_status"] == "locked"
    assert r["final_render_input_checklist_status"] == "pending"


def test_checklist_warning_gate_ready_no_bundle(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "ok1"
    gen = run / "generated_assets_ok1"
    work = root / ".preview_smoke_work" / "ok1"
    gen.mkdir(parents=True)
    work.mkdir(parents=True)
    (run / "script.json").write_text(_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_manifest_ok(), encoding="utf-8")
    open_md = work / "OPEN_PREVIEW_SMOKE.md"
    open_md.write_text("# ok\n", encoding="utf-8")
    (root / "preview_smoke_auto_summary_ok1.json").write_text(
        json.dumps({"ok": True, "open_preview_smoke_report_path": str(open_md.resolve())}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["final_render_gate_status"] == "ready"
    assert r["final_render_input_checklist_status"] == "warning"
    assert "render_input_bundle" in r["final_render_input_missing"]


def test_checklist_ready_with_extended_artifacts(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "ok1"
    gen = run / "generated_assets_ok1"
    gen.mkdir(parents=True)
    work_base = root / ".preview_smoke_work" / "ok1"
    work_base.mkdir(parents=True)
    lp_dir = work_base / "local_preview"
    lp_dir.mkdir(parents=True)
    (run / "script.json").write_text(_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_manifest_ok(), encoding="utf-8")
    open_md = work_base / "OPEN_PREVIEW_SMOKE.md"
    open_md.write_text("# ok\n", encoding="utf-8")
    (root / "preview_smoke_auto_summary_ok1.json").write_text(
        json.dumps({"ok": True, "open_preview_smoke_report_path": str(open_md.resolve())}),
        encoding="utf-8",
    )
    (root / "render_input_bundle_ok1.json").write_text("{}", encoding="utf-8")
    (root / "motion_timeline_manifest_ok1.json").write_text("{}", encoding="utf-8")
    (root / "motion_clip_manifest_ok1.json").write_text("{}", encoding="utf-8")
    (root / "production_pack_ok1").mkdir(parents=True)
    (lp_dir / "local_preview_render_result.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["final_render_input_checklist_status"] == "ready"
    by_id = {i["id"]: i for i in r["final_render_input_items"]}
    assert by_id["render_input_bundle"]["status"] == "present"
    assert by_id["motion_timeline_manifest"]["status"] == "present"
    assert by_id["production_pack"]["status"] == "present"
    assert by_id["local_preview_render_result"]["status"] == "present"


def test_build_final_render_input_checklist_minimal():
    d = build_final_render_input_checklist(
        {"final_render_gate_status": "locked", "latest_run_id": "", "script_json_present": False}
    )
    assert d.get("final_render_input_checklist_version") == "ba31_3_v1"


def test_dashboard_html_checklist_markers():
    html = get_founder_dashboard_html()
    assert "Final Render Input Checklist" in html
    assert "data-ba313-final-render-input-checklist" in html
    assert "fp-final-render-input-items" in html
    assert "fdFpApplyFinalRenderInputChecklist" in html
