"""BA 20.3 — Voice & Visual Style Calibration presets."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_PRESETS = _ROOT / "app" / "founder_calibration" / "ba203_presets.py"
_RUNNER = _ROOT / "scripts" / "run_asset_runner.py"


@pytest.fixture(scope="module")
def presets_mod():
    spec = importlib.util.spec_from_file_location("ba203_presets", _PRESETS)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def asset_runner_mod():
    spec = importlib.util.spec_from_file_location("run_asset_runner", _RUNNER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_voice_preset_maps_openai_and_elevenlabs(presets_mod, monkeypatch):
    monkeypatch.delenv("OPENAI_TTS_VOICE", raising=False)
    eff, oai, el, w = presets_mod.resolve_voice_preset("documentary_de")
    assert eff == "documentary_de"
    assert oai == "onyx"
    assert el is not None and el.get("stability") == 0.45
    assert not any("unknown" in x for x in w)


def test_voice_preset_unknown_warns(presets_mod):
    eff, oai, el, w = presets_mod.resolve_voice_preset("not_a_real_preset")
    assert eff == "default"
    assert oai is None and el is None
    assert any(x.startswith("voice_preset_unknown_defaulting_none:") for x in w)


def test_openai_env_overrides_preset_voice_with_notice(presets_mod, monkeypatch):
    monkeypatch.setenv("OPENAI_TTS_VOICE", "alloy")
    eff, oai, el, w = presets_mod.resolve_voice_preset("calm_explainer_de")
    assert eff == "calm_explainer_de"
    assert oai == "alloy"
    assert el is not None
    assert any("voice_preset_openai_env_overrides" in x for x in w)


def test_visual_style_prompt_contains_guidance(presets_mod):
    styled, w = presets_mod.apply_visual_style_to_prompt(
        "A minister at a press podium.",
        "documentary_news",
    )
    assert not w
    assert "documentary" in styled.lower() or "news" in styled.lower()
    assert "minister" in styled.lower()


def test_visual_style_unknown_single_warn_in_runner(asset_runner_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("LEONARDO_API_KEY", "fake-key")
    captured: list[str] = []

    def fake_beat(vp: str, dest: Path) -> tuple[bool, list[str]]:
        captured.append(vp)
        dest.write_bytes(b"\x89PNG\r\n\x1a\n")
        return True, []

    pack = {
        "export_version": "18.2-v1",
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": "City hall exterior.",
                    "camera_motion_hint": "static",
                    "duration_seconds": 6,
                    "asset_type": "establishing",
                    "continuity_note": "",
                    "safety_notes": [],
                },
                {
                    "chapter_index": 0,
                    "beat_index": 1,
                    "visual_prompt": "Crowd in square.",
                    "camera_motion_hint": "pan",
                    "duration_seconds": 6,
                    "asset_type": "establishing",
                    "continuity_note": "",
                    "safety_notes": [],
                },
            ],
        },
    }
    p = tmp_path / "pack.json"
    p.write_text(json.dumps(pack), encoding="utf-8")

    meta = asset_runner_mod.run_local_asset_runner(
        p,
        tmp_path / "out",
        run_id="ba203vs",
        mode="live",
        max_assets_live=2,
        visual_style_preset="totally_unknown_style",
        leonardo_beat_fn=fake_beat,
    )
    assert meta["visual_style_preset_effective"] == "default"
    unk = [w for w in meta["warnings"] if w.startswith("visual_style_preset_unknown_defaulting_none:")]
    assert len(unk) == 1
    assert "City hall" in captured[0] and "documentary" not in captured[0].lower()


def test_visual_style_preset_applied_to_leonardo_prompt(asset_runner_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("LEONARDO_API_KEY", "fake-key")
    captured: list[str] = []

    def fake_beat(vp: str, dest: Path) -> tuple[bool, list[str]]:
        captured.append(vp)
        dest.write_bytes(b"\x89PNG\r\n\x1a\n")
        return True, []

    pack = {
        "export_version": "18.2-v1",
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": "EU flag and parliament.",
                    "camera_motion_hint": "static",
                    "duration_seconds": 6,
                    "asset_type": "establishing",
                    "continuity_note": "",
                    "safety_notes": [],
                },
            ],
        },
    }
    p = tmp_path / "pack2.json"
    p.write_text(json.dumps(pack), encoding="utf-8")

    meta = asset_runner_mod.run_local_asset_runner(
        p,
        tmp_path / "out",
        run_id="ba203ok",
        mode="live",
        max_assets_live=1,
        visual_style_preset="cinematic_explainer",
        leonardo_beat_fn=fake_beat,
    )
    assert meta["visual_style_preset_effective"] == "cinematic_explainer"
    assert len(captured) == 1
    assert "cinematic" in captured[0].lower() or "explainer" in captured[0].lower()
    assert "EU flag" in captured[0]
