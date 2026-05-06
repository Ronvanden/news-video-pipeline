"""BA 22.5 — Dashboard Human Approval Gate (approve/revoke + panel payload)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _patch_out_root(monkeypatch, tmp: Path) -> None:
    import app.routes.founder_dashboard as fd

    monkeypatch.setattr(fd, "default_local_preview_out_root", lambda: tmp)


def _mk_run(
    tmp_path: Path,
    run_id: str,
    *,
    verdict: str = "PASS",
    quality_status: str = "pass",
    founder_decision: str = "GO_PREVIEW",
    with_preview: bool = True,
) -> Path:
    d = tmp_path / f"local_preview_{run_id}"
    d.mkdir(parents=True)
    if with_preview:
        (d / "preview_with_subtitles.mp4").write_bytes(b"\0\0")
    snap = {
        "verdict": verdict,
        "quality_checklist": {"status": quality_status},
        "founder_quality_decision": {"decision_code": founder_decision, "top_issue": "", "next_step": ""},
        "warning_classification": {"highest": "INFO", "summary": ""},
    }
    (d / "local_preview_result.json").write_text(json.dumps(snap), encoding="utf-8")
    return d


def test_panel_payload_includes_latest_approval_gate(tmp_path: Path):
    _mk_run(tmp_path, "a1", verdict="PASS", quality_status="pass", founder_decision="GO_PREVIEW", with_preview=True)
    from app.founder_dashboard.local_preview_panel import build_local_preview_panel_payload

    p = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=5)
    assert "latest_approval_gate" in p
    g = p["latest_approval_gate"]
    assert g["status"] in ("not_approved", "approved", "revoked", "blocked")
    assert g["actions"]["approve_enabled"] is True


def test_panel_blocks_when_quality_fail_or_founder_block(tmp_path: Path):
    _mk_run(tmp_path, "b1", verdict="FAIL", quality_status="fail", founder_decision="BLOCK", with_preview=True)
    from app.founder_dashboard.local_preview_panel import build_local_preview_panel_payload

    p = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=5)
    g = p["runs"][0]["approval_gate"]
    assert g["status"] == "blocked"
    assert g["eligible"] is False
    assert g["actions"]["approve_enabled"] is False


def test_panel_requires_preview_file(tmp_path: Path):
    _mk_run(tmp_path, "c1", verdict="PASS", quality_status="pass", founder_decision="GO_PREVIEW", with_preview=False)
    from app.founder_dashboard.local_preview_panel import build_local_preview_panel_payload

    p = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=5)
    g = p["runs"][0]["approval_gate"]
    assert g["eligible"] is False
    assert g["actions"]["approve_enabled"] is False


def test_panel_warning_review_required_still_eligible(tmp_path: Path):
    _mk_run(tmp_path, "d1", verdict="WARNING", quality_status="warning", founder_decision="REVIEW_REQUIRED", with_preview=True)
    from app.founder_dashboard.local_preview_panel import build_local_preview_panel_payload

    p = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=5)
    g = p["runs"][0]["approval_gate"]
    assert g["eligible"] is True
    assert g["actions"]["approve_enabled"] is True


def test_approve_and_revoke_routes_write_human_approval(monkeypatch, tmp_path: Path):
    _patch_out_root(monkeypatch, tmp_path)
    run_dir = _mk_run(tmp_path, "ap1", verdict="PASS", quality_status="pass", founder_decision="GO_PREVIEW", with_preview=True)

    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/approve/ap1", json={"note": "ok"})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert (run_dir / "human_approval.json").is_file()
    doc = json.loads((run_dir / "human_approval.json").read_text(encoding="utf-8"))
    assert doc["status"] == "approved"
    assert doc["approved_by"] == "local_operator"

    r2 = client.post("/founder/dashboard/local-preview/revoke-approval/ap1", json={"note": "revoke"})
    assert r2.status_code == 200
    j2 = r2.json()
    assert j2["ok"] is True
    doc2 = json.loads((run_dir / "human_approval.json").read_text(encoding="utf-8"))
    assert doc2["status"] == "revoked"


def test_approve_invalid_run_id_422():
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/approve/../x", json={})
    assert r.status_code in (404, 422)


def test_approve_missing_run_404(monkeypatch, tmp_path: Path):
    _patch_out_root(monkeypatch, tmp_path)
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/approve/missing", json={})
    assert r.status_code == 404


def test_dashboard_html_contains_human_approval_section():
    client = TestClient(app)
    t = client.get("/founder/dashboard").text
    assert "Human Approval" in t
    assert "Preview freigeben" in t
    assert "Freigabe zurückziehen" in t


def test_approve_ineligible_returns_409(monkeypatch, tmp_path: Path):
    _patch_out_root(monkeypatch, tmp_path)
    _mk_run(tmp_path, "blk1", verdict="FAIL", quality_status="fail", founder_decision="BLOCK", with_preview=True)
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/approve/blk1", json={})
    assert r.status_code == 409
    j = r.json()
    assert j["ok"] is False

