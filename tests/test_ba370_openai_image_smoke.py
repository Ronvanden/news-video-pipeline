"""BA 32.70 — OpenAI Image Smoke Wrapper/Sanitize (keine echten API-Calls)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

from app.production_connectors.openai_image_smoke import (
    run_openai_image_smoke_v1,
    sanitize_openai_image_smoke_warnings,
)

_ROOT = Path(__file__).resolve().parents[1]


def test_sanitize_drops_sk_pattern_and_bearer():
    raw = [
        "openai_image_http_403",
        "leak sk-abcdefghijklmnopqrstuvwxyz1234567890abcd",
        "Bearer secret-token",
        "openai_image_model:gpt-image-2",
    ]
    out = sanitize_openai_image_smoke_warnings(raw)
    assert "openai_image_http_403" in out
    assert "openai_image_model:gpt-image-2" in out
    assert "sk-abcdefghijklmnopqrstuvwxyz1234567890abcd" not in " ".join(out)
    assert not any("Bearer " in x for x in out)


def test_smoke_v1_success_shape(tmp_path):
    dest = tmp_path / "x.png"

    def _ok(*_a, **_k):
        dest.write_bytes(b"\x89PNG\r\n\x1a\n")
        return (
            True,
            [
                "openai_image_model:gpt-image-2",
                "openai_image_provider:openai_image",
                "openai_image_transport:images_api",
                "openai_image_size:1024x1024",
            ],
            {"model": "gpt-image-2", "size": "1024x1024", "bytes_written": 64, "dry_run": False, "ok": True},
        )

    with patch(
        "app.production_connectors.openai_image_smoke.run_openai_image_live_to_png",
        side_effect=_ok,
    ):
        r = run_openai_image_smoke_v1(dest)
    assert r["ok"] is True
    assert r["provider"] == "openai_image"
    assert r["model"] == "gpt-image-2"
    assert r["size"] == "1024x1024"
    assert r["bytes_written"] == 64
    assert r["smoke_version"] == "ba32_70_v1"
    assert str(dest.resolve()) in r["output_path"]


def test_smoke_v1_403_warns_in_report(tmp_path):
    dest = tmp_path / "f.png"

    def _fail(*_a, **_k):
        return (
            False,
            [
                "openai_image_model:gpt-image-2",
                "openai_image_provider:openai_image",
                "openai_image_transport:images_api",
                "openai_image_size:1024x1024",
                "openai_image_generation_failed:http_403",
                "openai_image_http_403",
                "openai_image_model_access_denied:gpt-image-2",
            ],
            {},
        )

    with patch(
        "app.production_connectors.openai_image_smoke.run_openai_image_live_to_png",
        side_effect=_fail,
    ):
        r = run_openai_image_smoke_v1(dest)
    assert r["ok"] is False
    w = " ".join(r["warnings"])
    assert "openai_image_http_403" in w
    assert "openai_image_model_access_denied:gpt-image-2" in w


def test_smoke_v1_missing_key_no_secret_echo(tmp_path):

    def _miss(*_a, **_k):
        return (
            False,
            [
                "openai_image_model:unknown",
                "openai_image_provider:openai_image",
                "openai_image_transport:images_api",
                "openai_image_key_missing_fallback_placeholder",
            ],
            {},
        )

    with patch(
        "app.production_connectors.openai_image_smoke.run_openai_image_live_to_png",
        side_effect=_miss,
    ):
        r = run_openai_image_smoke_v1(tmp_path / "m.png")
    assert r["ok"] is False
    blob = json.dumps(r)
    assert "sk-" not in blob.lower()
    assert "openai_image_key_missing_fallback_placeholder" in r["warnings"]


def test_cli_requires_confirm_flag():
    script = _ROOT / "scripts" / "run_openai_image_smoke.py"
    spec = importlib.util.spec_from_file_location("run_openai_image_smoke_ba370", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with patch.object(sys, "argv", ["run_openai_image_smoke.py"]):
        assert mod.main() == 3
