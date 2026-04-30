"""Watchlist-Service: Kanal auflösen, Metadaten, Firestore."""

from __future__ import annotations

import logging
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Literal, Optional, Set, Tuple

from app.youtube.scoring import is_likely_short_video
from app.youtube.service import get_latest_channel_videos
from app.youtube.rss import fetch_channel_feed_entries
from app.youtube.resolver import resolve_channel_id
from app.models import GenerateScriptResponse, ReviewScriptRequest
from app.utils import (
    WARN_TRANSCRIPT_UNAVAILABLE,
    check_youtube_transcript_available_by_video_id,
    count_words,
    generate_script_from_youtube_video,
)
from app.review.service import review_script
from app.watchlist.cost_calculator import (
    build_production_costs_document,
    compute_category_totals_v1,
    count_production_files_by_file_type,
)
from app.watchlist.execution_queue import build_execution_job_stub
from app.watchlist.input_quality_guard import build_input_quality_decision
from app.watchlist.provider_discipline import (
    seed_default_provider_configs,
    validate_provider_runtime_health,
)
from app.watchlist.pipeline_audit_scan import (
    pipeline_audit_document_id_from_draft,
    scan_production_job_for_issues,
    scan_stuck_running_script_issues,
)
from app.watchlist.status_normalizer import normalize_pipeline_status
from app.watchlist.export_download import (
    build_provider_templates as build_provider_templates_dict,
    export_download_body,
)
from app.watchlist.production_checklist import (
    auto_checklist_booleans,
    compute_target_production_status,
)
from app.watchlist.scene_plan import (
    build_scenes_from_generated_script,
    decide_plan_status,
)
from app.watchlist.scene_asset_prompts import build_scene_asset_items
from app.watchlist.render_manifest import (
    EXPORT_VERSION as RENDER_MANIFEST_EXPORT_VERSION,
    build_timeline,
    decide_manifest_status,
)
from app.watchlist.voice_plan import (
    build_voice_blocks,
    decide_voice_plan_status,
)
from app.watchlist.firestore_repo import (
    GENERATED_SCRIPTS_COLLECTION,
    FirestoreUnavailableError,
    FirestoreWatchlistRepository,
    PROCESSED_VIDEOS_COLLECTION,
)
from app.watchlist.models import (
    AutomationChannelResultItem,
    ChannelCheckVideoItem,
    CheckWatchlistChannelResponse,
    CreateProductionJobResponse,
    CreateWatchlistChannelResponse,
    CreatedScriptJobItem,
    DailyCycleStepResult,
    GeneratedScript,
    ExecutionQueueGetResponse,
    ExecutionQueueInitResponse,
    ExecutionJob,
    ListWatchlistChannelsResponse,
    ListWatchlistScriptJobsResponse,
    ListProviderConfigsResponse,
    ListProductionFilesResponse,
    PendingJobRunResultItem,
    PlanProductionFilesResponse,
    ProcessedVideo,
    ProductionFileRecord,
    ProductionJob,
    ProductionJobCreateRequest,
    ProductionConnectorExportResponse,
    ProductionFileTypeLiteral,
    ProviderConfig,
    ProviderConfigUpsertRequest,
    ProviderNameLiteral,
    ProviderSeedDefaultsResponse,
    ProviderStatusItem,
    ProviderStatusResponse,
    RenderManifest,
    RenderManifestGenerateResponse,
    RenderManifestGetResponse,
    ReviewGeneratedScriptJobResponse,
    ReviewResultStored,
    RunAutomationCycleResponse,
    RunDailyProductionCycleResponse,
    RunPendingScriptJobsResponse,
    RunScriptJobResponse,
    ScenePlan,
    ScenePlanGenerateResponse,
    ScenePlanGetResponse,
    SceneAssets,
    SceneAssetsGenerateRequest,
    SceneAssetsGenerateResponse,
    SceneAssetsGetResponse,
    ScriptJob,
    VoicePlan,
    VoicePlanGenerateRequest,
    VoicePlanGenerateResponse,
    VoicePlanGetResponse,
    WatchlistChannel,
    WatchlistChannelCreateRequest,
    WatchlistChannelStatusResponse,
    WatchlistDashboardCounts,
    WatchlistDashboardHealth,
    WatchlistDashboardResponse,
    WatchlistErrorCodeSummaryItem,
    WatchlistErrorsSummaryResponse,
    WatchlistJobActionResponse,
    WatchlistSkipReasonSummaryItem,
    WatchlistStuckRunningAnalysisResponse,
    WatchlistStuckRunningJobItem,
    ListProductionJobsResponse,
    ProductionChecklist,
    ProductionChecklistResponse,
    ProductionChecklistUpdateRequest,
    ProductionCostsCalculateResponse,
    ProductionCostsGetResponse,
    ProductionCosts,
    ListPipelineAuditsResponse,
    PipelineAudit,
    PipelineAuditDraft,
    PipelineAuditRunRequest,
    PipelineAuditRunResponse,
    StatusNormalizeRunRequest,
    StatusNormalizeRunResponse,
    ListPipelineEscalationsResponse,
    PipelineMonitoringSummaryResponse,
    ProductionPipelineRecoveryResponse,
    ProductionRecoveryRetryRequest,
    RecoveryAction,
    RecoveryActionKindLiteral,
    ProductionJobActionResponse,
    ControlPanelSummaryResponse,
)

logger = logging.getLogger(__name__)

JOB_ERR_TRANSCRIPT_NOT_AVAILABLE = "transcript_not_available"
JOB_ERR_SCRIPT_GEN_EMPTY = "script_generation_empty"
JOB_ERR_SCRIPT_GEN_FAILED = "script_generation_failed"
JOB_ERR_FIRESTORE_WRITE = "firestore_write_failed"


def _classify_empty_generate_response(
    gs: GenerateScriptResponse,
) -> tuple[str, List[str]]:
    """Leeres ``full_script``: standardisierten ``error``/``error_code`` + Response-Warnings."""
    ws = list(gs.warnings or [])
    joined = " ".join(ws)
    if "Transcript not available" in joined:
        out = ws.copy()
        if WARN_TRANSCRIPT_UNAVAILABLE not in out:
            out.append(WARN_TRANSCRIPT_UNAVAILABLE)
        return JOB_ERR_TRANSCRIPT_NOT_AVAILABLE, out
    if "Could not parse a YouTube video id" in joined:
        return JOB_ERR_SCRIPT_GEN_FAILED, ws
    if (
        "konnte nicht vollständig verarbeitet" in joined
        or "Technischer Hinweis" in joined
    ):
        return JOB_ERR_SCRIPT_GEN_FAILED, ws
    return JOB_ERR_SCRIPT_GEN_EMPTY, ws


class ScriptJobNotFoundError(Exception):
    """Kein Script-Job mit dieser ID."""

class ScriptJobConflictError(Exception):
    def __init__(self, detail: str):
        self.detail = detail


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _strip_feed_title(feed_title: str) -> str:
    s = (feed_title or "").strip()
    if s.endswith(" - YouTube"):
        s = s[: -len(" - YouTube")].strip()
    return s


def _canonical_channel_url(channel_id: str) -> str:
    return f"https://www.youtube.com/channel/{channel_id}"


def _doc_to_channel(data: dict) -> WatchlistChannel:
    return WatchlistChannel.model_validate(data)


def create_channel(
    request: WatchlistChannelCreateRequest,
    repo: FirestoreWatchlistRepository | None = None,
) -> CreateWatchlistChannelResponse:
    repo = repo or FirestoreWatchlistRepository()

    merged_warnings: List[str] = []

    channel_id, w_res = resolve_channel_id(request.channel_url)
    merged_warnings.extend(w_res)

    if not channel_id:
        merged_warnings.append(
            "Konnte keine Channel-ID auflösen; Kanal wird nicht gespeichert. "
            "Bitte vorzugsweise eine /channel/UC…-URL verwenden."
        )
        logger.info(
            "watchlist create aborted: unresolved channel_url (warnings=%s)",
            len(w_res),
        )
        return CreateWatchlistChannelResponse(channel=None, warnings=merged_warnings)

    feed_title, _entries, w_feed = fetch_channel_feed_entries(channel_id, 1)
    merged_warnings.extend(w_feed)

    display_name = _strip_feed_title(feed_title) or channel_id
    canon_url = _canonical_channel_url(channel_id)

    now = utc_now_iso()
    try:
        existing = repo.get_watch_channel_doc(channel_id)
    except FirestoreUnavailableError as e:
        raise FirestoreUnavailableError(str(e)) from e

    last_checked_at: str | None = None
    last_success_at: str | None = None
    last_error = ""

    if existing:
        raw_ca = existing.get("created_at")
        created_at = raw_ca if isinstance(raw_ca, str) and raw_ca.strip() else now
        st = existing.get("status")
        if st == "error":
            status_now = "active"
        elif st in ("active", "paused"):
            status_now = st
        else:
            status_now = "active"
        if isinstance(existing.get("last_checked_at"), str):
            last_checked_at = existing["last_checked_at"]
        if isinstance(existing.get("last_success_at"), str):
            last_success_at = existing["last_success_at"]
        last_error = str(existing.get("last_error") or "")
    else:
        created_at = now
        status_now = "active"

    channel = WatchlistChannel(
        id=channel_id,
        channel_url=canon_url,
        channel_id=channel_id,
        channel_name=display_name,
        status=status_now,
        check_interval=request.check_interval,
        max_results=request.max_results,
        auto_generate_script=request.auto_generate_script,
        auto_review_script=request.auto_review_script,
        target_language=request.target_language,
        duration_minutes=request.duration_minutes,
        min_score=request.min_score,
        ignore_shorts=request.ignore_shorts,
        created_at=created_at,
        updated_at=now,
        last_checked_at=last_checked_at,
        last_success_at=last_success_at,
        last_error=last_error,
        notes=request.notes,
    )

    try:
        repo.upsert_watch_channel(channel_id, channel.model_dump())
    except FirestoreUnavailableError:
        raise

    logger.info(
        "watchlist channel upserted: channel_id=%s status=%s",
        channel_id,
        channel.status,
    )
    return CreateWatchlistChannelResponse(channel=channel, warnings=merged_warnings)


def list_channels(
    repo: FirestoreWatchlistRepository | None = None,
) -> ListWatchlistChannelsResponse:
    repo = repo or FirestoreWatchlistRepository()
    try:
        docs = repo.list_watch_channel_docs()
    except FirestoreUnavailableError as e:
        raise FirestoreUnavailableError(str(e)) from e

    channels: List[WatchlistChannel] = []
    for d in docs:
        try:
            channels.append(_doc_to_channel(d))
        except Exception as e:
            logger.warning(
                "skipping malformed watch_channels doc doc_id=%s type=%s",
                d.get("id", "?"),
                type(e).__name__,
            )
            continue

    channels.sort(key=lambda c: c.created_at, reverse=True)
    return ListWatchlistChannelsResponse(channels=channels, warnings=[])


def list_script_jobs(
    repo: FirestoreWatchlistRepository | None = None,
    limit: int = 50,
) -> ListWatchlistScriptJobsResponse:
    """Listet persistierte Script-Jobs (keine Ausführung)."""
    repo = repo or FirestoreWatchlistRepository()
    try:
        jobs = repo.list_script_jobs(limit=limit)
    except FirestoreUnavailableError as e:
        raise FirestoreUnavailableError(str(e)) from e

    return ListWatchlistScriptJobsResponse(jobs=jobs, warnings=[])


def run_script_job(
    job_id: str,
    repo: FirestoreWatchlistRepository | None = None,
    generate_fn: Callable[..., Any] | None = None,
) -> RunScriptJobResponse:
    """Lädt einen pending/failed Job, erzeugt ein Skript wie ``/youtube/generate-script``, persistiert ``generated_scripts``."""
    repo = repo or FirestoreWatchlistRepository()
    gen = generate_fn or generate_script_from_youtube_video

    jid = (job_id or "").strip()
    if not jid:
        raise ScriptJobNotFoundError()

    try:
        job = repo.get_script_job(jid)
    except FirestoreUnavailableError:
        raise

    if job is None:
        raise ScriptJobNotFoundError()

    out_warnings: List[str] = []

    if job.status == "completed":
        out_warnings.append("Script job already completed.")
        script_loaded: GeneratedScript | None = None
        if job.generated_script_id:
            try:
                script_loaded = repo.get_generated_script(job.generated_script_id)
            except FirestoreUnavailableError:
                raise
        return RunScriptJobResponse(job=job, script=script_loaded, warnings=out_warnings)

    if job.status == "running":
        raise ScriptJobConflictError("Script job is already running.")

    if job.status == "skipped":
        raise ScriptJobConflictError("Script job cannot be run (skipped status).")

    if job.status not in ("pending", "failed"):
        raise ScriptJobConflictError(
            f"Script job cannot be run (status={job.status})."
        )

    try:
        repo.mark_script_job_running(jid)
    except FirestoreUnavailableError:
        raise

    try:
        job_after_run = repo.get_script_job(jid)
    except FirestoreUnavailableError:
        raise

    job_running = job_after_run if job_after_run is not None else job

    gs = gen(
        job_running.video_url,
        target_language=job_running.target_language,
        duration_minutes=job_running.duration_minutes,
    )

    full = (gs.full_script or "").strip()
    if not full:
        code, tw = _classify_empty_generate_response(gs)
        iq_d = build_input_quality_decision(error_code=code, warnings=tw)
        tw.extend(list(iq_d.get("warnings_append") or []))
        iq_st = str(iq_d.get("input_quality_status") or "")
        try:
            repo.mark_script_job_failed(
                jid,
                code,
                error_code=code,
                input_quality_status=(
                    iq_st if iq_st and iq_st != "unknown" else None
                ),
            )
        except FirestoreUnavailableError:
            raise
        try:
            job_failed = repo.get_script_job(jid)
        except FirestoreUnavailableError:
            raise
        final_job = job_failed if job_failed else job_running
        return RunScriptJobResponse(job=final_job, script=None, warnings=tw)

    wc = count_words(gs.full_script)
    created_iso = utc_now_iso()
    gs_doc = GeneratedScript(
        id=jid,
        script_job_id=jid,
        source_url=job_running.video_url,
        source_type="youtube_transcript",
        title=gs.title,
        hook=gs.hook,
        chapters=list(gs.chapters),
        full_script=gs.full_script,
        sources=list(gs.sources or []),
        warnings=list(gs.warnings or []),
        word_count=wc,
        created_at=created_iso,
    )

    try:
        repo.create_generated_script(gs_doc)
    except FirestoreUnavailableError:
        try:
            repo.mark_script_job_failed(
                jid,
                JOB_ERR_FIRESTORE_WRITE,
                error_code=JOB_ERR_FIRESTORE_WRITE,
            )
        except FirestoreUnavailableError:
            pass
        raise

    try:
        repo.mark_script_job_completed(jid, jid)
    except FirestoreUnavailableError:
        try:
            repo.mark_script_job_failed(
                jid,
                JOB_ERR_FIRESTORE_WRITE,
                error_code=JOB_ERR_FIRESTORE_WRITE,
            )
        except FirestoreUnavailableError:
            pass
        raise

    try:
        job_done = repo.get_script_job(jid)
    except FirestoreUnavailableError:
        raise

    final_job = job_done if job_done else job_running

    pv = None
    try:
        pv = repo.get_processed_video(job_running.video_id)
    except FirestoreUnavailableError:
        raise
    if pv:
        try:
            repo.update_processed_video_status(
                job_running.video_id,
                "script_generated",
                script_job_id=jid,
                generated_script_id=jid,
            )
        except FirestoreUnavailableError:
            raise
    else:
        out_warnings.append(
            "processed_videos entry not found; video status was not updated."
        )

    return RunScriptJobResponse(
        job=final_job,
        script=gs_doc,
        warnings=out_warnings,
    )


