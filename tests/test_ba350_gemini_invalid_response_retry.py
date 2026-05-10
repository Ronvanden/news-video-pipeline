"""BA 32.50 — Gemini invalid image response: classify + one retry per scene (no live HTTP)."""

from __future__ import annotations

import importlib.util
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_CONNECTOR = _ROOT / "app" / "production_connectors" / "gemini_image_connector.py"
_RUNNER = _ROOT / "scripts" / "run_asset_runner.py"


@pytest.fixture(scope="module")
def gem_mod():
    spec = importlib.util.spec_from_file_location("gemini_image_connector_ba350", _CONNECTOR)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def ar_mod():
    spec = importlib.util.spec_from_file_location("run_asset_runner_ba350", _RUNNER)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class _Resp200:
    __test__ = False

    def __init__(self, payload: dict):
        self._raw = json.dumps(payload).encode("utf-8")
        self.status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False

    def read(self):
        return self._raw

    def getcode(self):
        return 200


def _http_err(code: int) -> HTTPError:
    return HTTPError(
        "https://generativelanguage.googleapis.com/v1beta/models/x:generateContent",
        code,
        "err",
        {"Content-Type": "application/json"},
        BytesIO(b"{}"),
    )


def _ok_image_payload() -> dict:
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": "iVBORw0KGgo=",
                            }
                        }
                    ]
                }
            }
        ]
    }


def _invalid_text_only_payload() -> dict:
    return {"candidates": [{"content": {"parts": [{"text": "no image here"}]}}]}


def test_rest_invalid_then_success_retry_and_meta(gem_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "present")
    monkeypatch.setenv("GEMINI_IMAGE_TRANSPORT", "rest")
    dest = tmp_path / "o.png"
    with patch.object(gem_mod.time, "sleep"):
        with patch.object(
            gem_mod,
            "urlopen",
            side_effect=[_Resp200(_invalid_text_only_payload()), _Resp200(_ok_image_payload())],
        ) as uo:
            ok, warns, meta = gem_mod.run_gemini_image_live_to_png("prompt", dest)
    assert ok is True
    assert uo.call_count == 2
    blob = " ".join(warns)
    assert "gemini_image_response_invalid" in blob
    assert "gemini_image_no_inline_data" in blob
    assert "gemini_image_retry_1_after:gemini_image_response_invalid" in blob
    assert meta.get("gemini_invalid_response_retries_used") == 1
    assert dest.is_file() and dest.stat().st_size > 0


def test_rest_invalid_twice_exhausted(gem_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "present")
    monkeypatch.setenv("GEMINI_IMAGE_TRANSPORT", "rest")
    dest = tmp_path / "o.png"
    bad = _invalid_text_only_payload()
    with patch.object(gem_mod.time, "sleep"):
        with patch.object(gem_mod, "urlopen", side_effect=[_Resp200(bad), _Resp200(bad)]) as uo:
            ok, warns, meta = gem_mod.run_gemini_image_live_to_png("p", dest)
    assert ok is False
    assert uo.call_count == 2
    blob = " ".join(warns)
    assert "gemini_image_generation_failed:invalid_response_exhausted" in blob
    assert meta == {}


def test_rest_401_still_no_retry(gem_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "present")
    monkeypatch.setenv("GEMINI_IMAGE_TRANSPORT", "rest")
    dest = tmp_path / "o.png"
    with patch.object(gem_mod.time, "sleep"):
        with patch.object(gem_mod, "urlopen", side_effect=[_http_err(401), _http_err(401)]) as uo:
            ok, warns, _ = gem_mod.run_gemini_image_live_to_png("p", dest)
    assert ok is False
    assert uo.call_count == 1
    blob = " ".join(warns)
    assert "gemini_image_http_401" in blob
    assert "gemini_image_retry_1_after:gemini_image_response_invalid" not in blob


def _one_beat_pack(tmp_path: Path) -> Path:
    pack = {
        "export_version": "18.2-v1",
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": "Editorial still, clean composition, no readable text.",
                    "visual_prompt_effective": "Editorial still.\n\n[visual_no_text_guard_v26_4]\nNo readable text.",
                    "visual_prompt_raw": "Editorial still.",
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


def test_runner_invalid_then_success_production_ready(ar_mod, tmp_path, monkeypatch):
    from app.founder_dashboard.ba323_video_generate import build_asset_artifact

    monkeypatch.setenv("IMAGE_PROVIDER", "gemini_image")
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("GEMINI_IMAGE_TRANSPORT", "rest")
    pack = _one_beat_pack(tmp_path)
    with patch(
        "app.production_connectors.gemini_image_connector.urlopen",
        side_effect=[_Resp200(_invalid_text_only_payload()), _Resp200(_ok_image_payload())],
    ):
        with patch("app.production_connectors.gemini_image_connector.time.sleep"):
            meta = ar_mod.run_local_asset_runner(
                pack, tmp_path / "out", run_id="ba350ok", mode="live", max_assets_live=1
            )
    assert meta["ok"] is True
    w = " ".join(str(x) for x in (meta.get("warnings") or []))
    assert "gemini_image_retry_1_after:gemini_image_response_invalid" in w
    out = Path(meta["output_dir"])
    man = json.loads((out / "asset_manifest.json").read_text(encoding="utf-8"))
    assert man["assets"][0]["generation_mode"] == "gemini_image_live"
    aa = build_asset_artifact(asset_manifest_path=str(out / "asset_manifest.json"))
    assert (aa.get("asset_quality_gate") or {}).get("status") == "production_ready"


def test_runner_invalid_twice_mixed_placeholder(ar_mod, tmp_path, monkeypatch):
    from app.founder_dashboard.ba323_video_generate import build_asset_artifact

    monkeypatch.setenv("IMAGE_PROVIDER", "gemini_image")
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("GEMINI_IMAGE_TRANSPORT", "rest")
    pack = _one_beat_pack(tmp_path)
    bad = _invalid_text_only_payload()
    with patch(
        "app.production_connectors.gemini_image_connector.urlopen",
        side_effect=[_Resp200(bad), _Resp200(bad)],
    ):
        with patch("app.production_connectors.gemini_image_connector.time.sleep"):
            meta = ar_mod.run_local_asset_runner(
                pack, tmp_path / "out", run_id="ba350bad", mode="live", max_assets_live=1
            )
    assert meta["ok"] is True
    w = " ".join(str(x) for x in (meta.get("warnings") or []))
    assert "gemini_image_generation_failed:invalid_response_exhausted" in w
    out = Path(meta["output_dir"])
    man = json.loads((out / "asset_manifest.json").read_text(encoding="utf-8"))
    assert man["assets"][0]["generation_mode"] == "gemini_image_fallback_placeholder"
    aa = build_asset_artifact(asset_manifest_path=str(out / "asset_manifest.json"))
    assert (aa.get("asset_quality_gate") or {}).get("status") != "production_ready"
