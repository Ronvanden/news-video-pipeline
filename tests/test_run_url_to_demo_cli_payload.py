"""BA 18.1 — run_url_to_demo CLI JSON inkl. Scene-Expansion-Sicht."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_url_to_demo.py"


@pytest.fixture(scope="module")
def run_url_to_demo_mod():
    spec = importlib.util.spec_from_file_location("run_url_to_demo_cli", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_build_url_to_demo_payload_includes_scene_expansion_fields(run_url_to_demo_mod):
    plan = build_production_prompt_plan(
        PromptPlanRequest(topic="Polizei und Mord", title="", source_summary="")
    )
    assert plan.scene_expansion_result is not None
    p = run_url_to_demo_mod.build_url_to_demo_payload(
        plan,
        input_url="https://example.com/article",
        local_run_id="test-run-id",
    )
    assert p["local_run_id"] == "test-run-id"
    assert p["input_url"] == "https://example.com/article"
    assert "rewritten_story" in p
    assert p["scene_expansion_asset_count"] == len(plan.scene_expansion_result.expanded_scene_assets)
    assert p["beats_per_chapter_default"] == plan.scene_expansion_result.beats_per_chapter_default
    prev = p["first_visual_beats_preview"]
    assert isinstance(prev, list)
    assert len(prev) <= 3
    assert len(prev) >= 1
    for item in prev:
        assert set(item.keys()) == {
            "chapter_index",
            "beat_index",
            "asset_type",
            "visual_prompt",
            "camera_motion_hint",
        }


def test_scene_expansion_graceful_when_result_missing(run_url_to_demo_mod):
    plan = build_production_prompt_plan(
        PromptPlanRequest(topic="Polizei und Mord", title="", source_summary="")
    )
    plan2 = plan.model_copy(update={"scene_expansion_result": None})
    p = run_url_to_demo_mod.build_url_to_demo_payload(
        plan2,
        input_url="https://example.com/x",
        local_run_id="id2",
    )
    assert p["scene_expansion_asset_count"] == 0
    assert p["beats_per_chapter_default"] == 0
    assert p["first_visual_beats_preview"] == []
