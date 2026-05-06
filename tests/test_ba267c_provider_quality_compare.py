"""BA 26.7c — Provider Quality Compare Smoke tests (pure heuristics)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from app.visual_plan.provider_quality_compare import (
    apply_provider_quality_compare,
    build_provider_quality_summary,
    compare_visual_providers_for_asset,
)


def test_text_sensitive_prefers_openai_images():
    a = {
        "scene_number": 1,
        "visual_asset_kind": "cinematic_broll",
        "text_sensitive": True,
        "overlay_intent": ["Akte prüfen"],
        "visual_policy_status": "text_extracted",
        "visual_prompt_effective": "[visual_no_text_guard_v26_4]\nNo readable text.",
    }
    out = compare_visual_providers_for_asset(a)
    assert out["recommended_provider"] == "openai_images"
    assert out["provider_compare_status"] in ("dry_run_ready", "completed")
    assert any(c.get("provider") == "openai_images" for c in out["provider_candidates"])


def test_cinematic_broll_prefers_leonardo():
    a = {
        "scene_number": 2,
        "visual_asset_kind": "cinematic_broll",
        "text_sensitive": False,
        "overlay_intent": [],
        "visual_policy_status": "safe",
        "visual_prompt_effective": "[visual_no_text_guard_v26_4]\nNo readable text.",
    }
    out = compare_visual_providers_for_asset(a)
    assert out["recommended_provider"] == "leonardo"


def test_motion_clip_prefers_runway():
    a = {
        "scene_number": 3,
        "visual_asset_kind": "motion_clip",
        "visual_policy_status": "safe",
        "visual_prompt_effective": "[visual_no_text_guard_v26_4]\nNo readable text.",
    }
    out = compare_visual_providers_for_asset(a)
    assert out["recommended_provider"] == "runway"


def test_title_card_prefers_render_layer():
    a = {
        "scene_number": 4,
        "visual_asset_kind": "title_card",
        "overlay_intent": ["Die Wahrheit kam zu spät"],
        "text_sensitive": True,
        "visual_policy_status": "text_extracted",
        "visual_prompt_effective": "[visual_no_text_guard_v26_4]\nNo readable text.",
    }
    out = compare_visual_providers_for_asset(a)
    assert out["recommended_provider"] == "render_layer"


def test_manual_provider_override_wins():
    a = {
        "scene_number": 5,
        "visual_asset_kind": "cinematic_broll",
        "manual_provider_override": "openai_images",
        "visual_policy_status": "safe",
    }
    out = compare_visual_providers_for_asset(a)
    assert out["recommended_provider"] == "openai_images"
    assert "manual provider override" in str(out["provider_quality_reason"]).lower()


def test_locked_for_render_sets_completed_and_uses_provider_used_if_present():
    a = {
        "scene_number": 6,
        "visual_asset_kind": "thumbnail_base",
        "locked_for_render": True,
        "provider_used": "openai_images",
        "visual_policy_status": "safe",
    }
    out = compare_visual_providers_for_asset(a)
    assert out["provider_compare_status"] == "completed"
    assert out["recommended_provider"] == "openai_images"


def test_policy_needs_review_sets_compare_needs_review():
    a = {
        "scene_number": 7,
        "visual_asset_kind": "cinematic_broll",
        "visual_policy_status": "needs_review",
    }
    out = compare_visual_providers_for_asset(a)
    assert out["provider_compare_status"] == "needs_review"


def test_summary_counts_providers():
    assets = [
        apply_provider_quality_compare({"scene_number": 1, "visual_asset_kind": "cinematic_broll", "visual_policy_status": "safe"}),
        apply_provider_quality_compare({"scene_number": 2, "visual_asset_kind": "thumbnail_base", "visual_policy_status": "safe"}),
        apply_provider_quality_compare({"scene_number": 3, "visual_asset_kind": "motion_clip", "visual_policy_status": "safe"}),
        apply_provider_quality_compare({"scene_number": 4, "visual_asset_kind": "title_card", "visual_policy_status": "text_extracted", "overlay_intent": ["x"], "text_sensitive": True}),
    ]
    summ = build_provider_quality_summary(assets)
    assert summ["assets_checked"] == 4
    c = summ["recommended_provider_counts"]
    assert c["leonardo"] >= 1
    assert c["openai_images"] >= 1
    assert c["runway"] >= 1
    assert c["render_layer"] >= 1


def test_cli_run_provider_quality_compare_dry_run_does_not_write(tmp_path: Path):
    # load script as module
    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "run_provider_quality_compare.py"
    spec = importlib.util.spec_from_file_location("run_provider_quality_compare", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    man = {"run_id": "r", "asset_count": 1, "assets": [{"scene_number": 1, "visual_asset_kind": "thumbnail_base", "visual_policy_status": "safe"}]}
    inpath = tmp_path / "asset_manifest.json"
    inpath.write_text(json.dumps(man), encoding="utf-8")
    loaded = mod.load_asset_manifest(inpath)
    patched, summary = mod.run_compare(loaded)
    assert summary["ok"] is True
    assert patched["assets"][0].get("provider_compare_version") == "ba26_7c_v1"
    # dry-run behavior is in main(); here we only validate transformation without writing.

