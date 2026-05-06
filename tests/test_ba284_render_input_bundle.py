"""BA 28.4 — Render input bundle tests."""

from __future__ import annotations

from app.production_assembly.render_input_bundle import build_render_input_bundle


def test_build_bundle_blocked_keeps_ready_false():
    b = build_render_input_bundle(
        run_id="r1",
        ready_for_render=False,
        render_readiness_status="blocked",
        production_summary_path="p.json",
        asset_manifest_path="a.json",
        warnings=["w1"],
        blocking_reasons=["b1"],
    )
    assert b["render_input_bundle_version"] == "ba28_4_v1"
    assert b["ready_for_render"] is False
    assert b["blocking_reasons"] == ["b1"]

