"""Isolierter Leonardo-Smoke-Test ohne Pipeline-Live-Schaltung."""

import json
import os
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from app.production_connectors.leonardo_live_connector import DEFAULT_LEONARDO_MODEL_ID
from app.production_connectors.leonardo_smoke_test import (
    MINIMAL_LEONARDO_SMOKE_PAYLOAD,
    run_leonardo_connector_smoke_test,
)


class _FakeHeaders:
    def get_content_type(self):
        return "application/json"


class _FakeResponse:
    status = 200
    headers = _FakeHeaders()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(
            {
                "id": "leo_job_123",
                "asset_url": "https://cdn.example.test/leonardo/image.png",
                "status": "complete",
            }
        ).encode("utf-8")

    def getcode(self):
        return 200


def _posted_body(mock_urlopen):
    req = mock_urlopen.call_args.args[0]
    return json.loads(req.data.decode("utf-8"))


def test_leonardo_smoke_without_env_uses_clean_dry_run(monkeypatch):
    monkeypatch.delenv("LEONARDO_API_KEY", raising=False)
    monkeypatch.delenv("LEONARDO_API_ENDPOINT", raising=False)

    result = run_leonardo_connector_smoke_test(timeout_seconds=1.0)

    assert result.smoke_status == "dry_run_env_missing"
    assert result.env_presence == {"LEONARDO_API_KEY": False, "LEONARDO_API_ENDPOINT": False}
    assert result.http_attempted is False
    assert result.http_status is None
    assert result.blocking_reasons == []
    assert any("endpoint_missing" in warning for warning in result.warnings)


def test_leonardo_smoke_with_mocked_http_returns_normalized_asset():
    with patch.dict(
        os.environ,
        {
            "LEONARDO_API_KEY": "test-key-not-logged",
            "LEONARDO_API_ENDPOINT": "https://example.test/leonardo",
            "LEONARDO_MODEL_ID": "model-from-env",
        },
        clear=False,
    ):
        with patch("app.production_connectors.leonardo_live_connector.urlopen", return_value=_FakeResponse()) as uo:
            result = run_leonardo_connector_smoke_test(timeout_seconds=1.0)

    assert result.smoke_status == "live_attempted"
    assert result.env_presence == {"LEONARDO_API_KEY": True, "LEONARDO_API_ENDPOINT": True}
    assert result.http_attempted is True
    assert result.http_status == 200
    assert result.request_url == "example.test/leonardo"
    assert result.request_payload_keys == ["prompt", "width", "height", "num_images", "modelId"]
    assert result.authorization_header_present is True
    assert _posted_body(uo) == {
        "prompt": MINIMAL_LEONARDO_SMOKE_PAYLOAD["prompts"][0],
        "width": 512,
        "height": 512,
        "num_images": 1,
        "modelId": "model-from-env",
    }
    assert "provider" not in _posted_body(uo)
    assert "style_profile" not in _posted_body(uo)
    assert "prompts" not in _posted_body(uo)
    assert "dry_run" not in _posted_body(uo)
    assert result.normalized_asset_url == "https://cdn.example.test/leonardo/image.png"
    assert result.provider_job_id == "leo_job_123"
    assert result.response_shape_summary == {"asset_url": "str", "id": "str", "status": "str"}
    assert result.response_headers == {"content-type": "application/json"}
    assert len(result.response_text_preview) <= 300
    assert "test-key-not-logged" not in result.model_dump_json()


def test_leonardo_smoke_http_error_keeps_safe_diagnostics():
    with patch.dict(
        os.environ,
        {
            "LEONARDO_API_KEY": "test-key-not-logged",
            "LEONARDO_API_ENDPOINT": "https://example.test/leonardo?secretish=nope",
        },
        clear=False,
    ):
        err = HTTPError(
            "https://example.test/leonardo?secretish=nope",
            400,
            "Bad Request",
            {"Content-Type": "application/json"},
            BytesIO(b'{"error":"bad payload","detail":"safe"}'),
        )
        with patch("app.production_connectors.leonardo_live_connector.urlopen", side_effect=err) as uo:
            result = run_leonardo_connector_smoke_test(timeout_seconds=1.0)

    assert result.smoke_status == "live_attempted"
    assert result.http_attempted is True
    assert result.http_status == 400
    assert result.request_url == "example.test/leonardo"
    assert result.request_payload_keys == ["prompt", "width", "height", "num_images", "modelId"]
    assert result.authorization_header_present is True
    assert _posted_body(uo)["prompt"] == MINIMAL_LEONARDO_SMOKE_PAYLOAD["prompts"][0]
    assert _posted_body(uo)["modelId"] == DEFAULT_LEONARDO_MODEL_ID
    assert result.response_headers == {"content-type": "application/json"}
    assert result.response_shape_summary == {"code": "int", "http_error": "bool", "raw_text": "str"}
    assert len(result.response_text_preview) <= 300
    assert "test-key-not-logged" not in result.model_dump_json()
    assert "secretish" not in result.model_dump_json()


def test_minimal_smoke_payload_remains_valid():
    assert MINIMAL_LEONARDO_SMOKE_PAYLOAD["prompts"]
    assert MINIMAL_LEONARDO_SMOKE_PAYLOAD["style_profile"]


def test_cli_script_prints_safe_json_without_env():
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env.pop("LEONARDO_API_KEY", None)
    env.pop("LEONARDO_API_ENDPOINT", None)

    completed = subprocess.run(
        [sys.executable, str(root / "scripts" / "run_leonardo_smoke_test.py")],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    body = json.loads(completed.stdout)
    assert body["smoke_status"] == "dry_run_env_missing"
    assert body["env_presence"] == {"LEONARDO_API_KEY": False, "LEONARDO_API_ENDPOINT": False}
    assert body["request_payload_keys"] == ["prompts", "style_profile"]
    assert body["authorization_header_present"] is False
    assert "LEONARDO_API_KEY=" not in completed.stdout
    assert "LEONARDO_API_ENDPOINT=" not in completed.stdout
