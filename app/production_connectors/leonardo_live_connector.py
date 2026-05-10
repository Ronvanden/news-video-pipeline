"""BA 11.2 — Leonardo optional Live-HTTP (Fallback Dry-Run)."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.production_connectors.asset_normalization import normalize_provider_asset_result
from app.production_connectors.leonardo_connector import LeonardoProductionConnector
from app.production_connectors.schema import (
    ConnectorExecutionRequest,
    LiveConnectorExecutionResult,
    LiveRuntimeGuardBundle,
    NormalizedAssetResult,
)

_CONN = LeonardoProductionConnector()
# OpenAPI-Referenz (createGeneration): Default modelId laut Schema — öffentliche UUID, kein Secret.
DEFAULT_LEONARDO_MODEL_ID = "b24e16ff-06e3-43eb-8d33-4416c2d75876"
# GET listPlatformModels (BA 32.39) — nur für manuelles Discovery / Diagnose.
LEONARDO_PLATFORM_MODELS_URL = "https://cloud.leonardo.ai/api/rest/v1/platformModels"
DEFAULT_LEONARDO_MODEL_PUBLIC_LABEL = "openapi_schema_default"
# BA 32.38 — Minimalfelder nur für Mini-Smoke-Profile (keine Presets/Alchemy/Ultra im Body).
LEONARDO_MINI_SMOKE_SAFE_PROFILES = frozenset({"mini_smoke", "mini_smoke_safe"})
LEONARDO_MINI_SMOKE_SAFE_PAYLOAD_KEYS = frozenset(
    {"prompt", "modelId", "width", "height", "num_images"}
)


def leonardo_mini_smoke_safe_payload_is_minimal(body: Dict[str, Any]) -> bool:
    """True wenn der POST-Body nur die dokumentierten Minimal-Keys enthält (Smoke-Validierung)."""
    if not isinstance(body, dict):
        return False
    return set(body.keys()) == LEONARDO_MINI_SMOKE_SAFE_PAYLOAD_KEYS


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


def _build_leonardo_generation_payload(
    payload: Dict[str, Any],
    *,
    profile: str = "standard",
) -> Dict[str, Any]:
    prompts = payload.get("prompts")
    prompt = payload.get("prompt")
    if isinstance(prompts, list) and prompts:
        first = prompts[0]
        if isinstance(first, str) and first.strip():
            prompt = first.strip()
    if not isinstance(prompt, str) or not prompt.strip():
        prompt = "Cinematic documentary still, dramatic newsroom lighting, no text overlay."
    prof = (profile or "standard").strip().lower()
    # BA 32.37/32.38 — Mini-Smoke: Repo-Default-Modell (OpenAPI-Schema-Default), konservative 512×512.
    force_repo_default = prof in LEONARDO_MINI_SMOKE_SAFE_PROFILES
    if force_repo_default:
        model_id = (DEFAULT_LEONARDO_MODEL_ID or "").strip()
    else:
        model_id = (os.getenv("LEONARDO_MODEL_ID") or DEFAULT_LEONARDO_MODEL_ID or "").strip() or DEFAULT_LEONARDO_MODEL_ID
    # Nur die fünf Keys — optional setzt der Server Alchemy o. ä. per Default (siehe API-Doku).
    return {
        "prompt": prompt.strip(),
        "width": 512,
        "height": 512,
        "num_images": 1,
        "modelId": model_id,
    }


def build_leonardo_connector_request(plan: object) -> Optional[ConnectorExecutionRequest]:
    bundle = plan.provider_export_bundle_result
    if bundle is None:
        return None
    pkg = bundle.providers.image_package
    return ConnectorExecutionRequest(
        connector_name=pkg.provider_name or _CONN.provider_name,
        provider_type=pkg.provider_type or _CONN.provider_type,
        payload=dict(pkg.payload or {}),
        dry_run=False,
    )


def _dry_fallback(payload: Dict[str, Any], warns: list[str]) -> LiveConnectorExecutionResult:
    dr = _CONN.dry_run(payload)
    norm = normalize_provider_asset_result(
        dr.connector_name or "Leonardo",
        dr.normalized_response if isinstance(dr.normalized_response, dict) else {},
    )
    return LiveConnectorExecutionResult(
        live_connector_version="11.2-v1",
        provider_name=dr.connector_name or "Leonardo",
        provider_type=dr.provider_type or "image",
        execution_mode="dry_run",
        http_attempted=False,
        request_snapshot=dr.normalized_request if isinstance(dr.normalized_request, dict) else {},
        response_snapshot=dr.normalized_response if isinstance(dr.normalized_response, dict) else {},
        normalized_asset=norm,
        warnings=warns + dr.warnings,
        blocking_reasons=[],
    )


def execute_leonardo_live(
    request: ConnectorExecutionRequest,
    runtime_guard: LiveRuntimeGuardBundle,
    *,
    timeout_seconds: float = 25.0,
) -> LiveConnectorExecutionResult:
    """Führt Leonardo aus: bei geöffnetem Guard optional HTTP, sonst Dry-Run."""
    warns: list[str] = []
    payload = dict(request.payload or {})

    ok, vw, blockers = _CONN.validate_payload(payload)
    warns.extend(vw)
    if blockers or not ok:
        return LiveConnectorExecutionResult(
            live_connector_version="11.2-v1",
            provider_name=request.connector_name or "Leonardo",
            provider_type=request.provider_type or "image",
            execution_mode="blocked",
            http_attempted=False,
            request_snapshot={},
            response_snapshot={},
            normalized_asset=NormalizedAssetResult(
                provider_name="Leonardo",
                provider_type="image",
                normalization_status="invalid",
                asset_type="image",
                warnings=["payload_validation_failed"],
            ),
            warnings=warns,
            blocking_reasons=list(blockers) if blockers else ["leonardo_payload_invalid"],
        )

    if not runtime_guard.leonardo_live_ok:
        warns.append("leonardo_live_guard_closed_using_dry_run")
        return _dry_fallback(payload, warns)

    endpoint = (os.getenv("LEONARDO_API_ENDPOINT") or "").strip()
    api_key = (os.getenv("LEONARDO_API_KEY") or "").strip()
    if not endpoint:
        warns.append("leonardo_live_endpoint_missing_fallback_dry_run")
        return _dry_fallback(payload, warns)
    if not api_key:
        warns.append("leonardo_api_key_missing_fallback_dry_run")
        return _dry_fallback(payload, warns)

    body_dict = _build_leonardo_generation_payload(payload)
    body_bytes = json.dumps(body_dict).encode("utf-8")
    snap_req: Dict[str, Any] = {
        "url": endpoint,
        "method": "POST",
        "body_keys": list(body_dict.keys()),
        "authorization_header_present": True,
    }

    try:
        real_req = Request(
            endpoint,
            data=body_bytes,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
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
            norm = normalize_provider_asset_result(request.connector_name or "Leonardo", snap_resp)
            return LiveConnectorExecutionResult(
                live_connector_version="11.2-v1",
                provider_name=request.connector_name or "Leonardo",
                provider_type=request.provider_type or "image",
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
        warns.append(f"leonardo_http_error:{e.code}")
        content_type = _content_type_from_headers(getattr(e, "headers", None))
        try:
            raw_error = e.read()
            error_text = raw_error[:2048].decode("utf-8", errors="replace")
        except Exception:
            error_text = ""
        return LiveConnectorExecutionResult(
            live_connector_version="11.2-v1",
            provider_name=request.connector_name or "Leonardo",
            provider_type=request.provider_type or "image",
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
        warns.append(f"leonardo_url_error:{reason}")
        return LiveConnectorExecutionResult(
            live_connector_version="11.2-v1",
            provider_name=request.connector_name or "Leonardo",
            provider_type=request.provider_type or "image",
            execution_mode="live_attempt",
            http_attempted=True,
            request_snapshot=snap_req,
            response_snapshot={"url_error": True},
            normalized_asset=None,
            warnings=warns,
            blocking_reasons=[],
        )
