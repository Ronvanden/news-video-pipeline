"""BA 11.2 — Leonardo Live Connector."""

import os
from unittest.mock import patch

from urllib.error import URLError

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest
from app.production_connectors.leonardo_live_connector import (
    build_leonardo_connector_request,
    execute_leonardo_live,
)
from app.production_connectors.schema import ConnectorExecutionRequest, LiveRuntimeGuardBundle


def test_leonardo_without_guard_uses_dry_run():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    req = build_leonardo_connector_request(plan)
    assert req is not None
    guard = LiveRuntimeGuardBundle(leonardo_live_ok=False, voice_live_ok=False, allow_live_http=False)
    res = execute_leonardo_live(req, guard)
    assert res.execution_mode == "dry_run"
    assert res.http_attempted is False
    assert "leonardo_live_guard_closed" in " ".join(res.warnings)


def test_leonardo_payload_invalid_blocked():
    req = ConnectorExecutionRequest(
        connector_name="Leonardo",
        provider_type="image",
        payload={"prompts": []},
        dry_run=False,
    )
    guard = LiveRuntimeGuardBundle(leonardo_live_ok=True, voice_live_ok=False, allow_live_http=True)
    res = execute_leonardo_live(req, guard)
    assert res.execution_mode == "blocked"
    assert res.blocking_reasons


def test_leonardo_timeout_triggers_live_attempt_with_url_error():
    req = ConnectorExecutionRequest(
        connector_name="Leonardo",
        provider_type="image",
        payload={"prompts": ["a"], "style_profile": "cinematic"},
        dry_run=False,
    )
    guard = LiveRuntimeGuardBundle(leonardo_live_ok=True, voice_live_ok=False, allow_live_http=True)
    with patch.dict(
        os.environ,
        {"LEONARDO_API_ENDPOINT": "https://example.invalid/leonardo", "LEONARDO_API_KEY": "k"},
        clear=False,
    ):
        with patch("app.production_connectors.leonardo_live_connector.urlopen") as uo:
            uo.side_effect = URLError("timed out")
            res = execute_leonardo_live(req, guard, timeout_seconds=2.0)
    assert res.execution_mode == "live_attempt"
    assert res.http_attempted is True
    assert any("url_error" in w or "timed out" in w.lower() for w in res.warnings)
