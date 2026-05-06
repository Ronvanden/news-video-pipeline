"""BA 11.1 — ENV-Presence für Provider (keine Werte, keine Secret-Logs)."""

from __future__ import annotations

import os
from typing import List

from app.production_connectors.schema import (
    ProviderSecretStatus,
    RuntimeSecretCheckResult,
    RuntimeSecretCheckStatus,
)


def _check_contract(contract: object) -> ProviderSecretStatus:
    name = getattr(contract, "connector_name", "") or ""
    req_vars: List[str] = list(getattr(contract, "required_env_vars", None) or [])
    warns: List[str] = []
    auth_status = getattr(contract, "auth_status", "") or ""

    if auth_status == "auth_not_required" or not req_vars:
        return ProviderSecretStatus(
            provider_name=name,
            secret_status="not_required",
            required_env_vars=req_vars,
            warnings=warns,
        )

    missing = [v for v in req_vars if not (os.getenv(v) or "").strip()]
    if missing:
        return ProviderSecretStatus(
            provider_name=name,
            secret_status="missing",
            required_env_vars=req_vars,
            warnings=warns + [f"missing_env:{','.join(missing)}"],
        )
    return ProviderSecretStatus(
        provider_name=name,
        secret_status="configured",
        required_env_vars=req_vars,
        warnings=warns,
    )


def build_runtime_secret_check(plan: object) -> RuntimeSecretCheckResult:
    warns: List[str] = []
    auth = plan.connector_auth_contracts_result
    if auth is None or not auth.contracts:
        return RuntimeSecretCheckResult(
            runtime_status="blocked",
            provider_secrets=[],
            missing_required_secrets=[],
            warnings=["connector_auth_contracts_missing"],
        )

    seen: set[str] = set()
    targets = []
    for c in auth.contracts:
        key = (c.connector_name or "").lower()
        sig = None
        if key == "leonardo" or "leonardo" in key:
            sig = "leonardo"
        elif "voice" in key:
            sig = "voice"
        if sig and sig not in seen:
            seen.add(sig)
            targets.append(c)

    if not targets:
        warns.append("no_leonardo_or_voice_contract_in_auth_bundle")

    rows: List[ProviderSecretStatus] = [_check_contract(c) for c in targets]
    missing_flat: List[str] = []
    for r in rows:
        if r.secret_status != "configured":
            for ev in r.required_env_vars:
                if ev and not (os.getenv(ev) or "").strip() and ev not in missing_flat:
                    missing_flat.append(ev)

    configured = sum(1 for r in rows if r.secret_status == "configured")
    missing_need = sum(1 for r in rows if r.secret_status == "missing")

    status: RuntimeSecretCheckStatus
    if not rows:
        status = "blocked"
    elif missing_need == 0:
        status = "ready"
    elif configured > 0 and missing_need > 0:
        status = "partial"
    else:
        status = "blocked"

    return RuntimeSecretCheckResult(
        runtime_status=status,
        provider_secrets=rows,
        missing_required_secrets=missing_flat,
        warnings=list(dict.fromkeys(warns)),
    )
