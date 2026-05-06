"""Persist Voice smoke-test MP3 helper tests."""

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from app.production_connectors.voice_live_connector import DEFAULT_ELEVENLABS_TEST_VOICE_ID
from app.production_connectors.voice_smoke_file_save import run_voice_smoke_test_and_save
from app.production_connectors.voice_smoke_test import MINIMAL_VOICE_SMOKE_PROMPT


MP3_BYTES = b"ID3\x04\x00\x00\x00\x00\x00\x21fake-mp3-audio-bytes"


class _FakeBinaryResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return MP3_BYTES

    def getcode(self):
        return 200


def _posted_body(mock_urlopen):
    req = mock_urlopen.call_args.args[0]
    return json.loads(req.data.decode("utf-8"))


def test_voice_smoke_file_save_without_env_writes_no_file(tmp_path, monkeypatch):
    monkeypatch.delenv("VOICE_API_KEY", raising=False)
    monkeypatch.delenv("VOICE_API_ENDPOINT", raising=False)
    target = tmp_path / "output" / "voice_smoke_test_output.mp3"

    result = run_voice_smoke_test_and_save(output_path=target, timeout_seconds=1.0)

    assert result.http_status is None
    assert result.file_saved is False
    assert result.output_path == str(target)
    assert result.file_size_bytes == 0
    assert target.exists() is False
    assert result.blocking_reasons == ["voice_live_env_missing"]
    assert "voice_live_endpoint_missing_no_file_saved" in result.warnings
    assert "voice_api_key_missing_no_file_saved" in result.warnings


def test_voice_smoke_file_save_writes_mocked_binary_mp3(tmp_path):
    target = tmp_path / "output" / "voice_smoke_test_output.mp3"
    with patch.dict(
        os.environ,
        {
            "VOICE_API_KEY": "test-voice-key-not-logged",
            "VOICE_API_ENDPOINT": "https://example.test",
            "VOICE_ID": "voice_from_env",
        },
        clear=False,
    ):
        with patch("app.production_connectors.voice_smoke_file_save.urlopen", return_value=_FakeBinaryResponse()) as uo:
            result = run_voice_smoke_test_and_save(output_path=target, timeout_seconds=1.0)

    req = uo.call_args.args[0]
    assert req.full_url == "https://example.test/v1/text-to-speech/voice_from_env"
    assert req.get_method() == "POST"
    assert req.get_header("Xi-api-key") == "test-voice-key-not-logged"
    assert req.get_header("Content-type") == "application/json"
    assert _posted_body(uo) == {"text": MINIMAL_VOICE_SMOKE_PROMPT}
    assert result.http_status == 200
    assert result.file_saved is True
    assert result.output_path == str(target)
    assert result.file_size_bytes == len(MP3_BYTES)
    assert result.warnings == []
    assert result.blocking_reasons == []
    assert target.read_bytes() == MP3_BYTES
    assert target.read_bytes().startswith(b"ID3")


def test_voice_smoke_file_save_uses_default_voice_id(tmp_path):
    target = tmp_path / "voice.mp3"
    with patch.dict(
        os.environ,
        {
            "VOICE_API_KEY": "test-voice-key-not-logged",
            "VOICE_API_ENDPOINT": "https://example.test",
        },
        clear=False,
    ):
        os.environ.pop("VOICE_ID", None)
        with patch("app.production_connectors.voice_smoke_file_save.urlopen", return_value=_FakeBinaryResponse()) as uo:
            result = run_voice_smoke_test_and_save(output_path=target, timeout_seconds=1.0)

    req = uo.call_args.args[0]
    assert req.full_url == f"https://example.test/v1/text-to-speech/{DEFAULT_ELEVENLABS_TEST_VOICE_ID}"
    assert result.file_saved is True
    assert target.exists() is True


def test_voice_smoke_file_save_result_does_not_leak_secret(tmp_path):
    target = tmp_path / "voice.mp3"
    with patch.dict(
        os.environ,
        {
            "VOICE_API_KEY": "super-secret-voice-key",
            "VOICE_API_ENDPOINT": "https://example.test",
            "VOICE_ID": "voice_from_env",
        },
        clear=False,
    ):
        with patch("app.production_connectors.voice_smoke_file_save.urlopen", return_value=_FakeBinaryResponse()):
            result = run_voice_smoke_test_and_save(output_path=target, timeout_seconds=1.0)

    dumped = result.model_dump_json()
    assert "super-secret-voice-key" not in dumped
    assert "xi-api-key" not in dumped
    assert "voice_from_env" not in dumped


def test_cli_without_env_outputs_safe_json_and_writes_no_file(tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env.pop("VOICE_API_KEY", None)
    env.pop("VOICE_API_ENDPOINT", None)
    env.pop("VOICE_ID", None)

    completed = subprocess.run(
        [sys.executable, str(root / "scripts" / "run_voice_smoke_test_and_save.py")],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["http_status"] is None
    assert payload["file_saved"] is False
    assert payload["output_path"] == str(Path("output") / "voice_smoke_test_output.mp3")
    assert payload["file_size_bytes"] == 0
    assert (tmp_path / "output" / "voice_smoke_test_output.mp3").exists() is False
    assert payload["blocking_reasons"] == ["voice_live_env_missing"]
    assert "VOICE_API_KEY=" not in completed.stdout
