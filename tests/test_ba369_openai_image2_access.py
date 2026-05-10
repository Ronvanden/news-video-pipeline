"""BA 32.69 — OpenAI Image HTTP-Diagnose & Meta; keine echten Provider-Calls."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from app.production_connectors.openai_image_connector import run_openai_image_live_to_png
from app.production_connectors.openai_images_adapter import generate_openai_image_from_prompt


def test_http_403_warns_and_access_denied(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-used")
    monkeypatch.setenv("OPENAI_IMAGE_MODEL", "gpt-image-2")

    def _boom(*_a, **_kw):
        raise HTTPError("https://api.openai.com/v1/images/generations", 403, "Forbidden", hdrs={}, fp=None)

    outp = tmp_path / "o.png"
    with patch("app.production_connectors.openai_images_adapter.urlopen", side_effect=_boom):
        res = generate_openai_image_from_prompt("clean test prompt", outp, dry_run=False)
    assert res.ok is False
    assert res.error_code == "openai_images_http_403"
    assert "openai_image_http_403" in res.warnings
    assert any(str(w).startswith("openai_image_model_access_denied:") for w in res.warnings)
    assert "openai_image_model_access_denied:gpt-image-2" in res.warnings


def test_http_429_warn(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-used")

    def _boom(*_a, **_kw):
        raise HTTPError("https://api.openai.com/v1/images/generations", 429, "Too Many", hdrs={}, fp=None)

    with patch("app.production_connectors.openai_images_adapter.urlopen", side_effect=_boom):
        res = generate_openai_image_from_prompt("p", tmp_path / "a.png", dry_run=False)
    assert "openai_image_http_429" in res.warnings
    assert res.error_code == "openai_images_http_429"


def test_http_502_maps_to_5xx(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-used")

    def _boom(*_a, **_kw):
        raise HTTPError("https://api.openai.com/v1/images/generations", 502, "Bad GW", hdrs={}, fp=None)

    with patch("app.production_connectors.openai_images_adapter.urlopen", side_effect=_boom):
        res = generate_openai_image_from_prompt("p", tmp_path / "b.png", dry_run=False)
    assert "openai_image_http_5xx" in res.warnings
    assert res.error_code == "openai_images_http_5xx"


def test_connector_403_generation_failed_and_no_secret_echo(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-ultra-secret-value-do-not-leak")

    def _boom(*_a, **_kw):
        raise HTTPError("https://api.openai.com/v1/images/generations", 403, "Forbidden", hdrs={}, fp=None)

    with patch("app.production_connectors.openai_images_adapter.urlopen", side_effect=_boom):
        ok, warns, meta = run_openai_image_live_to_png("prompt text", tmp_path / "out.png")
    assert ok is False
    blob = " ".join(str(w) for w in warns)
    assert "openai_image_http_403" in blob
    assert any("openai_image_generation_failed:" in str(w) for w in warns)
    assert "sk-ultra-secret" not in blob
    assert meta == {}


def test_live_success_mock_transport_and_gate_meta(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-used-in-body")

    tiny = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"x" * 40).decode("ascii")
    payload = json.dumps({"data": [{"b64_json": tiny}]}).encode("utf-8")

    class _Resp:
        status = 200

        def getcode(self):
            return 200

        def read(self):
            return payload

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    outp = tmp_path / "ok.png"
    with patch("app.production_connectors.openai_images_adapter.urlopen", return_value=_Resp()):
        ok, warns, meta = run_openai_image_live_to_png("nice editorial frame", outp)
    assert ok is True
    blob = " ".join(str(w) for w in warns)
    assert "openai_image_transport:images_api" in blob
    assert "openai_image_provider:openai_image" in blob
    assert "openai_image_model:" in blob
    assert "openai_image_size:" in blob
    assert "sk-test-not-used-in-body" not in blob
    assert outp.is_file() and outp.stat().st_size > 0
    assert meta.get("ok") is True
    assert meta.get("dry_run") is False


def test_missing_key_placeholder_warning(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("app.config.settings.openai_api_key", "", raising=False)
    ok, warns, _meta = run_openai_image_live_to_png("x", tmp_path / "m.png")
    assert ok is False
    assert "openai_image_key_missing_fallback_placeholder" in warns
    assert "sk-" not in " ".join(warns).lower()
