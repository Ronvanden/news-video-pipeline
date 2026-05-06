"""BA 10.0 — Dry-Run über ProviderExportBundle (keine HTTP-Calls)."""

from __future__ import annotations

from typing import List

from app.production_connectors.registry import get_connector
from app.production_connectors.schema import (
    ConnectorExecutionResult,
    ConnectorExecutionStatus,
    ProductionConnectorSuiteResult,
    ProductionConnectorSuiteStatus,
)
from app.prompt_engine.schema import ProductionPromptPlan


def _blocked_result(
    *,
    pkg_name: str,
    role: str,
    reasons: List[str],
) -> ConnectorExecutionResult:
    return ConnectorExecutionResult(
        connector_name=pkg_name,
        provider_type=role,
        execution_status="blocked",
        normalized_request={},
        normalized_response={},
        warnings=[],
        blocking_reasons=list(reasons),
    )


def dry_run_provider_bundle(plan: ProductionPromptPlan) -> ProductionConnectorSuiteResult:
    bundle = plan.provider_export_bundle_result
    if bundle is None:
        return ProductionConnectorSuiteResult(
            suite_status="blocked",
            connector_results=[],
            summary="Kein provider_export_bundle_result — Connector-Suite nicht ausgeführt.",
            blocking_reasons=["missing_provider_export_bundle"],
            insights=["Bundle erforderlich für BA 10.0 Dry-Run."],
        )

    packages = [
        bundle.providers.image_package,
        bundle.providers.video_package,
        bundle.providers.voice_package,
        bundle.providers.thumbnail_package,
        bundle.providers.render_package,
    ]

    if bundle.bundle_status == "blocked":
        results = [
            _blocked_result(
                pkg_name=p.provider_name,
                role=p.provider_type,
                reasons=["export_bundle_blocked"],
            )
            for p in packages
        ]
        return ProductionConnectorSuiteResult(
            suite_status="blocked",
            connector_results=results,
            summary="Export-Bundle blockiert — keine Connector-Dry-Runs.",
            blocking_reasons=["bundle_status_blocked"],
            insights=list(dict.fromkeys(bundle.warnings or [])),
        )

    results: List[ConnectorExecutionResult] = []

    for pkg in packages:
        conn = get_connector(pkg.provider_type) or get_connector(pkg.provider_name)
        if conn is None:
            results.append(
                _blocked_result(
                    pkg_name=pkg.provider_name,
                    role=pkg.provider_type,
                    reasons=["connector_not_registered"],
                )
            )
            continue
        if pkg.package_status == "blocked":
            results.append(
                _blocked_result(
                    pkg_name=pkg.provider_name,
                    role=pkg.provider_type,
                    reasons=["provider_package_blocked"],
                )
            )
            continue
        res = conn.dry_run(dict(pkg.payload or {}))
        res.connector_name = pkg.provider_name
        res.provider_type = pkg.provider_type
        if pkg.package_status == "incomplete" and res.execution_status in (
            "dry_run_success",
            "dry_run_warning",
        ):
            w = list(res.warnings)
            w.append("provider_package_incomplete_flag_from_bundle")
            res = res.model_copy(update={"warnings": w, "execution_status": "dry_run_warning"})
        results.append(res)

    statuses: List[ConnectorExecutionStatus] = [r.execution_status for r in results]

    suite_status: ProductionConnectorSuiteStatus
    summary_parts: List[str] = []
    if all(s == "blocked" for s in statuses):
        suite_status = "blocked"
        summary_parts.append("Alle Slots blockiert.")
    elif "invalid_payload" in statuses:
        suite_status = "invalid_payload"
        summary_parts.append("Mindestens ein Payload ungültig.")
    elif all(s in ("dry_run_success", "dry_run_warning") for s in statuses):
        if any(s == "dry_run_warning" for s in statuses):
            suite_status = "dry_run_partial"
            summary_parts.append("Dry-Run abgeschlossen mit Warnungen.")
        else:
            suite_status = "dry_run_complete"
            summary_parts.append("Alle Connectoren Dry-Run erfolgreich.")
    else:
        suite_status = "dry_run_partial"
        summary_parts.append("Dry-Run teilweise — gemischte Slot-Status.")

    insights = [
        f"bundle_status={bundle.bundle_status}",
        f"slots_checked={len(results)}",
    ]

    return ProductionConnectorSuiteResult(
        suite_status=suite_status,
        connector_results=results,
        summary=" ".join(summary_parts).strip(),
        blocking_reasons=[],
        insights=insights,
    )
