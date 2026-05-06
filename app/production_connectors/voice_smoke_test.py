"""Isolierter Voice-Smoke-Test ohne Full-Pipeline-Ausführung."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from app.production_connectors.schema import ConnectorExecutionRequest, LiveRuntimeGuardBundle
from app.production_connectors.voice_live_connector import execute_voice_live


MINIMAL_VOICE_SMOKE_PROMPT = "This is a cinematic documentary voice test."
MINIMAL_VOICE_SMOKE_PAYLOAD: Dict[str, Any] = {
    "voice_style": "cinematic documentary",
    "chapter_voice_blocks": [{"text": MINIMAL_VOICE_SMOKE_PROMPT}],
}


class VoiceSmokeTestResult(BaseModel):
    """Safe result shape for one isolated Voice smoke test."""

    smoke_status: str = "not_run"
    env_presence: Dict[str, bool] = Field(default_factory=dict)
    http_attempted: bool = False
    http_status: Optional[int] = None
    request_url: Optional[str] = None
    request_payload_keys: List[str] = Field(default_factory=list)
    authorization_header_present: bool = False
    provider_job_id: Optional[str] = None
    normalized_asset_url: Optional[str] = None
    response_shape_summary: Dict[str, str] = Field(default_factory=dict)
    response_text_preview: str = ""
    warnings: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)


def _env_presence() -> Dict[str, bool]:
    return {
        "VOICE_API_KEY": bool((os.getenv("VOICE_API_KEY") or "").strip()),
        "VOICE_API_ENDPOINT": bool((os.getenv("VOICE_API_ENDPOINT") or "").strip()),
        "VOICE_ID": bool((os.getenv("VOICE_ID") or "").strip()),
    }


def _shape_summary(response: Dict[str, Any]) -> Dict[str, str]:
    return {str(k): type(v).__name__ for k, v in sorted(response.items())}


def _safe_host_path(url: str) -> Optional[str]:
    parsed = urlparse(url or "")
    if not parsed.netloc:
        return None
    return f"{parsed.netloc}{parsed.path or ''}"


def _response_preview(response: Dict[str, Any]) -> str:
    raw = response.get("raw_text")
    if isinstance(raw, str):
        text = raw
    else:
        text = json.dumps(response, ensure_ascii=False, sort_keys=True)
    return text[:300]


def _provider_job_id(response: Dict[str, Any]) -> Optional[str]:
    for key in ("provider_job_id", "job_id", "audio_job_id", "generation_id", "id"):
        value = response.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return None


def run_voice_connector_smoke_test(*, timeout_seconds: float = 25.0) -> VoiceSmokeTestResult:
    """Run only the Voice live connector with a fixed minimal payload."""
    presence = _env_presence()
    request = ConnectorExecutionRequest(
        connector_name="OpenAI / ElevenLabs (stub)",
        provider_type="voice",
        payload=dict(MINIMAL_VOICE_SMOKE_PAYLOAD),
        dry_run=False,
    )
    guard = LiveRuntimeGuardBundle(
        allow_live_http=True,
        leonardo_live_ok=False,
        voice_live_ok=True,
    )
    result = execute_voice_live(request, guard, timeout_seconds=timeout_seconds)
    normalized = result.normalized_asset
    response = dict(result.response_snapshot or {})
    request_snapshot = dict(result.request_snapshot or {})
    payload_keys = request_snapshot.get("body_keys") or list(MINIMAL_VOICE_SMOKE_PAYLOAD.keys())

    status = "live_attempted" if result.http_attempted else "dry_run"
    if result.blocking_reasons:
        status = "blocked"
    elif (not presence["VOICE_API_KEY"] or not presence["VOICE_API_ENDPOINT"]) and not result.http_attempted:
        status = "dry_run_env_missing"

    return VoiceSmokeTestResult(
        smoke_status=status,
        env_presence=presence,
        http_attempted=result.http_attempted,
        http_status=result.http_status_code,
        request_url=_safe_host_path(str(request_snapshot.get("url") or "")),
        request_payload_keys=[str(k) for k in payload_keys],
        authorization_header_present=bool(request_snapshot.get("authorization_header_present")),
        provider_job_id=_provider_job_id(response),
        normalized_asset_url=normalized.asset_url if normalized else None,
        response_shape_summary=_shape_summary(response),
        response_text_preview=_response_preview(response),
        warnings=list(result.warnings),
        blocking_reasons=list(result.blocking_reasons),
    )
