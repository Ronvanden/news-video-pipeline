"""Isolierter Voice-Smoke-Test ohne Full-Pipeline-Ausführung."""

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from app.production_connectors.voice_smoke_test import (
    MINIMAL_VOICE_SMOKE_PROMPT,
    run_voice_connector_smoke_test,
)
from app.production_connectors.voice_live_connector import DEFAULT_ELEVENLABS_TEST_VOICE_ID


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
                "id": "voice_job_123",
                "asset_url": "https://cdn.example.test/voice/audio.mp3",
                "status": "complete",
            }
        ).encode("utf-8")

    def getcode(self):
        return 200


def _posted_body(mock_urlopen):
    req = mock_urlopen.call_args.args[0]
    return json.loads(req.data.decode("utf-8"))


def test_voice_smoke_without_env_uses_clean_dry_run(monkeypatch):
    monkeypatch.delenv("VOICE_API_KEY", raising=False)
    monkeypatch.delenv("VOICE_API_ENDPOINT", raising=False)
    monkeypatch.delenv("VOICE_ID", raising=False)

    result = run_voice_connector_smoke_test(timeout_seconds=1.0)

    assert result.smoke_status == "dry_run_env_missing"
    assert result.env_presence == {"VOICE_API_KEY": False, "VOICE_API_ENDPOINT": False, "VOICE_ID": False}
    assert result.http_attempted is False
    assert result.http_status is None
    assert result.request_payload_keys == ["voice_style", "chapter_voice_blocks"]
    assert result.authorization_header_present is False
    assert result.blocking_reasons == []
    assert any("endpoint_missing" in warning for warning in result.warnings)


def test_voice_smoke_with_mocked_http_returns_audio_asset():
    with patch.dict(
        os.environ,
        {
            "VOICE_API_KEY": "test-voice-key-not-logged",
            "VOICE_API_ENDPOINT": "https://example.test",
            "VOICE_ID": "voice_from_env",
        },
        clear=False,
    ):
        with patch("app.production_connectors.voice_live_connector.urlopen", return_value=_FakeResponse()) as uo:
            result = run_voice_connector_smoke_test(timeout_seconds=1.0)

    posted = _posted_body(uo)
    req = uo.call_args.args[0]
    assert req.full_url == "https://example.test/v1/text-to-speech/voice_from_env"
    assert req.get_method() == "POST"
    assert req.get_header("Xi-api-key") == "test-voice-key-not-logged"
    assert req.get_header("Authorization") is None
    assert req.get_header("Content-type") == "application/json"
    assert posted == {"text": MINIMAL_VOICE_SMOKE_PROMPT}
    assert "provider" not in posted
    assert "operation" not in posted
    assert "dry_run" not in posted
    assert result.smoke_status == "live_attempted"
    assert result.env_presence == {"VOICE_API_KEY": True, "VOICE_API_ENDPOINT": True, "VOICE_ID": True}
    assert result.http_attempted is True
    assert result.http_status == 200
    assert result.request_url == "example.test/v1/text-to-speech/voice_from_env"
    assert result.request_payload_keys == ["text"]
    assert result.authorization_header_present is True
    assert result.provider_job_id == "voice_job_123"
    assert result.normalized_asset_url == "https://cdn.example.test/voice/audio.mp3"
    assert result.response_shape_summary == {"asset_url": "str", "id": "str", "status": "str"}
    assert len(result.response_text_preview) <= 300
    assert "test-voice-key-not-logged" not in result.model_dump_json()
    assert "test-voice-key-not-logged" not in result.model_dump_json()


def test_voice_smoke_response_does_not_leak_secret_values():
    with patch.dict(
        os.environ,
        {
            "VOICE_API_KEY": "another-test-voice-key",
            "VOICE_API_ENDPOINT": "https://example.test",
        },
        clear=False,
    ):
        with patch("app.production_connectors.voice_live_connector.urlopen", return_value=_FakeResponse()):
            result = run_voice_connector_smoke_test(timeout_seconds=1.0)

    dumped = result.model_dump_json()
    assert "another-test-voice-key" not in dumped
    assert "Bearer" not in dumped


def test_voice_smoke_uses_default_voice_id_when_env_missing():
    with patch.dict(
        os.environ,
        {
            "VOICE_API_KEY": "test-voice-key-not-logged",
            "VOICE_API_ENDPOINT": "https://example.test",
        },
        clear=False,
    ):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("VOICE_ID", None)
            with patch("app.production_connectors.voice_live_connector.urlopen", return_value=_FakeResponse()) as uo:
                result = run_voice_connector_smoke_test(timeout_seconds=1.0)

    req = uo.call_args.args[0]
    assert req.full_url == f"https://example.test/v1/text-to-speech/{DEFAULT_ELEVENLABS_TEST_VOICE_ID}"
    assert result.env_presence == {"VOICE_API_KEY": True, "VOICE_API_ENDPOINT": True, "VOICE_ID": False}
    assert result.request_url == f"example.test/v1/text-to-speech/{DEFAULT_ELEVENLABS_TEST_VOICE_ID}"


def test_cli_script_prints_safe_json_without_env():
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env.pop("VOICE_API_KEY", None)
    env.pop("VOICE_API_ENDPOINT", None)
    env.pop("VOICE_ID", None)

    completed = subprocess.run(
        [sys.executable, str(root / "scripts" / "run_voice_smoke_test.py")],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    body = json.loads(completed.stdout)
    assert body["smoke_status"] == "dry_run_env_missing"
    assert body["env_presence"] == {"VOICE_API_KEY": False, "VOICE_API_ENDPOINT": False, "VOICE_ID": False}
    assert body["request_payload_keys"] == ["voice_style", "chapter_voice_blocks"]
    assert body["authorization_header_present"] is False
    assert "VOICE_API_KEY=" not in completed.stdout
    assert "VOICE_API_ENDPOINT=" not in completed.stdout
