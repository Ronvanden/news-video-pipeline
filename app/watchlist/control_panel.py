"""BA 8.4 LIGHT — Founder Control Panel: read-only Aggregation über Firestore (keine Heavy-Logik)."""

from __future__ import annotations

from collections import Counter
from typing import List, Optional

from app.watchlist.firestore_repo import FirestoreWatchlistRepository
from app.watchlist.models import (
    ControlPanelAuditSummary,
    ControlPanelCostSummary,
    ControlPanelEscalationSummary,
    ControlPanelJobStatusSummary,
    ControlPanelProblemItem,
    ControlPanelProviderSummary,
    ControlPanelRecentProblemsSummary,
    ControlPanelRecoverySummary,
    ControlPanelSummaryResponse,
    PipelineAudit,
    PipelineEscalation,
    ProductionJob,
    RecoveryAction,
)

_SCRIPT_JOB_STATUSES = (
    "pending",
    "running",
    "completed",
    "failed",
    "skipped",
    "stuck",
)

_PRODUCTION_PROBLEM_STATUSES = frozenset(
    {"failed", "stuck", "retryable", "partial_failed"}
)
_SCRIPT_PROBLEM_STATUSES = frozenset({"failed", "stuck"})


def get_pipeline_health_summary(
    audits: List[PipelineAudit],
) -> ControlPanelAuditSummary:
    oc = ow = oi = 0
    for a in audits:
        if getattr(a, "status", "") != "open":
            continue
        se = (getattr(a, "severity", "") or "").lower()
        if se == "critical":
            oc += 1
        elif se == "warning":
            ow += 1
        elif se == "info":
            oi += 1
    return ControlPanelAuditSummary(
        open_critical=oc,
        open_warning=ow,
        open_info=oi,
    )


def get_escalation_summary(
    rows: List[PipelineEscalation],
    *,
    recent_limit: int = 40,
) -> ControlPanelEscalationSummary:
    by_sev: Counter[str] = Counter()
    by_cat: Counter[str] = Counter()
    for r in rows:
        by_sev[(r.severity or "").strip() or "unknown"] += 1
        by_cat[(r.category or "").strip() or "unknown"] += 1
    recent = rows[: max(0, int(recent_limit))]
    return ControlPanelEscalationSummary(
        recent_escalations=recent,
        count_by_severity=dict(by_sev),
        count_by_category=dict(by_cat),
    )


def get_recovery_summary(
    actions: List[RecoveryAction],
) -> ControlPanelRecoverySummary:
    return ControlPanelRecoverySummary(recent_actions=list(actions))


def get_job_status_summary(
    repo: FirestoreWatchlistRepository,
    *,
    production_jobs: Optional[List[ProductionJob]] = None,
    production_sample_limit: int = 600,
    warnings_out: Optional[List[str]] = None,
) -> ControlPanelJobStatusSummary:
    ws = warnings_out
    cap = max(1, min(int(production_sample_limit), 1200))
    if production_jobs is None:
        p_jobs = repo.stream_production_jobs_for_summary(cap)
    else:
        p_jobs = production_jobs
    prod_counts: Counter[str] = Counter()
    for j in p_jobs:
        prod_counts[(j.status or "").strip() or "unknown"] += 1
    if len(p_jobs) >= cap and ws is not None:
        ws.append(
            "production_jobs status aggregation may be truncated (sample cap reached)."
        )

    script_by_status: dict[str, int] = {}
    for st in _SCRIPT_JOB_STATUSES:
        n = repo.count_script_jobs_by_status(st)
        if n < 0:
            if ws is not None:
                ws.append(f"script_jobs count unavailable for status={st} (fallback).")
            n = 0
        script_by_status[st] = n

    return ControlPanelJobStatusSummary(
        production_jobs_by_status=dict(prod_counts),
        script_jobs_by_status=script_by_status,
        production_jobs_sampled=len(p_jobs),
    )


