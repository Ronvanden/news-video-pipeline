"""BA 32.38 — Leonardo Mini-Payload Shape + Model-/Label-Diagnostics (kein Live-HTTP)."""

from __future__ import annotations

import importlib.util
import json
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from urllib.error import HTTPError

from app.production_connectors.leonardo_live_connector import (
    DEFAULT_LEONARDO_MODEL_ID,
    DEFAULT_LEONARDO_MODEL_PUBLIC_LABEL,
    LEONARDO_MINI_SMOKE_SAFE_PAYLOAD_KEYS,
    _build_leonardo_generation_payload,
    leonardo_mini_smoke_safe_payload_is_minimal,
)

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_asset_runner.py"


@pytest.fixture(scope="module")
def ar_mod():
    spec = importlib.util.spec_from_file_location("run_asset_runner_ba338", _SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.mark.parametrize(
    "profile",
    ["mini_smoke", "mini_smoke_safe"],
)
def test_mini_profiles_only_allow_documented_generation_keys(profile: str):
    body = _build_leonardo_generation_payload({"prompts": ["still life"]}, profile=profile)
    assert leonardo_mini_smoke_safe_payload_is_minimal(body)
    assert set(body.keys()) == LEONARDO_MINI_SMOKE_SAFE_PAYLOAD_KEYS
    assert body["modelId"] == DEFAULT_LEONARDO_MODEL_ID
    assert body["num_images"] == 1
    assert body["width"] == 512 and body["height"] == 512


def test_diagnostics_emit_model_id_and_label(ar_mod):
    body = {"width": 512, "height": 512, "modelId": DEFAULT_LEONARDO_MODEL_ID}
    warns = ar_mod._leonardo_request_diagnostic_warnings(
        safe_prompt="x",
        payload_profile="mini_smoke_safe",
        body=body,
    )
    joined = ";".join(warns)
    assert f"leonardo_model_id:{DEFAULT_LEONARDO_MODEL_ID}" in joined
    assert f"leonardo_model_label:{DEFAULT_LEONARDO_MODEL_PUBLIC_LABEL}" in joined
    assert "leonardo_model_class:repo_default" in joined


def test_diagnostics_do_not_echo_raw_prompt_chunks(ar_mod):
    blob = ("visual_" * 400).strip()
    body = {"width": 512, "height": 512, "modelId": DEFAULT_LEONARDO_MODEL_ID}
    warns = ar_mod._leonardo_request_diagnostic_warnings(
        safe_prompt=blob,
        payload_profile="standard",
        body=body,
    )
    joined = "\n".join(warns)
    assert blob[1200:1280] not in joined


def test_http_500_diag_includes_codes_and_model_id(ar_mod, tmp_path):
    dest = tmp_path / "o.png"
    err500 = HTTPError(
        "https://cloud.leonardo.ai/api/rest/v1/generations",
        500,
        "Server Error",
        {"Content-Type": "application/json"},
        BytesIO(b"{}"),
    )
    with patch.object(ar_mod.time, "sleep"):
        with patch.object(ar_mod, "urlopen", side_effect=[err500, err500, err500]):
            ok, warns = ar_mod.leonardo_generate_image_to_path(
            "tiny",
            dest,
            api_key="key-token-mini",
            endpoint="https://cloud.leonardo.ai/api/rest/v1/generations",
            payload_profile="mini_smoke_safe",
        )
    blob = " ".join(warns)
    assert ok is False
    assert "leonardo_http_5xx" in blob
    assert "leonardo_model_id:" in blob
    assert "Bearer" not in blob
    assert "key-token-mini" not in blob


class _Resp200:
    __test__ = False

    def __init__(self, payload: dict) -> None:
        import json as _json

        self._raw = _json.dumps(payload).encode("utf-8")
        self.status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False

    def read(self):
        return self._raw

    def getcode(self):
        return 200


def test_http_500_retries_then_success_keeps_diag(ar_mod, tmp_path):
    dest = tmp_path / "z.png"
    err500 = HTTPError(
        "https://cloud.leonardo.ai/api/rest/v1/generations",
        500,
        "Server Error",
        {"Content-Type": "application/json"},
        BytesIO(b"{}"),
    )
    ok_body = {"url": "https://cdn.example.com/i.png"}
    with patch.object(ar_mod.time, "sleep"):
        with patch.object(ar_mod, "_download_leonardo_image_url", return_value=(True, [])):
            with patch.object(
                ar_mod,
                "urlopen",
                side_effect=[err500, _Resp200(ok_body)],
            ):
                meta: dict = {}
                ok, warns = ar_mod.leonardo_generate_image_to_path(
                    "pic",
                    dest,
                    api_key="key-token",
                    endpoint="https://cloud.leonardo.ai/api/rest/v1/generations",
                    payload_profile="mini_smoke_safe",
                    meta_out=meta,
                )
    blob = " ".join(warns)
    assert ok is True
    assert "leonardo_retry_1_after:leonardo_http_5xx" in blob
    assert meta.get("model_id") == DEFAULT_LEONARDO_MODEL_ID


def test_asset_provider_codes_include_new_model_diag(tmp_path):
    from app.founder_dashboard.ba323_video_generate import build_asset_artifact

    gen_dir = tmp_path / "g"
    gen_dir.mkdir()
    man = gen_dir / "asset_manifest.json"
    man.write_text(
        json.dumps(
            {
                "warnings": [
                    f"leonardo_model_id:{DEFAULT_LEONARDO_MODEL_ID}",
                    f"leonardo_model_label:{DEFAULT_LEONARDO_MODEL_PUBLIC_LABEL}",
                    "leonardo_http_error:500",
                ],
                "assets": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    aa = build_asset_artifact(asset_manifest_path=str(man))
    codes = [str(c) for c in (aa.get("asset_provider_warning_codes") or [])]
    assert any("leonardo_model_id:" in c for c in codes)
    assert any("leonardo_model_label:" in c for c in codes)
