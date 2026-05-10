"""BA 32.41 — Gemini / Nano Banana Image Spike (IMAGE_PROVIDER=gemini_image), keine echten Calls.

BA 32.50 — Invalid-Response + ein Retry pro Szene: siehe ``test_ba350_gemini_invalid_response_retry.py``.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.founder_dashboard.ba323_video_generate import build_asset_artifact

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_asset_runner.py"


@pytest.fixture(scope="module")
def ar_mod():
    spec = importlib.util.spec_from_file_location("run_asset_runner_ba341", _SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _one_beat_pack(tmp_path: Path) -> Path:
    pack = {
        "export_version": "18.2-v1",
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": "Editorial still, clean composition, no readable text.",
                    "visual_prompt_effective": "Editorial still, clean composition, no readable text.\n\n[visual_no_text_guard_v26_4]\nNo readable text.",
                    "visual_prompt_raw": "Editorial still, clean composition, no readable text.",
                    "camera_motion_hint": "static",
                    "duration_seconds": 8,
                    "asset_type": "establishing",
                    "overlay_intent": [],
                    "text_sensitive": False,
                    "visual_asset_kind": "cinematic_broll",
                    "routed_visual_provider": "leonardo",
                    "continuity_note": "",
                    "safety_notes": [],
                }
            ]
        },
    }
    p = tmp_path / "pack.json"
    p.write_text(json.dumps(pack), encoding="utf-8")
    return p


@pytest.fixture(autouse=True)
def _unset_image_provider(monkeypatch):
    monkeypatch.delenv("IMAGE_PROVIDER", raising=False)


def test_gemini_invalid_image_response_type_for_ba350():
    from app.production_connectors.gemini_image_connector import GeminiInvalidImageResponse

    assert issubclass(GeminiInvalidImageResponse, Exception)


def test_gemini_image_live_success_manifest_and_gate(ar_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "gemini_image")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-placeholder")

    def _stub(vp, dest, **_kw):
        dest.write_bytes(b"\x89PNG\r\n\x1a\n")
        return (
            True,
            ["gemini_image_model:test-model", "gemini_image_provider:gemini_image"],
            {"ok": True, "model": "test-model", "bytes_written": 8},
        )

    pack = _one_beat_pack(tmp_path)
    with patch.object(ar_mod, "run_gemini_image_live_to_png", side_effect=_stub):
        meta = ar_mod.run_local_asset_runner(
            pack, tmp_path / "out", run_id="ba341ok", mode="live", max_assets_live=1
        )
    out = Path(meta["output_dir"])
    man = json.loads((out / "asset_manifest.json").read_text(encoding="utf-8"))
    assert meta["ok"] is True
    assert man["generation_mode"] == "gemini_image_live"
    a0 = man["assets"][0]
    assert a0["generation_mode"] == "gemini_image_live"
    assert a0.get("provider_used") == "gemini_image"
    assert (out / "scene_001.png").is_file()
    aa = build_asset_artifact(asset_manifest_path=str(out / "asset_manifest.json"))
    assert int((aa.get("generation_modes") or {}).get("gemini_image_live", 0)) >= 1
    assert aa.get("real_asset_file_count") == 1
    assert aa.get("placeholder_asset_count") == 0
    assert (aa.get("asset_quality_gate") or {}).get("status") == "production_ready"


def test_gemini_image_missing_key_top_level_manifest(ar_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "gemini_image")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    pack = _one_beat_pack(tmp_path)
    meta = ar_mod.run_local_asset_runner(pack, tmp_path / "out", run_id="ba341_miss", mode="live", max_assets_live=1)
    assert "gemini_image_key_missing_fallback_placeholder" in meta["warnings"]
    out = Path(meta["output_dir"])
    man = json.loads((out / "asset_manifest.json").read_text(encoding="utf-8"))
    assert man["generation_mode"] == "gemini_image_fallback_placeholder"
    aa = build_asset_artifact(asset_manifest_path=str(out / "asset_manifest.json"))
    codes = [str(c) for c in (aa.get("asset_provider_warning_codes") or [])]
    assert any("gemini_image_key_missing_fallback_placeholder" in c for c in codes)


def test_gemini_image_generation_failure_row(ar_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "gemini_image")
    monkeypatch.setenv("GEMINI_API_KEY", "present")

    def _stub_fail(_vp, dest, **_kw):
        dest.write_bytes(b"junk")
        return (False, ["gemini_image_generation_failed:http_500"], {})

    pack = _one_beat_pack(tmp_path)
    with patch.object(ar_mod, "run_gemini_image_live_to_png", side_effect=_stub_fail):
        meta = ar_mod.run_local_asset_runner(pack, tmp_path / "out", run_id="ba341_bad", mode="live", max_assets_live=1)
    assert any("gemini_image_generation_failed" in str(w) for w in (meta.get("warnings") or []))
    out = Path(meta["output_dir"])
    man = json.loads((out / "asset_manifest.json").read_text(encoding="utf-8"))
    assert man["assets"][0]["generation_mode"] == "gemini_image_fallback_placeholder"

