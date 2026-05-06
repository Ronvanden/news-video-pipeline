"""BA 26.9c — Production Asset Approval Gate tests (asset_manifest-based)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from app.visual_plan.asset_approval_gate import evaluate_production_asset_approval


def _asset(
    *,
    scene_number: int,
    provider_used: str = "leonardo",
    image_path: str = "scene.png",
    visual_text_guard_applied: bool = True,
    visual_policy_status: str = "safe",
    text_sensitive: bool = False,
    overlay_intent=None,
    asset_decision_status: str = "pending",
    locked_for_render: bool = False,
    visual_asset_kind: str = "cinematic_broll",
    generation_mode: str = "placeholder",
    visual_cost_warning: str = "",
):
    if overlay_intent is None:
        overlay_intent = []
    return {
        "scene_number": scene_number,
        "provider_used": provider_used,
        "image_path": image_path,
        "generated_image_path": image_path,
        "visual_text_guard_applied": visual_text_guard_applied,
        "visual_policy_status": visual_policy_status,
        "text_sensitive": text_sensitive,
        "overlay_intent": overlay_intent,
        "asset_decision_status": asset_decision_status,
        "locked_for_render": locked_for_render,
        "visual_asset_kind": visual_asset_kind,
        "generation_mode": generation_mode,
        "visual_cost_warning": visual_cost_warning,
    }


def test_approved_when_assets_present_and_safe():
    man = {"run_id": "r", "assets": [_asset(scene_number=1), _asset(scene_number=2, provider_used="openai_images")]}
    res = evaluate_production_asset_approval(man)
    assert res["approval_status"] in ("approved", "needs_review")
    assert res["missing_asset_count"] == 0
    assert "scene_1:no_text_guard_missing" not in (res.get("blocking_reasons") or [])


def test_blocked_when_missing_asset_path_for_non_render_provider():
    a = _asset(scene_number=1, provider_used="leonardo", image_path="", visual_text_guard_applied=True)
    man = {"run_id": "r", "assets": [a]}
    res = evaluate_production_asset_approval(man)
    assert res["approval_status"] == "blocked"
    assert any("missing_asset_path" in b for b in (res.get("blocking_reasons") or []))


def test_blocked_when_policy_needs_review():
    a = _asset(scene_number=1, visual_policy_status="needs_review")
    man = {"run_id": "r", "assets": [a]}
    res = evaluate_production_asset_approval(man)
    assert res["approval_status"] == "blocked"
    assert any("visual_policy_needs_review" in b for b in (res.get("blocking_reasons") or []))


def test_blocked_when_guard_missing_for_non_render():
    a = _asset(scene_number=1, visual_text_guard_applied=False)
    man = {"run_id": "r", "assets": [a]}
    res = evaluate_production_asset_approval(man)
    assert res["approval_status"] == "blocked"
    assert any("no_text_guard_missing" in b for b in (res.get("blocking_reasons") or []))


def test_text_sensitive_requires_overlay_intent():
    a = _asset(scene_number=1, text_sensitive=True, overlay_intent=[])
    man = {"run_id": "r", "assets": [a]}
    res = evaluate_production_asset_approval(man)
    assert res["approval_status"] == "blocked"
    assert any("text_sensitive_missing_overlay_intent" in b for b in (res.get("blocking_reasons") or []))


def test_rejected_or_regeneration_blocks():
    a = _asset(scene_number=1, asset_decision_status="rejected")
    b = _asset(scene_number=2, asset_decision_status="needs_regeneration")
    man = {"run_id": "r", "assets": [a, b]}
    res = evaluate_production_asset_approval(man)
    assert res["approval_status"] == "blocked"
    br = res.get("blocking_reasons") or []
    assert any("decision_rejected" in x for x in br)
    assert any("decision_needs_regeneration" in x for x in br)


def test_render_layer_missing_overlay_intent_is_warning_not_blocking():
    a = _asset(scene_number=1, provider_used="render_layer", image_path="", visual_asset_kind="title_card", overlay_intent=[])
    man = {"run_id": "r", "assets": [a]}
    res = evaluate_production_asset_approval(man)
    # render_layer assets don't require image_path; missing overlay is warning
    assert res["approval_status"] in ("approved", "needs_review")
    assert any("overlay_intent_missing_for_render_layer" in w for w in (res.get("warnings") or []))


def test_cli_script_runs(tmp_path: Path):
    # load script as module
    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "run_production_asset_approval_gate.py"
    spec = importlib.util.spec_from_file_location("run_production_asset_approval_gate", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    man = {"run_id": "r", "assets": [_asset(scene_number=1)]}
    inpath = tmp_path / "asset_manifest.json"
    inpath.write_text(json.dumps(man), encoding="utf-8")
    loaded = mod.load_asset_manifest(inpath)
    res = evaluate_production_asset_approval(loaded)
    assert res["assets_checked"] == 1

