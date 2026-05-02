"""BA 14.4 — Cost vs Revenue Analyzer."""

from __future__ import annotations

from app.performance_feedback.schema import CostRevenueAnalysisResult, KpiNormalizationResult


def build_cost_revenue_analysis(plan: object, metrics: KpiNormalizationResult) -> CostRevenueAnalysisResult:
    warnings: list[str] = []
    cost_res = getattr(plan, "cost_projection_result", None)
    production_cost = float(getattr(cost_res, "total_estimated_cost_eur", 0.0) or 0.0)
    ingest = getattr(plan, "kpi_ingest_contract_result", None)
    imported = getattr(ingest, "imported_metrics", {}) or {}
    try:
        revenue = float(imported.get("revenue_optional", 0.0) or 0.0)
    except (TypeError, ValueError):
        revenue = 0.0
        warnings.append("revenue_optional_invalid")

    if production_cost <= 0:
        warnings.append("production_cost_missing_or_zero")
    if revenue <= 0:
        warnings.append("revenue_missing_or_zero")

    roi = None
    if production_cost > 0:
        roi = round((revenue - production_cost) / production_cost, 4)

    if production_cost <= 0 and revenue <= 0:
        status = "insufficient_data"
        break_even = "unknown"
    elif revenue > production_cost:
        status = "profitable"
        break_even = "above_break_even"
    elif revenue == production_cost and production_cost > 0:
        status = "break_even"
        break_even = "at_break_even"
    else:
        status = "loss"
        break_even = "below_break_even"

    notes = [
        "Revenue is optional in V1; do not automate monetization decisions.",
        f"Normalized RPM: {metrics.normalized_rpm:.2f}",
    ]

    return CostRevenueAnalysisResult(
        analysis_status=status,
        production_cost=round(production_cost, 2),
        revenue=round(revenue, 2),
        roi=roi,
        break_even_status=break_even,
        monetization_notes=notes,
        warnings=list(dict.fromkeys(warnings)),
    )
