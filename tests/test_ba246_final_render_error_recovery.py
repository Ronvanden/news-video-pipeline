"""BA 24.6 — Final Render Error Recovery / Idempotenz."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from scripts.run_final_render import main as run_final_render_main


def _mk_preview_run(out_root: Path, run_id: str, *, approved: bool = True) -> None:
    d = out_root / f"local_preview_{run_id}"
    d.mkdir(parents=True)
    (d / "preview_with_subtitles.mp4").write_bytes(b"\0\0\0\x20ftypisom")
    snap = {
        "verdict": "PASS",
        "quality_checklist": {"status": "pass"},
        "founder_quality_decision": {"decision_code": "GO_PREVIEW", "top_issue": "", "next_step": ""},
        "production_costs": {"estimated_total_cost": 1.0, "over_budget_flag": False},
    }
    (d / "local_preview_result.json").write_text(json.dumps(snap), encoding="utf-8")
    if approved:
        appr = {
            "schema_version": "local_preview_human_approval_v1",
            "run_id": run_id,
            "status": "approved",
            "approved_at": "2026-01-01T00:00:00+00:00",
            "approved_by": "local_operator",
            "note": "",
            "source": "test",
        }
        (d / "human_approval.json").write_text(json.dumps(appr), encoding="utf-8")


def test_existing_nonempty_no_force_skips_and_updates_reports(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    _mk_preview_run(out_root, "r1", approved=True)
    final_dir = out_root / "final_render_r1"
    final_dir.mkdir()
    (final_dir / "final_video.mp4").write_bytes(b"existing")
    code = run_final_render_main(["--run-id", "r1", "--out-root", str(out_root)])
    assert code == 0
    j = json.loads((final_dir / "final_render_result.json").read_text(encoding="utf-8"))
    assert j["status"] == "skipped_existing"
    assert (final_dir / "FINAL_OPEN_ME.md").is_file()
    assert (final_dir / "final_render_report.md").is_file()


def test_existing_empty_no_force_fails_and_recommends_force(tmp_path: Path, capsys):
    out_root = tmp_path / "output"
    out_root.mkdir()
    _mk_preview_run(out_root, "r2", approved=True)
    final_dir = out_root / "final_render_r2"
    final_dir.mkdir()
    (final_dir / "final_video.mp4").write_bytes(b"")  # 0 bytes
    code = run_final_render_main(["--run-id", "r2", "--out-root", str(out_root), "--print-json"])
    assert code == 1
    out = capsys.readouterr().out
    j = json.loads(out)
    assert j["ok"] is False
    assert j["status"] == "failed"
    assert "--force" in (j.get("recommended_action") or "")


def test_existing_empty_with_force_overwrites(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    _mk_preview_run(out_root, "r3", approved=True)
    final_dir = out_root / "final_render_r3"
    final_dir.mkdir()
    (final_dir / "final_video.mp4").write_bytes(b"")  # 0 bytes
    code = run_final_render_main(["--run-id", "r3", "--out-root", str(out_root), "--force"])
    assert code == 0
    assert (final_dir / "final_video.mp4").stat().st_size > 0


def test_completed_has_required_artifacts(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    _mk_preview_run(out_root, "r4", approved=True)
    code = run_final_render_main(["--run-id", "r4", "--out-root", str(out_root)])
    assert code == 0
    final_dir = out_root / "final_render_r4"
    assert (final_dir / "final_video.mp4").stat().st_size > 0
    assert (final_dir / "final_render_result.json").is_file()
    assert (final_dir / "FINAL_OPEN_ME.md").is_file()
    assert (final_dir / "final_render_report.md").is_file()


def test_copy_failure_returns_structured_failed_json(tmp_path: Path, monkeypatch, capsys):
    import scripts.run_final_render as rfr

    out_root = tmp_path / "output"
    out_root.mkdir()
    _mk_preview_run(out_root, "r5", approved=True)

    def _boom(*args, **kwargs):
        raise OSError("no space left on device")

    monkeypatch.setattr(rfr.shutil, "copy2", _boom)
    code = run_final_render_main(["--run-id", "r5", "--out-root", str(out_root), "--print-json"])
    assert code == 1
    out = capsys.readouterr().out
    j = json.loads(out)
    assert j["ok"] is False
    assert j["status"] == "failed"
    assert "copy" in (j.get("blocking_reasons") or []) or "copy_failed" in (j.get("blocking_reasons") or [])


def test_dashboard_route_propagates_failed_with_recommended_action(tmp_path: Path, monkeypatch):
    import app.routes.founder_dashboard as fd
    import scripts.run_final_render as rfr

    monkeypatch.setattr(fd, "default_local_preview_out_root", lambda: tmp_path)
    _mk_preview_run(tmp_path, "frfail", approved=True)

    def _boom(*args, **kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr(rfr.shutil, "copy2", _boom)
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/final-render/run/frfail", json={"force": True})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is False
    assert j["status"] == "failed"
    assert "recommended_action" in j


def test_locked_readiness_still_does_not_create_final_dir(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    _mk_preview_run(out_root, "lock1", approved=False)  # no approval -> locked
    code = run_final_render_main(["--run-id", "lock1", "--out-root", str(out_root)])
    assert code == 2
    assert not (out_root / "final_render_lock1").exists()

