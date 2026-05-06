"""BA 24.2 — Final Render Dry-Run Endpoint (read-only)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _patch_out_root(monkeypatch, tmp: Path) -> None:
    import app.routes.founder_dashboard as fd

    monkeypatch.setattr(fd, "default_local_preview_out_root", lambda: tmp)


def _mk_run(
    tmp_path: Path,
    run_id: str,
    *,
    with_preview: bool = True,
    quality_status: str | None = "pass",
    verdict: str | None = "PASS",
    founder_decision: str | None = "GO_PREVIEW",
    approval_status: str | None = None,
    over_budget: bool | None = None,
) -> Path:
    d = tmp_path / f"local_preview_{run_id}"
    d.mkdir(parents=True)
    if with_preview:
        (d / "preview_with_subtitles.mp4").write_bytes(b"\0\0")
    snap: dict = {}
    if verdict is not None:
        snap["verdict"] = verdict
    if quality_status is not None:
        snap["quality_checklist"] = {"status": quality_status}
    if founder_decision is not None:
        snap["founder_quality_decision"] = {"decision_code": founder_decision, "top_issue": "", "next_step": ""}
    if over_budget is not None:
        snap["production_costs"] = {"estimated_total_cost": 1.0, "over_budget_flag": bool(over_budget)}
    (d / "local_preview_result.json").write_text(json.dumps(snap), encoding="utf-8")
    if approval_status is not None:
        appr = {
            "schema_version": "local_preview_human_approval_v1",
            "run_id": run_id,
            "status": approval_status,
            "approved_at": "2026-01-01T00:00:00+00:00",
            "approved_by": "local_operator",
            "note": "",
            "source": "dashboard",
        }
        (d / "human_approval.json").write_text(json.dumps(appr), encoding="utf-8")
    return d


def test_dry_run_ready(monkeypatch, tmp_path: Path):
    _patch_out_root(monkeypatch, tmp_path)
    _mk_run(tmp_path, "rdy1", approval_status="approved", over_budget=False, quality_status="pass")
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/final-render/dry-run/rdy1")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["status"] == "ready"
    assert j["contract"]["schema_version"] == "final_render_result_v1"


def test_dry_run_locked_when_approval_missing(monkeypatch, tmp_path: Path):
    _patch_out_root(monkeypatch, tmp_path)
    _mk_run(tmp_path, "lck1", approval_status=None, over_budget=False, quality_status="pass")
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/final-render/dry-run/lck1")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["status"] == "locked"


def test_dry_run_blocked_when_quality_fail(monkeypatch, tmp_path: Path):
    _patch_out_root(monkeypatch, tmp_path)
    _mk_run(tmp_path, "blk1", approval_status="approved", over_budget=False, quality_status="fail")
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/final-render/dry-run/blk1")
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "blocked"


def test_dry_run_blocked_when_preview_missing(monkeypatch, tmp_path: Path):
    _patch_out_root(monkeypatch, tmp_path)
    _mk_run(tmp_path, "blk2", with_preview=False, approval_status="approved", quality_status="pass")
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/final-render/dry-run/blk2")
    assert r.status_code == 200
    assert r.json()["status"] == "blocked"


def test_dry_run_locked_when_over_budget(monkeypatch, tmp_path: Path):
    _patch_out_root(monkeypatch, tmp_path)
    _mk_run(tmp_path, "lck2", approval_status="approved", over_budget=True, quality_status="pass")
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/final-render/dry-run/lck2")
    assert r.status_code == 200
    assert r.json()["status"] == "locked"


def test_dry_run_missing_run_returns_404(monkeypatch, tmp_path: Path):
    _patch_out_root(monkeypatch, tmp_path)
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/final-render/dry-run/missing")
    assert r.status_code == 404


def test_dry_run_does_not_write_final_render_dir(monkeypatch, tmp_path: Path):
    _patch_out_root(monkeypatch, tmp_path)
    _mk_run(tmp_path, "rdy2", approval_status="approved", over_budget=False, quality_status="pass")
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/final-render/dry-run/rdy2")
    assert r.status_code == 200
    # should not create output/final_render_<run_id>/ by dry-run
    assert not (tmp_path / "final_render_rdy2").exists()


def test_dashboard_html_contains_dry_run_button_label():
    client = TestClient(app)
    t = client.get("/founder/dashboard").text
    assert "Dry-Run prüfen" in t

