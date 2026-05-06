"""BA 11.0–11.5 — Live-Provider-Suite nach Run-Core-Summary."""

from __future__ import annotations

from app.production_connectors.asset_persistence import build_asset_persistence_contract
from app.production_connectors.error_recovery import build_provider_error_recovery
from app.production_connectors.leonardo_live_connector import (
    build_leonardo_connector_request,
    execute_leonardo_live,
)
from app.production_connectors.live_provider_safety import evaluate_live_provider_safety
from app.production_connectors.runtime_secret_check import build_runtime_secret_check
from app.production_connectors.schema import LiveConnectorExecutionResult, LiveRuntimeGuardBundle
from app.production_connectors.voice_live_connector import build_voice_connector_request, execute_voice_live


def build_live_runtime_guard_bundle(plan: object) -> LiveRuntimeGuardBundle:
    safety = plan.live_provider_safety_result
    sec = plan.runtime_secret_check_result
    allow = bool(getattr(plan, "allow_live_provider_execution", False))

    bundle = plan.provider_export_bundle_result
    img_name = bundle.providers.image_package.provider_name if bundle else "Leonardo"
    voice_name = bundle.providers.voice_package.provider_name if bundle else "OpenAI / ElevenLabs (stub)"

    def secret_ready(substr: str) -> bool:
        if sec is None:
            return False
        sub = substr.lower()
        for ps in sec.provider_secrets:
            if sub in (ps.provider_name or "").lower():
                return ps.secret_status == "configured"
        return False

    live_ok = bool(
        allow and safety and safety.live_provider_allowed and safety.live_provider_mode == "guarded_live_ready"
    )

    leo_ok = (
        live_ok
        and img_name in (safety.approved_providers if safety else [])
        and secret_ready("leonardo")
    )
    voice_ok = (
        live_ok
        and voice_name in (safety.approved_providers if safety else [])
        and secret_ready("voice")
    )

    return LiveRuntimeGuardBundle(
        allow_live_http=live_ok,
        leonardo_live_ok=leo_ok,
        voice_live_ok=voice_ok,
    )


def _blocked_connector_stub(provider_name: str, provider_type: str, reason: str) -> LiveConnectorExecutionResult:
    return LiveConnectorExecutionResult(
        live_connector_version="11.x-v1",
        provider_name=provider_name,
        provider_type=provider_type,
        execution_mode="blocked",
        blocking_reasons=[reason],
        warnings=[reason],
    )


def apply_live_provider_suite(plan: object) -> object:
    """Safety → Secrets → optional Live-Versuche → Persistenz → Recovery."""
    p = plan.model_copy(update={"live_provider_safety_result": evaluate_live_provider_safety(plan)})
    p = p.model_copy(update={"runtime_secret_check_result": build_runtime_secret_check(p)})
    guard = build_live_runtime_guard_bundle(p)

    leo_req = build_leonardo_connector_request(p)
    if leo_req is None:
        leo_res = _blocked_connector_stub("Leonardo", "image", "missing_bundle_for_leonardo_live")
    else:
        leo_res = execute_leonardo_live(leo_req, guard)

    vo_req = build_voice_connector_request(p)
    if vo_req is None:
        vo_res = _blocked_connector_stub("Voice", "voice", "missing_bundle_for_voice_live")
    else:
        vo_res = execute_voice_live(vo_req, guard)

    p = p.model_copy(update={"leonardo_live_result": leo_res, "voice_live_result": vo_res})
    p = p.model_copy(update={"asset_persistence_result": build_asset_persistence_contract(p)})
    p = p.model_copy(update={"provider_error_recovery_result": build_provider_error_recovery(p)})
    return p
