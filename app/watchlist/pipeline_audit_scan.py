"""BA 8.0: Heuristisches Pipeline-Audit (Firestore-Reads) — ermittelt Befunde, keine Auto-Fixes."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.watchlist.firestore_repo import FirestoreUnavailableError, FirestoreWatchlistRepository
from app.watchlist.models import PipelineAuditDraft


def _safe_slug(s: str, max_len: int = 64) -> str:
    raw = (s or "").strip()
    slug = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in raw)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return (slug[:max_len] if slug else "x")[:max_len]


def audit_document_id(
    *,
    audit_type: str,
    production_job_id: Optional[str],
    script_job_id: Optional[str],
    extra_slug: Optional[str] = None,
) -> str:
    t = _safe_slug(audit_type.replace(".", "_"), 48)
    if script_job_id and not (production_job_id or "").strip():
        sj = _safe_slug(script_job_id, 72)
        ex = ("_" + _safe_slug(extra_slug, 32)) if extra_slug else ""
        return f"aud_sj_{sj}_{t}{ex}"
    pj = _safe_slug(production_job_id or "", 72)
    ex = ("_" + _safe_slug(extra_slug, 24)) if extra_slug else ""
    return f"aud_pj_{pj}_{t}{ex}"


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


def scan_stuck_running_script_issues(
    repo: FirestoreWatchlistRepository,
    *,
    threshold_minutes: int,
) -> List[PipelineAuditDraft]:
    thr = max(5, min(int(threshold_minutes), 24 * 60))
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=thr)
    out: List[PipelineAuditDraft] = []
    try:
        running = repo.list_running_script_jobs()
    except FirestoreUnavailableError:
        raise
    for sj in running:
        jid = (getattr(sj, "id", "") or "").strip()
        if not jid:
            continue
        st = _parse_iso_to_utc(getattr(sj, "started_at", "") or "")
        if st is None:
            out.append(
                PipelineAuditDraft(
                    audit_type="dead_job",
                    severity="critical",
                    detected_issue=(
                        "running-ScriptJob ohne auswertbares started_at — manuell prüfen."
                    ),
                    recommended_action="reset_pipeline_step",
                    auto_repairable=False,
                    production_job_id=None,
                    script_job_id=jid,
                    extra_slug="no_started_at",
                )
            )
            continue
        if st <= cutoff:
            out.append(
                PipelineAuditDraft(
                    audit_type="dead_job",
                    severity="critical",
                    detected_issue=(
                        f"ScriptJob seit mindestens {thr} Minuten im Status „running“."
                    ),
                    recommended_action="reset_pipeline_step",
                    auto_repairable=False,
                    production_job_id=None,
                    script_job_id=jid,
                    extra_slug="stuck_running",
                )
            )
    return out


def scan_production_job_for_issues(
    repo: FirestoreWatchlistRepository,
    *,
    pj_id: str,
    pj_status: str,
    generated_script_ref: str,
) -> List[PipelineAuditDraft]:
    out: List[PipelineAuditDraft] = []
    drift_notes: List[str] = []

    pj = pj_id.strip()
    gst = (pj_status or "").strip()
    terminal_bad = gst in ("failed", "skipped")

    gid = (generated_script_ref or "").strip()
    if gid:
        try:
            gs = repo.get_generated_script(gid)
        except FirestoreUnavailableError:
            raise
        if gs is None:
            out.append(
                PipelineAuditDraft(
                    audit_type="orphaned_generated_script_missing",
                    severity="critical",
                    detected_issue=(
                        "production_job.generated_script_id existiert nicht in generated_scripts."
                    ),
                    recommended_action="rebuild",
                    auto_repairable=False,
                    production_job_id=pj,
                    script_job_id=None,
                )
            )

    try:
        sp = repo.get_scene_plan(pj)
        sa = repo.get_scene_assets(pj)
        vp = repo.get_voice_plan(pj)
        rm = repo.get_render_manifest(pj)
        cl = repo.get_production_checklist(pj)
    except FirestoreUnavailableError:
        raise

    statuses_need_scene_plan = {
        "planning_ready",
        "assets_ready",
        "voice_ready",
        "editing_ready",
        "upload_ready",
        "published",
        "completed",
        "in_progress",
    }
    if not terminal_bad and gst in statuses_need_scene_plan and sp is None:
        out.append(
            PipelineAuditDraft(
                audit_type="missing_scene_plan",
                severity="warning",
                detected_issue=(
                    f"Production-Status „{gst}“ ohne scene_plan Firestore-Dokument."
                ),
                recommended_action="retry_scene_plan",
                auto_repairable=True,
                production_job_id=pj,
                script_job_id=None,
            )
        )

    statuses_need_assets = {
        "assets_ready",
        "voice_ready",
        "editing_ready",
        "upload_ready",
        "published",
        "completed",
        "in_progress",
    }
    if not terminal_bad and gst in statuses_need_assets and sa is None:
        out.append(
            PipelineAuditDraft(
                audit_type="missing_scene_assets",
                severity="warning",
                detected_issue=(
                    f"Production-Status „{gst}“ ohne scene_assets Firestore-Dokument."
                ),
                recommended_action="retry_scene_assets",
                auto_repairable=True,
                production_job_id=pj,
                script_job_id=None,
            )
        )

    statuses_need_voice = {
        "voice_ready",
        "editing_ready",
        "upload_ready",
        "published",
        "completed",
        "in_progress",
    }
    if not terminal_bad and gst in statuses_need_voice and vp is None:
        out.append(
            PipelineAuditDraft(
                audit_type="missing_voice_plan",
                severity="warning",
                detected_issue=(
                    f"Production-Status „{gst}“ ohne voice_plan Firestore-Dokument."
                ),
                recommended_action="retry_voice_plan",
                auto_repairable=True,
                production_job_id=pj,
                script_job_id=None,
            )
        )

    statuses_need_manifest = {"editing_ready", "upload_ready", "published", "completed"}
    if gst in statuses_need_manifest and rm is None:
        out.append(
            PipelineAuditDraft(
                audit_type="missing_render_manifest",
                severity="warning",
                detected_issue=(
                    "render_manifest erwartbar für fortgeschrittene Stufe — fehlt."
                ),
                recommended_action="retry_render_manifest",
                auto_repairable=True,
                production_job_id=pj,
                script_job_id=None,
            )
        )

    if gst == "failed":
        out.append(
            PipelineAuditDraft(
                audit_type="failed_production_job",
                severity="critical",
                detected_issue=(
                    'ProductionJob-Status "failed" — Ursache im Job prüfen, dann retry.'
                ),
                recommended_action="reset_pipeline_step",
                auto_repairable=False,
                production_job_id=pj,
                script_job_id=None,
                extra_slug="pj_failed",
            )
        )

    if gst not in ("queued", "failed", "skipped"):
        try:
            pc = repo.get_production_costs(pj)
        except FirestoreUnavailableError:
            raise
        if pc is None:
            out.append(
                PipelineAuditDraft(
                    audit_type="missing_production_costs",
                    severity="info",
                    detected_issue=(
                        "Kein production_costs-Dokument (Schätzung fehlt oder veraltet)."
                    ),
                    recommended_action="retry_cost_estimate",
                    auto_repairable=True,
                    production_job_id=pj,
                    script_job_id=None,
                    extra_slug="nocost",
                )
            )

    if not terminal_bad and gst != "queued":
        try:
            files = repo.list_production_files_for_job(pj)
            exe = repo.list_execution_jobs_for_job(pj)
        except FirestoreUnavailableError:
            raise
        if files and not exe:
            out.append(
                PipelineAuditDraft(
                    audit_type="missing_execution_jobs",
                    severity="info",
                    detected_issue=(
                        "production_files ohne zugehörige execution_jobs — Queue nicht initialisiert."
                    ),
                    recommended_action="retry_execution_job",
                    auto_repairable=True,
                    production_job_id=pj,
                    script_job_id=None,
                    extra_slug="missing_exec_init",
                )
            )

    if cl is not None:
        if (
            gst in statuses_need_scene_plan
            and sp is not None
            and getattr(cl, "scene_plan_ready", False) is not True
        ):
            drift_notes.append(
                "checklist.scene_plan_ready false trotz vorhandenen scene_plan."
            )
        if (
            gst in statuses_need_assets
            and sa is not None
            and getattr(cl, "scene_assets_ready", False) is not True
        ):
            drift_notes.append(
                "checklist.scene_assets_ready false trotz vorhandenen scene_assets."
            )
        if (
            gst in statuses_need_voice
            and vp is not None
            and getattr(cl, "voice_plan_ready", False) is not True
        ):
            drift_notes.append(
                "checklist.voice_plan_ready false trotz vorhandenen voice_plan."
            )
        if gst in statuses_need_manifest and rm is not None:
            if not getattr(cl, "render_manifest_ready", False):
                drift_notes.append(
                    "checklist.render_manifest_ready false trotz vorhandenen render_manifest."
                )

    if drift_notes:
        out.append(
            PipelineAuditDraft(
                audit_type="status_drift",
                severity="info",
                detected_issue=" / ".join(drift_notes),
                recommended_action="rebuild",
                auto_repairable=False,
                production_job_id=pj,
                script_job_id=None,
                extra_slug="chk",
            )
        )

    return out


def pipeline_audit_document_id_from_draft(draft: PipelineAuditDraft) -> str:
    return audit_document_id(
        audit_type=draft.audit_type,
        production_job_id=draft.production_job_id,
        script_job_id=draft.script_job_id,
        extra_slug=draft.extra_slug,
    )
