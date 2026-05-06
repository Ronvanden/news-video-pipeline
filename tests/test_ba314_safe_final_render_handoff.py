"""BA 31.4 — Safe Final Render Handoff (Snapshot + Dashboard)."""

from __future__ import annotations

import json
from pathlib import Path

from app.founder_dashboard.html import get_founder_dashboard_html
from app.production_assembly.fresh_preview_snapshot import (
    build_latest_fresh_preview_snapshot,
    build_safe_final_render_handoff,
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


def test_handoff_minimal_build():
    d = build_safe_final_render_handoff(
        {
            "final_render_gate_status": "ready",
            "final_render_input_checklist_status": "ready",
            "latest_run_id": "rid",
            "script_json_present": True,
            "scene_asset_pack_present": True,
            "asset_manifest_present": True,
        }
    )
    assert d["safe_final_render_handoff_version"] == "ba31_4_v1"
    assert d["safe_final_render_handoff_available"] is True
    assert "scripts/run_safe_final_render.py" in d["safe_final_render_cli_command"]
    assert "scripts/run_safe_final_render.py" in d["safe_final_render_cli_command_powershell"]
    assert "--production-summary" in d["safe_final_render_cli_command"]
    assert "--output-dir" in d["safe_final_render_cli_command"]
    assert "production_pack_rid/production_summary.json" in d["safe_final_render_cli_command"].replace("\\", "/")
    assert "safe_final_render_rid" in d["safe_final_render_cli_command"].replace("\\", "/")
    assert "allow-live-assets" not in d["safe_final_render_cli_command"].lower()
    assert "--execute" not in d["safe_final_render_cli_command"]
    assert d["safe_final_render_handoff_reasons"] == []


def test_handoff_gate_locked_false():
    d = build_safe_final_render_handoff(
        {
            "final_render_gate_status": "locked",
            "final_render_input_checklist_status": "pending",
            "latest_run_id": "x",
            "script_json_present": True,
            "scene_asset_pack_present": True,
            "asset_manifest_present": True,
        }
    )
    assert d["safe_final_render_handoff_available"] is False
    assert not d["safe_final_render_cli_command"]
    assert d["safe_final_render_handoff_reasons"]


def test_handoff_gate_blocked_false():
    d = build_safe_final_render_handoff(
        {
            "final_render_gate_status": "blocked",
            "final_render_input_checklist_status": "blocked",
            "latest_run_id": "",
            "script_json_present": False,
            "scene_asset_pack_present": False,
            "asset_manifest_present": False,
        }
    )
    assert d["safe_final_render_handoff_available"] is False
    assert not d["safe_final_render_cli_command_powershell"]


def test_handoff_checklist_pending_false():
    d = build_safe_final_render_handoff(
        {
            "final_render_gate_status": "ready",
            "final_render_input_checklist_status": "pending",
            "latest_run_id": "ok1",
            "script_json_present": True,
            "scene_asset_pack_present": True,
            "asset_manifest_present": True,
        }
    )
    assert d["safe_final_render_handoff_available"] is False


def test_snapshot_handoff_ready_checklist_ready(tmp_path: Path, monkeypatch):
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
    assert r["final_render_gate_status"] == "ready"
    assert r["final_render_input_checklist_status"] == "ready"
    assert r["safe_final_render_handoff_available"] is True
    assert "run_safe_final_render.py" in r["safe_final_render_cli_command"]


def test_snapshot_handoff_ready_checklist_warning_no_bundle(tmp_path: Path, monkeypatch):
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
    assert r["final_render_input_checklist_status"] == "warning"
    assert r["safe_final_render_handoff_available"] is True


def test_snapshot_handoff_incomplete_core_false(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "empty_run"
    run.mkdir(parents=True)
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["safe_final_render_handoff_available"] is False


def test_dashboard_html_handoff_markers():
    html = get_founder_dashboard_html()
    assert "Safe Final Render Handoff" in html
    assert "data-ba314-safe-final-render-handoff" in html
    assert "fp-safe-final-render-handoff" in html
    assert "fp-safe-final-render-cli" in html
    assert "fp-safe-final-render-copy" in html
    assert "fdFpApplySafeFinalRenderHandoff" in html
