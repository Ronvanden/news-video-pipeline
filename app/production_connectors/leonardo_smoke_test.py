"""Isolierter Leonardo-Smoke-Test ohne Pipeline-Live-Schaltung."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from app.production_connectors.leonardo_live_connector import execute_leonardo_live
from app.production_connectors.schema import ConnectorExecutionRequest, LiveRuntimeGuardBundle


MINIMAL_LEONARDO_SMOKE_PAYLOAD: Dict[str, Any] = {
    "prompts": ["Cinematic documentary still, dramatic newsroom lighting, no text overlay."],
    "style_profile": "cinematic documentary",
}


class LeonardoSmokeTestResult(BaseModel):
    """Dev-only Ergebnisform für einen isolierten Leonardo-Connector-Smoke-Test."""

    smoke_status: str = "not_run"
    env_presence: Dict[str, bool] = Field(default_factory=dict)
    http_attempted: bool = False
    http_status: Optional[int] = None
    request_url: Optional[str] = None
    request_payload_keys: List[str] = Field(default_factory=list)
    authorization_header_present: bool = False
    response_shape_summary: Dict[str, str] = Field(default_factory=dict)
    response_text_preview: str = ""
    response_headers: Dict[str, str] = Field(default_factory=dict)
    normalized_asset_url: Optional[str] = None
    provider_job_id: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)


def _env_presence() -> Dict[str, bool]:
    return {
        "LEONARDO_API_KEY": bool((os.getenv("LEONARDO_API_KEY") or "").strip()),
        "LEONARDO_API_ENDPOINT": bool((os.getenv("LEONARDO_API_ENDPOINT") or "").strip()),
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


def _safe_response_headers(headers: Dict[str, str]) -> Dict[str, str]:
    content_type = (headers.get("content-type") or "").strip()
    return {"content-type": content_type} if content_type else {}


def _provider_job_id(response: Dict[str, Any]) -> Optional[str]:
    for key in ("provider_job_id", "job_id", "generation_id", "generationId", "id"):
        value = response.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return None


def run_leonardo_connector_smoke_test(*, timeout_seconds: float = 25.0) -> LeonardoSmokeTestResult:
    """Führt nur den Leonardo-Live-Connector mit einem festen Minimal-Payload aus."""
    presence = _env_presence()
    request = ConnectorExecutionRequest(
        connector_name="Leonardo",
        provider_type="image",
        payload=dict(MINIMAL_LEONARDO_SMOKE_PAYLOAD),
        dry_run=False,
    )
    guard = LiveRuntimeGuardBundle(
        allow_live_http=True,
        leonardo_live_ok=True,
        voice_live_ok=False,
    )
    result = execute_leonardo_live(request, guard, timeout_seconds=timeout_seconds)
    normalized = result.normalized_asset
    response = dict(result.response_snapshot or {})
    request_snapshot = dict(result.request_snapshot or {})
    payload_keys = request_snapshot.get("body_keys") or list(MINIMAL_LEONARDO_SMOKE_PAYLOAD.keys())
    status = "live_attempted" if result.http_attempted else "dry_run"
    if result.blocking_reasons:
        status = "blocked"
    elif not all(presence.values()) and not result.http_attempted:
        status = "dry_run_env_missing"

    return LeonardoSmokeTestResult(
        smoke_status=status,
        env_presence=presence,
        http_attempted=result.http_attempted,
        http_status=result.http_status_code,
        request_url=_safe_host_path(str(request_snapshot.get("url") or "")),
        request_payload_keys=[str(k) for k in payload_keys],
        authorization_header_present=bool(request_snapshot.get("authorization_header_present")),
        response_shape_summary=_shape_summary(response),
        response_text_preview=_response_preview(response),
        response_headers=_safe_response_headers(result.response_headers),
        normalized_asset_url=normalized.asset_url if normalized else None,
        provider_job_id=_provider_job_id(response),
        warnings=list(result.warnings),
        blocking_reasons=list(result.blocking_reasons),
    )
