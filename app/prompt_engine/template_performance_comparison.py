"""BA 9.26 — Template-Vergleich aus PerformanceRecords (read-only, keine APIs)."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from app.prompt_engine.performance_learning import evaluate_performance_snapshot
from app.prompt_engine.schema import (
    PerformanceRecord,
    TemplatePerformanceComparisonResult,
    TemplatePerformanceEntry,
)


def _overall_score(avg_q: float, avg_n: float, avg_l: float, has_learning: bool) -> float:
    if has_learning:
        return round(0.35 * avg_q + 0.35 * avg_n + 0.30 * avg_l, 2)
    return round(0.5 * avg_q + 0.5 * avg_n, 2)


def _entry_strengths_weaknesses(
    avg_q: float, avg_n: float, avg_l: float, has_learning: bool
) -> tuple[List[str], List[str]]:
    strengths: List[str] = []
    weaknesses: List[str] = []
    if avg_q >= 75:
        strengths.append("Strukturelle Qualität über Durchschnitt.")
    elif avg_q < 55:
        weaknesses.append("Qualitätsscores unter Zielkorridor.")
    if avg_n >= 75:
        strengths.append("Narrative Scores stabil hoch.")
    elif avg_n < 55:
        weaknesses.append("Narrative Scores schwach — Template prüfen.")
    if has_learning:
        if avg_l >= 60:
            strengths.append("Lern-/KPI-Signal nutzbar.")
        elif avg_l < 35:
            weaknesses.append("Wenig belastbare KPI-/Learning-Daten.")
    else:
        weaknesses.append("Kein Learning-Score (KPIs fehlen größtenteils).")
    return strengths, weaknesses


def compare_template_performance(records: List[PerformanceRecord]) -> TemplatePerformanceComparisonResult:
    insights: List[str] = []
    if not records:
        insights.append("Keine PerformanceRecords übergeben — Vergleich ausgesetzt (V1).")
        return TemplatePerformanceComparisonResult(
            comparison_status="insufficient_data",
            best_template_type=None,
            templates=[],
            insights=insights,
        )

    buckets: Dict[str, List[PerformanceRecord]] = defaultdict(list)
    for r in records:
        key = (r.template_type or "").strip() or "unknown"
        buckets[key].append(r)

    entries: List[TemplatePerformanceEntry] = []
    for tt in sorted(buckets.keys()):
        items = buckets[tt]
        qs = [float(r.quality_score) for r in items if r.quality_score is not None]
        ns = [float(r.narrative_score) for r in items if r.narrative_score is not None]
        learns: List[float] = []
        for r in items:
            snap = evaluate_performance_snapshot(r)
            if snap.learning_score is not None:
                learns.append(float(snap.learning_score))
        avg_q = sum(qs) / len(qs) if qs else 0.0
        avg_n = sum(ns) / len(ns) if ns else 0.0
        avg_l = sum(learns) / len(learns) if learns else 0.0
        has_learning = bool(learns)
        overall = _overall_score(avg_q, avg_n, avg_l, has_learning)
        st, we = _entry_strengths_weaknesses(avg_q, avg_n, avg_l, has_learning)
        entries.append(
            TemplatePerformanceEntry(
                template_type=tt,
                total_records=len(items),
                avg_quality_score=round(avg_q, 2),
                avg_narrative_score=round(avg_n, 2),
                avg_learning_score=round(avg_l, 2),
                overall_template_score=overall,
                strengths=st,
                weaknesses=we,
            )
        )

    entries.sort(key=lambda e: (-e.overall_template_score, e.template_type))
    best: Optional[str] = entries[0].template_type if entries else None
    if len(entries) > 1:
        insights.append(
            f"Stärkstes Template nach kombiniertem Score: {best} "
            f"(V1-Gewichtung Qualität/Narrativ/Learning)."
        )
    elif len(entries) == 1:
        insights.append("Nur ein Template-Typ in den Daten — Vergleich begrenzt aussagekräftig.")
    if any(e.total_records < 2 for e in entries):
        insights.append("Einige Templates haben wenige Records — Mittelwerte mit Vorsicht interpretieren.")

    return TemplatePerformanceComparisonResult(
        comparison_status="ready",
        best_template_type=best,
        templates=entries,
        insights=insights,
    )
