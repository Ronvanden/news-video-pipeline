"""BA 32.44 — Gemini SDK Transport Spike (gemockt, keine echten Calls)."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_MOD = _ROOT / "app" / "production_connectors" / "gemini_image_connector.py"


@pytest.fixture(scope="module")
def gem_mod():
    spec = importlib.util.spec_from_file_location("gemini_image_connector_ba344", _MOD)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _install_fake_google_genai(monkeypatch, *, first_exc: Exception | None = None):
    """Installiert ein minimales Fake-`google.genai` SDK in sys.modules."""

    class _Inline:
        def __init__(self, data):
            self.data = data

    class _Part:
        def __init__(self, inline_data=None):
            self.inline_data = inline_data

    class _Content:
        def __init__(self, parts):
            self.parts = parts

    class _Cand:
        def __init__(self, content):
            self.content = content

    class _Resp:
        def __init__(self, parts):
            self.parts = parts
            self.candidates = [_Cand(_Content(parts))]

    class _Models:
        def __init__(self):
            self._calls = 0

        def generate_content(self, **_kwargs):
            self._calls += 1
            if first_exc is not None and self._calls == 1:
                raise first_exc
            # minimal PNG header bytes
            return _Resp([_Part(_Inline(b"\x89PNG\r\n\x1a\n"))])

    class _Client:
        def __init__(self, *a, **k):
            self.models = _Models()

    # Minimal types namespace used by connector
    class _ImageConfig:
        def __init__(self, aspect_ratio: str = "1:1"):
            self.aspect_ratio = aspect_ratio

    class _GenerateContentConfig:
        def __init__(self, response_modalities=None, image_config=None):
            self.response_modalities = response_modalities or []
            self.image_config = image_config

    google_mod = types.ModuleType("google")
    genai_mod = types.SimpleNamespace(Client=_Client)
    # Provide google.genai.types
    genai_pkg_mod = types.ModuleType("google.genai")
    genai_pkg_mod.types = types.SimpleNamespace(
        GenerateContentConfig=_GenerateContentConfig,
        ImageConfig=_ImageConfig,
    )
    google_mod.genai = genai_mod
    monkeypatch.setitem(sys.modules, "google", google_mod)
    monkeypatch.setitem(sys.modules, "google.genai", genai_pkg_mod)
    return google_mod


def test_sdk_unavailable_fallbacks_to_rest(gem_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "present")
    monkeypatch.setenv("GEMINI_IMAGE_TRANSPORT", "sdk")
    # Ensure google/genai are not importable
    monkeypatch.delitem(sys.modules, "google", raising=False)

    dest = tmp_path / "x.png"
    # Patch REST helper to avoid real HTTP and to return bytes.
    with patch.object(gem_mod, "_rest_generate_image_bytes", return_value=b"\x89PNG\r\n\x1a\n"):
        ok, warns, _meta = gem_mod.run_gemini_image_live_to_png("p", dest)
    assert ok is True
    blob = " ".join(warns)
    assert "gemini_image_sdk_unavailable_fallback_rest" in blob
    assert "gemini_image_transport:rest" in blob


def test_sdk_success_sets_transport_and_writes_png(gem_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "present")
    monkeypatch.setenv("GEMINI_IMAGE_TRANSPORT", "sdk")
    _install_fake_google_genai(monkeypatch)

    dest = tmp_path / "o.png"
    ok, warns, meta = gem_mod.run_gemini_image_live_to_png("p", dest)
    assert ok is True
    assert dest.is_file()
    assert meta.get("bytes_written", 0) > 0
    blob = " ".join(warns)
    assert "gemini_image_transport:sdk" in blob


def test_sdk_rate_limit_retries_then_success(gem_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "present")
    monkeypatch.setenv("GEMINI_IMAGE_TRANSPORT", "sdk")
    _install_fake_google_genai(monkeypatch)
    dest = tmp_path / "r.png"
    calls = {"n": 0}

    def _fake_sdk_bytes(**_kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("429 RESOURCE_EXHAUSTED")
        return b"\x89PNG\r\n\x1a\n"

    with patch.object(gem_mod.time, "sleep"):
        with patch.object(gem_mod, "_sdk_generate_image_bytes", side_effect=_fake_sdk_bytes):
            ok, warns, _ = gem_mod.run_gemini_image_live_to_png("p", dest)
    assert ok is True
    blob = " ".join(warns)
    assert "gemini_image_http_429" in blob
    assert "gemini_image_retry_1_after:gemini_image_http_429" in blob

