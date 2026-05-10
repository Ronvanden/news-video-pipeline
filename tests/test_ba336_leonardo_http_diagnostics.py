"""BA 32.36 — Leonardo POST: Diagnose-Codes und Retry ohne echte Provider-Calls."""

from __future__ import annotations

import importlib.util
import json
import socket
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_asset_runner.py"


@pytest.fixture(scope="module")
def ar_mod():
    spec = importlib.util.spec_from_file_location("run_asset_runner_ba336", _SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class _Resp200:
    __test__ = False

    def __init__(self, payload: dict) -> None:
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


def test_leonardo_post_401_diagnostic_no_retry(ar_mod, tmp_path):
    dest = tmp_path / "out.png"
    err = HTTPError(
        "https://cloud.leonardo.ai/api/rest/v1/generations",
        401,
        "Unauthorized",
        {"Content-Type": "application/json"},
        BytesIO(b"{}"),
    )
    with patch.object(ar_mod, "urlopen", side_effect=err) as uo:
        ok, warns = ar_mod.leonardo_generate_image_to_path(
            "a prompt",
            dest,
            api_key="key",
            endpoint="https://cloud.leonardo.ai/api/rest/v1/generations",
        )
    assert ok is False
    assert uo.call_count == 1
    blob = " ".join(warns)
    assert "leonardo_http_401" in blob
    assert "leonardo_http_error:401" in blob
    assert "leonardo_retry_1_after" not in blob


def test_leonardo_post_429_retries_then_success(ar_mod, tmp_path):
    dest = tmp_path / "out.png"
    err429 = HTTPError(
        "https://cloud.leonardo.ai/api/rest/v1/generations",
        429,
        "Too Many Requests",
        {"Content-Type": "application/json"},
        BytesIO(b"{}"),
    )
    ok_body = {"url": "https://cdn.example.com/img.png"}
    with patch.object(ar_mod.time, "sleep"):
        with patch.object(ar_mod, "_download_leonardo_image_url", return_value=(True, [])):
            with patch.object(
                ar_mod,
                "urlopen",
                side_effect=[err429, _Resp200(ok_body)],
            ) as uo:
                ok, warns = ar_mod.leonardo_generate_image_to_path(
                    "prompt",
                    dest,
                    api_key="key",
                    endpoint="https://cloud.leonardo.ai/api/rest/v1/generations",
                )
    assert ok is True
    assert uo.call_count == 2
    blob = " ".join(warns)
    assert "leonardo_retry_1_after:leonardo_http_429" in blob


def test_leonardo_post_500_exhausts_retries(ar_mod, tmp_path):
    dest = tmp_path / "out.png"
    err500 = HTTPError(
        "https://cloud.leonardo.ai/api/rest/v1/generations",
        500,
        "Server Error",
        {"Content-Type": "application/json"},
        BytesIO(b"{}"),
    )
    with patch.object(ar_mod.time, "sleep"):
        with patch.object(ar_mod, "urlopen", side_effect=[err500, err500, err500]) as uo:
            ok, warns = ar_mod.leonardo_generate_image_to_path(
                "prompt",
                dest,
                api_key="key",
                endpoint="https://cloud.leonardo.ai/api/rest/v1/generations",
            )
    assert ok is False
    assert uo.call_count == 3
    blob = " ".join(warns)
    assert "leonardo_http_5xx" in blob
    assert "leonardo_retry_1_after:leonardo_http_5xx" in blob
    assert "leonardo_retry_2_after:leonardo_http_5xx" in blob


def test_leonardo_urllib_timeout_retries(ar_mod, tmp_path):
    dest = tmp_path / "out.png"
    ok_body = {"url": "https://cdn.example.com/img.png"}
    with patch.object(ar_mod.time, "sleep"):
        with patch.object(ar_mod, "_download_leonardo_image_url", return_value=(True, [])):
            with patch.object(
                ar_mod,
                "urlopen",
                side_effect=[
                    URLError(socket.timeout()),
                    _Resp200(ok_body),
                ],
            ):
                ok, warns = ar_mod.leonardo_generate_image_to_path(
                    "prompt",
                    dest,
                    api_key="key",
                    endpoint="https://cloud.leonardo.ai/api/rest/v1/generations",
                )
    assert ok is True
    blob = " ".join(warns)
    assert "leonardo_retry_1_after:leonardo_timeout" in blob


def test_asset_artifact_keeps_retry_warning_codes(tmp_path):
    from app.founder_dashboard.ba323_video_generate import build_asset_artifact

    gen_dir = tmp_path / "generated_assets_x"
    gen_dir.mkdir(parents=True, exist_ok=True)
    manifest = gen_dir / "asset_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "warnings": [
                    "leonardo_http_429",
                    "leonardo_retry_1_after:leonardo_http_429",
                    "leonardo_http_error:429",
                ],
                "assets": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    aa = build_asset_artifact(asset_manifest_path=str(manifest))
    codes = aa.get("asset_provider_warning_codes") or []
    assert any(c.startswith("leonardo_http_429") for c in codes if isinstance(c, str))
    assert any("leonardo_retry_1_after" in c for c in codes if isinstance(c, str))

