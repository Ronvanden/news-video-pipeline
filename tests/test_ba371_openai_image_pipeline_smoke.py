"""BA 32.71 — Pipeline-Smoke-Helfer & CLI-Gates (keine echten API-Calls)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

from app.production_connectors.openai_image_pipeline_smoke import (
    run_openai_image_pipeline_smoke_v1,
    trim_scene_asset_pack,
    write_builtin_minimal_scene_pack,
)

_ROOT = Path(__file__).resolve().parents[1]


def test_trim_scene_asset_pack_keeps_order_and_cap(tmp_path):
    pack = {
        "scene_expansion": {
            "expanded_scene_assets": [
                {"chapter_index": 0, "beat_index": 2, "visual_prompt": "c"},
                {"chapter_index": 0, "beat_index": 0, "visual_prompt": "a"},
                {"chapter_index": 0, "beat_index": 1, "visual_prompt": "b"},
            ]
        },
    }
    src = tmp_path / "full.json"
    src.write_text(json.dumps(pack), encoding="utf-8")
    dst = tmp_path / "trim.json"
    trim_scene_asset_pack(src, 2, dst)
    data = json.loads(dst.read_text(encoding="utf-8"))
    beats = data["scene_expansion"]["expanded_scene_assets"]
    assert len(beats) == 2
    assert beats[0]["visual_prompt"] == "a"
    assert beats[1]["visual_prompt"] == "b"


def test_write_builtin_minimal_scene_pack_two_beats(tmp_path):
    p = write_builtin_minimal_scene_pack(tmp_path / "b.json", 2)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert len(data["scene_expansion"]["expanded_scene_assets"]) == 2


def test_pipeline_smoke_ok_with_mock_runner(tmp_path):
    rid = "ba371_mock"

    def fake_runner(pack_path: Path, out_root: Path, **kwargs):
        assert kwargs.get("mode") == "live"
        assert kwargs.get("max_assets_live") == 1
        assert kwargs.get("openai_image_model") == "gpt-image-1"
        od = Path(out_root).resolve() / f"generated_assets_{kwargs.get('run_id')}"
        od.mkdir(parents=True, exist_ok=True)
        png = od / "scene_001.png"
        png.write_bytes(b"\x89PNG\r\n\x1a\n")
        man = {
            "run_id": kwargs.get("run_id"),
            "assets": [
                {
                    "generation_mode": "openai_image_live",
                    "image_path": "scene_001.png",
                }
            ],
            "warnings": [],
        }
        mp = od / "asset_manifest.json"
        mp.write_text(json.dumps(man), encoding="utf-8")
        return {
            "ok": True,
            "output_dir": str(od),
            "manifest_path": str(mp),
            "warnings": ["openai_image_model:gpt-image-1", "openai_image_size:1024x1024"],
        }

    pack = write_builtin_minimal_scene_pack(tmp_path / "pack.json", 1)
    body = run_openai_image_pipeline_smoke_v1(
        pack_path=pack,
        out_root=tmp_path / "out",
        run_id=rid,
        max_scenes=1,
        openai_image_model="gpt-image-1",
        openai_image_size="1024x1024",
        openai_image_timeout_seconds=30.0,
        invoke_runner=fake_runner,
    )
    assert body["ok"] is True
    assert body["generated_count"] == 1
    assert body["failed_count"] == 0
    assert body["provider"] == "openai_image"
    assert len(body["asset_paths"]) == 1
    assert body["smoke_version"] == "ba32_71_v1"
    assert "sk-" not in json.dumps(body)


def test_pipeline_smoke_counts_fallback(tmp_path):
    rid = "ba371_fail"

    def fake_runner(_pack, out_root: Path, **kwargs):
        od = Path(out_root).resolve() / f"generated_assets_{kwargs.get('run_id')}"
        od.mkdir(parents=True, exist_ok=True)
        man = {
            "assets": [{"generation_mode": "openai_image_fallback_placeholder", "image_path": "scene_001.png"}],
        }
        mp = od / "asset_manifest.json"
        mp.write_text(json.dumps(man), encoding="utf-8")
        (od / "scene_001.png").write_bytes(b"x")
        return {"ok": True, "output_dir": str(od), "manifest_path": str(mp), "warnings": ["openai_image_http_403"]}

    pack = write_builtin_minimal_scene_pack(tmp_path / "p2.json", 1)
    body = run_openai_image_pipeline_smoke_v1(
        pack_path=pack,
        out_root=tmp_path / "out2",
        run_id=rid,
        max_scenes=1,
        openai_image_model="gpt-image-2",
        openai_image_size="1024x1024",
        openai_image_timeout_seconds=30.0,
        invoke_runner=fake_runner,
    )
    assert body["ok"] is False
    assert body["generated_count"] == 0
    assert body["failed_count"] == 1


def test_pipeline_smoke_max_scenes_clamped(tmp_path):
    """Logic: max_scenes capped at 2 inside run_openai_image_pipeline_smoke_v1."""

    def fake_runner(_pack, out_root: Path, **kwargs):
        od = Path(out_root).resolve() / f"generated_assets_{kwargs.get('run_id')}"
        od.mkdir(parents=True, exist_ok=True)
        mp = od / "asset_manifest.json"
        mp.write_text(json.dumps({"assets": []}), encoding="utf-8")
        return {"ok": True, "output_dir": str(od), "manifest_path": str(mp), "warnings": []}

    body = run_openai_image_pipeline_smoke_v1(
        pack_path=tmp_path / "unused_pack.json",
        out_root=tmp_path / "oroot",
        run_id="x",
        max_scenes=99,
        openai_image_model="m",
        openai_image_size="1024x1024",
        openai_image_timeout_seconds=1.0,
        invoke_runner=fake_runner,
    )
    assert body["max_scenes"] == 2


def test_cli_pipeline_requires_confirm():
    script = _ROOT / "scripts" / "run_openai_image_pipeline_smoke.py"
    spec = importlib.util.spec_from_file_location("run_openai_image_pipeline_smoke_ba371", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with patch.object(sys, "argv", ["run_openai_image_pipeline_smoke.py"]):
        assert mod.main() == 3


def test_cli_pipeline_rejects_max_scenes_over_2():
    script = _ROOT / "scripts" / "run_openai_image_pipeline_smoke.py"
    spec = importlib.util.spec_from_file_location("run_oai_pl_smoke_ba371b", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with patch.object(
        sys,
        "argv",
        [
            "run_openai_image_pipeline_smoke.py",
            "--confirm-live-openai-image",
            "--max-scenes",
            "5",
        ],
    ):
        assert mod.main() == 3
