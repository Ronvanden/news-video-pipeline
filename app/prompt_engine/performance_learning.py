"""BA 9.13 — Performance Learning Loop V1: Modelle bauen, Snapshots auswerten, Templates aggregieren.

Keine YouTube-API, keine Firestore-Writes in V1 — nur strukturierte Vorbereitung für spätere KPIs.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.prompt_engine.schema import (
    PerformanceRecord,
    PerformanceSnapshotResult,
    ProductionPromptPlan,
    TemplatePerformanceSummary,
)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_performance_record_from_prompt_plan(
    plan: ProductionPromptPlan,
    *,
    production_job_id: str = "",
    script_job_id: Optional[str] = None,
    video_id: Optional[str] = None,
    record_id: Optional[str] = None,
    now_iso: Optional[str] = None,
) -> PerformanceRecord:
    """
    Erzeugt einen ``PerformanceRecord``-Entwurf aus Plan + BA 9.11/9.12-Ergebnissen.

    KPI-Felder bleiben leer bis echte Produktions-/Plattform-Daten eingespielt werden.
    """
    ts = now_iso or _utc_iso()
    rid = (record_id or "").strip() or uuid.uuid4().hex
    q = plan.quality_result
    n = plan.narrative_score_result

    sj = (script_job_id or "").strip() or None
    vid = (video_id or "").strip() or None

    na = (plan.narrative_archetype_id or "").strip() or None
    ht = (plan.hook_type or "").strip() or None

    return PerformanceRecord(
        id=rid,
        production_job_id=(production_job_id or "").strip(),
        script_job_id=sj,
        video_id=vid,
        template_type=(plan.template_type or "").strip(),
        video_template=(plan.video_template or "").strip() or None,
        narrative_archetype_id=na,
        hook_type=ht,
        hook_score=float(plan.hook_score),
        quality_score=q.score if q else None,
        quality_status=q.status if q else None,
        narrative_score=n.score if n else None,
        narrative_status=n.status if n else None,
        created_at=ts,
        updated_at=ts,
    )


def _has_positive(v: Optional[float]) -> bool:
    return v is not None and float(v) > 0


def _ctr_component(ctr: float) -> float:
    """CTR sowohl als Anteil (0–1) als auch als Prozent (0–100) tolerieren."""
    c = float(ctr)
    if c <= 1.0:
        return min(100.0, max(0.0, c * 400.0))
    return min(100.0, max(0.0, c * 4.0))


def _learning_score_ready(record: PerformanceRecord) -> float:
    v = max(0.0, float(record.views or 0.0))
    view_part = min(100.0, (math.log1p(v) / math.log1p(1_000_000.0)) * 100.0)
    ctr_part = _ctr_component(float(record.ctr or 0.0)) if record.ctr is not None else 0.0
    return round(min(100.0, 0.45 * ctr_part + 0.55 * view_part), 2)


def evaluate_performance_snapshot(record: PerformanceRecord) -> PerformanceSnapshotResult:
    """
    V1: Ohne echte KPIs → ``pending_data``.
    Mit Kernsignalen (Views + CTR + Watch/Retention) → ``ready`` + grober ``learning_score``.
    """
    notes: List[str] = []

    has_impr = _has_positive(record.impressions)
    has_views = _has_positive(record.views)
    has_ctr = record.ctr is not None
    has_watch = (
        _has_positive(record.average_view_duration)
        or _has_positive(record.watch_time_minutes)
        or (record.retention_percent is not None)
    )
    has_rev_side = any(
        x is not None
        for x in (
            record.rpm,
            record.estimated_revenue,
            record.production_cost_estimate,
            record.profit_estimate,
        )
    )

    any_kpi = any([has_impr, has_views, has_ctr, has_watch, has_rev_side])

    if not any_kpi:
        notes.append(
            "Keine KPI-Felder gesetzt — Auswertung wartet auf Produktions-/YouTube-Daten (V1)."
        )
        return PerformanceSnapshotResult(status="pending_data", learning_score=None, notes=notes)

    if has_views and has_ctr and has_watch:
        score = _learning_score_ready(record)
        notes.append("Kern-KPIs (Views, CTR, Watch/Retention) vorhanden — V1-Learning-Score berechnet.")
        return PerformanceSnapshotResult(status="ready", learning_score=score, notes=notes)

    notes.append("Teil-KPIs vorhanden — vollständige Lernbewertung noch nicht möglich (V1).")
    return PerformanceSnapshotResult(status="partial_data", learning_score=None, notes=notes)


def summarize_template_performance(
    records: List[PerformanceRecord],
) -> List[TemplatePerformanceSummary]:
    """Gruppiert nach ``template_type``; Mittelwerte nur wo Daten vorliegen."""
    buckets: Dict[str, List[PerformanceRecord]] = {}
    for r in records:
        key = (r.template_type or "").strip() or "unknown"
        buckets.setdefault(key, []).append(r)

    summaries: List[TemplatePerformanceSummary] = []
    for tt in sorted(buckets.keys()):
        items = buckets[tt]
        qs = [r.quality_score for r in items if r.quality_score is not None]
        ns = [r.narrative_score for r in items if r.narrative_score is not None]
        pending = 0
        learns: List[float] = []
        for r in items:
            snap = evaluate_performance_snapshot(r)
            if snap.status == "pending_data":
                pending += 1
            if snap.learning_score is not None:
                learns.append(snap.learning_score)
        summaries.append(
            TemplatePerformanceSummary(
                template_type=tt,
                record_count=len(items),
                avg_quality_score=(sum(qs) / len(qs)) if qs else None,
                avg_narrative_score=(sum(ns) / len(ns)) if ns else None,
                pending_kpi_count=pending,
                avg_learning_score=(sum(learns) / len(learns)) if learns else None,
            )
        )
    return summaries
