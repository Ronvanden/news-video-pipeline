"""BA 11.3 — Voice optional Live-HTTP (Fallback Dry-Run)."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.production_connectors.asset_normalization import normalize_provider_asset_result
from app.production_connectors.schema import (
    ConnectorExecutionRequest,
    LiveConnectorExecutionResult,
    LiveRuntimeGuardBundle,
    NormalizedAssetResult,
)
from app.production_connectors.voice_connector import VoiceProductionConnector

_CONN = VoiceProductionConnector()
DEFAULT_ELEVENLABS_TEST_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"


def _content_type_from_headers(headers: Any) -> str:
    if headers is None:
        return ""
    getter = getattr(headers, "get_content_type", None)
    if callable(getter):
        try:
            return str(getter() or "")
        except Exception:
            return ""
    getter = getattr(headers, "get", None)
    if callable(getter):
        try:
            return str(getter("Content-Type") or getter("content-type") or "")
        except Exception:
            return ""
    return ""


def _text_from_payload(payload: Dict[str, Any]) -> str:
    prompt = payload.get("prompt") or payload.get("text")
    if isinstance(prompt, str) and prompt.strip():
        return prompt.strip()
    blocks = payload.get("chapter_voice_blocks")
    if isinstance(blocks, list) and blocks:
        first = blocks[0]
        if isinstance(first, dict):
            for key in ("text", "summary", "t"):
                value = first.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        if isinstance(first, str) and first.strip():
            return first.strip()
    return "This is a cinematic documentary voice test."


def _build_voice_generation_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"text": _text_from_payload(payload)}


def _voice_id() -> str:
    return (os.getenv("VOICE_ID") or DEFAULT_ELEVENLABS_TEST_VOICE_ID).strip() or DEFAULT_ELEVENLABS_TEST_VOICE_ID


def _build_elevenlabs_tts_endpoint(endpoint: str, voice_id: str) -> str:
    base = (endpoint or "").strip()
    if "{voice_id}" in base:
        return base.replace("{voice_id}", voice_id)
    if "/v1/text-to-speech/" in urlparse(base).path:
        return base
    return f"{base.rstrip('/')}/v1/text-to-speech/{voice_id}"


def build_voice_connector_request(plan: object) -> Optional[ConnectorExecutionRequest]:
    bundle = plan.provider_export_bundle_result
    if bundle is None:
        return None
    pkg = bundle.providers.voice_package
    return ConnectorExecutionRequest(
        connector_name=pkg.provider_name or _CONN.provider_name,
        provider_type=pkg.provider_type or _CONN.provider_type,
        payload=dict(pkg.payload or {}),
        dry_run=False,
    )


def _dry_fallback(payload: Dict[str, Any], warns: list[str]) -> LiveConnectorExecutionResult:
    dr = _CONN.dry_run(payload)
    norm = normalize_provider_asset_result(
        dr.connector_name or _CONN.provider_name,
        dr.normalized_response if isinstance(dr.normalized_response, dict) else {},
    )
    return LiveConnectorExecutionResult(
        live_connector_version="11.3-v1",
        provider_name=dr.connector_name or _CONN.provider_name,
        provider_type=dr.provider_type or "voice",
        execution_mode="dry_run",
        http_attempted=False,
        request_snapshot=dr.normalized_request if isinstance(dr.normalized_request, dict) else {},
        response_snapshot=dr.normalized_response if isinstance(dr.normalized_response, dict) else {},
        normalized_asset=norm,
        warnings=warns + dr.warnings,
        blocking_reasons=[],
    )


def execute_voice_live(
    request: ConnectorExecutionRequest,
    runtime_guard: LiveRuntimeGuardBundle,
    *,
    timeout_seconds: float = 25.0,
) -> LiveConnectorExecutionResult:
    warns: list[str] = []
    payload = dict(request.payload or {})

    ok, vw, blockers = _CONN.validate_payload(payload)
    warns.extend(vw)
    if blockers or not ok:
        return LiveConnectorExecutionResult(
            live_connector_version="11.3-v1",
            provider_name=request.connector_name or _CONN.provider_name,
            provider_type=request.provider_type or "voice",
            execution_mode="blocked",
            http_attempted=False,
            request_snapshot={},
            response_snapshot={},
            normalized_asset=NormalizedAssetResult(
                provider_name=request.connector_name or _CONN.provider_name,
                provider_type="voice",
                normalization_status="invalid",
                asset_type="audio",
                warnings=["payload_validation_failed"],
            ),
            warnings=warns,
            blocking_reasons=list(blockers) if blockers else ["voice_payload_invalid"],
        )

    if not runtime_guard.voice_live_ok:
        warns.append("voice_live_guard_closed_using_dry_run")
        return _dry_fallback(payload, warns)

    endpoint_base = (os.getenv("VOICE_API_ENDPOINT") or "").strip()
    api_key = (os.getenv("VOICE_API_KEY") or "").strip()
    if not endpoint_base:
        warns.append("voice_live_endpoint_missing_fallback_dry_run")
        return _dry_fallback(payload, warns)
    if not api_key:
        warns.append("voice_api_key_missing_fallback_dry_run")
        return _dry_fallback(payload, warns)

    voice_id = _voice_id()
    endpoint = _build_elevenlabs_tts_endpoint(endpoint_base, voice_id)
    body_dict = _build_voice_generation_payload(payload)
    body_bytes = json.dumps(body_dict).encode("utf-8")
    snap_req: Dict[str, Any] = {
        "url": endpoint,
        "method": "POST",
        "body_keys": list(body_dict.keys()),
        "authorization_header_present": True,
        "voice_id_present": bool(voice_id),
    }

    try:
        real_req = Request(
            endpoint,
            data=body_bytes,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "xi-api-key": api_key,
            },
        )
        with urlopen(real_req, timeout=timeout_seconds) as resp:
            raw_bytes = resp.read()
            code = getattr(resp, "status", None) or resp.getcode()
            content_type = _content_type_from_headers(getattr(resp, "headers", None))
            try:
                parsed: Any = json.loads(raw_bytes.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                parsed = {"raw_text": raw_bytes[:2048].decode("utf-8", errors="replace")}
            snap_resp = parsed if isinstance(parsed, dict) else {"value": parsed}
            norm = normalize_provider_asset_result(request.connector_name or _CONN.provider_name, snap_resp)
            return LiveConnectorExecutionResult(
                live_connector_version="11.3-v1",
                provider_name=request.connector_name or _CONN.provider_name,
                provider_type=request.provider_type or "voice",
                execution_mode="live_attempt",
                http_attempted=True,
                http_status_code=int(code) if code is not None else None,
                request_snapshot=snap_req,
                response_snapshot=snap_resp,
                response_headers={"content-type": content_type} if content_type else {},
                normalized_asset=norm,
                warnings=warns,
                blocking_reasons=[],
            )
    except HTTPError as e:
        warns.append(f"voice_http_error:{e.code}")
        content_type = _content_type_from_headers(getattr(e, "headers", None))
        try:
            raw_error = e.read()
            error_text = raw_error[:2048].decode("utf-8", errors="replace")
        except Exception:
            error_text = ""
        return LiveConnectorExecutionResult(
            live_connector_version="11.3-v1",
            provider_name=request.connector_name or _CONN.provider_name,
            provider_type=request.provider_type or "voice",
            execution_mode="live_attempt",
            http_attempted=True,
            http_status_code=int(e.code),
            request_snapshot=snap_req,
            response_snapshot={"http_error": True, "code": e.code, "raw_text": error_text},
            response_headers={"content-type": content_type} if content_type else {},
            normalized_asset=None,
            warnings=warns,
            blocking_reasons=[],
        )
    except URLError as e:
        reason = getattr(e, "reason", e)
        warns.append(f"voice_url_error:{reason}")
        return LiveConnectorExecutionResult(
            live_connector_version="11.3-v1",
            provider_name=request.connector_name or _CONN.provider_name,
            provider_type=request.provider_type or "voice",
            execution_mode="live_attempt",
            http_attempted=True,
            request_snapshot=snap_req,
            response_snapshot={"url_error": True},
            normalized_asset=None,
            warnings=warns,
            blocking_reasons=[],
        )
