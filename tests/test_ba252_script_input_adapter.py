from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_ADAPTER_PATH = _ROOT / "app" / "real_video_build" / "script_input_adapter.py"
_ORCH_PATH = _ROOT / "scripts" / "run_real_video_build.py"


@pytest.fixture(scope="module")
def adapter_mod():
    spec = importlib.util.spec_from_file_location("script_input_adapter", _ADAPTER_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def orch_mod():
    spec = importlib.util.spec_from_file_location("run_real_video_build", _ORCH_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _beats(pack: Dict[str, Any]):
    return ((pack.get("scene_expansion") or {}).get("expanded_scene_assets") or [])


def test_generate_script_response_with_chapters_builds_pack(adapter_mod):
    data = {
        "title": "Test",
        "hook": "Hook line.",
        "chapters": [
            {"title": "A", "content": "Alpha."},
            {"title": "B", "content": "Beta."},
            {"title": "C", "content": "Gamma."},
        ],
        "full_script": "",
        "sources": [],
        "warnings": [],
    }
    pack = adapter_mod.build_scene_asset_pack_from_generate_script_response(data, run_id="rid")
    assert pack["export_version"] == "25.2-v1"
    assert pack["run_id"] == "rid"
    beats = _beats(pack)
    assert len(beats) >= 4  # hook + 3 chapters
    assert any((b.get("narration") or "") == "Alpha." for b in beats)
    assert any((b.get("voiceover_text") or "") == "Beta." for b in beats)
    # BA 26.4c: Policy-Felder additiv vorhanden
    b0 = beats[0]
    assert "visual_prompt_raw" in b0
    assert "visual_prompt_effective" in b0
    assert "visual_text_guard_applied" in b0
    assert b0.get("visual_text_guard_applied") is True
    assert "[visual_no_text_guard_v26_4]" in str(b0.get("visual_prompt_effective") or "")
    assert b0.get("visual_policy_status") in ("safe", "text_extracted", "needs_review")


def test_full_script_without_chapters_is_chunked(adapter_mod):
    data = {
        "title": "T",
        "hook": "",
        "chapters": [],
        "full_script": "Satz eins. Satz zwei. Satz drei. Satz vier. Satz fünf. Satz sechs. Satz sieben.",
        "sources": [],
        "warnings": [],
    }
    pack = adapter_mod.build_scene_asset_pack_from_generate_script_response(data, run_id="rid2")
    beats = _beats(pack)
    # 3–8 Szenen/Chunks als Ziel
    assert 3 <= len(beats) <= 8


def test_chapter_dict_keys_are_read(adapter_mod):
    data = {
        "title": "T",
        "hook": "",
        "chapters": [
            {"title": "X", "text": "Text key works."},
            {"title": "Y", "summary": "Summary key works."},
        ],
        "full_script": "",
        "sources": [],
        "warnings": [],
    }
    pack = adapter_mod.build_scene_asset_pack_from_generate_script_response(data)
    beats = _beats(pack)
    narr = "\n".join((b.get("narration") or "") for b in beats)
    assert "Text key works." in narr
    assert "Summary key works." in narr


def test_empty_input_raises_value_error(adapter_mod):
    with pytest.raises(ValueError):
        adapter_mod.build_scene_asset_pack_from_generate_script_response(
            {"title": "", "hook": "", "chapters": [], "full_script": "", "sources": [], "warnings": []}
        )


def test_write_scene_asset_pack_writes_json(adapter_mod, tmp_path: Path):
    pack = adapter_mod.build_scene_asset_pack_from_story_pack({"scenes": ["A", "B", "C"]}, run_id="ridw")
    out = tmp_path / "scene_asset_pack.json"
    p = adapter_mod.write_scene_asset_pack(pack, out)
    assert p.is_file()
    parsed = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(parsed, dict)
    assert parsed["run_id"] == "ridw"


def test_pack_is_compatible_with_orchestrator_narration_preference(adapter_mod, orch_mod):
    pack = adapter_mod.build_scene_asset_pack_from_story_pack(
        {"title": "T", "hook": "H", "scenes": [{"title": "S1", "narration": "Narration wins."}]},
        run_id="ridn",
    )
    text = orch_mod.derive_narration_from_scene_pack(pack)
    assert "Narration wins." in text

