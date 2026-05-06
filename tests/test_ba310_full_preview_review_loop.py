"""BA 31.0 — Operator Review Loop (read-only Empfehlung im Snapshot)."""

from __future__ import annotations

import json
from pathlib import Path

from app.production_assembly.fresh_preview_snapshot import build_latest_fresh_preview_snapshot


def _fp_script():
    return json.dumps({"title": "T", "hook": "H", "chapters": [{"title": "K", "content": "Text."}]})


def _fp_pack():
    return json.dumps({"scene_expansion": {"expanded_scene_assets": [{"visual_prompt": "p", "narration": "n"}]}})


def _fp_manifest_non_placeholder():
    return json.dumps(
        {
            "assets": [
                {"scene_number": 1, "image_path": "scene_001.png", "video_path": "delivered_clip.mp4"},
            ]
        }
    )


def test_review_pending_no_fresh_dir(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: Path(p).resolve(),
    )
    r = build_latest_fresh_preview_snapshot(tmp_path)
    assert r["review_decision"] == "pending"
    assert r["full_preview_available"] is False


def test_review_blocked_missing_script(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "b1"
    gen = run / "generated_assets_b1"
    gen.mkdir(parents=True)
    (run / "scene_asset_pack.json").write_text(_fp_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_fp_manifest_non_placeholder(), encoding="utf-8")
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["readiness_status"] == "blocked"
    assert r["review_decision"] == "blocked"


def test_review_blocked_summary_ok_false(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "badsum"
    gen = run / "generated_assets_badsum"
    work = root / ".preview_smoke_work" / "badsum"
    gen.mkdir(parents=True)
    work.mkdir(parents=True)
    (run / "script.json").write_text(_fp_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_fp_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_fp_manifest_non_placeholder(), encoding="utf-8")
    (work / "OPEN_PREVIEW_SMOKE.md").write_text("# x\n", encoding="utf-8")
    (root / "preview_smoke_auto_summary_badsum.json").write_text(json.dumps({"ok": False}), encoding="utf-8")
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["review_decision"] == "blocked"
    assert r["preview_smoke_summary_ok"] is False


def test_review_pending_manifest_only_before_full_preview(tmp_path: Path, monkeypatch):
    """Nur Dry-Run-Kernartefakte — Full Preview/Summary/Open-Me fehlen → pending (nicht rework)."""
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "w1"
    gen = run / "generated_assets_w1"
    gen.mkdir(parents=True)
    (run / "script.json").write_text(_fp_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_fp_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_fp_manifest_non_placeholder(), encoding="utf-8")
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["readiness_status"] == "warning"
    assert r["review_decision"] == "pending"
    assert r["full_preview_available"] is False


def test_review_rework_summary_ok_but_open_missing(tmp_path: Path, monkeypatch):
    """Summary vorhanden (ok true), OPEN_PREVIEW-Pfad ungültig → warning + rework."""
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "wrk1"
    gen = run / "generated_assets_wrk1"
    gen.mkdir(parents=True)
    bogus_open = (root / "nonexistent" / "OPEN_PREVIEW_SMOKE.md").resolve()
    (run / "script.json").write_text(_fp_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_fp_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_fp_manifest_non_placeholder(), encoding="utf-8")
    (root / "preview_smoke_auto_summary_wrk1.json").write_text(
        json.dumps({"ok": True, "open_preview_smoke_report_path": str(bogus_open)}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "app.production_assembly.fresh_preview_snapshot._resolve_output_root",
        lambda p: root.resolve(),
    )
    r = build_latest_fresh_preview_snapshot(root)
    assert r["readiness_status"] == "warning"
    assert r["review_decision"] == "rework"
    assert "missing_open_preview_smoke_md" in r["readiness_reasons"]


def test_review_approve_ready_full(tmp_path: Path, monkeypatch):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "ok1"
    gen = run / "generated_assets_ok1"
    work = root / ".preview_smoke_work" / "ok1"
    gen.mkdir(parents=True)
    work.mkdir(parents=True)
    (run / "script.json").write_text(_fp_script(), encoding="utf-8")
    (run / "scene_asset_pack.json").write_text(_fp_pack(), encoding="utf-8")
    (gen / "asset_manifest.json").write_text(_fp_manifest_non_placeholder(), encoding="utf-8")
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
    assert r["readiness_status"] == "ready"
    assert r["review_decision"] == "approve"
    assert r["full_preview_available"] is True
    assert r["preview_smoke_summary_ok"] is True