def _try_create_script_job_for_seen_video(
    *,
    repo: FirestoreWatchlistRepository,
    channel: WatchlistChannel,
    vid: str,
    url_raw: str,
    now_iso: str,
    merged_warnings: List[str],
    created_jobs_acc: List[CreatedScriptJobItem],
) -> None:
    """Nach ``seen`` in ``processed_videos``: optional pending ``script_job`` (Schritt 3, kein Run)."""
    if not channel.auto_generate_script:
        return
    try:
        existing_job = repo.get_script_job(vid)
    except FirestoreUnavailableError:
        raise
    if existing_job:
        merged_warnings.append(
            f"Script job already exists for video {vid}; skipping duplicate job creation."
        )
        try:
            repo.update_processed_video_job_link(vid, existing_job.id)
        except FirestoreUnavailableError:
            raise
        return

    job = ScriptJob(
        id=vid,
        video_id=vid,
        channel_id=channel.channel_id,
        video_url=url_raw,
        status="pending",
        source_type="youtube_transcript",
        target_language=channel.target_language,
        duration_minutes=channel.duration_minutes,
        created_at=now_iso,
        started_at=None,
        completed_at=None,
        error="",
        error_code="",
        generated_script_id=None,
        review_result_id=None,
    )
    try:
        repo.create_script_job(job)
    except FirestoreUnavailableError:
        raise
    try:
        repo.update_processed_video_job_link(vid, job.id)
    except FirestoreUnavailableError:
        raise

    created_jobs_acc.append(
        CreatedScriptJobItem(
            id=job.id,
            video_id=job.video_id,
            video_url=job.video_url,
            status=job.status,
            target_language=job.target_language,
            duration_minutes=job.duration_minutes,
        )
    )


def _check_item_from_raw(
    raw: Dict[str, Any],
    *,
    is_short: bool,
    status: Literal["new", "known", "skipped"],
    skip_reason: str = "",
    input_quality_status: str = "",
) -> ChannelCheckVideoItem:
    score_val = raw.get("score")
    try:
        sc = int(score_val) if score_val is not None else 0
    except (TypeError, ValueError):
        sc = 0
    return ChannelCheckVideoItem(
        title=str(raw.get("title") or ""),
        url=str(raw.get("url") or ""),
        video_id=str(raw.get("video_id") or ""),
        published_at=str(raw.get("published_at") or ""),
        score=sc,
        reason=str(raw.get("reason") or ""),
        is_short=is_short,
        status=status,
        skip_reason=skip_reason,
        input_quality_status=(input_quality_status or "")[:120],
    )


WARN_RECHECK_SINGLE_DOCUMENT_REMOVED_DE = (
    "Ein vorhandenes processed_videos-Dokument für genau diese video_id wurde zur "
    "Neuprüfung entfernt. Es handelt sich um keine Massenlöschung; Umfang: ein Video."
)


def _consume_watchlist_feed_video_row(
    *,
    repo: FirestoreWatchlistRepository,
    channel: WatchlistChannel,
    raw: Dict[str, Any],
    now_iso: str,
    checker: Callable[[str], Tuple[bool, List[str]]],
    transcript_warn_flags: Dict[str, bool],
    merged_warnings: List[str],
    created_jobs_out: List[CreatedScriptJobItem],
    new_out: List[ChannelCheckVideoItem],
    known_out: List[ChannelCheckVideoItem],
    skipped_out: List[ChannelCheckVideoItem],
) -> None:
    """Eine Feed-Zelle wie beim Kanal-Check verarbeiten (inkl. Transcript-Preflight)."""
    vid = str(raw.get("video_id") or "").strip()
    if not vid:
        return
    ds = raw.get("duration_seconds")
    if ds is not None and not isinstance(ds, (int, float)):
        try:
            ds = int(ds)
        except (TypeError, ValueError):
            ds = None
    elif isinstance(ds, float):
        ds = int(ds)
    media_kw = str(raw.get("media_keywords") or "")
    title_raw = str(raw.get("title") or "")
    url_raw = str(raw.get("url") or "")
    is_short = is_likely_short_video(
        title_raw, url_raw, ds, media_kw
    )
    processed = repo.get_processed_video(vid)

    score_val = raw.get("score")
    try:
        sc_num = int(score_val) if score_val is not None else 0
    except (TypeError, ValueError):
        sc_num = 0
    reason_s = str(raw.get("reason") or "")

    if processed:
        known_out.append(
            _check_item_from_raw(raw, is_short=is_short, status="known")
        )
        return

    if channel.ignore_shorts and is_short:
        pv = ProcessedVideo(
            id=vid,
            channel_id=channel.channel_id,
            video_id=vid,
            video_url=url_raw,
            title=title_raw,
            published_at=str(raw.get("published_at") or ""),
            first_seen_at=now_iso,
            status="skipped",
            score=sc_num,
            reason=reason_s,
            is_short=True,
            skip_reason="shorts_ignored",
            script_job_id=None,
            review_result_id=None,
            last_error="",
        )
        repo.create_processed_video(pv)
        skipped_out.append(
            _check_item_from_raw(
                raw,
                is_short=True,
                status="skipped",
                skip_reason="shorts_ignored",
            )
        )
        return

    if sc_num < channel.min_score:
        pv = ProcessedVideo(
            id=vid,
            channel_id=channel.channel_id,
            video_id=vid,
            video_url=url_raw,
            title=title_raw,
            published_at=str(raw.get("published_at") or ""),
            first_seen_at=now_iso,
            status="skipped",
            score=sc_num,
            reason=reason_s,
            is_short=is_short,
            skip_reason="score_below_minimum",
            script_job_id=None,
            review_result_id=None,
            last_error="",
        )
        repo.create_processed_video(pv)
        skipped_out.append(
            _check_item_from_raw(
                raw,
                is_short=is_short,
                status="skipped",
                skip_reason="score_below_minimum",
            )
        )
        return

    if channel.auto_generate_script:
        ok_tr, _preflight_ws = checker(vid)
        if not ok_tr:
            if any(
                WARN_TRANSCRIPT_UNAVAILABLE in (x or "")
                or "Transcript not available" in (x or "")
                for x in _preflight_ws
            ):
                skip_tr = "transcript_not_available"
                transcript_warn_flags["unavailable"] = True
            else:
                skip_tr = "transcript_check_failed"
                transcript_warn_flags["check_failed"] = True
            iq_dec = build_input_quality_decision(
                skip_reason=skip_tr,
                warnings=_preflight_ws,
            )
            iq_label = str(iq_dec.get("input_quality_status") or "")[:120]
            pv_tr = ProcessedVideo(
                id=vid,
                channel_id=channel.channel_id,
                video_id=vid,
                video_url=url_raw,
                title=title_raw,
                published_at=str(raw.get("published_at") or ""),
                first_seen_at=now_iso,
                status="skipped",
                score=sc_num,
                reason=reason_s,
                is_short=is_short,
                skip_reason=skip_tr,
                input_quality_status=iq_label,
                script_job_id=None,
                generated_script_id=None,
                review_result_id=None,
                last_error="",
            )
            repo.create_processed_video(pv_tr)
            skipped_out.append(
                _check_item_from_raw(
                    raw,
                    is_short=is_short,
                    status="skipped",
                    skip_reason=skip_tr,
                    input_quality_status=iq_label,
                )
            )
            return

    pv_seen = ProcessedVideo(
        id=vid,
        channel_id=channel.channel_id,
        video_id=vid,
        video_url=url_raw,
        title=title_raw,
        published_at=str(raw.get("published_at") or ""),
        first_seen_at=now_iso,
        status="seen",
        score=sc_num,
        reason=reason_s,
        is_short=is_short,
        skip_reason="",
        script_job_id=None,
        generated_script_id=None,
        review_result_id=None,
        last_error="",
    )
    repo.create_processed_video(pv_seen)
    new_out.append(
        _check_item_from_raw(raw, is_short=is_short, status="new")
    )
    _try_create_script_job_for_seen_video(
        repo=repo,
        channel=channel,
        vid=vid,
        url_raw=url_raw,
        now_iso=now_iso,
        merged_warnings=merged_warnings,
        created_jobs_acc=created_jobs_out,
    )


def check_channel(
    channel_id: str,
    repo: FirestoreWatchlistRepository | None = None,
    get_videos: Callable[..., Dict[str, Any]] | None = None,
    transcript_checker: Callable[[str], Tuple[bool, List[str]]] | None = None,
) -> CheckWatchlistChannelResponse:
    """RSS-Check gegen ``processed_videos``; optional ``script_jobs`` (pending) bei ``auto_generate_script``."""
    repo = repo or FirestoreWatchlistRepository()
    cid = (channel_id or "").strip()
    getter = get_videos
    if getter is None:
        getter = lambda url, mx: get_latest_channel_videos(
            url, mx, include_feed_metadata=True
        )

    not_found_resp = CheckWatchlistChannelResponse(
        channel_id=cid,
        warnings=["Watchlist channel not found."],
    )

    channel: WatchlistChannel | None = None
    try:
        channel = repo.get_watch_channel(cid)
    except FirestoreUnavailableError:
        raise
    except Exception as e:
        logger.warning(
            "watchlist check_channel load failed: channel_id=%s type=%s",
            cid,
            type(e).__name__,
        )
        return CheckWatchlistChannelResponse(
            channel_id=cid,
            warnings=["Watchlist channel could not be loaded."],
        )

    if not channel:
        return not_found_resp

    if channel.status != "active":
        return CheckWatchlistChannelResponse(
            channel_id=channel.channel_id,
            warnings=["Watchlist channel is not active."],
        )

    now_iso = utc_now_iso()
    new_out: List[ChannelCheckVideoItem] = []
    known_out: List[ChannelCheckVideoItem] = []
    skipped_out: List[ChannelCheckVideoItem] = []
    merged_warnings: List[str] = []
    created_jobs_out: List[CreatedScriptJobItem] = []
    transcript_warn_flags = {"unavailable": False, "check_failed": False}
    checker = transcript_checker or check_youtube_transcript_available_by_video_id

    try:
        feed_result = getter(channel.channel_url, channel.max_results)
        merged_warnings.extend(list(feed_result.get("warnings") or []))
        rows = feed_result.get("videos") or []
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            _consume_watchlist_feed_video_row(
                repo=repo,
                channel=channel,
                raw=raw,
                now_iso=now_iso,
                checker=checker,
                transcript_warn_flags=transcript_warn_flags,
                merged_warnings=merged_warnings,
                created_jobs_out=created_jobs_out,
                new_out=new_out,
                known_out=known_out,
                skipped_out=skipped_out,
            )

        created_n = len(new_out) + len(skipped_out)

        if transcript_warn_flags["unavailable"]:
            merged_warnings.append(
                "Mindestens ein Video wurde ohne Script-Job übersprungen: Transkript nicht verfügbar."
            )
        if transcript_warn_flags["check_failed"]:
            merged_warnings.append(
                "Mindestens ein Video wurde ohne Script-Job übersprungen: Transkript-Check technisch fehlgeschlagen."
            )

        ok_channel = channel.model_copy(
            update={
                "updated_at": now_iso,
                "last_checked_at": now_iso,
                "last_success_at": now_iso,
                "last_error": "",
            }
        )
        repo.upsert_watch_channel(channel.channel_id, ok_channel.model_dump())

        return CheckWatchlistChannelResponse(
            channel_id=channel.channel_id,
            new_videos=new_out,
            known_videos=known_out,
            skipped_videos=skipped_out,
            created_processed_videos=created_n,
            created_jobs=created_jobs_out,
            warnings=merged_warnings,
        )
    except FirestoreUnavailableError:
        raise
    except Exception as e:
        logger.warning(
            "watchlist check_channel run failed: channel_id=%s type=%s",
            channel.channel_id,
            type(e).__name__,
        )
        err_msg = "Channel check failed."
        try:
            fail_ch = channel.model_copy(
                update={
                    "updated_at": now_iso,
                    "last_checked_at": now_iso,
                    "last_error": err_msg,
                }
            )
            repo.upsert_watch_channel(channel.channel_id, fail_ch.model_dump())
        except FirestoreUnavailableError:
            raise
        except Exception as persist_e:
            logger.warning(
                "could not persist last_error: type=%s", type(persist_e).__name__
            )
            merged_warnings.append("Could not persist channel error status.")
        return CheckWatchlistChannelResponse(
            channel_id=channel.channel_id,
            new_videos=new_out,
            known_videos=known_out,
            skipped_videos=skipped_out,
            created_processed_videos=len(new_out) + len(skipped_out),
            created_jobs=created_jobs_out,
            warnings=merged_warnings
            + [err_msg, "Check could not be completed."],
        )


def _find_feed_row_for_video_id(rows: Any, vid: str) -> Dict[str, Any] | None:
    for raw in rows or []:
        if not isinstance(raw, dict):
            continue
        v = str(raw.get("video_id") or "").strip()
        if v == vid:
            return raw
    return None


def _synthetic_feed_row_from_processed(pv: ProcessedVideo) -> Dict[str, Any]:
    return {
        "title": pv.title,
        "url": pv.video_url,
        "video_id": pv.video_id,
        "published_at": pv.published_at or "",
        "score": pv.score,
        "reason": pv.reason,
        "duration_seconds": None,
        "media_keywords": "",
    }


