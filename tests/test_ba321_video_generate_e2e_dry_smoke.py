"""BA 32.21 / 32.22 — E2E Dry Smoke ohne Provider (Stub: Asset Runner, Timeline, Render, Script-Pipeline).

BA 32.22: Laufzeit — dominiert sonst von ``build_script_response_from_extracted_text`` (LLM/Expander-Kette);
dieser Test ersetzt sie durch einen rein lokalen Stub auf dem geladenen Orchestrator-Modul.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, Tuple
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

_DUMMY_PNG = b"\x89PNG\r\n\x1a\n"


def write_dummy_png(path: Path) -> None:
    path.write_bytes(_DUMMY_PNG)


def stub_build_script_response_from_extracted_text(
    *,
    extracted_text: str,
    source_url: str,
    target_language: str,
    duration_minutes: int,
    extraction_warnings=None,
    extra_warnings=None,
    **kwargs: Any,
) -> Tuple[str, str, list, str, list, list]:
    """Minimal gültiges Skript ohne app.utils-Script-Pipeline (schnell, deterministisch)."""
    del extracted_text, target_language, duration_minutes, kwargs
    w = list(extraction_warnings or [])
    if extra_warnings:
        w.extend(extra_warnings)
    return (
        "BA3222 Dry Smoke Titel",
        "Ein Satz Hook für genau eine Szene im Dry-Smoke-Lauf.",
        [{"title": "K1", "content": "Reserve-Kapitel falls Hook unerwartet leer wäre."}],
        "Reserve full_script für BA3222 Dry Smoke.",
        [source_url],
        w,
    )


def _patched_load_submodule_factory(orig_load: Callable[..., Any]):
    class _FakeAssetMod:
        def run_local_asset_runner(self, *, pack_path: Path, out_root: Path, run_id: str, mode: str, **kwargs):
            del pack_path, mode, kwargs
            out_dir = Path(out_root).resolve() / f"generated_assets_{run_id}"
            out_dir.mkdir(parents=True, exist_ok=True)
            write_dummy_png(out_dir / "scene_001.png")
            man = {
                "run_id": run_id,
                "asset_count": 1,
                "generation_mode": "leonardo_live",
                "warnings": [],
                "assets": [{"image_path": "scene_001.png", "generation_mode": "leonardo_live"}],
            }
            mp = out_dir / "asset_manifest.json"
            mp.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
            return {"ok": True, "output_dir": str(out_dir), "asset_count": 1, "warnings": [], "manifest_path": str(mp)}

    class _FakeTimelineMod:
        def load_asset_manifest(self, manifest_path: Path):
            return {"manifest_path": str(manifest_path)}

        def write_timeline_manifest(self, *_args, asset_manifest_path: Path, out_root: Path, run_id: str, **_kw):
            out_dir = Path(out_root).resolve()
            tfile = out_dir / "timeline_manifest.json"
            tfile.write_text(
                json.dumps({"run_id": run_id, "asset_manifest_path": str(asset_manifest_path)}),
                encoding="utf-8",
            )
            return tfile, "{}"

    class _FakeRenderMod:
        def render_final_story_video(self, _timeline_path: Path, *, output_video: Path, **_kw):
            Path(output_video).write_bytes(b"FAKE_MP4")
            return {"video_created": True, "warnings": [], "blocking_reasons": []}

    def _patched(name: str, path: Path):
        del name
        p = str(path).replace("\\", "/")
        if p.endswith("/scripts/run_asset_runner.py"):
            return _FakeAssetMod()
        if p.endswith("/scripts/build_timeline_manifest.py"):
            return _FakeTimelineMod()
        if p.endswith("/scripts/render_final_story_video.py"):
            return _FakeRenderMod()
        return orig_load(name, path)

    return _patched


def apply_e2e_dry_smoke_patches(real_mod: ModuleType) -> Dict[str, Any]:
    """Mutiert ``run_url_to_final_mp4``-Modul für den Test; Rückgabe für ``restore_e2e_dry_smoke_patches``."""
    originals = {
        "_load_submodule": real_mod._load_submodule,
        "_apply_cinematic_placeholders": real_mod._apply_cinematic_placeholders,
        "extract_text_from_url": real_mod.extract_text_from_url,
        "build_script_response_from_extracted_text": real_mod.build_script_response_from_extracted_text,
    }
    real_mod._load_submodule = _patched_load_submodule_factory(real_mod._load_submodule)  # type: ignore[attr-defined]
    real_mod._apply_cinematic_placeholders = lambda *a, **k: []  # type: ignore[attr-defined]
    real_mod.extract_text_from_url = lambda _url: ("stub extract — kein Netzwerk", [])  # type: ignore[attr-defined]
    real_mod.build_script_response_from_extracted_text = stub_build_script_response_from_extracted_text  # type: ignore[attr-defined]
    return originals


def restore_e2e_dry_smoke_patches(real_mod: ModuleType, originals: Dict[str, Any]) -> None:
    for key, val in originals.items():
        setattr(real_mod, key, val)


def assert_live_asset_quality_gate(tc: unittest.TestCase, data: Dict[str, Any]) -> None:
    tc.assertTrue(data.get("ok"), msg="expected ok true from stub render")
    aa = data.get("asset_artifact") or {}
    tc.assertGreater(int(aa.get("real_asset_file_count") or 0), 0)
    tc.assertEqual(int(aa.get("placeholder_asset_count") or 0), 0)
    tc.assertGreater(int((aa.get("generation_modes") or {}).get("leonardo_live") or 0), 0)
    gate = aa.get("asset_quality_gate") or {}
    tc.assertEqual(gate.get("status"), "production_ready")
    ra = data.get("readiness_audit") or {}
    tc.assertTrue(ra.get("asset_strict_ready"))
    tc.assertEqual(ra.get("asset_quality_status"), "production_ready")
    warns = data.get("warnings") or []
    tc.assertFalse(any("leonardo_env_missing_fallback_placeholder" in str(w) for w in warns))
    report_path = str(data.get("open_me_report_path") or "").strip()
    tc.assertTrue(report_path, msg="open_me_report_path expected")
    rp = Path(report_path)
    tc.assertTrue(rp.is_file(), msg="OPEN_ME report missing")
    txt = rp.read_text(encoding="utf-8")
    tc.assertIn("Asset Artifact", txt)
    tc.assertIn("production_ready", txt)
    tc.assertIn("leonardo_live", txt)


class VideoGenerateE2EDrySmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_video_generate_e2e_live_assets_stub_production_ready_gate(self) -> None:
        import app.founder_dashboard.ba323_video_generate as ba323

        real_mod = ba323._load_run_url_to_final_mod()
        originals = apply_e2e_dry_smoke_patches(real_mod)
        try:
            with tempfile.TemporaryDirectory() as td:
                out_root = Path(td).resolve()
                with patch.dict(os.environ, {"LEONARDO_API_KEY": "present"}, clear=False):
                    with patch("app.routes.founder_dashboard.default_local_preview_out_root", lambda: out_root):
                        r = self.client.post(
                            "/founder/dashboard/video/generate",
                            json={
                                "url": "https://example.com/a",
                                "allow_live_assets": True,
                                "confirm_provider_costs": True,
                                "voice_mode": "none",
                                "motion_mode": "static",
                                "duration_target_seconds": 60,
                                "max_scenes": 1,
                                "max_live_assets": 1,
                                "max_motion_clips": 0,
                                "motion_clip_every_seconds": 600,
                            },
                        )

                self.assertEqual(r.status_code, 200, msg=r.text)
                assert_live_asset_quality_gate(self, r.json())
        finally:
            restore_e2e_dry_smoke_patches(real_mod, originals)


if __name__ == "__main__":
    unittest.main()
