"""BA 31.2 — Final Render Preparation Gate (Snapshot + Dashboard)."""

from __future__ import annotations

import json
from pathlib import Path

from app.founder_dashboard.html import get_founder_dashboard_html
from app.production_assembly.fresh_preview_snapshot import (
    build_final_render_preparation_gate,
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


def test_gate_pending_dry_run_locked(tmp_path: Path, monkeypatch):
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
    assert r["review_decision"] == "pending"
    assert r["final_render_gate_version"] == "ba31_2_v1"
    assert r["final_render_gate_status"] == "locked"
    assert "gesperrt" in r["final_render_next_action"].lower()


def test_gate_approve_ready_ready(tmp_path: Path, monkeypatch):
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
    assert r["final_render_gate_label"] == "Freigegeben"
    assert "Render-Inputs" in r["final_render_next_action"]
    by_id = {s["id"]: s["status"] for s in (r.get("guided_flow_steps") or [])}
    assert by_id["final_render"] == "pending"


def test_gate_rework_needs_rework(tmp_path: Path, monkeypatch):
    """Summary ok, OPEN_PREVIEW-Pfad ungültig → Review rework (wie test_ba310 rework-Pfad)."""
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "rw1"
    gen = run / "generated_assets_rw1"
    gen.mkdir(parents=True)
    bogus_open = (root / "nonexistent" / "OPEN_PREVIEW_SMOKE.md").resolve()
    (run / "script.json").write_text(_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_manifest_ok(), encoding="utf-8")
    (root / "preview_smoke_auto_summary_rw1.json").write_text(
        json.dumps({"ok": True, "open_preview_smoke_report_path": str(bogus_open)}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["review_decision"] == "rework"
    assert r["final_render_gate_status"] == "needs_rework"
    assert r["final_render_gate_label"] == "Nacharbeit"
    assert "Anpassungen" in r["final_render_next_action"]
    by_id = {s["id"]: s["status"] for s in (r.get("guided_flow_steps") or [])}
    assert by_id["final_render"] == "warning"


def test_gate_blocked_summary(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "badsum"
    gen = run / "generated_assets_badsum"
    work = root / ".preview_smoke_work" / "badsum"
    gen.mkdir(parents=True)
    work.mkdir(parents=True)
    (run / "script.json").write_text(_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_manifest_ok(), encoding="utf-8")
    (work / "OPEN_PREVIEW_SMOKE.md").write_text("# x\n", encoding="utf-8")
    (root / "preview_smoke_auto_summary_badsum.json").write_text(json.dumps({"ok": False}), encoding="utf-8")
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["final_render_gate_status"] == "blocked"
    assert "Blocker" in r["final_render_next_action"]


def test_build_final_render_preparation_gate_exported():
    d = build_final_render_preparation_gate({"review_decision": "pending", "readiness_status": "warning"})
    assert d.get("final_render_gate_version") == "ba31_2_v1"
    assert d.get("final_render_gate_status") == "locked"


def test_dashboard_html_final_render_gate_markers():
    html = get_founder_dashboard_html()
    assert "Final Render Preparation" in html
    assert "data-ba312-final-render-gate" in html
    assert "fp-final-render-gate" in html
    assert "fp-final-render-gate-status" in html
    assert "fp-final-render-next-action" in html
    assert "fdFpApplyFinalRenderGate" in html