def recheck_video(
    channel_id: str,
    video_id: str,
    *,
    repo: FirestoreWatchlistRepository | None = None,
    get_videos: Callable[..., Dict[str, Any]] | None = None,
    transcript_checker: Callable[[str], Tuple[bool, List[str]]] | None = None,
) -> CheckWatchlistChannelResponse:
    """Einzelnes Video erneut prüfen (Transcript-Preflight wie Channel-Check, kein Massenweg)."""
    repo = repo or FirestoreWatchlistRepository()
    cid = (channel_id or "").strip()
    vid = str(video_id or "").strip()
    if not vid:
        return CheckWatchlistChannelResponse(
            channel_id=cid,
            warnings=["video_id is required."],
        )

    getter = get_videos
    if getter is None:
        getter = lambda url, mx: get_latest_channel_videos(
            url, mx, include_feed_metadata=True
        )

    not_found_resp = CheckWatchlistChannelResponse(
        channel_id=cid,
        warnings=["Watchlist channel not found."],
    )

    try:
        channel = repo.get_watch_channel(cid)
    except FirestoreUnavailableError:
        raise
    except Exception as e:
        logger.warning(
            "watchlist recheck_video load failed: channel_id=%s type=%s",
            cid,
            type(e).__name__,
        )
        return CheckWatchlistChannelResponse(
            channel_id=cid,
            warnings=["Watchlist channel could not be loaded."],
        )

    if not channel:
        return not_found_resp

    if channel.status != "active":
        return CheckWatchlistChannelResponse(
            channel_id=channel.channel_id,
            warnings=["Watchlist channel is not active."],
        )

    snapshot: ProcessedVideo | None = None
    try:
        snapshot = repo.get_processed_video(vid)
    except FirestoreUnavailableError:
        raise
    if snapshot is not None and snapshot.channel_id != channel.channel_id:
        return CheckWatchlistChannelResponse(
            channel_id=channel.channel_id,
            warnings=[
                "processed_videos entry belongs to a different channel_id; recheck refused."
            ],
        )

    merged_warnings: List[str] = []
    try:
        removed = repo.delete_processed_video(vid)
    except FirestoreUnavailableError:
        raise
    if removed:
        merged_warnings.append(WARN_RECHECK_SINGLE_DOCUMENT_REMOVED_DE)
    else:
        merged_warnings.append(
            "Kein processed_videos-Eintrag für diese video_id; Neuprüfung läuft dennoch (kein Löschvorgang)."
        )

    now_iso = utc_now_iso()
    new_out: List[ChannelCheckVideoItem] = []
    known_out: List[ChannelCheckVideoItem] = []
    skipped_out: List[ChannelCheckVideoItem] = []
    created_jobs_out: List[CreatedScriptJobItem] = []
    transcript_warn_flags = {"unavailable": False, "check_failed": False}
    checker = transcript_checker or check_youtube_transcript_available_by_video_id

    feed_width = max(50, int(channel.max_results or 5))
    try:
        feed_result = getter(channel.channel_url, feed_width)
        merged_warnings.extend(list(feed_result.get("warnings") or []))
        rows = feed_result.get("videos") or []
        raw = _find_feed_row_for_video_id(rows, vid)
        if raw is None and snapshot is not None:
            raw = _synthetic_feed_row_from_processed(snapshot)
            merged_warnings.append(
                "Video war im gewählten RSS-Ausschnitt nicht enthalten — Metadaten aus "
                "früherer Verarbeitung wurden für die Neuprüfung verwendet."
            )
        elif raw is None:
            merged_warnings.append(
                "Konnte keine Feed-Zeile für diese video_id finden; keine erneute Klassifikation möglich."
            )
            return CheckWatchlistChannelResponse(
                channel_id=channel.channel_id,
                new_videos=new_out,
                known_videos=known_out,
                skipped_videos=skipped_out,
                created_processed_videos=0,
                created_jobs=created_jobs_out,
                warnings=merged_warnings,
            )

        assert raw is not None
        _consume_watchlist_feed_video_row(
            repo=repo,
            channel=channel,
            raw=raw,
            now_iso=now_iso,
            checker=checker,
            transcript_warn_flags=transcript_warn_flags,
            merged_warnings=merged_warnings,
            created_jobs_out=created_jobs_out,
            new_out=new_out,
            known_out=known_out,
            skipped_out=skipped_out,
        )

        if transcript_warn_flags["unavailable"]:
            merged_warnings.append(
                "Mindestens ein Video wurde ohne Script-Job übersprungen: Transkript nicht verfügbar."
            )
        if transcript_warn_flags["check_failed"]:
            merged_warnings.append(
                "Mindestens ein Video wurde ohne Script-Job übersprungen: Transkript-Check technisch fehlgeschlagen."
            )

        ok_channel = channel.model_copy(
            update={
                "updated_at": now_iso,
                "last_checked_at": now_iso,
                "last_success_at": now_iso,
                "last_error": "",
            }
        )
        repo.upsert_watch_channel(channel.channel_id, ok_channel.model_dump())

        created_n = len(new_out) + len(skipped_out)
        return CheckWatchlistChannelResponse(
            channel_id=channel.channel_id,
            new_videos=new_out,
            known_videos=known_out,
            skipped_videos=skipped_out,
            created_processed_videos=created_n,
            created_jobs=created_jobs_out,
            warnings=merged_warnings,
        )
    except FirestoreUnavailableError:
        raise
    except Exception as e:
        logger.warning(
            "watchlist recheck_video failed: channel_id=%s video_id=%s type=%s",
            cid,
            vid,
            type(e).__name__,
        )
        err_msg = "Recheck failed."
        try:
            fail_ch = channel.model_copy(
                update={
                    "updated_at": now_iso,
                    "last_checked_at": now_iso,
                    "last_error": err_msg,
                }
            )
            repo.upsert_watch_channel(channel.channel_id, fail_ch.model_dump())
        except FirestoreUnavailableError:
            raise
        except Exception as persist_e:
            logger.warning(
                "could not persist last_error (recheck): type=%s", type(persist_e).__name__
            )
            merged_warnings.append("Could not persist channel error status.")
        return CheckWatchlistChannelResponse(
            channel_id=channel.channel_id,
            new_videos=new_out,
            known_videos=known_out,
            skipped_videos=skipped_out,
            created_processed_videos=len(new_out) + len(skipped_out),
            created_jobs=created_jobs_out,
            warnings=merged_warnings
            + [err_msg, "Recheck could not be completed."],
        )


def run_pending_script_jobs(
    limit: int = 3,
    *,
    repo: FirestoreWatchlistRepository | None = None,
    generate_fn: Callable[..., Any] | None = None,
) -> RunPendingScriptJobsResponse:
    """Führt pending ScriptJobs nacheinander aus; Fehler einzelner Jobs stoppen den Batch nicht."""
    repo = repo or FirestoreWatchlistRepository()
    lim = max(1, min(int(limit), 10))
    base_warnings: List[str] = []
    try:
        pending = repo.list_pending_script_jobs(lim)
    except FirestoreUnavailableError:
        raise

    results: List[PendingJobRunResultItem] = []
    checked_jobs = 0
    completed_jobs = 0
    failed_jobs = 0
    skipped_jobs = 0

    if not pending:
        base_warnings.append("No pending script jobs.")
        return RunPendingScriptJobsResponse(
            checked_jobs=checked_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            skipped_jobs=skipped_jobs,
            results=results,
            warnings=base_warnings,
        )

    gen = generate_fn or generate_script_from_youtube_video

    for job in pending:
        checked_jobs += 1
        jid = job.id
        item = PendingJobRunResultItem(job_id=jid, outcome="skipped", warnings=[])
        try:
            out = run_script_job(jid, repo=repo, generate_fn=gen)
        except ScriptJobNotFoundError:
            item.outcome = "skipped"
            item.warnings.append("Script job not found at run time.")
            skipped_jobs += 1
            results.append(item)
            continue
        except ScriptJobConflictError as e:
            item.outcome = "skipped"
            item.warnings.append(str(e.detail or "Script job cannot be run."))
            skipped_jobs += 1
            results.append(item)
            continue
        except FirestoreUnavailableError as e:
            item.outcome = "failed"
            item.warnings.append(str(e) if str(e) else "Firestore unavailable.")
            failed_jobs += 1
            results.append(item)
            continue
        except Exception as e:
            logger.warning(
                "run_pending_script_jobs job failed unexpectedly: job_id=%s type=%s",
                jid,
                type(e).__name__,
            )
            item.outcome = "failed"
            item.warnings.append("Unexpected error while running script job.")
            failed_jobs += 1
            results.append(item)
            continue

        st = (out.job.status or "").strip()
        item.warnings.extend(list(out.warnings or []))
        if st == "completed":
            item.outcome = "completed"
            completed_jobs += 1
        elif st == "failed":
            item.outcome = "failed"
            failed_jobs += 1
        else:
            item.outcome = "skipped"
            item.warnings.append(f"Unexpected job status after run: {st!r}.")
            skipped_jobs += 1
        results.append(item)

    return RunPendingScriptJobsResponse(
        checked_jobs=checked_jobs,
        completed_jobs=completed_jobs,
        failed_jobs=failed_jobs,
        skipped_jobs=skipped_jobs,
        results=results,
        warnings=base_warnings,
    )


def run_automation_cycle(
    *,
    channel_limit: int = 3,
    job_limit: int = 3,
    repo: FirestoreWatchlistRepository | None = None,
    get_videos: Callable[..., Dict[str, Any]] | None = None,
    transcript_checker: Callable[[str], Tuple[bool, List[str]]] | None = None,
    generate_fn: Callable[..., Any] | None = None,
) -> RunAutomationCycleResponse:
    """Scheduler-tauglicher Zyklus: aktive Kanäle prüfen, danach pending Jobs ausführen."""
    repo = repo or FirestoreWatchlistRepository()
    ch_lim = max(1, min(int(channel_limit), 50))
    jb_lim = max(1, min(int(job_limit), 10))
    out = RunAutomationCycleResponse(
        checked_channels=0,
        created_jobs=0,
        run_jobs=0,
        completed_jobs=0,
        failed_jobs=0,
        warnings=[],
        channel_results=[],
        job_results=[],
    )

    try:
        listed = list_channels(repo=repo)
    except FirestoreUnavailableError:
        raise

    channels = sorted(
        [c for c in listed.channels if c.status == "active"], key=lambda c: c.channel_id
    )
    slice_ch = channels[:ch_lim]

    for ch in slice_ch:
        out.checked_channels += 1
        ch_item = AutomationChannelResultItem(channel_id=ch.channel_id)
        try:
            resp = check_channel(
                ch.channel_id,
                repo=repo,
                get_videos=get_videos,
                transcript_checker=transcript_checker,
            )
        except FirestoreUnavailableError:
            raise
        except Exception as e:
            logger.warning(
                "watchlist run_automation_cycle check failed: channel_id=%s type=%s",
                ch.channel_id,
                type(e).__name__,
            )
            ch_item.ok = False
            ch_item.warnings.append(f"Channel check failed: {type(e).__name__}.")
            out.warnings.extend(ch_item.warnings)
            out.channel_results.append(ch_item)
            continue

        ch_item.created_jobs_from_check = len(resp.created_jobs)
        out.created_jobs += ch_item.created_jobs_from_check
        ch_item.new_videos_count = len(resp.new_videos or [])
        ch_item.skipped_videos_count = len(resp.skipped_videos or [])
        ch_item.warnings.extend(resp.warnings or [])
        out.warnings.extend(resp.warnings or [])
        out.channel_results.append(ch_item)

    try:
        job_batch = run_pending_script_jobs(jb_lim, repo=repo, generate_fn=generate_fn)
    except FirestoreUnavailableError:
        raise

    out.run_jobs = job_batch.checked_jobs
    out.completed_jobs = job_batch.completed_jobs
    out.failed_jobs = job_batch.failed_jobs
    out.job_results = list(job_batch.results)
    extra = [w for w in job_batch.warnings if w not in out.warnings]
    out.warnings.extend(extra)
    try:
        repo.set_last_automation_cycle_at(utc_now_iso())
    except FirestoreUnavailableError:
        out.warnings.append(
            "Konnte last_run_cycle_at in watchlist_meta nicht schreiben (Firestore)."
        )
    except Exception as e:
        logger.warning(
            "watchlist run_automation_cycle meta persist failed: type=%s",
            type(e).__name__,
        )
        out.warnings.append("Konnte last_run_cycle_at nicht speichern.")
    return out


def _completed_script_jobs_missing_production(
    repo: FirestoreWatchlistRepository,
    limit: int,
) -> List[ScriptJob]:
    try:
        jobs = repo.list_script_jobs(500)
    except FirestoreUnavailableError:
        raise
    eligible: List[ScriptJob] = []
    for j in jobs:
        if j.status != "completed":
            continue
        gid = (j.generated_script_id or "").strip()
        if not gid:
            continue
        try:
            pj = repo.get_production_job(gid)
        except FirestoreUnavailableError:
            raise
        if pj is None:
            eligible.append(j)
    eligible.sort(
        key=lambda x: (x.completed_at or x.created_at or ""),
        reverse=True,
    )
    lim = max(0, min(int(limit), 50))
    return eligible[:lim]


def _scene_count_for_file_plan(repo: FirestoreWatchlistRepository, pid: str) -> int:
    try:
        sa = repo.get_scene_assets(pid)
        if sa is not None and sa.scenes:
            return max(1, len(sa.scenes))
        sp = repo.get_scene_plan(pid)
        if sp is not None and sp.scenes:
            return max(1, len(sp.scenes))
    except FirestoreUnavailableError:
        raise
    return 1


def _production_file_doc_id(
    production_job_id: str,
    file_type: str,
    scene_number: int,
) -> str:
    safe = "".join(
        ch if (ch.isalnum() or ch in "-_") else "_" for ch in production_job_id
    )
    return f"pfile_{safe}_{file_type}_{scene_number:04d}"


ALL_PROVIDER_NAMES: Tuple[ProviderNameLiteral, ...] = (
    "elevenlabs",
    "openai",
    "google",
    "leonardo",
    "kling",
    "runway",
    "generic",
    "voice_default",
    "image_default",
    "render_default",
)


