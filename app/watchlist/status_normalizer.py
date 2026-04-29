"""BA 8.3: Status-Normalisierung (Heuristiken) — Detektion ohne Firestore-Schreibzwang."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from app.watchlist.firestore_repo import FirestoreUnavailableError, FirestoreWatchlistRepository
from app.watchlist.models import (
    PipelineEscalation,
    ProductionCosts,
    ProductionJob,
    ProviderNameLiteral,
    ScriptJob,
    StatusNormalizeRunRequest,
    StatusNormalizeRunResponse,
)


def _safe_slug(s: str, max_len: int = 64) -> str:
    raw = (s or "").strip()
    slug = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in raw)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return (slug[:max_len] if slug else "x")[:max_len]


def _parse_iso_to_utc(s: str) -> Optional[datetime]:
    if not isinstance(s, str) or not s.strip():
        return None
    raw = s.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def escalation_document_id(
    *,
    category: str,
    production_job_id: Optional[str],
    script_job_id: Optional[str],
    reason_key: str,
) -> str:
    rk = _safe_slug(reason_key, 80)
    raw = "|".join(
        [
            _safe_slug(category, 48),
            (production_job_id or "").strip(),
            (script_job_id or "").strip(),
            rk,
        ]
    )
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:22]
    cat = _safe_slug(category, 36)
    return f"esc_{cat}_{h}"


# Auftragsgleicher Alias für API-Klarheit („auto escalation IDs“).
escalate_document_id = escalation_document_id


def exponential_backoff_seconds(retry_index: int, base_seconds: int = 60) -> int:
    """Exponential Backoff: base * 2^n (n = retry_index, ab 0)."""
    n = max(0, int(retry_index))
    b = max(1, int(base_seconds))
    return b * (2**n)


def hard_fail_after_max_retries(retry_count: int, max_retries: int) -> bool:
    """Hard fail, wenn die Schritt-Zählerzahl die erlaubte Max-Wiederholung überschreitet."""
    return int(retry_count) > int(max_retries)


def require_retry_reason(reason: Optional[str]) -> str:
    """Validiert, dass ein Retry-Grund gesetzt ist (Disziplin)."""
    s = (reason or "").strip()
    if not s:
        raise ValueError("retry_reason ist erforderlich.")
    return s


@dataclass(frozen=True)
class OrphanFinding:
    kind: str
    production_job_id: Optional[str] = None
    script_job_id: Optional[str] = None
    detail: str = ""


def detect_orphaned_jobs(
    repo: FirestoreWatchlistRepository,
    *,
    production_job_limit: int,
) -> List[OrphanFinding]:
    """ProductionJob ohne referenzierten ScriptJob / generated_script oder umgekehrt keine Referenz."""
    out: List[OrphanFinding] = []
    try:
        rows = repo.list_production_jobs(limit=production_job_limit)
    except FirestoreUnavailableError:
        raise
    for pj in rows:
        sid = (pj.script_job_id or "").strip()
        if sid:
            try:
                sj = repo.get_script_job(sid)
            except FirestoreUnavailableError:
                raise
            if sj is None:
                out.append(
                    OrphanFinding(
                        kind="script_job_missing",
                        production_job_id=pj.id,
                        script_job_id=sid,
                        detail="production_jobs.script_job_id nicht in script_jobs gefunden.",
                    )
                )
        gid = (pj.generated_script_id or "").strip()
        if gid:
            try:
                gs = repo.get_generated_script(gid)
            except FirestoreUnavailableError:
                raise
            if gs is None:
                out.append(
                    OrphanFinding(
                        kind="generated_script_missing",
                        production_job_id=pj.id,
                        detail=(
                            "production_jobs.generated_script_id nicht in generated_scripts gefunden."
                        ),
                    )
                )
    return out


def _minutes_running_without_progress(sj: ScriptJob, *, now: datetime) -> float:
    st = _parse_iso_to_utc(getattr(sj, "started_at", "") or "")
    heartbeat = _parse_iso_to_utc(getattr(sj, "last_attempt_at", "") or "")
    progress_at = heartbeat or st
    if progress_at is None:
        return float("inf")
    return (now - progress_at).total_seconds() / 60.0


def detect_stuck_without_heartbeat(
    repo: FirestoreWatchlistRepository,
    *,
    stuck_running_minutes: int,
) -> List[ScriptJob]:
    """running länger als Schranke ohne erkennbaren Fortschritt (last_attempt_at/started_at)."""
    thr = max(5, min(int(stuck_running_minutes), 24 * 60))
    now = datetime.now(timezone.utc)
    out: List[ScriptJob] = []
    try:
        running = repo.list_running_script_jobs()
    except FirestoreUnavailableError:
        raise
    for sj in running:
        mins = _minutes_running_without_progress(sj, now=now)
        started = getattr(sj, "started_at", "") or ""
        lat = getattr(sj, "last_attempt_at", "") or ""
        progress_ref = lat or started
        if progress_ref.strip() == "":
            continue
        if mins >= thr:
            out.append(sj)
    return out


def detect_queued_without_progress(
    repo: FirestoreWatchlistRepository,
    *,
    queued_stall_minutes: int,
    production_job_limit: int,
) -> List[ProductionJob]:
    """queued ohne Folge-Schritte (kein scene_plan) nach Wartezeit."""
    stall = max(15, min(int(queued_stall_minutes), 48 * 60))
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=stall)
    out: List[ProductionJob] = []
    try:
        rows = repo.list_production_jobs(limit=production_job_limit)
    except FirestoreUnavailableError:
        raise
    for pj in rows:
        if (pj.status or "").strip().lower() != "queued":
            continue
        created = _parse_iso_to_utc(pj.created_at or "")
        if created is None or created > cutoff:
            continue
        try:
            sp = repo.get_scene_plan(pj.id)
        except FirestoreUnavailableError:
            raise
        if sp is None:
            out.append(pj)
    return out


def detect_partial_artifact_mismatch(
    repo: FirestoreWatchlistRepository,
    *,
    production_job_id: str,
) -> bool:
    """production_files: geplant/ready-Inkonsistenz → partial_failed taucht beim Normalizer auf."""
    pid = (production_job_id or "").strip()
    if not pid:
        return False
    try:
        files = repo.list_production_files_for_job(pid)
    except FirestoreUnavailableError:
        raise
    if not files:
        return False
    statuses = {(f.status or "").strip().lower() for f in files}
    if "failed" in statuses and "planned" in statuses:
        return True
    planned_cnt = sum(1 for f in files if (f.status or "").strip().lower() == "planned")
    ready_cnt = sum(1 for f in files if (f.status or "").strip().lower() == "ready")
    total = len(files)
    return total > 0 and ready_cnt > 0 and planned_cnt > 0 and ready_cnt + planned_cnt < total


def detect_repairable_completed_script_without_production_job(
    repo: FirestoreWatchlistRepository,
    *,
    script_job_scan_limit: int,
    production_job_scan_limit: int,
) -> List[ScriptJob]:
    """ScriptJob completed ohne zugeordneten ProductionJob."""
    try:
        sjobs = repo.list_script_jobs(limit=script_job_scan_limit)
        pjobs = repo.list_production_jobs(limit=production_job_scan_limit)
    except FirestoreUnavailableError:
        raise
    linked: Set[str] = set()
    for pj in pjobs:
        sjid = (pj.script_job_id or "").strip()
        if sjid:
            linked.add(sjid)
    out: List[ScriptJob] = []
    for sj in sjobs:
        if (sj.status or "").strip().lower() != "completed":
            continue
        if sj.id in linked:
            continue
        out.append(sj)
    return out


def _gather_provider_failure_clusters_for_job(
    repo: FirestoreWatchlistRepository,
    *,
    pj_id: str,
    threshold: int,
) -> Tuple[Optional[ProviderNameLiteral], int]:
    try:
        ex = repo.list_execution_jobs_for_job(pj_id)
    except FirestoreUnavailableError:
        raise
    by_prov: Dict[str, int] = {}
    for e in ex:
        if (e.status or "").strip().lower() != "failed":
            continue
        pn = getattr(e, "provider_name", "generic") or "generic"
        by_prov[str(pn)] = by_prov.get(str(pn), 0) + 1
    for prov, cnt in by_prov.items():
        if cnt >= threshold:
            return prov, cnt  # type: ignore[return-value]
    return None, 0


def summarize_cost_anomaly(
    costs: ProductionCosts,
    *,
    ratio: float,
) -> Tuple[bool, str]:
    est = float(getattr(costs, "estimated_total_cost", 0.0) or 0.0)
    act = float(getattr(costs, "actual_total_cost", 0.0) or 0.0)
    if est <= 0:
        return False, ""
    if act <= 0:
        return False, ""
    r = ratio if ratio >= 1.05 else 3.0
    if act > est * r:
        return True, f"actual {act:.4f} > {r:.2f}x estimated {est:.4f}"
    return False, ""


def detect_dead_after_recovery(
    *,
    recent_recovery: List[Any],
    production_job_id: str,
    min_failed: int = 2,
) -> bool:
    """Mehrere fehlgeschlagene Recovery-Aktionen zum selben Produktjob."""
    pid = (production_job_id or "").strip()
    n = 0
    for ra in recent_recovery:
        pj = (getattr(ra, "production_job_id", "") or "").strip()
        if pj != pid:
            continue
        if (getattr(ra, "status", "") or "").strip().lower() == "failed":
            n += 1
    return n >= min_failed


def normalize_pipeline_status(
    repo: FirestoreWatchlistRepository,
    *,
    opts: StatusNormalizeRunRequest,
    utc_now_iso: str,
    recent_recovery_actions: Optional[List[Any]] = None,
) -> Tuple[StatusNormalizeRunResponse, List[PipelineEscalation]]:
    """Detektiert Schieflagen und wendet bei ``dry_run=false`` Status-Patches sowie Eskalationen an."""
    req = opts
    log: List[str] = []
    esc: List[PipelineEscalation] = []

    orphans = detect_orphaned_jobs(
        repo, production_job_limit=req.production_job_scan_limit
    )
    orphaned_n = len(orphans)

    stuck_jobs = detect_stuck_without_heartbeat(
        repo, stuck_running_minutes=req.stuck_running_minutes
    )
    queued_stall = detect_queued_without_progress(
        repo,
        queued_stall_minutes=req.queued_stall_minutes,
        production_job_limit=req.production_job_scan_limit,
    )

    repairable = detect_repairable_completed_script_without_production_job(
        repo,
        script_job_scan_limit=req.script_job_scan_limit,
        production_job_scan_limit=req.production_job_scan_limit,
    )

    recovery_list = recent_recovery_actions or []

    normalized_stuck = 0
    marked_queued = 0
    partial_marked = 0
    esc_repairable = 0
    esc_upserts = 0
    hard_fail = 0

    try:
        rreason = require_retry_reason(req.retry_reason)
    except ValueError as e:
        return (
            StatusNormalizeRunResponse(warnings=[str(e)]),
            [],
        )

    pj_cache: Dict[str, Optional[ProductionJob]] = {}

    def _get_pj(pid: str) -> Optional[ProductionJob]:
        key = pid.strip()
        if key in pj_cache:
            return pj_cache[key]
        try:
            pj_cache[key] = repo.get_production_job(key)
        except FirestoreUnavailableError:
            raise
        return pj_cache[key]

    for o in orphans:
        rr = int(req.max_step_retries)
        eid = escalation_document_id(
            category="repairable_gap",
            production_job_id=o.production_job_id,
            script_job_id=o.script_job_id,
            reason_key=o.kind + "|" + (o.detail or "")[:40],
        )
        pj = None
        if o.production_job_id:
            pj = _get_pj(o.production_job_id)
        retries = (
            pj.pipeline_step_retry_counts.get("normalize", 0) if pj is not None else 0
        )
        severity = "critical" if hard_fail_after_max_retries(retries, rr) else "high"
        cat = (
            "repairable_gap"
            if o.kind in ("script_job_missing", "generated_script_missing")
            else "repeated_failure"
        )
        esc.append(
            PipelineEscalation(
                escalation_id=eid,
                production_job_id=o.production_job_id,
                script_job_id=o.script_job_id,
                severity=severity,
                category=cat,
                reason=o.detail or o.kind,
                retry_count=retries,
                provider_flag=None,
                created_at=utc_now_iso,
            )
        )
        log.append(f"orphan_escalate:{o.kind}:{o.production_job_id or ''}")

    # --- stuck script_jobs → stuck
    for sj in stuck_jobs:
        step_key = "stuck_normalize"
        try:
            pj_ref = sj.id
            prev = getattr(sj, "pipeline_step_retry_counts", {}) or {}
            cnt = int(prev.get(step_key, 0)) + 1
            backoff = exponential_backoff_seconds(cnt - 1)
            if hard_fail_after_max_retries(cnt, req.max_step_retries):
                if not req.dry_run:
                    repo.patch_script_job(
                        sj.id,
                        {
                            "status": "failed",
                            "completed_at": utc_now_iso,
                            "error_code": "norm_hard_fail_retries",
                            "error": (
                                f"Nach {req.max_step_retries} Normalisierungsschritten: "
                                f"running ohne Fortschritt ({rreason})"
                            ),
                            "pipeline_step_retry_counts": {**prev, step_key: cnt},
                            "normalize_backoff_hint_seconds": backoff,
                        },
                    )
                hard_fail += 1
                log.append(f"script_hard_fail:{sj.id}")
            else:
                if not req.dry_run:
                    repo.patch_script_job(
                        sj.id,
                        {
                            "status": "stuck",
                            "error_code": "norm_running_stuck",
                            "error": f"Heartbeat/Fortschritt ausgeblieben ({rreason})",
                            "pipeline_step_retry_counts": {**prev, step_key: cnt},
                            "normalize_backoff_hint_seconds": backoff,
                        },
                    )
                normalized_stuck += 1
                log.append(f"script_stuck:{sj.id}:{backoff}s")
        except FirestoreUnavailableError:
            raise

    # --- queued production → retryable
    for pj in queued_stall:
        step_key = "queued_normalize"
        prev = pj.pipeline_step_retry_counts or {}
        cnt = int(prev.get(step_key, 0)) + 1
        if hard_fail_after_max_retries(cnt, req.max_step_retries):
            if not req.dry_run:
                repo.patch_production_job(
                    pj.id,
                    {
                        "status": "failed",
                        "error_code": "norm_queued_hard_fail",
                        "error": f"queued ohne scene_plan über Limit ({rreason})",
                        "pipeline_step_retry_counts": {**prev, step_key: cnt},
                        "updated_at": utc_now_iso,
                    },
                )
            hard_fail += 1
            eid = escalation_document_id(
                category="repeated_failure",
                production_job_id=pj.id,
                script_job_id=pj.script_job_id,
                reason_key="queued_stall|" + pj.id,
            )
            esc.append(
                PipelineEscalation(
                    escalation_id=eid,
                    production_job_id=pj.id,
                    script_job_id=pj.script_job_id,
                    severity="high",
                    category="repeated_failure",
                    reason="queued ohne Fortschritt: max retries erreicht",
                    retry_count=cnt,
                    provider_flag=None,
                    created_at=utc_now_iso,
                )
            )
        else:
            if not req.dry_run:
                repo.patch_production_job(
                    pj.id,
                    {
                        "status": "retryable",
                        "error_code": "norm_queued_retryable",
                        "error": f"queued ohne scene_plan; retry mit Backoff ({rreason})",
                        "pipeline_step_retry_counts": {**prev, step_key: cnt},
                        "normalize_backoff_hint_seconds": exponential_backoff_seconds(
                            cnt - 1
                        ),
                        "updated_at": utc_now_iso,
                    },
                )
            marked_queued += 1
            log.append(f"p_j_retryable:{pj.id}")

    # --- partial_failed per production_job with files mismatch
    try:
        pjobs = repo.list_production_jobs(limit=req.production_job_scan_limit)
    except FirestoreUnavailableError:
        raise
    for pj in pjobs:
        if detect_partial_artifact_mismatch(repo, production_job_id=pj.id):
            if not req.dry_run:
                repo.patch_production_job(
                    pj.id,
                    {
                        "status": "partial_failed",
                        "error_code": "norm_partial_artifacts",
                        "error": f"production_files heterogen/fehlte Teile ({rreason})",
                        "updated_at": utc_now_iso,
                    },
                )
            partial_marked += 1
            log.append(f"partial_failed:{pj.id}")

    esc2: List[PipelineEscalation] = []
    for pj in pjobs:
        prov, nfail = _gather_provider_failure_clusters_for_job(
            repo,
            pj_id=pj.id,
            threshold=int(req.provider_failed_cluster_threshold),
        )
        if prov is not None and nfail >= int(req.provider_failed_cluster_threshold):
            eid = escalation_document_id(
                category="provider_failure_cluster",
                production_job_id=pj.id,
                script_job_id=pj.script_job_id,
                reason_key=f"provider|{prov}|{nfail}",
            )
            esc2.append(
                PipelineEscalation(
                    escalation_id=eid,
                    production_job_id=pj.id,
                    script_job_id=pj.script_job_id,
                    severity="high",
                    category="provider_failure_cluster",
                    reason=(
                        f"Cluster: >= {req.provider_failed_cluster_threshold} ExecutionJob-Fehler bei "
                        f"Provider {prov}"
                    ),
                    retry_count=nfail,
                    provider_flag=str(prov),
                    created_at=utc_now_iso,
                )
            )
        try:
            pc = repo.get_production_costs(pj.id)
        except FirestoreUnavailableError:
            raise
        if pc is not None:
            bad, txt = summarize_cost_anomaly(pc, ratio=float(req.cost_anomaly_ratio))
            if bad:
                eid = escalation_document_id(
                    category="cost_anomaly",
                    production_job_id=pj.id,
                    script_job_id=pj.script_job_id,
                    reason_key="cost|" + pj.id,
                )
                esc2.append(
                    PipelineEscalation(
                        escalation_id=eid,
                        production_job_id=pj.id,
                        script_job_id=pj.script_job_id,
                        severity="critical",
                        category="cost_anomaly",
                        reason=txt or "cost anomaly",
                        retry_count=0,
                        provider_flag=None,
                        created_at=utc_now_iso,
                    )
                )
        if recovery_list:
            pid = pj.id.strip()
            if detect_dead_after_recovery(
                recent_recovery=recovery_list, production_job_id=pid
            ):
                eid = escalation_document_id(
                    category="dead_after_recovery",
                    production_job_id=pj.id,
                    script_job_id=pj.script_job_id,
                    reason_key="recovery_fail|" + pj.id,
                )
                esc2.append(
                    PipelineEscalation(
                        escalation_id=eid,
                        production_job_id=pj.id,
                        script_job_id=pj.script_job_id,
                        severity="critical",
                        category="dead_after_recovery",
                        reason=(
                            "Wiederholte fehlgeschlagene Recovery-Schritte — manuelle Intervention."
                        ),
                        retry_count=2,
                        provider_flag=None,
                        created_at=utc_now_iso,
                    )
                )

    # --- repairable_gap escalations für completed Scripts ohne Produktion
    for sj in repairable:
        eid = escalation_document_id(
            category="repairable_gap",
            production_job_id=None,
            script_job_id=sj.id,
            reason_key="no_production|" + sj.id,
        )
        esc.append(
            PipelineEscalation(
                escalation_id=eid,
                production_job_id=None,
                script_job_id=sj.id,
                severity="medium",
                category="repairable_gap",
                reason="completed Script ohne passenden production_jobs-Eintrag",
                retry_count=0,
                provider_flag=None,
                created_at=utc_now_iso,
            )
        )
        esc_repairable += 1
        log.append(f"esc_repairable_gap:{sj.id}")

    esc.extend(esc2)

    if not req.dry_run:
        for row in esc:
            repo.upsert_pipeline_escalation(row)
            esc_upserts += 1

    warnings: List[str] = []
    if req.dry_run:
        warnings.append(
            "dry_run: keine Schreibupdates (Patches und Eskalationen wurden nur gezählt)."
        )

    resp = StatusNormalizeRunResponse(
        orphaned_detected=orphaned_n,
        stuck_normalized=normalized_stuck,
        queued_retryable_marked=marked_queued,
        partial_failed_marked=partial_marked,
        repairable_gap_escalations=esc_repairable,
        escalations_upserted=esc_upserts,
        hard_fails_retry_cap=hard_fail,
        actions_log=log,
        warnings=warnings,
    )
    return resp, esc
