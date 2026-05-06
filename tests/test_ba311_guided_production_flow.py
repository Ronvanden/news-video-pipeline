"""BA 31.1 / 31.1b — Guided Production Flow + Microcopy."""

from __future__ import annotations

import json
from pathlib import Path

from app.founder_dashboard.html import get_founder_dashboard_html
from app.production_assembly.fresh_preview_snapshot import (
    build_guided_production_flow,
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


def test_guided_flow_version_and_steps_no_run(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: Path(p).resolve(),
    )
    r = build_latest_fresh_preview_snapshot(tmp_path)
    assert r.get("guided_flow_version") == "ba31_1b_v1"
    steps = r.get("guided_flow_steps") or []
    assert len(steps) == 6
    ids = [s["id"] for s in steps]
    assert ids == ["input", "dry_run", "snapshot", "full_preview", "review", "final_render"]
    snap = next(s for s in steps if s.get("id") == "snapshot")
    assert "Fresh Preview aktualisieren" in (snap.get("detail") or "")
    assert r["guided_flow_next_step_action"] == "Fresh Preview Dry-Run starten"
    assert r["guided_flow_current_step"] == "input"


def test_guided_dry_run_only_full_preview_pending(tmp_path: Path, monkeypatch):
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
    by_id = {s["id"]: s["status"] for s in (r.get("guided_flow_steps") or [])}
    assert by_id["full_preview"] == "pending"
    assert by_id["review"] == "pending"
    na = r["guided_flow_next_step_action"]
    assert "Der Dry-Run ist vorhanden." in na
    assert "Kopiere unten den Full-Preview-CLI-Befehl" in na
    assert "Fresh Preview aktualisieren" in na
    assert r["guided_flow_current_step"] == "full_preview"


def test_guided_approve_final_render_next(tmp_path: Path, monkeypatch):
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
    by_id = {s["id"]: s["status"] for s in (r.get("guided_flow_steps") or [])}
    assert by_id["review"] == "done"
    assert by_id["final_render"] == "pending"
    assert r["guided_flow_next_step_action"] == "Final Render vorbereiten"
    assert r["guided_flow_current_step"] == "final_render"


def test_guided_blocked_next_action(tmp_path: Path, monkeypatch):
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
    assert r["review_decision"] == "blocked"
    assert r["guided_flow_next_step_action"] == "Blocker beheben, bevor weiter produziert wird"
    by_id = {s["id"]: s["status"] for s in (r.get("guided_flow_steps") or [])}
    assert by_id["final_render"] == "blocked"


def test_build_guided_production_flow_exported_minimal():
    d = build_guided_production_flow({"fresh_preview_available": False})
    assert "guided_flow_steps" in d


def test_dashboard_html_guided_flow_markers():
    html = get_founder_dashboard_html()
    assert "Production Flow" in html
    assert "data-ba311-guided-flow" in html
    assert "fd-guided-production-flow" in html
    assert "fd-guided-flow-steps" in html
    assert "fd-guided-flow-next-action" in html
    assert "Snapshot = aktueller Dashboard-Abgleich" in html
    assert "fd-guided-flow-microcopy-help" in html
    assert "Nach erfolgreichem Lauf: zurück ins Dashboard" in html
    assert "fp-handoff-after-run" in html
