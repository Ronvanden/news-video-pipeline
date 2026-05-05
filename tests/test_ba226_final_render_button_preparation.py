"""BA 22.6 — Final Render Button Preparation (Readiness only, no execution)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.founder_dashboard.local_preview_panel import build_local_preview_panel_payload
from app.main import app


def _mk_run(
    tmp_path: Path,
    run_id: str,
    *,
    verdict: str = "PASS",
    quality_status: str = "pass",
    founder_decision: str = "GO_PREVIEW",
    with_preview: bool = True,
    approval_status: str | None = None,
    cost_status: str | None = None,
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
    if cost_status:
        snap["production_costs"] = {"estimated_total_cost": 1.0, "over_budget_flag": cost_status == "OVER_BUDGET"}
    (d / "local_preview_result.json").write_text(json.dumps(snap), encoding="utf-8")
    if approval_status:
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


def test_final_render_unknown_without_contract():
    p = build_local_preview_panel_payload(out_root=Path("this/does/not/exist"), runs_limit=1)
    g = p["latest_final_render_gate"]
    assert g["status"] == "unknown"
    assert g["button_enabled"] is False


def test_final_render_blocked_when_preview_missing(tmp_path: Path):
    _mk_run(tmp_path, "r1", with_preview=False, approval_status="approved")
    p = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=5)
    g = p["runs"][0]["final_render_gate"]
    assert g["status"] == "blocked"
    assert g["button_enabled"] is False


def test_final_render_blocked_on_fail_states(tmp_path: Path):
    _mk_run(tmp_path, "r2", verdict="FAIL", approval_status="approved")
    p = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=5)
    assert p["runs"][0]["final_render_gate"]["status"] == "blocked"


def test_final_render_locked_when_not_approved(tmp_path: Path):
    _mk_run(tmp_path, "r3", approval_status="not_approved", cost_status="OK")
    p = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=5)
    g = p["runs"][0]["final_render_gate"]
    assert g["status"] == "locked"
    assert g["button_enabled"] is False


def test_final_render_locked_when_over_budget(tmp_path: Path):
    _mk_run(tmp_path, "r4", approval_status="approved", cost_status="OVER_BUDGET")
    p = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=5)
    g = p["runs"][0]["final_render_gate"]
    assert g["status"] == "locked"
    assert g["button_enabled"] is False


def test_final_render_ready_when_all_requirements_pass(tmp_path: Path):
    _mk_run(tmp_path, "r5", approval_status="approved", cost_status="OK", verdict="PASS", quality_status="pass", founder_decision="GO_PREVIEW")
    p = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=5)
    g = p["runs"][0]["final_render_gate"]
    assert g["status"] == "ready"
    assert g["button_enabled"] is True


def test_dashboard_html_contains_final_render_placeholder_text():
    client = TestClient(app)
    t = client.get("/founder/dashboard").text
    assert "Final Render (BA 22.6)" in t
    assert "Finales Video erstellen" in t
    assert "Final Render ist vorbereitet. Die Ausführung folgt in einer späteren BA." in t

