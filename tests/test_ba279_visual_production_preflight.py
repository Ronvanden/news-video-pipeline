"""BA 27.9 — Visual production preflight tests."""

from __future__ import annotations

from app.visual_plan.visual_production_preflight import build_visual_production_preflight_result


def test_ready_when_approved_and_ready_for_render_and_no_warnings():
    man = {
        "assets": [{}],
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
        "visual_cost_summary": {},
        "reference_provider_payload_summary": {},
        "continuity_wiring_summary": {},
    }
    ps = {"ready_for_render": True, "approval_status": "approved", "asset_manifest_reference_index_path": "x.json"}
    r = build_visual_production_preflight_result(asset_manifest=man, production_summary=ps)
    assert r["preflight_status"] in ("ready", "needs_review")
    assert r["ok"] is True


def test_blocked_when_approval_gate_missing():
    man = {"assets": [{}]}
    r = build_visual_production_preflight_result(asset_manifest=man, production_summary={"ready_for_render": False})
    assert r["preflight_status"] == "blocked"

