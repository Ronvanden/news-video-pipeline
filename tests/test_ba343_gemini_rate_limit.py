"""BA 32.43 — Gemini 429/5xx Diagnose + Retry/Backoff (kein Live-HTTP)."""

from __future__ import annotations

import importlib.util
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_MOD = _ROOT / "app" / "production_connectors" / "gemini_image_connector.py"


@pytest.fixture(scope="module")
def gem_mod():
    spec = importlib.util.spec_from_file_location("gemini_image_connector_ba343", _MOD)
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


def test_429_retries_then_success(gem_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "present")
    dest = tmp_path / "o.png"
    ok_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": "iVBORw0KGgo=",  # minimal PNG header base64
                            }
                        }
                    ]
                }
            }
        ]
    }
    with patch.object(gem_mod.time, "sleep"):
        with patch.object(gem_mod, "urlopen", side_effect=[_http_err(429), _Resp200(ok_payload)]) as uo:
            ok, warns, meta = gem_mod.run_gemini_image_live_to_png("p", dest)
    assert ok is True
    assert uo.call_count == 2
    blob = " ".join(warns)
    assert "gemini_image_http_429" in blob
    assert "gemini_image_retry_1_after:gemini_image_http_429" in blob
    assert meta.get("bytes_written", 0) > 0


def test_401_no_retry(gem_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "present")
    dest = tmp_path / "o.png"
    with patch.object(gem_mod.time, "sleep"):
        with patch.object(gem_mod, "urlopen", side_effect=[_http_err(401), _http_err(401), _http_err(401)]) as uo:
            ok, warns, _ = gem_mod.run_gemini_image_live_to_png("p", dest)
    assert ok is False
    assert uo.call_count == 1
    blob = " ".join(warns)
    assert "gemini_image_http_401" in blob
    assert "gemini_image_retry_1_after" not in blob


def test_5xx_retries_then_exhausts(gem_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "present")
    dest = tmp_path / "o.png"
    with patch.object(gem_mod.time, "sleep"):
        with patch.object(gem_mod, "urlopen", side_effect=[_http_err(503), _http_err(503), _http_err(503)]) as uo:
            ok, warns, _ = gem_mod.run_gemini_image_live_to_png("p", dest)
    assert ok is False
    assert uo.call_count == 3
    blob = " ".join(warns)
    assert "gemini_image_http_5xx" in blob
    assert "gemini_image_retry_1_after:gemini_image_http_5xx" in blob
    assert "gemini_image_retry_2_after:gemini_image_http_5xx" in blob

