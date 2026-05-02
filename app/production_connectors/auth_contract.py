"""BA 10.1 — Live-Connector-Auth-Contract (Mapping only, keine ENV-Lesung, keine Secrets)."""

from __future__ import annotations

from typing import List

from app.production_connectors.registry import get_connector
from app.production_connectors.schema import (
    ConnectorAuthContractResult,
    ConnectorAuthContractsResult,
    ConnectorAuthStatus,
    ConnectorAuthType,
)

_WARN_V1 = "V1: Keine ENV-Prüfung — auth_status spiegelt nur Contract-Erwartung."


def build_connector_auth_contract(connector_name: str) -> ConnectorAuthContractResult:
    """Liefert erwartete Auth-Felder je Connector-Name/Typ — ohne Werte aus der Umgebung."""
    raw = (connector_name or "").strip()
    key = raw.lower()
    warnings = [_WARN_V1]

    if not key:
        return ConnectorAuthContractResult(
            connector_name="",
            auth_status="auth_unknown",
            required_env_vars=[],
            optional_env_vars=[],
            auth_type="unknown",
            warnings=["empty_connector_name"],
        )

    if get_connector(raw) is None and key not in (
        "leonardo",
        "kling",
        "openai / elevenlabs (stub)",
        "thumbnail (stub)",
        "render timeline (stub)",
    ):
        return ConnectorAuthContractResult(
            connector_name=raw,
            auth_status="auth_unknown",
            required_env_vars=[],
            optional_env_vars=[],
            auth_type="unknown",
            warnings=warnings + ["unregistered_connector_name"],
        )

    if key in ("leonardo",) or key == "image":
        return ConnectorAuthContractResult(
            connector_name="Leonardo",
            auth_status="auth_missing",
            required_env_vars=["LEONARDO_API_KEY"],
            optional_env_vars=[],
            auth_type="api_key",
            warnings=warnings,
        )
    if key in ("kling",) or key == "video":
        return ConnectorAuthContractResult(
            connector_name="Kling",
            auth_status="auth_missing",
            required_env_vars=["KLING_API_KEY"],
            optional_env_vars=[],
            auth_type="api_key",
            warnings=warnings,
        )
    if "voice" in key or "elevenlabs" in key or "openai" in key:
        return ConnectorAuthContractResult(
            connector_name="Voice (stub)",
            auth_status="auth_missing",
            required_env_vars=["VOICE_API_KEY"],
            optional_env_vars=["VOICE_API_ENDPOINT"],
            auth_type="api_key",
            warnings=warnings,
        )
    if "thumbnail" in key:
        return ConnectorAuthContractResult(
            connector_name="Thumbnail (stub)",
            auth_status="auth_not_required",
            required_env_vars=[],
            optional_env_vars=[],
            auth_type="none",
            warnings=[],
        )
    if "render" in key:
        return ConnectorAuthContractResult(
            connector_name="Render (stub)",
            auth_status="auth_not_required",
            required_env_vars=[],
            optional_env_vars=[],
            auth_type="none",
            warnings=[],
        )

    return ConnectorAuthContractResult(
        connector_name=raw,
        auth_status="auth_unknown",
        required_env_vars=[],
        optional_env_vars=[],
        auth_type="unknown",
        warnings=warnings + ["no_auth_rule_matched"],
    )


def build_connector_auth_contracts_result(plan: object) -> ConnectorAuthContractsResult:
    """Ein Contract-Eintrag pro Bundle-Slot (Reihenfolge wie Export-Bundle)."""
    from app.prompt_engine.schema import ProductionPromptPlan

    if not isinstance(plan, ProductionPromptPlan):
        return ConnectorAuthContractsResult(contracts=[])
    bundle = plan.provider_export_bundle_result
    if bundle is None:
        return ConnectorAuthContractsResult(contracts=[])

    packages = [
        bundle.providers.thumbnail_package,
        bundle.providers.image_package,
        bundle.providers.voice_package,
        bundle.providers.video_package,
        bundle.providers.render_package,
    ]
    seen: set[str] = set()
    out: List[ConnectorAuthContractResult] = []
    for pkg in packages:
        name = (pkg.provider_name or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(build_connector_auth_contract(name))
    return ConnectorAuthContractsResult(contracts=out)
