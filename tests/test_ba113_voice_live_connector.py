"""BA 11.3 — Voice Live Connector."""

from unittest.mock import patch

from app.production_connectors.schema import ConnectorExecutionRequest, LiveRuntimeGuardBundle
from app.production_connectors.voice_live_connector import execute_voice_live


def test_voice_guard_closed_dry_run():
    req = ConnectorExecutionRequest(
        connector_name="OpenAI / ElevenLabs (stub)",
        provider_type="voice",
        payload={"voice_style": "calm", "chapter_voice_blocks": [{"t": "x"}]},
        dry_run=False,
    )
    guard = LiveRuntimeGuardBundle(leonardo_live_ok=False, voice_live_ok=False, allow_live_http=False)
    res = execute_voice_live(req, guard)
    assert res.execution_mode == "dry_run"
    assert "voice_live_guard_closed" in " ".join(res.warnings)


def test_voice_payload_blocked():
    req = ConnectorExecutionRequest(
        connector_name="Voice",
        provider_type="voice",
        payload={},
        dry_run=False,
    )
    guard = LiveRuntimeGuardBundle(leonardo_live_ok=False, voice_live_ok=True, allow_live_http=True)
    res = execute_voice_live(req, guard)
    assert res.execution_mode == "blocked"
