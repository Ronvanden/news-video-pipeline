"""BA 32.20 — Leonardo Live Boundary Smoke (no real provider calls)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.run_asset_runner import run_local_asset_runner


def _write_min_scene_asset_pack(path: Path) -> None:
    pack = {
        "export_version": "x",
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": "a cinematic test image",
                    "asset_type": "image",
                    "camera_motion_hint": "static",
                    "duration_seconds": 6,
                }
            ]
        },
    }
    path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")


class AssetRunnerLiveBoundaryTests(unittest.TestCase):
    def test_live_mode_with_mocked_leonardo_success_writes_real_file_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_root = Path(td).resolve()
            pack_path = out_root / "scene_asset_pack.json"
            _write_min_scene_asset_pack(pack_path)

            def _ok_fn(_prompt: str, out_png: Path):
                out_png.write_bytes(b"\x89PNG\r\n\x1a\n")  # tiny dummy file
                return True, []

            with patch.dict(os.environ, {"LEONARDO_API_KEY": "present"}, clear=False):
                meta = run_local_asset_runner(
                    pack_path=pack_path,
                    out_root=out_root,
                    run_id="ba320_ok",
                    mode="live",
                    max_assets_live=1,
                    leonardo_beat_fn=_ok_fn,
                )

            self.assertTrue(meta.get("ok"))
            mp = Path(str(meta.get("manifest_path") or "")).resolve()
            self.assertTrue(mp.exists(), msg="asset_manifest.json missing")
            man = json.loads(mp.read_text(encoding="utf-8"))
            self.assertEqual(man.get("generation_mode"), "leonardo_live")
            assets = man.get("assets") or []
            self.assertEqual(len(assets), 1)
            self.assertEqual((assets[0] or {}).get("generation_mode"), "leonardo_live")
            img_name = str((assets[0] or {}).get("image_path") or "")
            self.assertTrue((mp.parent / img_name).is_file(), msg="generated png missing")

    def test_live_mode_missing_key_falls_back_with_warning(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_root = Path(td).resolve()
            pack_path = out_root / "scene_asset_pack.json"
            _write_min_scene_asset_pack(pack_path)

            with patch.dict(os.environ, {"LEONARDO_API_KEY": ""}, clear=False):
                meta = run_local_asset_runner(
                    pack_path=pack_path,
                    out_root=out_root,
                    run_id="ba320_missing_key",
                    mode="live",
                    max_assets_live=1,
                )

            self.assertTrue(meta.get("ok"))
            self.assertIn("leonardo_env_missing_fallback_placeholder", meta.get("warnings") or [])

    def test_live_mode_provider_failure_marks_fallback_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out_root = Path(td).resolve()
            pack_path = out_root / "scene_asset_pack.json"
            _write_min_scene_asset_pack(pack_path)

            def _fail_fn(_prompt: str, _out_png: Path):
                return False, ["leonardo_stub_failure"]

            with patch.dict(os.environ, {"LEONARDO_API_KEY": "present"}, clear=False):
                meta = run_local_asset_runner(
                    pack_path=pack_path,
                    out_root=out_root,
                    run_id="ba320_fail",
                    mode="live",
                    max_assets_live=1,
                    leonardo_beat_fn=_fail_fn,
                )

            self.assertTrue(meta.get("ok"))
            warnings = meta.get("warnings") or []
            self.assertIn("leonardo_stub_failure", warnings)
            self.assertTrue(any(str(w).startswith("leonardo_live_beat_failed_fallback_placeholder:") for w in warnings))


if __name__ == "__main__":
    unittest.main()

