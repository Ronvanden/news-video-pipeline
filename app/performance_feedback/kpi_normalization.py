"""BA 14.1 — YouTube KPI Normalization."""

from __future__ import annotations

from typing import Any, Dict

from app.performance_feedback.schema import KpiNormalizationResult


def _num(raw: Dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        value = raw.get(key, default)
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_kpi_metrics(raw_metrics: Dict[str, Any]) -> KpiNormalizationResult:
    warnings: list[str] = []
    views = _num(raw_metrics, "views")
    impressions = _num(raw_metrics, "impressions")
    ctr = _num(raw_metrics, "ctr")
    watch_time = _num(raw_metrics, "watch_time")
    avg_view_duration = _num(raw_metrics, "avg_view_duration")
    subscribers = _num(raw_metrics, "subscribers_gained")
    revenue = _num(raw_metrics, "revenue_optional")

    if ctr > 1.0:
        ctr = ctr / 100.0
    if ctr == 0.0 and impressions > 0 and views > 0:
        ctr = views / impressions
        warnings.append("ctr_derived_from_views_impressions")

    retention = 0.0
    if avg_view_duration > 0:
        retention = min(1.0, avg_view_duration / 600.0)
    elif watch_time > 0 and views > 0:
        retention = min(1.0, (watch_time * 60.0 / views) / 600.0)
        warnings.append("retention_derived_from_watch_time")

    rpm = (revenue / views * 1000.0) if views > 0 and revenue > 0 else 0.0
    growth = subscribers / views if views > 0 and subscribers > 0 else 0.0

    present = sum(1 for key in ("views", "impressions", "ctr", "avg_view_duration", "watch_time", "subscribers_gained") if key in raw_metrics)
    if present >= 5:
        status = "ready"
    elif present > 0:
        status = "partial"
    else:
        status = "insufficient_data"
        warnings.append("no_normalizable_kpi_metrics")

    return KpiNormalizationResult(
        normalized_status=status,
        normalized_ctr=round(max(0.0, ctr), 4),
        normalized_retention=round(max(0.0, retention), 4),
        normalized_rpm=round(rpm, 4),
        normalized_growth=round(growth, 6),
        warnings=list(dict.fromkeys(warnings)),
    )
