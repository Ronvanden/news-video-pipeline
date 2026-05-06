"""BA 26.8c — Visual Cost Tracking tests (heuristisch, keine Billing-API)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from app.visual_plan.visual_costs import (
    apply_visual_cost_to_asset,
    build_visual_cost_summary,
    estimate_visual_asset_cost,
    get_default_visual_unit_costs,
)


def test_provider_detection_priority_provider_used_wins():
    a = {
        "provider_used": "openai_images",
        "recommended_provider": "leonardo",
        "manual_provider_override": "runway",
        "routed_visual_provider": "render_layer",
    }
    est = estimate_visual_asset_cost(a, unit_costs={"openai_images": 0.08, "unknown": 0.0})
    assert est["provider"] == "openai_images"
    assert est["estimate_eur"] == 0.08


def test_unknown_provider_warns_but_costs_zero():
    a = {"provider_used": "mystery_provider_x"}
    est = estimate_visual_asset_cost(a, unit_costs={"unknown": 0.0})
    assert est["estimate_eur"] == 0.0
    assert any("unknown" in w for w in est["warnings"])


def test_apply_visual_cost_adds_fields_and_patches_candidates():
    a = {
        "provider_used": "leonardo",
        "provider_candidates": [{"provider": "leonardo", "estimated_cost": 0.0}, {"provider": "runway", "estimated_cost": 0.0}],
    }
    out = apply_visual_cost_to_asset(a, unit_costs={"leonardo": 0.05, "runway": 0.25, "unknown": 0.0})
    assert out["visual_cost_currency"] == "EUR"
    assert out["visual_cost_source"] == "estimate"
    assert out["visual_cost_estimate_eur"] == 0.05
    assert out["visual_cost_version"] == "ba26_8c_v1"
    c = out["provider_candidates"]
    assert c[0]["estimated_cost"] == 0.05
    assert c[1]["estimated_cost"] == 0.25


def test_summary_aggregates_by_provider():
    assets = [
        apply_visual_cost_to_asset({"provider_used": "openai_images"}, unit_costs={"openai_images": 0.1, "unknown": 0.0}),
        apply_visual_cost_to_asset({"provider_used": "render_layer"}, unit_costs={"render_layer": 0.0, "unknown": 0.0}),
    ]
    summ = build_visual_cost_summary(assets, unit_costs={"openai_images": 0.1, "render_layer": 0.0, "unknown": 0.0})
    assert summ["visual_total_estimated_cost_eur"] == 0.1
    br = summ["visual_cost_breakdown_by_provider"]
    assert br["openai_images"] == 0.1


def test_cli_run_visual_cost_tracking_transforms_manifest(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "run_visual_cost_tracking.py"
    spec = importlib.util.spec_from_file_location("run_visual_cost_tracking", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    man = {"run_id": "r", "asset_count": 1, "assets": [{"scene_number": 1, "provider_used": "openai_images"}]}
    inpath = tmp_path / "asset_manifest.json"
    inpath.write_text(json.dumps(man), encoding="utf-8")
    loaded = mod.load_asset_manifest(inpath)
    patched, summary = mod.run_cost_tracking(loaded, unit_costs={"openai_images": 0.2, "unknown": 0.0})
    assert patched["assets"][0]["visual_cost_estimate_eur"] == 0.2
    assert patched["visual_cost_summary"]["visual_total_estimated_cost_eur"] == 0.2

