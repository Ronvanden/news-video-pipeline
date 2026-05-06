"""BA 11.5 — Recovery-Empfehlung aus Live-Connector-Ergebnissen."""

from __future__ import annotations

from typing import List, Optional, Tuple

from app.production_connectors.schema import (
    LiveConnectorExecutionResult,
    ProviderErrorClassification,
    ProviderErrorRecoveryResult,
    ProviderRecoveryStatus,
)


def _is_timeout(res: LiveConnectorExecutionResult) -> bool:
    joined = " ".join(res.warnings).lower()
    return "url_error" in joined or "timeout" in joined


def build_provider_error_recovery(plan: object) -> ProviderErrorRecoveryResult:
    notes: List[str] = []
    leo: Optional[LiveConnectorExecutionResult] = getattr(plan, "leonardo_live_result", None)
    vo: Optional[LiveConnectorExecutionResult] = getattr(plan, "voice_live_result", None)

    rows: List[Tuple[str, LiveConnectorExecutionResult]] = []
    if leo:
        rows.append(("Leonardo", leo))
    if vo:
        rows.append(("Voice", vo))

    if not rows:
        return ProviderErrorRecoveryResult(
            recovery_status="no_action",
            retry_recommended=False,
            fallback_provider="",
            recovery_notes=["no_live_connector_results"],
            error_classification="unknown",
        )

    def worst() -> ProviderErrorRecoveryResult:
        # Priorität: payload-block > auth-block > timeout-retry > provider-fallback > dry_run ok
        for label, res in rows:
            if res.execution_mode == "blocked":
                return ProviderErrorRecoveryResult(
                    recovery_status="blocked",
                    retry_recommended=False,
                    fallback_provider="",
                    recovery_notes=notes + [f"{label}:payload_blocked"],
                    error_classification="payload",
                )
        for label, res in rows:
            if res.http_status_code in (401, 403):
                return ProviderErrorRecoveryResult(
                    recovery_status="blocked",
                    retry_recommended=False,
                    fallback_provider="",
                    recovery_notes=notes + [f"{label}:auth_http_{res.http_status_code}"],
                    error_classification="auth",
                )
        for label, res in rows:
            if _is_timeout(res):
                return ProviderErrorRecoveryResult(
                    recovery_status="retry_available",
                    retry_recommended=True,
                    fallback_provider="",
                    recovery_notes=notes + [f"{label}:timeout_retry_recommended"],
                    error_classification="timeout",
                )
        for label, res in rows:
            if res.execution_mode == "live_attempt" and (
                res.normalized_asset is None or (res.http_status_code or 0) >= 400
            ):
                return ProviderErrorRecoveryResult(
                    recovery_status="fallback_to_dry_run",
                    retry_recommended=False,
                    fallback_provider=label,
                    recovery_notes=notes + [f"{label}:live_provider_error_use_dry_run"],
                    error_classification="provider",
                )
        if all(res.execution_mode == "dry_run" for _, res in rows):
            for label, res in rows:
                notes.append(f"{label}:dry_run_ok")
            return ProviderErrorRecoveryResult(
                recovery_status="no_action",
                retry_recommended=False,
                fallback_provider="",
                recovery_notes=notes,
                error_classification="unknown",
            )
        return ProviderErrorRecoveryResult(
            recovery_status="no_action",
            retry_recommended=False,
            fallback_provider="",
            recovery_notes=notes or ["no_recovery_rule_matched"],
            error_classification="unknown",
        )

    return worst()
