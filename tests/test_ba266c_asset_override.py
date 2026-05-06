"""BA 26.6c — Asset override helpers + manifest patch CLI smoke."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from app.visual_plan.asset_override import (
    apply_scene_asset_override,
    ensure_asset_override_defaults,
    mark_scene_asset_accepted,
    mark_scene_asset_locked,
    mark_scene_asset_rejected,
    request_scene_asset_regeneration,
)


def test_defaults_are_additive_and_stable():
    a = {"scene_number": 2, "image_path": "scene_002.png"}
    out = ensure_asset_override_defaults(a)
    assert out["scene_number"] == 2
    assert out["asset_decision_status"] == "pending"
    assert out["manual_override_applied"] is False
    assert out["candidate_asset_paths"] == []
    assert out["replacement_history"] == []
    assert out["locked_for_render"] is False


def test_marking_appends_history_deterministically():
    a = {"scene_number": 1, "image_path": "scene_001.png"}
    a1 = mark_scene_asset_accepted(a, "ok", now_iso="t1")
    a2 = mark_scene_asset_rejected(a1, "bad", now_iso="t2")
    assert a2["asset_decision_status"] == "rejected"
    hist = a2["replacement_history"]
    assert len(hist) == 2
    assert hist[0]["action"] == "mark_accepted"
    assert hist[0]["now_iso"] == "t1"
    assert hist[1]["action"] == "mark_rejected"
    assert hist[1]["now_iso"] == "t2"


def test_apply_override_sets_fields_and_history():
    a = {"scene_number": 3, "image_path": "scene_003.png"}
    out = apply_scene_asset_override(
        a,
        selected_asset_path="assets/scene_003_alt.png",
        manual_provider_override="openai_images",
        manual_prompt_override="new prompt",
        manual_override_reason="operator",
        decision_status="accepted",
        candidate_asset_paths=["a.png", "", "b.png"],
        now_iso="t",
    )
    assert out["manual_override_applied"] is True
    assert out["selected_asset_path"] == "assets/scene_003_alt.png"
    assert out["manual_provider_override"] == "openai_images"
    assert out["manual_prompt_override"] == "new prompt"
    assert out["asset_decision_status"] == "accepted"
    assert out["candidate_asset_paths"] == ["a.png", "b.png"]
    assert len(out["replacement_history"]) == 1
    assert out["replacement_history"][0]["action"] == "apply_override"


def test_locked_for_render_behavior():
    a = {"scene_number": 4, "image_path": "scene_004.png"}
    out = mark_scene_asset_locked(a, "lock", now_iso="t")
    assert out["asset_decision_status"] == "locked"
    assert out["locked_for_render"] is True
    out2 = request_scene_asset_regeneration(out, "regen", now_iso="t2")
    assert out2["asset_decision_status"] == "needs_regeneration"
    assert out2["locked_for_render"] is False


def test_patch_script_updates_manifest(tmp_path: Path):
    # load patch script as module (no subprocess)
    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "patch_asset_manifest_override.py"
    spec = importlib.util.spec_from_file_location("patch_asset_manifest_override", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    manifest = {
        "run_id": "r",
        "asset_count": 1,
        "assets": [
            {"scene_number": 2, "image_path": "scene_002.png", "visual_prompt": "x"},
        ],
    }
    patched = mod.patch_asset_manifest(
        manifest,
        scene_number=2,
        status="accepted",
        selected_asset_path="scene_002_alt.png",
        manual_provider_override="openai_images",
        manual_prompt_override="override",
        reason="approved",
        candidate_asset_paths=["c1.png", "c2.png"],
        now_iso="t",
    )
    a0 = patched["assets"][0]
    assert a0["asset_decision_status"] == "accepted"
    assert a0["selected_asset_path"] == "scene_002_alt.png"
    assert a0["manual_provider_override"] == "openai_images"
    assert a0["manual_prompt_override"] == "override"
    assert a0["candidate_asset_paths"] == ["c1.png", "c2.png"]
    assert len(a0["replacement_history"]) >= 1

