"""BA 14.0 — KPI Ingest Contract."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.performance_feedback.schema import KpiIngestContractResult, KpiSourceType

CORE_METRICS = [
    "views",
    "impressions",
    "ctr",
    "avg_view_duration",
    "watch_time",
    "subscribers_gained",
    "revenue_optional",
]


def _coerce_metrics(raw: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    aliases = {
        "average_view_duration": "avg_view_duration",
        "watch_time_minutes": "watch_time",
        "revenue": "revenue_optional",
        "estimated_revenue": "revenue_optional",
    }
    for key, value in raw.items():
        canonical = aliases.get(key, key)
        if canonical in CORE_METRICS:
            out[canonical] = value
    return out


def build_kpi_ingest_contract(
    plan: object,
    external_metrics: Optional[Dict[str, Any]] = None,
    source_type: Optional[KpiSourceType] = None,
) -> KpiIngestContractResult:
    """Importiert manuelle/CSV/API-Stub-KPIs als Contract, ohne Live-Abfrage."""
    warnings: list[str] = []
    raw = external_metrics
    if raw is None:
        raw = dict(getattr(plan, "external_kpi_metrics", {}) or {})
    src: KpiSourceType = source_type or getattr(plan, "kpi_source_type", "unknown") or "unknown"

    imported = _coerce_metrics(raw)
    missing = [metric for metric in CORE_METRICS if metric not in imported]
    if src == "youtube_api_stub":
        warnings.append("youtube_api_stub_no_live_fetch")
    if src == "csv":
        warnings.append("csv_import_contract_only_no_file_io")
    if not imported:
        warnings.append("no_kpi_metrics_imported")

    if not imported:
        status = "missing"
    elif missing:
        status = "partial"
    else:
        status = "ready"

    return KpiIngestContractResult(
        ingest_status=status,
        source_type=src,
        imported_metrics=imported,
        missing_metrics=missing,
        warnings=list(dict.fromkeys(warnings)),
    )
