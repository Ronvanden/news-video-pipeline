"""BA 28.5 — Final render dry-run contract tests."""

from __future__ import annotations

from app.production_assembly.final_render_contract import build_final_render_dry_run_result


def test_ready_bundle_would_render_true():
    b = {
        "ready_for_render": True,
        "render_readiness_status": "ready",
        "production_summary_path": "p.json",
        "asset_manifest_path": "a.json",
        "motion_timeline_manifest_path": "t.json",
    }
    r = build_final_render_dry_run_result(input_bundle=b, input_bundle_path="bundle.json")
    assert r["would_render"] is True


def test_blocked_bundle_would_render_false():
    b = {"ready_for_render": False, "render_readiness_status": "blocked"}
    r = build_final_render_dry_run_result(input_bundle=b, input_bundle_path="bundle.json")
    assert r["would_render"] is False