def run_daily_production_cycle(
    channel_limit: int = 3,
    job_limit: int = 3,
    production_limit: int = 3,
    dry_run: bool = True,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
    get_videos: Optional[Callable[..., Dict[str, Any]]] = None,
    transcript_checker: Optional[Callable[[str], Tuple[bool, List[str]]]] = None,
    generate_fn: Optional[Callable[..., Any]] = None,
) -> RunDailyProductionCycleResponse:
    """Scheduler-tauglicher End-to-End-Lauf: Watchlist → Jobs → Production-Artefakte."""
    repo = repo or FirestoreWatchlistRepository()
    ch_lim = max(1, min(int(channel_limit), 50))
    jb_lim = max(1, min(int(job_limit), 10))
    prod_lim = max(1, min(int(production_limit), 50))

    out = RunDailyProductionCycleResponse(
        warnings=[],
        results=[],
    )

    if not dry_run:
        try:
            auto = run_automation_cycle(
                channel_limit=ch_lim,
                job_limit=jb_lim,
                repo=repo,
                get_videos=get_videos,
                transcript_checker=transcript_checker,
                generate_fn=generate_fn,
            )
        except FirestoreUnavailableError:
            raise
        out.checked_channels = auto.checked_channels
        out.completed_jobs = auto.completed_jobs
        out.failed_jobs = auto.failed_jobs
        out.warnings.extend(auto.warnings)
        for jr in auto.job_results:
            out.results.append(
                DailyCycleStepResult(
                    step="pending_script_job",
                    script_job_id=jr.job_id,
                    outcome=str(jr.outcome),
                    detail=(jr.warnings[0] if jr.warnings else ""),
                )
            )
        for ch in auto.channel_results:
            out.results.append(
                DailyCycleStepResult(
                    step="watchlist_channel",
                    outcome="ok" if ch.ok else "failed",
                    detail=ch.channel_id,
                )
            )
    else:
        try:
            listed = list_channels(repo=repo)
        except FirestoreUnavailableError:
            raise
        active = [c for c in listed.channels if c.status == "active"]
        slice_ch = sorted(active, key=lambda c: c.channel_id)[:ch_lim]
        out.checked_channels = len(slice_ch)
        out.warnings.append(
            "dry_run: Watchlist-Kanalchecks und Pending-Skriptjobs wurden nicht "
            "ausgeführt (keine Schreibvorgänge)."
        )

    # --- Script-Jobs ohne Production-Job anlegen ---
    try:
        need_pj = _completed_script_jobs_missing_production(repo, prod_lim)
    except FirestoreUnavailableError:
        raise

    for sj in need_pj:
        if dry_run:
            out.production_jobs_created += 1
            out.results.append(
                DailyCycleStepResult(
                    step="create_production_job",
                    script_job_id=sj.id,
                    outcome="dry_run",
                    detail="Would create production job.",
                )
            )
            continue
        try:
            cr = create_production_job_from_script_job(sj.id, repo=repo)
            if cr.created and cr.job is not None:
                out.production_jobs_created += 1
            out.results.append(
                DailyCycleStepResult(
                    step="create_production_job",
                    script_job_id=sj.id,
                    outcome="ok" if cr.created else "skipped",
                    detail=(cr.warnings[0] if cr.warnings else ""),
                )
            )
        except FirestoreUnavailableError:
            raise
        except Exception as e:
            logger.warning(
                "daily cycle create production job failed: job_id=%s type=%s",
                sj.id,
                type(e).__name__,
            )
            out.results.append(
                DailyCycleStepResult(
                    step="create_production_job",
                    script_job_id=sj.id,
                    outcome="failed",
                    detail=type(e).__name__,
                )
            )
            out.warnings.append(
                f"Production-Job-Erstellung fehlgeschlagen (script_job_id={sj.id})."
            )

    # --- Production-Pipeline (max. prod_lim neueste Jobs) ---
    try:
        pjobs = repo.list_production_jobs(300)
    except FirestoreUnavailableError:
        raise
    pjobs.sort(key=lambda j: j.created_at or "", reverse=True)
    batch = pjobs[:prod_lim]

    for pj in batch:
        pid = (pj.id or "").strip()
        if not pid:
            continue

        if dry_run:
            try:
                if repo.get_scene_plan(pid) is None:
                    gs_id = (pj.generated_script_id or "").strip()
                    gs_ok = False
                    if gs_id:
                        gs_ok = repo.get_generated_script(gs_id) is not None
                    if gs_ok:
                        out.scene_plans_created += 1
                if (
                    repo.get_scene_plan(pid) is not None
                    and repo.get_scene_assets(pid) is None
                ):
                    out.scene_assets_created += 1
                if (
                    repo.get_scene_assets(pid) is not None
                    and repo.get_voice_plan(pid) is None
                ):
                    out.voice_plans_created += 1
                if (
                    repo.get_voice_plan(pid) is not None
                    and repo.get_render_manifest(pid) is None
                ):
                    out.render_manifests_created += 1
                if repo.get_production_checklist(pid) is None:
                    out.checklists_initialized += 1
            except FirestoreUnavailableError:
                raise
            except Exception as e:
                logger.warning(
                    "daily cycle dry_run inspect failed: production_job_id=%s type=%s",
                    pid,
                    type(e).__name__,
                )
                out.warnings.append(
                    f"dry_run Inspektion fehlgeschlagen (production_job_id={pid})."
                )
            continue

        def _run_step(
            label: str,
            fn: Callable[[], None],
        ) -> None:
            try:
                fn()
            except FirestoreUnavailableError:
                raise
            except Exception as e:
                logger.warning(
                    "daily cycle %s failed: production_job_id=%s type=%s",
                    label,
                    pid,
                    type(e).__name__,
                )
                out.warnings.append(
                    f"{label} fehlgeschlagen ({pid}): {type(e).__name__}."
                )
                out.results.append(
                    DailyCycleStepResult(
                        step=label,
                        production_job_id=pid,
                        outcome="failed",
                        detail=type(e).__name__,
                    )
                )

        def step_scene_plan() -> None:
            before_sp = repo.get_scene_plan(pid)
            sp_out = generate_scene_plan(pid, repo=repo)
            if before_sp is None and sp_out.scene_plan is not None:
                out.scene_plans_created += 1

        def step_assets() -> None:
            before_sa = repo.get_scene_assets(pid)
            sa_out = generate_scene_assets(
                pid, SceneAssetsGenerateRequest(), repo=repo
            )
            if before_sa is None and sa_out.scene_assets is not None:
                out.scene_assets_created += 1

        def step_voice() -> None:
            before_vp = repo.get_voice_plan(pid)
            vp_out = generate_voice_plan(
                pid, VoicePlanGenerateRequest(), repo=repo
            )
            if before_vp is None and vp_out.voice_plan is not None:
                out.voice_plans_created += 1

        def step_manifest() -> None:
            before_rm = repo.get_render_manifest(pid)
            rm_out = generate_render_manifest(pid, repo=repo)
            if before_rm is None and rm_out.render_manifest is not None:
                out.render_manifests_created += 1

        def step_checklist() -> None:
            before_cl = repo.get_production_checklist(pid)
            cl_out = initialize_checklist(pid, repo=repo)
            if before_cl is None and cl_out.checklist is not None:
                out.checklists_initialized += 1

        try:
            _run_step("scene_plan", step_scene_plan)
            _run_step("scene_assets", step_assets)
            _run_step("voice_plan", step_voice)
            _run_step("render_manifest", step_manifest)
            _run_step("checklist", step_checklist)
        except FirestoreUnavailableError:
            raise

    return out


def normalize_provider_route_name(name: str) -> ProviderNameLiteral:
    n = (name or "").strip().lower()
    allowed = set(ALL_PROVIDER_NAMES)
    if n not in allowed:
        raise ValueError("Unknown provider_name.")
    return n  # type: ignore[return-value]


