"""ElevenLabs voices-list helper tests."""

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from app.production_connectors.elevenlabs_voices_list import list_elevenlabs_voices


class _FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(
            {
                "voices": [
                    {
                        "voice_id": "voice_1",
                        "name": "Rachel",
                        "category": "premade",
                        "labels": {"accent": "american", "gender": "female"},
                        "preview_url": "https://example.test/preview.mp3",
                    },
                    {
                        "voice_id": "voice_2",
                        "name": "Documentary",
                        "category": "cloned",
                    },
                ]
            }
        ).encode("utf-8")

    def getcode(self):
        return 200


def test_list_without_api_key_does_not_attempt_http(monkeypatch):
    monkeypatch.delenv("VOICE_API_KEY", raising=False)

    result = list_elevenlabs_voices(timeout_seconds=1.0)

    assert result.voices == []
    assert result.safe_output() == []
    assert result.warnings == ["voice_api_key_missing_no_http_attempt"]


def test_list_with_mocked_http_returns_safe_voice_rows():
    with patch.dict(os.environ, {"VOICE_API_KEY": "test-voice-key-not-logged"}, clear=False):
        with patch(
            "app.production_connectors.elevenlabs_voices_list.urlopen",
            return_value=_FakeResponse(),
        ) as uo:
            result = list_elevenlabs_voices(timeout_seconds=1.0)

    req = uo.call_args.args[0]
    assert req.full_url == "https://api.elevenlabs.io/v1/voices"
    assert req.get_method() == "GET"
    assert req.get_header("Xi-api-key") == "test-voice-key-not-logged"
    assert req.get_header("Accept") == "application/json"
    assert result.safe_output() == [
        {
            "voice_id": "voice_1",
            "name": "Rachel",
            "category": "premade",
            "labels": {"accent": "american", "gender": "female"},
        },
        {
            "voice_id": "voice_2",
            "name": "Documentary",
            "category": "cloned",
        },
    ]
    dumped = json.dumps(result.safe_output(), ensure_ascii=False)
    assert "preview_url" not in dumped
    assert "test-voice-key-not-logged" not in result.model_dump_json()


def test_cli_outputs_safe_empty_list_without_api_key():
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env.pop("VOICE_API_KEY", None)

    completed = subprocess.run(
        [sys.executable, str(root / "scripts" / "list_elevenlabs_voices.py")],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == []
    assert "VOICE_API_KEY=" not in completed.stdout
