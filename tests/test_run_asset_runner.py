"""BA 19.0 — run_asset_runner.py Placeholder + Manifest."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_asset_runner.py"


@pytest.fixture(scope="module")
def asset_runner_mod():
    spec = importlib.util.spec_from_file_location("run_asset_runner", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _minimal_pack(tmp_path: Path) -> Path:
    pack = {
        "export_version": "18.2-v1",
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": "Establishing wide shot of the city skyline at dusk.",
                    "camera_motion_hint": "slow push-in",
                    "duration_seconds": 10,
                    "asset_type": "establishing",
                    "continuity_note": "",
                    "safety_notes": [],
                },
                {
                    "chapter_index": 0,
                    "beat_index": 1,
                    "visual_prompt": "Detail: documents on a desk.",
                    "camera_motion_hint": "static",
                    "duration_seconds": 8,
                    "asset_type": "detail",
                    "continuity_note": "match prior",
                    "safety_notes": [],
                },
            ],
        },
    }
    p = tmp_path / "scene_asset_pack.json"
    p.write_text(json.dumps(pack), encoding="utf-8")
    return p


def test_placeholder_creates_pngs_and_manifest(asset_runner_mod, tmp_path):
    pack = _minimal_pack(tmp_path)
    out_root = tmp_path / "out"
    meta = asset_runner_mod.run_local_asset_runner(
        pack,
        out_root,
        run_id="testrun19",
        mode="placeholder",
    )
    assert meta["ok"] is True
    assert meta["asset_count"] == 2
    out_dir = Path(meta["output_dir"])
    assert (out_dir / "scene_001.png").is_file()
    assert (out_dir / "scene_002.png").is_file()
    man = json.loads((out_dir / "asset_manifest.json").read_text(encoding="utf-8"))
    assert man["run_id"] == "testrun19"
    assert man["asset_count"] == 2
    assert man["generation_mode"] == "placeholder"
    assert len(man["assets"]) == 2
    assert man["assets"][0]["scene_number"] == 1
    assert man["assets"][0]["image_path"] == "scene_001.png"
    assert "visual_prompt" in man["assets"][0]
    assert man["assets"][0]["generation_mode"] == "placeholder"


def test_missing_pack_raises_cleanly_via_runner(asset_runner_mod, tmp_path):
    with pytest.raises(FileNotFoundError):
        asset_runner_mod.run_local_asset_runner(
            tmp_path / "nope.json",
            tmp_path / "out",
            run_id="x",
            mode="placeholder",
        )


def test_empty_beats_raises(asset_runner_mod, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"scene_expansion": {"expanded_scene_assets": []}}), encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        asset_runner_mod.run_local_asset_runner(bad, tmp_path / "out", run_id="y", mode="placeholder")


def test_live_without_key_skips_images(asset_runner_mod, tmp_path, monkeypatch):
    monkeypatch.delenv("LEONARDO_API_KEY", raising=False)
    pack = _minimal_pack(tmp_path)
    meta = asset_runner_mod.run_local_asset_runner(
        pack,
        tmp_path / "out",
        run_id="liveskip",
        mode="live",
    )
    assert meta["ok"] is False
    assert meta["asset_count"] == 0
    out_dir = Path(meta["output_dir"])
    man = json.loads((out_dir / "asset_manifest.json").read_text(encoding="utf-8"))
    assert man["generation_mode"] == "live_skipped"
    assert man["asset_count"] == 0
    assert not (out_dir / "scene_001.png").exists()