def list_provider_configs_service(
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ListProviderConfigsResponse:
    repo = repo or FirestoreWatchlistRepository()
    try:
        rows = repo.list_provider_configs()
    except FirestoreUnavailableError:
        raise
    return ListProviderConfigsResponse(configs=rows, warnings=[])


def upsert_provider_config_service(
    provider_name: str,
    body: ProviderConfigUpsertRequest,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ProviderConfig:
    repo = repo or FirestoreWatchlistRepository()
    name = normalize_provider_route_name(provider_name)
    now = utc_now_iso()
    try:
        existing = repo.get_provider_config(name)
    except FirestoreUnavailableError:
        raise
    base_data: Dict[str, Any]
    if existing is None:
        base_data = {
            "id": name,
            "provider_name": name,
            "enabled": False,
            "dry_run": True,
            "monthly_budget_limit": 0.0,
            "current_month_estimated_cost": 0.0,
            "status": "disabled",
            "notes": "",
            "created_at": now,
            "updated_at": now,
        }
    else:
        base_data = existing.model_dump()
    if body.enabled is not None:
        base_data["enabled"] = body.enabled
    if body.dry_run is not None:
        base_data["dry_run"] = body.dry_run
    if body.monthly_budget_limit is not None:
        base_data["monthly_budget_limit"] = float(body.monthly_budget_limit)
    if body.current_month_estimated_cost is not None:
        base_data["current_month_estimated_cost"] = float(
            body.current_month_estimated_cost
        )
    if body.status is not None:
        base_data["status"] = body.status
    if body.notes is not None:
        base_data["notes"] = body.notes
    merged = ProviderConfig.model_validate(base_data)
    merged = merged.model_copy(update={"updated_at": now})
    if existing is None:
        merged = merged.model_copy(update={"created_at": now})
    try:
        repo.upsert_provider_config(merged)
    except FirestoreUnavailableError:
        raise
    return merged


def seed_default_provider_configs_service(
    *,
    apply_writes: bool = False,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ProviderSeedDefaultsResponse:
    """BA 8.6: Standard-Seed auf ``provider_configs`` — idempotent (überspringt vorhandene IDs)."""
    repo = repo or FirestoreWatchlistRepository()
    now = utc_now_iso()
    seeds = seed_default_provider_configs(now_iso=now)
    ws: List[str] = []
    if not apply_writes:
        ws.append(
            "seed_defaults: apply_writes=false — keine Firestore-Schreibvorgänge (Vorschau)."
        )
        return ProviderSeedDefaultsResponse(
            created=0,
            skipped_existing=0,
            seeds=seeds,
            warnings=ws,
        )
    created = 0
    skipped = 0
    for doc in seeds:
        try:
            existing = repo.get_provider_config(doc.provider_name)
        except FirestoreUnavailableError:
            raise
        if existing is not None:
            skipped += 1
            continue
        try:
            repo.upsert_provider_config(doc)
        except FirestoreUnavailableError:
            raise
        created += 1
    if created == 0 and skipped == len(seeds):
        ws.append("Alle Seed-Provider existieren bereits — nichts geschrieben.")
    return ProviderSeedDefaultsResponse(
        created=created,
        skipped_existing=skipped,
        seeds=seeds,
        warnings=ws,
    )


def get_provider_status_service(
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ProviderStatusResponse:
    repo = repo or FirestoreWatchlistRepository()
    try:
        stored_list = repo.list_provider_configs()
    except FirestoreUnavailableError:
        raise
    by_name = {c.provider_name: c for c in stored_list}
    items: List[ProviderStatusItem] = []
    for name in ALL_PROVIDER_NAMES:
        row = by_name.get(name)
        if row is None:
            items.append(
                ProviderStatusItem(
                    provider_name=name,
                    enabled=False,
                    dry_run=True,
                    status="disabled",
                )
            )
        else:
            items.append(
                ProviderStatusItem(
                    provider_name=row.provider_name,
                    enabled=row.enabled,
                    dry_run=row.dry_run,
                    status=row.status,
                )
            )
    healthy, health_issues = validate_provider_runtime_health(stored_list)
    ws_tail: List[str] = []
    if not healthy:
        ws_tail.extend(health_issues)
    return ProviderStatusResponse(providers=items, warnings=ws_tail)


def plan_production_files_service(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> PlanProductionFilesResponse:
    """Geplante Storage-Pfade anlegen (idempotent für ``planned``)."""
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    ws: List[str] = []
    if not pid:
        return PlanProductionFilesResponse(
            files=[], planned_new=0, skipped_existing_planned=0, warnings=["empty id"]
        )
    try:
        pj = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if pj is None:
        return PlanProductionFilesResponse(
            files=[], planned_new=0, skipped_existing_planned=0, warnings=["not found"]
        )

    n_scenes = _scene_count_for_file_plan(repo, pid)
    now = utc_now_iso()

    desired: List[ProductionFileRecord] = []

    def add_rec(
        ft: ProductionFileTypeLiteral,
        path: str,
        scene_no: int,
        prov: ProviderNameLiteral,
    ) -> None:
        desired.append(
            ProductionFileRecord(
                id=_production_file_doc_id(pid, ft, scene_no),
                production_job_id=pid,
                file_type=ft,
                storage_path=path,
                public_url="",
                status="planned",
                provider_name=prov,
                scene_number=scene_no,
                created_at=now,
                updated_at=now,
            )
        )

    base = pid
    add_rec(
        "export_json",
        f"exports/{base}/production.json",
        0,
        "generic",
    )
    add_rec(
        "manifest",
        f"exports/{base}/manifest.json",
        0,
        "generic",
    )
    add_rec(
        "export_markdown",
        f"exports/{base}/production.md",
        0,
        "generic",
    )
    add_rec(
        "export_csv",
        f"exports/{base}/production.csv",
        0,
        "generic",
    )
    add_rec(
        "thumbnail",
        f"thumbnails/{base}/thumbnail.png",
        0,
        "generic",
    )
    for i in range(1, n_scenes + 1):
        sn = f"{i:03d}"
        add_rec(
            "voice",
            f"voice/{base}/scene_{sn}.mp3",
            i,
            "elevenlabs",
        )
        add_rec(
            "image",
            f"images/{base}/scene_{sn}.png",
            i,
            "leonardo",
        )
        add_rec(
            "video",
            f"videos/{base}/scene_{sn}.mp4",
            i,
            "kling",
        )

    planned_new = 0
    skipped = 0
    out_files: List[ProductionFileRecord] = []

    for rec in desired:
        try:
            ex = repo.get_production_file_by_id(rec.id)
        except FirestoreUnavailableError:
            raise
        if ex is not None and ex.status == "planned":
            skipped += 1
            out_files.append(ex)
            continue
        if ex is not None:
            out_files.append(ex)
            continue
        try:
            repo.upsert_production_file(rec)
        except FirestoreUnavailableError:
            raise
        planned_new += 1
        out_files.append(rec)

    out_files.sort(key=lambda x: (x.file_type, x.scene_number, x.storage_path))
    return PlanProductionFilesResponse(
        files=out_files,
        planned_new=planned_new,
        skipped_existing_planned=skipped,
        warnings=ws,
    )


def list_production_files_service(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ListProductionFilesResponse:
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    if not pid:
        return ListProductionFilesResponse(files=[], warnings=["empty id"])
    try:
        rows = repo.list_production_files_for_job(pid)
    except FirestoreUnavailableError:
        raise
    return ListProductionFilesResponse(files=rows, warnings=[])


def init_execution_queue_service(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ExecutionQueueInitResponse:
    """Aus ``production_files`` ausführbare ``execution_jobs`` erzeugen (idempotent)."""
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    ws: List[str] = []
    if not pid:
        return ExecutionQueueInitResponse(
            production_job_id="",
            jobs=[],
            created_new=0,
            reused_existing=0,
            warnings=["production_job_id ist leer."],
        )
    try:
        pj = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if pj is None:
        return ExecutionQueueInitResponse(
            production_job_id=pid,
            jobs=[],
            created_new=0,
            reused_existing=0,
            warnings=["not found"],
        )
    try:
        files = repo.list_production_files_for_job(pid)
    except FirestoreUnavailableError:
        raise
    if not files:
        ws.append(
            "Keine production_files — zuerst POST …/production/jobs/{id}/files/plan ausführen."
        )
        return ExecutionQueueInitResponse(
            production_job_id=pid,
            jobs=[],
            created_new=0,
            reused_existing=0,
            warnings=ws,
        )

    cat = compute_category_totals_v1(repo=repo, pj=pj)
    counts = count_production_files_by_file_type(files)
    now = utc_now_iso()
    jobs_out: List[ExecutionJob] = []
    created_new = 0
    reused_existing = 0

    for pf in sorted(files, key=lambda x: (x.file_type, x.scene_number, x.id)):
        try:
            stub = build_execution_job_stub(
                pf,
                production_job_id=pid,
                repo=repo,
                cat=cat,
                file_type_counts=counts,
                now_iso=now,
            )
        except FirestoreUnavailableError:
            raise
        try:
            existing = repo.get_execution_job(stub.id)
        except FirestoreUnavailableError:
            raise
        if existing is not None:
            jobs_out.append(existing)
            reused_existing += 1
            continue
        try:
            repo.upsert_execution_job(stub)
        except FirestoreUnavailableError:
            raise
        created_new += 1
        jobs_out.append(stub)

    if reused_existing > 0:
        ws.append(
            "Ein oder mehrere execution_jobs existierten bereits; bestehende Einträge wurden nicht überschrieben (idempotent)."
        )
    jobs_sorted = sorted(
        jobs_out,
        key=lambda j: (
            getattr(j, "priority", 5),
            getattr(j, "job_type", ""),
            getattr(j, "scene_number", None) or 0,
            getattr(j, "id", ""),
        ),
    )
    return ExecutionQueueInitResponse(
        production_job_id=pid,
        jobs=jobs_sorted,
        created_new=created_new,
        reused_existing=reused_existing,
        warnings=ws,
    )


def list_execution_jobs_service(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ExecutionQueueGetResponse:
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    ws: List[str] = []
    if not pid:
        return ExecutionQueueGetResponse(jobs=[], warnings=["production_job_id ist leer."])
    try:
        pj = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if pj is None:
        return ExecutionQueueGetResponse(jobs=[], warnings=["not found"])
    try:
        jobs = repo.list_execution_jobs_for_job(pid)
    except FirestoreUnavailableError:
        raise
    return ExecutionQueueGetResponse(jobs=jobs, warnings=ws)


def calculate_production_costs_service(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ProductionCostsCalculateResponse:
    repo = repo or FirestoreWatchlistRepository()
    ws: List[str] = []
    pid = (production_job_id or "").strip()
    if not pid:
        return ProductionCostsCalculateResponse(costs=None, warnings=["production_job_id ist leer."])
    try:
        pj = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if pj is None:
        return ProductionCostsCalculateResponse(costs=None, warnings=["not found"])

    existed: Optional[ProductionCosts] = None
    try:
        existed = repo.get_production_costs(pid)
    except FirestoreUnavailableError:
        raise

    existed_created = getattr(existed, "created_at", None) if existed else None

    merged = build_production_costs_document(
        repo=repo,
        pj=pj,
        now_iso=utc_now_iso(),
        existing_created_at=existed_created if isinstance(existed_created, str) else None,
    )
    try:
        repo.upsert_production_costs(merged)
    except FirestoreUnavailableError:
        raise
    return ProductionCostsCalculateResponse(costs=merged, warnings=ws)


def get_production_costs_service(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ProductionCostsGetResponse:
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    ws: List[str] = []
    if not pid:
        return ProductionCostsGetResponse(costs=None, warnings=["production_job_id ist leer."])
    try:
        pj = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if pj is None:
        return ProductionCostsGetResponse(costs=None, warnings=["not found"])
    try:
        row = repo.get_production_costs(pid)
    except FirestoreUnavailableError:
        raise
    if row is None:
        ws.append("production_costs nicht berechnet — POST …/costs/calculate nutzen.")
    return ProductionCostsGetResponse(costs=row, warnings=ws)


def _pipeline_audit_row_from_draft(
    *,
    draft: PipelineAuditDraft,
    doc_id: str,
    now_iso: str,
    existing: Optional[PipelineAudit],
) -> PipelineAudit:
    first_at = getattr(existing, "detected_at", None) if existing else None
    detected_at_val = (
        first_at if isinstance(first_at, str) and first_at.strip() else now_iso
    )
    prev_notes = getattr(existing, "notes", "") if existing else ""
    return PipelineAudit(
        id=doc_id,
        production_job_id=draft.production_job_id,
        script_job_id=draft.script_job_id,
        audit_type=draft.audit_type,
        severity=draft.severity,
        status="open",
        detected_issue=draft.detected_issue,
        recommended_action=draft.recommended_action,
        auto_repairable=draft.auto_repairable,
        detected_at=detected_at_val,
        resolved_at=None,
        notes=prev_notes or "",
    )


def run_pipeline_audit_service(
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
    body: Optional[PipelineAuditRunRequest] = None,
) -> PipelineAuditRunResponse:
    """Lädt Produktjobs + läuft Stuck-Analyse für ScriptJobs; persistiert Audits."""
    repo = repo or FirestoreWatchlistRepository()
    req = body if body is not None else PipelineAuditRunRequest()
    ws: List[str] = []
    now_iso = utc_now_iso()

    drafts: List[PipelineAuditDraft] = []
    stuck_drafts: List[PipelineAuditDraft] = []
    try:
        stuck_drafts = scan_stuck_running_script_issues(
            repo, threshold_minutes=req.stuck_threshold_minutes
        )
        drafts.extend(stuck_drafts)
    except FirestoreUnavailableError:
        raise

    scanned_pids: List[str] = []
    try:
        pjobs = repo.list_production_jobs(limit=req.production_job_limit)
    except FirestoreUnavailableError:
        raise
    for pj in pjobs:
        scanned_pids.append(pj.id)
        try:
            drafts.extend(
                scan_production_job_for_issues(
                    repo,
                    pj_id=pj.id,
                    pj_status=pj.status,
                    generated_script_ref=pj.generated_script_id,
                )
            )
        except FirestoreUnavailableError:
            raise

    this_run_doc_ids: Set[str] = set()
    written: List[PipelineAudit] = []
    audits_written = 0
    for d in drafts:
        doc_id = pipeline_audit_document_id_from_draft(d)
        existing: Optional[PipelineAudit] = None
        try:
            existing = repo.get_pipeline_audit(doc_id)
        except FirestoreUnavailableError:
            raise
        row = _pipeline_audit_row_from_draft(
            draft=d, doc_id=doc_id, now_iso=now_iso, existing=existing
        )
        try:
            repo.upsert_pipeline_audit(row)
        except FirestoreUnavailableError:
            raise
        this_run_doc_ids.add(doc_id)
        written.append(row)
        audits_written += 1

    resolved_cnt = 0
    scanned_set = set(scanned_pids)
    if req.resolve_missing_from_scan_set and (scanned_set or drafts):
        try:
            opens = repo.stream_pipeline_audits_recent(limit=2200)
        except FirestoreUnavailableError:
            raise
        open_only = [a for a in opens if getattr(a, "status", "") == "open"]
        for a in open_only:
            if a.id in this_run_doc_ids:
                continue
            pj_here = (a.production_job_id or "").strip()
            if not pj_here:
                continue
            if pj_here in scanned_set:
                resolve_me = True
            else:
                resolve_me = False
            if resolve_me:
                try:
                    repo.patch_pipeline_audit(
                        a.id,
                        {"status": "resolved", "resolved_at": now_iso},
                    )
                except FirestoreUnavailableError:
                    raise
                resolved_cnt += 1

    return PipelineAuditRunResponse(
        scanned_production_jobs=len(scanned_set),
        scanned_script_jobs_stuck_candidates=len(stuck_drafts),
        audits_written=audits_written,
        audits_resolved=resolved_cnt,
        audits=written,
        warnings=ws,
    )


def list_pipeline_audits_service(
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
    limit: int = 150,
    status: Optional[str] = None,
    severity: Optional[str] = None,
) -> ListPipelineAuditsResponse:
    repo = repo or FirestoreWatchlistRepository()
    lim = max(1, min(int(limit), 500))
    ws: List[str] = []
    try:
        rows = repo.stream_pipeline_audits_recent(limit=2200)
    except FirestoreUnavailableError:
        raise
    filt: List[PipelineAudit] = []
    st_ok = (status or "").strip().lower() if status else None
    sv_ok = (severity or "").strip().lower() if severity else None
    for r in rows:
        if st_ok:
            rr = getattr(r, "status", "") or ""
            if (rr or "").lower() != st_ok:
                continue
        if sv_ok:
            sev = getattr(r, "severity", "") or ""
            if (sev or "").lower() != sv_ok:
                continue
        filt.append(r)
        if len(filt) >= lim:
            break
    return ListPipelineAuditsResponse(audits=filt[:lim], warnings=ws)


def _normalize_recovery_step(raw: str) -> str:
    s = (raw or "").strip().lower().replace("-", "_")
    aliases = {
        "sceneplan": "scene_plan",
        "scene_assets": "scene_assets",
        "voiceplan": "voice_plan",
        "voice_plan": "voice_plan",
        "render": "render_manifest",
        "manifest": "render_manifest",
        "execution_queue": "execution",
        "cost": "costs",
        "budget": "costs",
        "production_files": "files",
    }
    return aliases.get(s, s)


def retry_production_pipeline_step_service(
    production_job_id: str,
    body: ProductionRecoveryRetryRequest,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ProductionPipelineRecoveryResponse:
    """Gezielt Generate-/Planning-Schritte erneut ausführen — getrennt von Status-„retry“."""
    repo = repo or FirestoreWatchlistRepository()
    ws: List[str] = []
    pid = (production_job_id or "").strip()
    if not pid:
        ra = RecoveryAction(
            id="rec_invalid",
            production_job_id="",
            action_kind="retry_scene_plan",
            requested_step_raw=(body.step or ""),
            status="failed",
            detail="production_job_id leer",
            warnings=["production_job_id leer"],
            created_at=utc_now_iso(),
            finished_at=utc_now_iso(),
        )
        return ProductionPipelineRecoveryResponse(action=ra, warnings=ws)
    step = _normalize_recovery_step(body.step)
    rid = f"rec_{uuid.uuid4().hex[:26]}"
    now_start = utc_now_iso()

    kind: RecoveryActionKindLiteral = "retry_scene_plan"
    warn_accum: List[str] = []

    def _finalize(
        *,
        kk: RecoveryActionKindLiteral,
        ok: bool,
        detail_txt: str,
    ) -> RecoveryAction:
        finished = utc_now_iso()
        ra = RecoveryAction(
            id=rid,
            production_job_id=pid,
            action_kind=kk,
            requested_step_raw=body.step or "",
            status="completed" if ok else "failed",
            detail=detail_txt,
            warnings=list(warn_accum),
            created_at=now_start,
            finished_at=finished,
        )
        try:
            repo.upsert_recovery_action(ra)
        except FirestoreUnavailableError:
            raise
        return ra

    try:
        pj = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if pj is None:
        ra = RecoveryAction(
            id=rid,
            production_job_id=pid,
            action_kind="reset_pipeline_step",
            requested_step_raw=body.step or "",
            status="failed",
            detail="Production job nicht gefunden",
            warnings=["not found"],
            created_at=now_start,
            finished_at=utc_now_iso(),
        )
        try:
            repo.upsert_recovery_action(ra)
        except FirestoreUnavailableError:
            raise
        return ProductionPipelineRecoveryResponse(action=ra, warnings=["not found"])

    ok_detail = "ok"

    try:
        if step in ("scene_plan",):
            kind = "retry_scene_plan"
            out = generate_scene_plan(pid, repo=repo)
            if out.scene_plan is None:
                ws.extend(out.warnings or [])
                return ProductionPipelineRecoveryResponse(
                    action=_finalize(
                        kk=kind,
                        ok=False,
                        detail_txt=out.warnings[0] if out.warnings else "scene_plan failed",
                    ),
                    warnings=list(ws),
                )

        elif step in ("scene_assets",):
            kind = "retry_scene_assets"
            out_a = generate_scene_assets(
                pid, SceneAssetsGenerateRequest(), repo=repo
            )
            if out_a.scene_assets is None:
                ws.extend(out_a.warnings or [])
                return ProductionPipelineRecoveryResponse(
                    action=_finalize(
                        kk=kind,
                        ok=False,
                        detail_txt=out_a.warnings[0]
                        if out_a.warnings
                        else "scene_assets failed",
                    ),
                    warnings=list(ws),
                )

        elif step in ("voice_plan",):
            kind = "retry_voice_plan"
            out_v = generate_voice_plan(
                pid,
                VoicePlanGenerateRequest(),
                repo=repo,
            )
            if out_v.voice_plan is None:
                ws.extend(out_v.warnings or [])
                return ProductionPipelineRecoveryResponse(
                    action=_finalize(
                        kk=kind,
                        ok=False,
                        detail_txt=out_v.warnings[0]
                        if out_v.warnings
                        else "voice_plan failed",
                    ),
                    warnings=list(ws),
                )

        elif step in ("render_manifest",):
            kind = "retry_render_manifest"
            out_rm = generate_render_manifest(pid, repo=repo)
            if out_rm.render_manifest is None:
                ws.extend(out_rm.warnings or [])
                return ProductionPipelineRecoveryResponse(
                    action=_finalize(
                        kk=kind,
                        ok=False,
                        detail_txt=out_rm.warnings[0]
                        if out_rm.warnings
                        else "render_manifest failed",
                    ),
                    warnings=list(ws),
                )

        elif step in ("execution",):
            kind = "retry_execution_job"
            ex_out = init_execution_queue_service(pid, repo=repo)
            ws.extend(ex_out.warnings or [])
            ok_detail = f"jobs={len(ex_out.jobs)} created_new={ex_out.created_new}"

        elif step in ("costs",):
            kind = "retry_cost_estimate"
            c_out = calculate_production_costs_service(pid, repo=repo)
            if c_out.costs is None:
                ws.extend(c_out.warnings or [])
                return ProductionPipelineRecoveryResponse(
                    action=_finalize(
                        kk=kind,
                        ok=False,
                        detail_txt=c_out.warnings[0]
                        if c_out.warnings
                        else "costs failed",
                    ),
                    warnings=list(ws),
                )

        elif step in ("files",):
            kind = "retry_production_files"
            fp = plan_production_files_service(pid, repo=repo)
            ws.extend(fp.warnings or [])
            ok_detail = f"planned_new={fp.planned_new}"

        elif step == "full_rebuild":
            kind = "full_rebuild"
            seq_warnings: List[str] = []

            sp = generate_scene_plan(pid, repo=repo)
            if sp.scene_plan is None:
                seq_warnings.extend(sp.warnings or [])
                warn_accum.extend(seq_warnings)
                return ProductionPipelineRecoveryResponse(
                    action=_finalize(
                        kk=kind,
                        ok=False,
                        detail_txt="scene_plan blocking",
                    ),
                    warnings=list(warn_accum),
                )
            sa2 = generate_scene_assets(
                pid, SceneAssetsGenerateRequest(), repo=repo
            )
            if sa2.scene_assets is None:
                seq_warnings.extend(sa2.warnings or [])
                warn_accum.extend(seq_warnings)
                return ProductionPipelineRecoveryResponse(
                    action=_finalize(kk=kind, ok=False, detail_txt="scene_assets blocking"),
                    warnings=list(warn_accum),
                )
            vp2 = generate_voice_plan(
                pid, VoicePlanGenerateRequest(), repo=repo
            )
            if vp2.voice_plan is None:
                seq_warnings.extend(vp2.warnings or [])
                warn_accum.extend(seq_warnings)
                return ProductionPipelineRecoveryResponse(
                    action=_finalize(kk=kind, ok=False, detail_txt="voice_plan blocking"),
                    warnings=list(warn_accum),
                )
            rm2 = generate_render_manifest(pid, repo=repo)
            if rm2.render_manifest is None:
                seq_warnings.extend(rm2.warnings or [])
                warn_accum.extend(seq_warnings)
                return ProductionPipelineRecoveryResponse(
                    action=_finalize(
                        kk=kind, ok=False, detail_txt="render_manifest blocking"
                    ),
                    warnings=list(warn_accum),
                )
            pf2 = plan_production_files_service(pid, repo=repo)
            seq_warnings.extend(pf2.warnings or [])
            init_execution_queue_service(pid, repo=repo)
            calculate_production_costs_service(pid, repo=repo)
            warn_accum.extend(seq_warnings)
            ok_detail = "full_rebuild ok"

        else:
            ws.append(f"Unbekannter recovery step: {body.step}")
            warn_accum.extend(ws)
            return ProductionPipelineRecoveryResponse(
                action=_finalize(
                    kk="reset_pipeline_step",
                    ok=False,
                    detail_txt=f"unsupported step={body.step}",
                ),
                warnings=list(warn_accum),
            )

        warn_accum.extend(ws)
        return ProductionPipelineRecoveryResponse(
            action=_finalize(kk=kind, ok=True, detail_txt=ok_detail),
            warnings=list(warn_accum),
        )
    except FirestoreUnavailableError:
        raise


def pipeline_monitoring_summary_service(
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> PipelineMonitoringSummaryResponse:
    repo = repo or FirestoreWatchlistRepository()
    ws: List[str] = []
    try:
        audits = repo.stream_pipeline_audits_recent(limit=1500)
    except FirestoreUnavailableError:
        raise
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
    resolved_recent = [
        a
        for a in audits
        if getattr(a, "status", "") == "resolved"
    ][:24]
    try:
        rec = repo.stream_recovery_actions_recent(limit=30)
    except FirestoreUnavailableError:
        raise
    return PipelineMonitoringSummaryResponse(
        audits_open_critical=oc,
        audits_open_warning=ow,
        audits_open_info=oi,
        audits_recent_resolved_sample=resolved_recent,
        recovery_actions_recent=rec,
        warnings=ws,
    )


def get_control_panel_summary_service(
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ControlPanelSummaryResponse:
    """BA 8.4 LIGHT — Founder Control Panel (read-only Aggregate)."""
    from app.watchlist.control_panel import build_control_panel_summary

    repo = repo or FirestoreWatchlistRepository()
    return build_control_panel_summary(repo=repo)


def run_status_normalization_service(
    *,
    body: StatusNormalizeRunRequest,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> StatusNormalizeRunResponse:
    """BA 8.3 — Statusketten stabilisieren und Eskalationen schreiben."""
    repo = repo or FirestoreWatchlistRepository()
    now_iso = utc_now_iso()
    try:
        recovery = repo.stream_recovery_actions_recent(limit=120)
    except FirestoreUnavailableError:
        raise
    resp, _ = normalize_pipeline_status(
        repo,
        opts=body,
        utc_now_iso=now_iso,
        recent_recovery_actions=recovery,
    )
    return resp


def list_pipeline_escalations_service(
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
    limit: int = 150,
) -> ListPipelineEscalationsResponse:
    repo = repo or FirestoreWatchlistRepository()
    lim = max(1, min(int(limit), 400))
    try:
        rows = repo.stream_pipeline_escalations_recent(limit=lim)
    except FirestoreUnavailableError:
        raise
    return ListPipelineEscalationsResponse(escalations=rows, warnings=[])


def review_generated_script_for_job(
    job_id: str,
    *,
    repo: FirestoreWatchlistRepository | None = None,
) -> ReviewGeneratedScriptJobResponse:
    """Optionaler Review-Schritt; schlägt niemals den ScriptJob-Status fehl."""
    repo = repo or FirestoreWatchlistRepository()
    jid = (job_id or "").strip()
    ws: List[str] = []
    if not jid:
        ws.append("job_id is empty.")
        return ReviewGeneratedScriptJobResponse(job_id=jid, review=None, warnings=ws)

    try:
        job = repo.get_script_job(jid)
    except FirestoreUnavailableError:
        raise

    if job is None:
        ws.append("Script job not found.")
        return ReviewGeneratedScriptJobResponse(job_id=jid, review=None, warnings=ws)

    if job.status != "completed":
        ws.append(
            f"Review nur für completed Jobs gedacht (aktueller Status: {job.status})."
        )
        return ReviewGeneratedScriptJobResponse(job_id=jid, review=None, warnings=ws)

    gid_raw = (job.generated_script_id or "").strip()
    if not gid_raw:
        ws.append(
            "Review nur mit gesetztem generated_script_id am ScriptJob (kein Skriptbezug)."
        )
        return ReviewGeneratedScriptJobResponse(job_id=jid, review=None, warnings=ws)

    script_id = gid_raw
    try:
        gs = repo.get_generated_script(script_id)
    except FirestoreUnavailableError:
        raise

    if gs is None:
        ws.append("Generated script document not found; review skipped.")
        return ReviewGeneratedScriptJobResponse(job_id=jid, review=None, warnings=ws)

    text = (gs.full_script or "").strip()
    if not text:
        ws.append("Generated script body is empty; review skipped.")
        return ReviewGeneratedScriptJobResponse(job_id=jid, review=None, warnings=ws)

    req = ReviewScriptRequest(
        source_url=job.video_url or gs.source_url,
        source_type="youtube_transcript",
        source_text="",
        generated_script=text,
        target_language=job.target_language,
        prior_warnings=list(gs.warnings or []),
    )
    try:
        resp = review_script(req)
    except Exception as e:
        logger.warning(
            "review_generated_script_for_job unexpected: job_id=%s type=%s",
            jid,
            type(e).__name__,
        )
        ws.append(
            "Review-Schritt konnte nicht ausgeführt werden; gespeichertes Skript und Job-Status bleiben unverändert."
        )
        return ReviewGeneratedScriptJobResponse(job_id=jid, review=None, warnings=ws)

    rid = f"rr_{uuid.uuid4().hex[:24]}"
    stored = ReviewResultStored(
        id=rid,
        script_job_id=jid,
        generated_script_id=gid_raw,
        source_url=req.source_url,
        risk_level=str(resp.risk_level),
        originality_score=resp.originality_score,
        similarity_flags=list(resp.similarity_flags),
        issues=list(resp.issues),
        recommendations=list(resp.recommendations),
        warnings=list(resp.warnings or []),
        created_at=utc_now_iso(),
    )
    try:
        repo.create_review_result(stored)
        repo.set_script_job_review_result_id(jid, rid)
        try:
            pv_link = repo.get_processed_video(job.video_id)
        except FirestoreUnavailableError:
            raise
        if pv_link is not None:
            same_job = (pv_link.script_job_id or "").strip() == jid
            same_script = (pv_link.generated_script_id or "").strip() == gid_raw
            if same_job or same_script:
                try:
                    repo.update_processed_video_review_result_id(
                        pv_link.video_id, rid
                    )
                except FirestoreUnavailableError:
                    ws.append(
                        "Review gespeichert; Verknüpfung auf processed_videos "
                        "konnte nicht gesetzt werden (Firestore)."
                    )
    except FirestoreUnavailableError:
        raise
    except Exception as e:
        logger.warning(
            "review_result persist failed: job_id=%s type=%s",
            jid,
            type(e).__name__,
        )
        ws.append(
            "Review-Ergebnis konnte nicht in Firestore gespeichert werden; "
            "HTTP-Antwort enthält die Auswertung, ScriptJob-Status unverändert."
        )

    return ReviewGeneratedScriptJobResponse(job_id=jid, review=resp, warnings=ws)


def _parse_iso_to_utc(s: str) -> datetime | None:
    raw = (s or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _count_or_warn(
    label_de: str,
    fn: Callable[[], int],
    warnings: List[str],
) -> int:
    v = fn()
    if v < 0:
        warnings.append(
            f"Zählung „{label_de}“ nicht ermittelbar (Firestore-Aggregation/Stream); "
            "Wert als 0 gesetzt."
        )
        return 0
    return v


def analyze_stuck_running_script_jobs(
    threshold_minutes: int = 45,
    *,
    repo: FirestoreWatchlistRepository | None = None,
) -> WatchlistStuckRunningAnalysisResponse:
    """Nur Analyse: ``running``-Jobs mit ``started_at`` älter als Schwelle — kein Auto-Fix."""
    repo = repo or FirestoreWatchlistRepository()
    thr = max(5, min(int(threshold_minutes), 24 * 60))
    ws: List[str] = []
    try:
        running = repo.list_running_script_jobs()
    except FirestoreUnavailableError:
        raise
    now = datetime.now(timezone.utc)
    cut = now - timedelta(minutes=thr)
    stuck: List[WatchlistStuckRunningJobItem] = []
    missing_started = 0
    for j in running:
        st = _parse_iso_to_utc(j.started_at or "")
        if st is None:
            missing_started += 1
            continue
        if st <= cut:
            stuck.append(
                WatchlistStuckRunningJobItem(
                    job_id=j.id,
                    started_at=j.started_at,
                    channel_id=j.channel_id,
                    video_id=j.video_id,
                )
            )
    if missing_started:
        ws.append(
            f"{missing_started} running Job(s) ohne auswertbares started_at "
            "(manuell prüfen)."
        )
    if stuck:
        ws.append(
            f"{len(stuck)} Job(s) seit mindestens {thr} Minuten im Status „running“."
        )
    return WatchlistStuckRunningAnalysisResponse(
        threshold_minutes=thr,
        stuck_jobs=stuck,
        warnings=ws,
    )


def get_watchlist_dashboard(
    *,
    repo: FirestoreWatchlistRepository | None = None,
    stuck_threshold_minutes: int = 45,
) -> WatchlistDashboardResponse:
    repo = repo or FirestoreWatchlistRepository()
    health_ws: List[str] = []
    try:
        ch_resp = list_channels(repo=repo)
    except FirestoreUnavailableError:
        raise
    chs = ch_resp.channels
    pv_total = _count_or_warn(
        "processed_videos gesamt",
        lambda: repo.count_collection(PROCESSED_VIDEOS_COLLECTION),
        health_ws,
    )
    pv_skipped = _count_or_warn(
        "processed_videos übersprungen",
        lambda: repo.count_processed_videos_by_status("skipped"),
        health_ws,
    )
    pv_tr = _count_or_warn(
        "processed_videos transcript_not_available",
        lambda: repo.count_processed_videos_by_skip_reason(
            "transcript_not_available"
        ),
        health_ws,
    )
    sj_pending = _count_or_warn(
        "script_jobs pending",
        lambda: repo.count_script_jobs_by_status("pending"),
        health_ws,
    )
    sj_running = _count_or_warn(
        "script_jobs running",
        lambda: repo.count_script_jobs_by_status("running"),
        health_ws,
    )
    sj_completed = _count_or_warn(
        "script_jobs completed",
        lambda: repo.count_script_jobs_by_status("completed"),
        health_ws,
    )
    sj_failed = _count_or_warn(
        "script_jobs failed",
        lambda: repo.count_script_jobs_by_status("failed"),
        health_ws,
    )
    sj_skipped = _count_or_warn(
        "script_jobs skipped",
        lambda: repo.count_script_jobs_by_status("skipped"),
        health_ws,
    )
    gs_total = _count_or_warn(
        "generated_scripts gesamt",
        lambda: repo.count_collection(GENERATED_SCRIPTS_COLLECTION),
        health_ws,
    )
    counts = WatchlistDashboardCounts(
        channels_active=sum(1 for c in chs if c.status == "active"),
        channels_paused=sum(1 for c in chs if c.status == "paused"),
        channels_error=sum(1 for c in chs if c.status == "error"),
        processed_videos_total=pv_total,
        processed_videos_skipped_total=pv_skipped,
        processed_videos_transcript_not_available_total=pv_tr,
        script_jobs_pending=sj_pending,
        script_jobs_running=sj_running,
        script_jobs_completed=sj_completed,
        script_jobs_failed=sj_failed,
        script_jobs_skipped=sj_skipped,
        generated_scripts_total=gs_total,
    )

    last_ok: str | None = None
    try:
        last_ok = repo.get_latest_completed_job_completed_at()
        if last_ok is None and sj_completed > 0:
            health_ws.append(
                "Es gibt completed Jobs, aber der neueste completed_at "
                "konnte nicht gelesen werden (Index oder Daten inkonsistent)."
            )
    except Exception as e:
        logger.warning(
            "dashboard latest completed lookup failed: type=%s", type(e).__name__
        )
        health_ws.append(
            "Letzter erfolgreicher Job-Zeitpunkt nicht verfügbar (Query-Fehler)."
        )

    last_cycle: str | None = None
    try:
        last_cycle = repo.get_last_automation_cycle_at()
    except FirestoreUnavailableError:
        raise
    except Exception as e:
        logger.warning(
            "dashboard last cycle read failed: type=%s", type(e).__name__
        )
        health_ws.append("last_run_cycle_at konnte nicht gelesen werden.")

    try:
        stuck_info = analyze_stuck_running_script_jobs(
            stuck_threshold_minutes, repo=repo
        )
        health_ws.extend(stuck_info.warnings)
    except FirestoreUnavailableError:
        raise
    except Exception as e:
        logger.warning("dashboard stuck analysis failed: type=%s", type(e).__name__)
        health_ws.append("Stuck-Job-Analyse übersprungen (unerwarteter Fehler).")

    return WatchlistDashboardResponse(
        counts=counts,
        health=WatchlistDashboardHealth(
            last_successful_job_at=last_ok,
            last_run_cycle_at=last_cycle,
            warnings=health_ws,
        ),
    )


def _job_error_code_key(job: ScriptJob) -> str:
    c = (job.error_code or "").strip()
    if c:
        return c
    return "(empty_error_code)"


def get_watchlist_errors_summary(
    *,
    max_docs: int = 500,
    repo: FirestoreWatchlistRepository | None = None,
) -> WatchlistErrorsSummaryResponse:
    repo = repo or FirestoreWatchlistRepository()
    warnings: List[str] = []
    cap = max(50, min(int(max_docs), 2000))
    try:
        jobs, trunc_j = repo.stream_script_jobs_for_error_summary(max_docs=cap)
        pvs, trunc_p = repo.stream_processed_videos_skipped_for_summary(max_docs=cap)
    except FirestoreUnavailableError:
        raise

    if trunc_j:
        warnings.append(
            f"script_jobs-Stichprobe erreichte das Limit ({cap}); Aggregation unvollständig."
        )
    if trunc_p:
        warnings.append(
            f"processed_videos-Stichprobe erreichte das Limit ({cap}); Aggregation unvollständig."
        )

    code_counter: Counter[str] = Counter()
    code_samples: Dict[str, List[str]] = {}
    for j in jobs:
        key = _job_error_code_key(j)
        code_counter[key] += 1
        if key not in code_samples:
            code_samples[key] = []
        if len(code_samples[key]) < 3:
            code_samples[key].append(j.id)

    skip_counter: Counter[str] = Counter()
    skip_samples: Dict[str, List[str]] = {}
    for pv in pvs:
        key = (pv.skip_reason or "").strip() or "(empty_skip_reason)"
        skip_counter[key] += 1
        if key not in skip_samples:
            skip_samples[key] = []
        if len(skip_samples[key]) < 3:
            skip_samples[key].append(pv.video_id)

    by_err = [
        WatchlistErrorCodeSummaryItem(
            error_code=k,
            count=v,
            sample_job_ids=list(code_samples.get(k, [])),
        )
        for k, v in sorted(
            code_counter.items(), key=lambda x: (-x[1], x[0])
        )
    ]
    by_skip = [
        WatchlistSkipReasonSummaryItem(
            skip_reason=k,
            count=v,
            sample_video_ids=list(skip_samples.get(k, [])),
        )
        for k, v in sorted(
            skip_counter.items(), key=lambda x: (-x[1], x[0])
        )
    ]

    warnings.append(
        "Error-Summary basiert auf Stichproben fehlgeschlagener/übersprungener Jobs "
        "und übersprungener Videos (kein vollständiger Collection-Scan)."
    )
    return WatchlistErrorsSummaryResponse(
        by_error_code=by_err,
        by_skip_reason=by_skip,
        warnings=warnings,
        scanned_script_jobs=len(jobs),
        scanned_processed_videos=len(pvs),
    )


def retry_script_job(
    job_id: str,
    *,
    repo: FirestoreWatchlistRepository | None = None,
) -> WatchlistJobActionResponse:
    repo = repo or FirestoreWatchlistRepository()
    jid = (job_id or "").strip()
    ws: List[str] = []
    if not jid:
        ws.append("job_id is empty.")
        return WatchlistJobActionResponse(job=None, warnings=ws)
    try:
        job = repo.get_script_job(jid)
    except FirestoreUnavailableError:
        raise
    if job is None:
        ws.append("Script job not found.")
        return WatchlistJobActionResponse(job=None, warnings=ws)
    if job.status not in ("failed", "skipped"):
        ws.append(
            f"Retry nur für failed/skipped sinnvoll (aktuell: {job.status})."
        )
        return WatchlistJobActionResponse(job=job, warnings=ws)
    try:
        repo.reset_script_job_to_pending(jid)
    except FirestoreUnavailableError:
        raise
    try:
        refreshed = repo.get_script_job(jid)
    except FirestoreUnavailableError:
        raise
    return WatchlistJobActionResponse(job=refreshed or job, warnings=ws)


def skip_script_job_manually(
    job_id: str,
    *,
    repo: FirestoreWatchlistRepository | None = None,
) -> WatchlistJobActionResponse:
    repo = repo or FirestoreWatchlistRepository()
    jid = (job_id or "").strip()
    ws: List[str] = []
    if not jid:
        ws.append("job_id is empty.")
        return WatchlistJobActionResponse(job=None, warnings=ws)
    try:
        job = repo.get_script_job(jid)
    except FirestoreUnavailableError:
        raise
    if job is None:
        ws.append("Script job not found.")
        return WatchlistJobActionResponse(job=None, warnings=ws)
    if job.status not in ("pending", "failed"):
        ws.append(
            "Skip nur für pending oder failed vorgesehen "
            f"(aktuell: {job.status})."
        )
        return WatchlistJobActionResponse(job=job, warnings=ws)
    try:
        repo.mark_script_job_skipped_manual(
            jid,
            error_code="manual_skip",
            error_message="manual_skip",
        )
    except FirestoreUnavailableError:
        raise
    try:
        refreshed = repo.get_script_job(jid)
    except FirestoreUnavailableError:
        raise
    return WatchlistJobActionResponse(job=refreshed or job, warnings=ws)


def pause_watchlist_channel(
    channel_id: str,
    *,
    repo: FirestoreWatchlistRepository | None = None,
) -> WatchlistChannelStatusResponse:
    repo = repo or FirestoreWatchlistRepository()
    cid = (channel_id or "").strip()
    ws: List[str] = []
    if not cid:
        ws.append("channel_id is empty.")
        return WatchlistChannelStatusResponse(channel=None, warnings=ws)
    try:
        ch = repo.get_watch_channel(cid)
    except FirestoreUnavailableError:
        raise
    if ch is None:
        ws.append("Watchlist channel not found.")
        return WatchlistChannelStatusResponse(channel=None, warnings=ws)
    now_iso = utc_now_iso()
    try:
        repo.patch_watch_channel_fields(
            cid, {"status": "paused", "updated_at": now_iso}
        )
    except FirestoreUnavailableError:
        raise
    refreshed = ch.model_copy(
        update={"status": "paused", "updated_at": now_iso},
    )
    return WatchlistChannelStatusResponse(channel=refreshed, warnings=ws)


def resume_watchlist_channel(
    channel_id: str,
    *,
    repo: FirestoreWatchlistRepository | None = None,
) -> WatchlistChannelStatusResponse:
    repo = repo or FirestoreWatchlistRepository()
    cid = (channel_id or "").strip()
    ws: List[str] = []
    if not cid:
        ws.append("channel_id is empty.")
        return WatchlistChannelStatusResponse(channel=None, warnings=ws)
    try:
        ch = repo.get_watch_channel(cid)
    except FirestoreUnavailableError:
        raise
    if ch is None:
        ws.append("Watchlist channel not found.")
        return WatchlistChannelStatusResponse(channel=None, warnings=ws)
    if ch.status != "paused":
        ws.append(
            f"Resume ist für „paused“ gedacht (aktueller Status: {ch.status})."
        )
        return WatchlistChannelStatusResponse(channel=ch, warnings=ws)
    now_iso = utc_now_iso()
    try:
        repo.patch_watch_channel_fields(
            cid, {"status": "active", "updated_at": now_iso}
        )
    except FirestoreUnavailableError:
        raise
    refreshed = ch.model_copy(
        update={"status": "active", "updated_at": now_iso},
    )
    return WatchlistChannelStatusResponse(channel=refreshed, warnings=ws)


def create_production_job_from_script_job(
    job_id: str,
    req: ProductionJobCreateRequest | None = None,
    *,
    repo: FirestoreWatchlistRepository | None = None,
) -> CreateProductionJobResponse:
    repo = repo or FirestoreWatchlistRepository()
    body = req or ProductionJobCreateRequest()
    jid = (job_id or "").strip()
    ws: List[str] = []
    if not jid:
        ws.append("job_id is empty.")
        return CreateProductionJobResponse(job=None, created=False, warnings=ws)
    try:
        job = repo.get_script_job(jid)
    except FirestoreUnavailableError:
        raise
    if job is None:
        ws.append("Script job not found.")
        return CreateProductionJobResponse(job=None, created=False, warnings=ws)
    if job.status != "completed":
        ws.append(
            f"Production-Job nur für completed ScriptJobs (aktuell: {job.status})."
        )
        return CreateProductionJobResponse(job=None, created=False, warnings=ws)
    gid = (job.generated_script_id or job.id or "").strip()
    if not gid:
        ws.append("Kein generated_script_id am Job gesetzt.")
        return CreateProductionJobResponse(job=None, created=False, warnings=ws)
    try:
        existing = repo.get_production_job(gid)
    except FirestoreUnavailableError:
        raise
    if existing:
        ws.append(
            "Production-Job für dieses generated_script_id existiert bereits."
        )
        return CreateProductionJobResponse(
            job=existing, created=False, warnings=ws
        )
    now_iso = utc_now_iso()
    pj = ProductionJob(
        id=gid,
        generated_script_id=gid,
        script_job_id=job.id,
        status="queued",
        content_category=body.content_category,
        visual_style=body.visual_style,
        narrator_style=body.narrator_style,
        thumbnail_prompt=body.thumbnail_prompt,
        created_at=now_iso,
        updated_at=now_iso,
    )
    try:
        repo.create_production_job(pj)
    except FirestoreUnavailableError:
        raise
    return CreateProductionJobResponse(job=pj, created=True, warnings=ws)


def list_production_jobs(
    limit: int = 50,
    *,
    repo: FirestoreWatchlistRepository | None = None,
) -> ListProductionJobsResponse:
    repo = repo or FirestoreWatchlistRepository()
    try:
        jobs = repo.list_production_jobs(limit=limit)
    except FirestoreUnavailableError:
        raise
    return ListProductionJobsResponse(jobs=jobs, warnings=[])


def get_production_job_detail(
    production_job_id: str,
    *,
    repo: FirestoreWatchlistRepository | None = None,
) -> ProductionJobActionResponse:
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    ws: List[str] = []
    if not pid:
        ws.append("production_job_id is empty.")
        return ProductionJobActionResponse(job=None, warnings=ws)
    try:
        job = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if job is None:
        ws.append("Production job not found.")
        return ProductionJobActionResponse(job=None, warnings=ws)
    return ProductionJobActionResponse(job=job, warnings=ws)


def skip_production_job(
    production_job_id: str,
    *,
    repo: FirestoreWatchlistRepository | None = None,
) -> ProductionJobActionResponse:
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    ws: List[str] = []
    if not pid:
        ws.append("production_job_id is empty.")
        return ProductionJobActionResponse(job=None, warnings=ws)
    try:
        job = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if job is None:
        ws.append("Production job not found.")
        return ProductionJobActionResponse(job=None, warnings=ws)
    _skip_ok = (
        "queued",
        "failed",
        "planning_ready",
        "assets_ready",
        "voice_ready",
        "editing_ready",
        "upload_ready",
        "in_progress",
    )
    if job.status not in _skip_ok:
        ws.append(
            "Skip ist für diesen Produktionsstatus nicht vorgesehen "
            f"(aktuell: {job.status})."
        )
        return ProductionJobActionResponse(job=job, warnings=ws)
    now_iso = utc_now_iso()
    try:
        repo.patch_production_job(
            pid,
            {
                "status": "skipped",
                "updated_at": now_iso,
                "error": "",
                "error_code": "",
            },
        )
    except FirestoreUnavailableError:
        raise
    try:
        refreshed = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    return ProductionJobActionResponse(job=refreshed or job, warnings=ws)


def retry_production_job(
    production_job_id: str,
    *,
    repo: FirestoreWatchlistRepository | None = None,
) -> ProductionJobActionResponse:
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    ws: List[str] = []
    if not pid:
        ws.append("production_job_id is empty.")
        return ProductionJobActionResponse(job=None, warnings=ws)
    try:
        job = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if job is None:
        ws.append("Production job not found.")
        return ProductionJobActionResponse(job=None, warnings=ws)
    if job.status not in ("failed", "skipped"):
        ws.append(
            "Retry nur für Status „failed“ oder „skipped“ vorgesehen "
            f"(aktuell: {job.status})."
        )
        return ProductionJobActionResponse(job=job, warnings=ws)
    now_iso = utc_now_iso()
    try:
        repo.patch_production_job(
            pid,
            {
                "status": "queued",
                "updated_at": now_iso,
                "error": "",
                "error_code": "",
            },
        )
    except FirestoreUnavailableError:
        raise
    try:
        refreshed = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    return ProductionJobActionResponse(job=refreshed or job, warnings=ws)


_CHECKLIST_EXISTS_WARN_DE = (
    "Checklist existiert bereits — bestehendes Dokument zurückgegeben (Auto-Flags aktualisiert)."
)


def sync_production_status_from_checklist(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
    checklist_override: Optional[ProductionChecklist] = None,
) -> None:
    """``production_jobs.status`` anhand Artefakte + Checkliste (kein Überspringen von failed/skipped/legacy)."""
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    if not pid:
        return
    try:
        job = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if job is None:
        return
    cl: Optional[ProductionChecklist] = checklist_override
    if cl is None:
        try:
            cl = repo.get_production_checklist(pid)
        except FirestoreUnavailableError:
            raise
    target = compute_target_production_status(
        current_status=job.status,
        production_job_id=pid,
        repo=repo,
        checklist=cl,
    )
    if not target:
        return
    now_iso = utc_now_iso()
    try:
        repo.patch_production_job(
            pid, {"status": target, "updated_at": now_iso}
        )
    except FirestoreUnavailableError:
        raise


def _safe_sync_production_status(
    production_job_id: str,
    repo: FirestoreWatchlistRepository,
) -> None:
    try:
        sync_production_status_from_checklist(production_job_id, repo=repo)
    except FirestoreUnavailableError:
        raise
    except Exception as e:
        logger.warning(
            "sync_production_status_from_checklist failed: job_id=%s type=%s",
            production_job_id,
            type(e).__name__,
        )


def _apply_auto_to_checklist(
    cl: ProductionChecklist,
    repo: FirestoreWatchlistRepository,
    pid: str,
) -> ProductionChecklist:
    auto = auto_checklist_booleans(repo, pid)
    data = cl.model_dump()
    for key, val in auto.items():
        if val is True:
            data[key] = True
    return ProductionChecklist.model_validate(data)


def initialize_checklist(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ProductionChecklistResponse:
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    ws: List[str] = []
    if not pid:
        ws.append("production_job_id is empty.")
        return ProductionChecklistResponse(checklist=None, warnings=ws)
    try:
        pj = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if pj is None:
        ws.append("Production job not found.")
        return ProductionChecklistResponse(checklist=None, warnings=ws)
    now_iso = utc_now_iso()
    try:
        existing = repo.get_production_checklist(pid)
    except FirestoreUnavailableError:
        raise
    if existing is not None:
        merged = _apply_auto_to_checklist(existing, repo, pid)
        merged = merged.model_copy(update={"updated_at": now_iso})
        try:
            repo.upsert_production_checklist(merged)
        except FirestoreUnavailableError:
            raise
        sync_production_status_from_checklist(
            pid, repo=repo, checklist_override=merged
        )
        ws.append(_CHECKLIST_EXISTS_WARN_DE)
        return ProductionChecklistResponse(checklist=merged, warnings=ws)

    auto = auto_checklist_booleans(repo, pid)
    doc = ProductionChecklist(
        id=pid,
        production_job_id=pid,
        script_ready=bool(auto.get("script_ready")),
        scene_plan_ready=bool(auto.get("scene_plan_ready")),
        scene_assets_ready=bool(auto.get("scene_assets_ready")),
        voice_plan_ready=bool(auto.get("voice_plan_ready")),
        render_manifest_ready=bool(auto.get("render_manifest_ready")),
        thumbnail_ready=False,
        editing_ready=False,
        upload_ready=False,
        published=False,
        notes="",
        created_at=now_iso,
        updated_at=now_iso,
    )
    try:
        repo.upsert_production_checklist(doc)
    except FirestoreUnavailableError:
        raise
    sync_production_status_from_checklist(pid, repo=repo, checklist_override=doc)
    return ProductionChecklistResponse(checklist=doc, warnings=ws)


def get_production_checklist_for_job(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ProductionChecklistResponse:
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    if not pid:
        return ProductionChecklistResponse(
            checklist=None, warnings=["production_job_id is empty."]
        )
    try:
        cl = repo.get_production_checklist(pid)
    except FirestoreUnavailableError:
        raise
    if cl is None:
        return ProductionChecklistResponse(
            checklist=None, warnings=["Checklist not found."]
        )
    return ProductionChecklistResponse(checklist=cl, warnings=[])


def update_checklist(
    production_job_id: str,
    body: ProductionChecklistUpdateRequest,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ProductionChecklistResponse:
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    ws: List[str] = []
    if not pid:
        ws.append("production_job_id is empty.")
        return ProductionChecklistResponse(checklist=None, warnings=ws)
    try:
        existing = repo.get_production_checklist(pid)
    except FirestoreUnavailableError:
        raise
    if existing is None:
        ws.append("Checklist not found.")
        return ProductionChecklistResponse(checklist=None, warnings=ws)
    data = existing.model_dump()
    if body.thumbnail_ready is not None:
        data["thumbnail_ready"] = body.thumbnail_ready
    if body.editing_ready is not None:
        data["editing_ready"] = body.editing_ready
    if body.upload_ready is not None:
        data["upload_ready"] = body.upload_ready
    if body.published is not None:
        data["published"] = body.published
    if body.notes is not None:
        data["notes"] = body.notes
    merged = ProductionChecklist.model_validate(data)
    merged = _apply_auto_to_checklist(merged, repo, pid)
    merged = merged.model_copy(update={"updated_at": utc_now_iso()})
    try:
        repo.upsert_production_checklist(merged)
    except FirestoreUnavailableError:
        raise
    sync_production_status_from_checklist(pid, repo=repo, checklist_override=merged)
    return ProductionChecklistResponse(checklist=merged, warnings=ws)


def build_provider_templates(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> Dict[str, Any]:
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    if not pid:
        return {}
    pj: Optional[ProductionJob] = None
    rm_doc: Optional[RenderManifest] = None
    vp: Optional[VoicePlan] = None
    gs: Optional[GeneratedScript] = None
    try:
        pj = repo.get_production_job(pid)
        rm_doc = repo.get_render_manifest(pid)
        vp = repo.get_voice_plan(pid)
        if pj is not None:
            gid = (pj.generated_script_id or "").strip()
            if gid:
                gs = repo.get_generated_script(gid)
    except FirestoreUnavailableError:
        raise
    return build_provider_templates_dict(
        manifest=rm_doc,
        voice_plan=vp,
        production_job=pj,
        generated_script=gs,
    )


def generate_export_download(
    production_job_id: str,
    fmt: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> Tuple[Optional[bytes], str, str, List[str]]:
    """Liefert ``(body, media_type, filename, warnings)``; ``body is None`` bei 404-Fehler."""
    repo = repo or FirestoreWatchlistRepository()
    ws: List[str] = []
    pid = (production_job_id or "").strip()
    if not pid:
        return None, "", "", ["production_job_id is empty."]
    try:
        pj = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if pj is None:
        return None, "", "", ["Production job not found."]
    try:
        manifest = repo.get_render_manifest(pid)
    except FirestoreUnavailableError:
        raise
    if manifest is None:
        return None, "", "", ["Render manifest not found."]
    vp: Optional[VoicePlan] = None
    gs: Optional[GeneratedScript] = None
    try:
        vp = repo.get_voice_plan(pid)
        gid = (pj.generated_script_id or "").strip()
        if gid:
            gs = repo.get_generated_script(gid)
    except FirestoreUnavailableError:
        raise
    templates = build_provider_templates_dict(
        manifest=manifest,
        voice_plan=vp,
        production_job=pj,
        generated_script=gs,
    )
    title = ""
    if gs is not None and (gs.title or "").strip():
        title = (gs.title or "").strip()
    elif pj is not None:
        title = ((pj.thumbnail_prompt or "").strip() or pj.id or "").strip()
    try:
        body, mt, suf = export_download_body(
            fmt,
            manifest=manifest,
            provider_templates=templates,
            title=title,
        )
    except ValueError as e:
        return None, "", "", [str(e)]
    fname = f"production_{pid}_export.{suf}"
    return body, mt, fname, ws


_SCENE_PLAN_IDEMP_WARN = (
    "Szenenplan existierte bereits — keine Neuerstellung (idempotent)."
)


def generate_scene_plan(
    production_job_id: str,
    *,
    repo: FirestoreWatchlistRepository | None = None,
) -> ScenePlanGenerateResponse:
    """Erzeugt deterministisch einen ``scene_plan`` oder liefert den bestehenden."""
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    if not pid:
        return ScenePlanGenerateResponse(
            scene_plan=None,
            warnings=["production_job_id is empty."],
        )
    try:
        existing = repo.get_scene_plan(pid)
    except FirestoreUnavailableError:
        raise
    if existing:
        _safe_sync_production_status(pid, repo)
        return ScenePlanGenerateResponse(
            scene_plan=existing,
            warnings=[_SCENE_PLAN_IDEMP_WARN],
        )
    try:
        pj = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if pj is None:
        return ScenePlanGenerateResponse(
            scene_plan=None,
            warnings=["Production job not found."],
        )
    gid = (pj.generated_script_id or "").strip()
    if not gid:
        return ScenePlanGenerateResponse(
            scene_plan=None,
            warnings=["generated_script_id am Production Job fehlend."],
        )
    try:
        gs = repo.get_generated_script(gid)
    except FirestoreUnavailableError:
        raise
    if gs is None:
        return ScenePlanGenerateResponse(
            scene_plan=None,
            warnings=["Generated script not found."],
        )

    scenes, fp, lw = build_scenes_from_generated_script(gs)
    status = decide_plan_status(scenes)
    now_iso = utc_now_iso()
    plan = ScenePlan(
        id=pid,
        production_job_id=pid,
        generated_script_id=gs.id,
        script_job_id=pj.script_job_id,
        status=status,
        plan_version=1,
        source_fingerprint=fp,
        scenes=scenes,
        warnings=list(lw),
        created_at=now_iso,
        updated_at=now_iso,
    )
    try:
        repo.upsert_scene_plan(plan)
    except FirestoreUnavailableError:
        raise

    _safe_sync_production_status(pid, repo)
    out_warn = list(lw)
    return ScenePlanGenerateResponse(scene_plan=plan, warnings=out_warn)


def get_scene_plan_for_production_job(
    production_job_id: str,
    *,
    repo: FirestoreWatchlistRepository | None = None,
) -> ScenePlanGetResponse:
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    if not pid:
        return ScenePlanGetResponse(scene_plan=None, warnings=["production_job_id is empty."])
    try:
        sp = repo.get_scene_plan(pid)
    except FirestoreUnavailableError:
        raise
    if sp is None:
        return ScenePlanGetResponse(scene_plan=None, warnings=["Scene plan not found."])
    return ScenePlanGetResponse(scene_plan=sp, warnings=[])


_SCENE_ASSETS_IDEMP_WARN = (
    "Scene-Assets existierten bereits — keine Neuerstellung (idempotent)."
)


def generate_scene_assets(
    production_job_id: str,
    req: Optional[SceneAssetsGenerateRequest] = None,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> SceneAssetsGenerateResponse:
    """Erzeugt ``scene_assets`` aus ``scene_plans`` (Prompt-Entwürfe, kein Rendering)."""
    repo = repo or FirestoreWatchlistRepository()
    body = req or SceneAssetsGenerateRequest()
    pid = (production_job_id or "").strip()
    if not pid:
        return SceneAssetsGenerateResponse(
            scene_assets=None,
            warnings=["production_job_id is empty."],
        )
    try:
        existing = repo.get_scene_assets(pid)
    except FirestoreUnavailableError:
        raise
    if existing is not None:
        ws = [_SCENE_ASSETS_IDEMP_WARN]
        _safe_sync_production_status(pid, repo)
        return SceneAssetsGenerateResponse(scene_assets=existing, warnings=ws)
    try:
        pj = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if pj is None:
        return SceneAssetsGenerateResponse(
            scene_assets=None,
            warnings=["Production job not found."],
        )
    try:
        plan = repo.get_scene_plan(pid)
    except FirestoreUnavailableError:
        raise
    if plan is None:
        return SceneAssetsGenerateResponse(
            scene_assets=None,
            warnings=["Scene plan not found."],
        )
    scenes_src = list(plan.scenes or [])
    if not scenes_src:
        return SceneAssetsGenerateResponse(
            scene_assets=None,
            warnings=["Scene plan has no scenes; generate scene plan first."],
        )

    style = body.style_profile
    items, eng_warns = build_scene_asset_items(scenes_src, style_profile=style)
    merged_warns = list(plan.warnings or []) + list(eng_warns)
    st = "ready" if items else "failed"
    now_iso = utc_now_iso()
    doc = SceneAssets(
        id=pid,
        production_job_id=pid,
        scene_plan_id=(plan.id or pid).strip() or pid,
        generated_script_id=(plan.generated_script_id or "").strip() or (
            pj.generated_script_id or ""
        ),
        script_job_id=(plan.script_job_id or "").strip() or (pj.script_job_id or ""),
        style_profile=style,
        status=st,
        asset_version=1,
        scenes=items,
        warnings=merged_warns,
        created_at=now_iso,
        updated_at=now_iso,
    )
    try:
        repo.upsert_scene_assets(doc)
    except FirestoreUnavailableError:
        raise
    _safe_sync_production_status(pid, repo)
    return SceneAssetsGenerateResponse(scene_assets=doc, warnings=list(merged_warns))


def get_scene_assets_for_production_job(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> SceneAssetsGetResponse:
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    if not pid:
        return SceneAssetsGetResponse(
            scene_assets=None,
            warnings=["production_job_id is empty."],
        )
    try:
        sa = repo.get_scene_assets(pid)
    except FirestoreUnavailableError:
        raise
    if sa is None:
        return SceneAssetsGetResponse(
            scene_assets=None,
            warnings=["Scene assets not found."],
        )
    return SceneAssetsGetResponse(scene_assets=sa, warnings=[])


_VOICE_PLAN_IDEMP_WARN = (
    "Voice-Plan existierte bereits — keine Neuerstellung (idempotent)."
)

_RENDER_MANIFEST_IDEMP_WARN = (
    "Render-Manifest existierte bereits — keine Neuerstellung (idempotent)."
)


def generate_voice_plan(
    production_job_id: str,
    req: Optional[VoicePlanGenerateRequest] = None,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> VoicePlanGenerateResponse:
    """Erzeugt ``voice_plans`` aus Scene-Assets (kein TTS)."""
    repo = repo or FirestoreWatchlistRepository()
    body = req or VoicePlanGenerateRequest()
    pid = (production_job_id or "").strip()
    if not pid:
        return VoicePlanGenerateResponse(
            voice_plan=None,
            warnings=["production_job_id is empty."],
        )
    try:
        existing = repo.get_voice_plan(pid)
    except FirestoreUnavailableError:
        raise
    if existing is not None:
        _safe_sync_production_status(pid, repo)
        return VoicePlanGenerateResponse(
            voice_plan=existing,
            warnings=[_VOICE_PLAN_IDEMP_WARN],
        )
    try:
        pj = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if pj is None:
        return VoicePlanGenerateResponse(
            voice_plan=None,
            warnings=["Production job not found."],
        )
    try:
        assets = repo.get_scene_assets(pid)
    except FirestoreUnavailableError:
        raise
    if assets is None:
        return VoicePlanGenerateResponse(
            voice_plan=None,
            warnings=["Scene assets not found; generate scene assets first."],
        )
    merged_warns = list(assets.warnings or [])
    blocks, bw = build_voice_blocks(
        pj, assets, voice_profile=body.voice_profile
    )
    merged_warns.extend(bw)
    st = decide_voice_plan_status(blocks, assets)
    merged_warns = _dedupe_preserve_order(merged_warns)
    now_iso = utc_now_iso()
    doc = VoicePlan(
        id=pid,
        production_job_id=pid,
        scene_assets_id=pid,
        generated_script_id=(assets.generated_script_id or pj.generated_script_id or "").strip(),
        script_job_id=(assets.script_job_id or pj.script_job_id or "").strip(),
        voice_profile=body.voice_profile,
        status=st if st in ("ready", "failed") else "failed",
        voice_version=1,
        blocks=blocks,
        warnings=merged_warns,
        created_at=now_iso,
        updated_at=now_iso,
    )
    try:
        repo.upsert_voice_plan(doc)
    except FirestoreUnavailableError:
        raise
    _safe_sync_production_status(pid, repo)
    return VoicePlanGenerateResponse(voice_plan=doc, warnings=list(merged_warns))


def _dedupe_preserve_order(seq: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for x in seq:
        k = str(x).strip()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(k)
    return out


def get_voice_plan_for_production_job(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> VoicePlanGetResponse:
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    if not pid:
        return VoicePlanGetResponse(
            voice_plan=None,
            warnings=["production_job_id is empty."],
        )
    try:
        vp = repo.get_voice_plan(pid)
    except FirestoreUnavailableError:
        raise
    if vp is None:
        return VoicePlanGetResponse(
            voice_plan=None,
            warnings=["Voice plan not found."],
        )
    return VoicePlanGetResponse(voice_plan=vp, warnings=[])


def generate_render_manifest(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> RenderManifestGenerateResponse:
    """Bündelt Bausteine in ``render_manifests`` (ohne externe Aufrufe)."""
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    if not pid:
        return RenderManifestGenerateResponse(
            render_manifest=None,
            warnings=["production_job_id is empty."],
        )
    try:
        existing_rm = repo.get_render_manifest(pid)
    except FirestoreUnavailableError:
        raise
    if existing_rm is not None:
        _safe_sync_production_status(pid, repo)
        return RenderManifestGenerateResponse(
            render_manifest=existing_rm,
            warnings=[_RENDER_MANIFEST_IDEMP_WARN],
        )
    try:
        pj = repo.get_production_job(pid)
    except FirestoreUnavailableError:
        raise
    if pj is None:
        return RenderManifestGenerateResponse(
            render_manifest=None,
            warnings=["Production job not found."],
        )
    try:
        assets = repo.get_scene_assets(pid)
    except FirestoreUnavailableError:
        raise
    if assets is None:
        return RenderManifestGenerateResponse(
            render_manifest=None,
            warnings=["Scene assets not found — cannot assemble render manifest."],
        )

    try:
        sp = repo.get_scene_plan(pid)
    except FirestoreUnavailableError:
        raise
    try:
        vp = repo.get_voice_plan(pid)
    except FirestoreUnavailableError:
        raise

    timeline, est_total = build_timeline(sp, assets, vp)
    st = decide_manifest_status(
        production_job=pj,
        scene_plan=sp,
        scene_assets=assets,
        voice_plan=vp,
    )
    mw: List[str] = []
    mw.extend(sp.warnings if sp else [])
    mw.extend(assets.warnings if assets else [])
    if vp:
        mw.extend(vp.warnings or [])
    else:
        mw.append(
            "Voice Plan fehlt — Render-Manifest ist unvollständig (Timeline nutzt Fallback-Text)."
        )
    if sp is None:
        mw.append("Scene Plan fehlt — Dauer-Schätzungen nutzen Fallback-Werte.")

    mw = _dedupe_preserve_order(mw)
    now_iso = utc_now_iso()
    rm_doc = RenderManifest(
        id=pid,
        production_job_id=pid,
        production_job=pj,
        scene_plan=sp,
        scene_assets=assets,
        voice_plan=vp,
        timeline=timeline,
        estimated_total_duration_seconds=est_total,
        export_version=RENDER_MANIFEST_EXPORT_VERSION,
        status=st,
        warnings=mw,
        created_at=now_iso,
        updated_at=now_iso,
    )
    try:
        repo.upsert_render_manifest(rm_doc)
    except FirestoreUnavailableError:
        raise
    _safe_sync_production_status(pid, repo)
    out_warn = list(mw)
    return RenderManifestGenerateResponse(render_manifest=rm_doc, warnings=out_warn)


def get_render_manifest_for_production_job(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> RenderManifestGetResponse:
    repo = repo or FirestoreWatchlistRepository()
    pid = (production_job_id or "").strip()
    if not pid:
        return RenderManifestGetResponse(
            render_manifest=None,
            warnings=["production_job_id is empty."],
        )
    try:
        rm = repo.get_render_manifest(pid)
    except FirestoreUnavailableError:
        raise
    if rm is None:
        return RenderManifestGetResponse(
            render_manifest=None,
            warnings=["Render manifest not found."],
        )
    return RenderManifestGetResponse(render_manifest=rm, warnings=[])


def get_production_connector_export(
    production_job_id: str,
    *,
    repo: Optional[FirestoreWatchlistRepository] = None,
) -> ProductionConnectorExportResponse:
    repo = repo or FirestoreWatchlistRepository()
    ws: List[str] = []
    pid = (production_job_id or "").strip()
    if not pid:
        ws.append("production_job_id is empty.")
        return ProductionConnectorExportResponse(
            export=build_connector_export_payload(
                production_job=None,
                manifest=None,
                voice_plan=None,
                scene_assets=None,
                generated_script=None,
                render_manifest_warnings=ws,
            ),
            warnings=ws,
        )

    pj: Optional[ProductionJob] = None
    gs: Optional[GeneratedScript] = None
    vp: Optional[VoicePlan] = None
    rm_doc: Optional[RenderManifest] = None
    sa: Optional[SceneAssets] = None

    try:
        pj = repo.get_production_job(pid)
        if pj is None:
            ws.append("Production job nicht geladen oder nicht vorhanden.")
        else:
            gid = (pj.generated_script_id or "").strip()
            if gid:
                gs = repo.get_generated_script(gid)
        vp = repo.get_voice_plan(pid)
        rm_doc = repo.get_render_manifest(pid)
        sa = repo.get_scene_assets(pid)
        if pj is None and sa is None:
            ws.append("Keine exportierbaren Bausteine für diese ID.")
    except FirestoreUnavailableError:
        raise

    extra = list(rm_doc.warnings) if rm_doc else []
    block_warns = build_connector_export_payload(
        production_job=pj,
        manifest=rm_doc,
        voice_plan=vp,
        scene_assets=sa,
        generated_script=gs,
        render_manifest_warnings=extra,
    )
    top = list(block_warns.metadata.warnings or [])
    top.extend(ws)
    merged = _dedupe_preserve_order(top)
    return ProductionConnectorExportResponse(
        export=block_warns.model_copy(
            update={
                "metadata": block_warns.metadata.model_copy(
                    update={"warnings": merged}
                )
            }
        ),
        warnings=merged,
    )