def get_provider_summary(
    configs: List,
) -> ControlPanelProviderSummary:
    total = len(configs)
    enabled = sum(1 for c in configs if getattr(c, "enabled", False))
    dry_run_true = sum(1 for c in configs if getattr(c, "dry_run", False))
    status_error = sum(
        1 for c in configs if (getattr(c, "status", "") or "") == "error"
    )
    return ControlPanelProviderSummary(
        total_configs=total,
        enabled=enabled,
        disabled=max(0, total - enabled),
        dry_run_true=dry_run_true,
        status_error=status_error,
    )


def get_cost_summary(
    cost_rows: List,
    escalations: List[PipelineEscalation],
) -> ControlPanelCostSummary:
    anomaly_n = sum(
        1 for e in escalations if (e.category or "") == "cost_anomaly"
    )
    with_warn = sum(1 for c in cost_rows if getattr(c, "warnings", None))
    est = sum(float(getattr(c, "estimated_total_cost", 0.0) or 0.0) for c in cost_rows)
    return ControlPanelCostSummary(
        cost_records_count=len(cost_rows),
        estimated_total_eur=round(est, 6),
        cost_anomaly_escalations=anomaly_n,
        cost_records_with_warnings=with_warn,
    )


def get_recent_failure_summary(
    production_jobs: List[ProductionJob],
    script_jobs_sample: List,
    *,
    max_items: int = 28,
) -> ControlPanelRecentProblemsSummary:
    items: List[ControlPanelProblemItem] = []
    for j in production_jobs:
        st = (j.status or "").strip()
        if st not in _PRODUCTION_PROBLEM_STATUSES:
            continue
        detail = (j.error_code or j.error or "").strip()
        if len(detail) > 240:
            detail = detail[:237] + "..."
        items.append(
            ControlPanelProblemItem(
                kind="production_job",
                job_id=j.id,
                status=st,
                detail=detail,
            )
        )
    for j in script_jobs_sample:
        st = (getattr(j, "status", None) or "").strip()
        if st not in _SCRIPT_PROBLEM_STATUSES:
            continue
        jid = getattr(j, "id", None) or getattr(j, "video_id", "")
        detail = (
            (getattr(j, "error_code", None) or getattr(j, "error", None) or "")
        ).strip()
        if len(detail) > 240:
            detail = detail[:237] + "..."
        items.append(
            ControlPanelProblemItem(
                kind="script_job",
                job_id=str(jid),
                status=st,
                detail=detail,
            )
        )
    return ControlPanelRecentProblemsSummary(items=items[: max(1, int(max_items))])


def build_control_panel_summary(
    *,
    repo: FirestoreWatchlistRepository,
) -> ControlPanelSummaryResponse:
    warnings: List[str] = []

    audits = repo.stream_pipeline_audits_recent(limit=1500)
    audit_summary = get_pipeline_health_summary(audits)

    esc_rows = repo.stream_pipeline_escalations_recent(limit=220)
    esc_summary = get_escalation_summary(esc_rows, recent_limit=40)

    recovery_actions = repo.stream_recovery_actions_recent(limit=35)
    recovery_summary = get_recovery_summary(recovery_actions)

    p_jobs_sample = repo.stream_production_jobs_for_summary(600)
    job_summary = get_job_status_summary(
        repo,
        production_jobs=p_jobs_sample,
        production_sample_limit=600,
        warnings_out=warnings,
    )
    sj_sample = repo.list_script_jobs(limit=150)

    provider_summary = get_provider_summary(repo.list_provider_configs())

    cost_rows = repo.stream_production_costs_recent(400)
    cost_summary = get_cost_summary(cost_rows, esc_rows)

    recent = get_recent_failure_summary(p_jobs_sample, sj_sample)

    return ControlPanelSummaryResponse(
        audit=audit_summary,
        escalation=esc_summary,
        recovery=recovery_summary,
        jobs=job_summary,
        providers=provider_summary,
        costs=cost_summary,
        recent_problems=recent,
        warnings=list(warnings),
    )
