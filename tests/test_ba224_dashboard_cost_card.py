"""BA 22.4 — Dashboard Cost Card / Production Estimate (defensiv, keine erfundenen Zahlen)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.founder_dashboard.local_preview_panel import build_cost_card_from_saved_result, build_local_preview_panel_payload
from app.main import app


def test_cost_card_unknown_when_missing():
    cc = build_cost_card_from_saved_result(None)
    assert cc["status"] == "UNKNOWN"
    assert cc["mode"] == "unavailable"
    assert cc["estimated_total_eur"] is None
    assert "Noch keine Kostenschätzung" in (cc.get("hint") or "")


def test_cost_card_ok_when_estimated_total_present():
    blob = {
        "production_costs": {
            "estimated_total_cost": 1.23,
            "over_budget_flag": False,
            "step_cost_breakdown": {"voice": 0.3, "image": 0.2, "video": 0.4, "buffer": 0.1},
        }
    }
    cc = build_cost_card_from_saved_result(blob)
    assert cc["status"] in ("OK", "CHECK")  # CHECK optional, aber nie UNKNOWN
    assert cc["mode"] == "estimate"
    assert cc["estimated_total_eur"] == 1.23
    assert cc["breakdown"]["voice_eur"] == 0.3
    assert cc["breakdown"]["buffer_eur"] == 0.1
    assert cc["breakdown"]["assets_eur"] == 0.2 + 0.4


def test_cost_card_over_budget_flag_maps_to_over_budget():
    blob = {"production_costs": {"estimated_total_cost": 2.0, "over_budget_flag": True}}
    cc = build_cost_card_from_saved_result(blob)
    assert cc["status"] == "OVER_BUDGET"


def test_panel_payload_includes_latest_cost_card(tmp_path: Path):
    run_dir = tmp_path / "local_preview_cost1"
    run_dir.mkdir(parents=True)
    snap = {
        "verdict": "PASS",
        "production_costs": {"estimated_total_cost": 1.11, "over_budget_flag": False},
    }
    (run_dir / "local_preview_result.json").write_text(json.dumps(snap), encoding="utf-8")
    p = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=5)
    assert "latest_cost_card" in p
    assert (p["latest_cost_card"] or {}).get("estimated_total_eur") == 1.11
    assert (p["runs"][0].get("cost_card") or {}).get("estimated_total_eur") == 1.11


def test_dashboard_html_contains_cost_card_section():
    client = TestClient(app)
    t = client.get("/founder/dashboard").text
    assert "Kosten-Schätzung" in t
    assert "lp-cost-card" in t

