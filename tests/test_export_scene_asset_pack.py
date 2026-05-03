"""BA 18.2 — export_scene_asset_pack.py lokaler Export."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "export_scene_asset_pack.py"


@pytest.fixture(scope="module")
def export_pack_mod():
    spec = importlib.util.spec_from_file_location("export_scene_asset_pack", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_write_scene_asset_pack_creates_files_and_json_shape(export_pack_mod, tmp_path):
    plan = build_production_prompt_plan(
        PromptPlanRequest(topic="Polizei und Mord", title="", source_summary="")
    )
    dest = tmp_path / "scene_asset_pack_test_run"
    meta = export_pack_mod.write_scene_asset_pack(plan, dest, source_label="test:unit")
    assert dest.is_dir()
    for name in meta["files"]:
        assert (dest / name).is_file(), name
    data = json.loads((dest / "scene_asset_pack.json").read_text(encoding="utf-8"))
    assert data["export_version"] == "18.2-v1"
    assert "scene_expansion" in data
    assert data["scene_expansion"]["layer_version"] == "18.0-v1"
    assert len(data["scene_expansion"]["expanded_scene_assets"]) >= 1
    leo = (dest / "leonardo_prompts.txt").read_text(encoding="utf-8").strip().splitlines()
    assert len(leo) >= 1
    assert all(len(ln) <= 600 for ln in leo)
    summary = (dest / "founder_summary.txt").read_text(encoding="utf-8")
    assert "Total chapters:" in summary
    assert "Total beats:" in summary
    assert "Recommended production mode:" in summary
    assert "Viral hook" in summary
    assert "Template type:" in summary


def test_ensure_scene_expansion_fills_when_missing(export_pack_mod):
    plan = build_production_prompt_plan(
        PromptPlanRequest(topic="Polizei und Mord", title="", source_summary="")
    )
    stripped = plan.model_copy(update={"scene_expansion_result": None})
    fixed = export_pack_mod.ensure_scene_expansion_on_plan(stripped)
    assert fixed.scene_expansion_result is not None


def test_clean_leonardo_prompt_strips_establishing_prefix(export_pack_mod):
    raw = "Establishing:   Something important here — wide readable composition."
    out = export_pack_mod.clean_leonardo_prompt_line(raw, "slow push-in")
    assert not out.lower().startswith("establishing:")
    assert "Something important" in out
    assert "Camera:" in out or "slow push-in" in out
