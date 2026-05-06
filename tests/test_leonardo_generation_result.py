"""Safe Leonardo generation GET helper tests."""

import json
import os
import subprocess
import sys
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from app.production_connectors.leonardo_generation_result import fetch_leonardo_generation_result


class _FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(
            {
                "generations_by_pk": {
                    "id": "gen_123",
                    "status": "COMPLETE",
                    "generated_images": [
                        {"url": "https://cdn.example.test/one.png"},
                        {"imageUrl": "https://cdn.example.test/two.png"},
                    ],
                }
            }
        ).encode("utf-8")

    def getcode(self):
        return 200


def test_fetch_without_env_does_not_attempt_http(monkeypatch):
    monkeypatch.delenv("LEONARDO_API_KEY", raising=False)

    result = fetch_leonardo_generation_result("gen_123", timeout_seconds=1.0)

    assert result.http_attempted is False
    assert result.http_status is None
    assert result.method == "GET"
    assert result.request_url == "https://cloud.leonardo.ai/api/rest/v1/generations/gen_123"
    assert result.header_names == []
    assert result.generation_id == "gen_123"
    assert result.image_urls == []
    assert result.warnings == ["leonardo_api_key_missing_no_http_attempt"]


def test_fetch_with_mocked_http_returns_safe_generation_result():
    with patch.dict(os.environ, {"LEONARDO_API_KEY": "test-key-not-logged"}, clear=False):
        with patch(
            "app.production_connectors.leonardo_generation_result.urlopen",
            return_value=_FakeResponse(),
        ) as uo:
            result = fetch_leonardo_generation_result("gen_123", timeout_seconds=1.0)

    req = uo.call_args.args[0]
    assert req.full_url == "https://cloud.leonardo.ai/api/rest/v1/generations/gen_123"
    assert req.get_method() == "GET"
    assert req.get_header("Authorization") == "Bearer test-key-not-logged"
    assert req.get_header("Accept") == "application/json"
    assert req.get_header("Content-type") is None
    assert result.http_attempted is True
    assert result.http_status == 200
    assert result.method == "GET"
    assert result.request_url == "https://cloud.leonardo.ai/api/rest/v1/generations/gen_123"
    assert result.header_names == ["accept", "Authorization"]
    assert result.generation_status == "COMPLETE"
    assert result.image_urls == [
        "https://cdn.example.test/one.png",
        "https://cdn.example.test/two.png",
    ]
    assert result.response_shape_summary == {"generations_by_pk": "dict"}
    assert "Bearer" not in result.model_dump_json()
    assert "test-key-not-logged" not in result.model_dump_json()


def test_fetch_http_error_keeps_safe_diagnostics():
    error_body = json.dumps({"error": "not found", "status": "FAILED"}).encode("utf-8")
    http_errors = [
        HTTPError(
            "https://example.test/generations/gen_404",
            404,
            "Not Found",
            hdrs=None,
            fp=BytesIO(error_body),
        )
        for _ in range(3)
    ]
    with patch.dict(os.environ, {"LEONARDO_API_KEY": "test-key-not-logged"}, clear=False):
        with patch("app.production_connectors.leonardo_generation_result.time.sleep") as sleep:
            with patch("app.production_connectors.leonardo_generation_result.urlopen", side_effect=http_errors) as uo:
                result = fetch_leonardo_generation_result("gen_404", timeout_seconds=1.0, retry_sleep_seconds=0.0)

    assert result.http_attempted is True
    assert result.http_status == 404
    assert uo.call_count == 3
    assert sleep.call_count == 2
    assert sleep.call_args_list[0].args == (0.0,)
    assert result.generation_status == "FAILED"
    assert result.method == "GET"
    assert result.request_url == "https://cloud.leonardo.ai/api/rest/v1/generations/gen_404"
    assert result.header_names == ["accept", "Authorization"]
    assert result.response_text_preview
    assert len(result.response_text_preview) <= 300
    assert result.warnings == ["leonardo_http_error:404"]
    assert "Bearer" not in result.model_dump_json()
    assert "test-key-not-logged" not in result.model_dump_json()


def test_fetch_retries_transient_url_error_then_succeeds():
    with patch.dict(os.environ, {"LEONARDO_API_KEY": "test-key-not-logged"}, clear=False):
        with patch("app.production_connectors.leonardo_generation_result.time.sleep") as sleep:
            with patch(
                "app.production_connectors.leonardo_generation_result.urlopen",
                side_effect=[URLError("temporary"), URLError("temporary"), _FakeResponse()],
            ) as uo:
                result = fetch_leonardo_generation_result("gen_retry", timeout_seconds=1.0, retry_sleep_seconds=0.0)

    assert uo.call_count == 3
    assert sleep.call_count == 2
    assert result.http_attempted is True
    assert result.http_status == 200
    assert result.generation_status == "COMPLETE"
    assert result.warnings == []


def test_cli_script_prints_safe_json_without_env(monkeypatch):
    monkeypatch.delenv("LEONARDO_API_KEY", raising=False)

    completed = subprocess.run(
        [sys.executable, "scripts/get_leonardo_generation.py", "gen_cli_123"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["http_attempted"] is False
    assert payload["method"] == "GET"
    assert payload["request_url"] == "https://cloud.leonardo.ai/api/rest/v1/generations/gen_cli_123"
    assert payload["header_names"] == []
    assert payload["generation_id"] == "gen_cli_123"
    assert payload["warnings"] == ["leonardo_api_key_missing_no_http_attempt"]
