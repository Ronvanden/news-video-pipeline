"""Watchlist-Service: Kanal auflösen, Metadaten, Firestore."""

from __future__ import annotations

import logging
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Literal, Tuple

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
from app.watchlist.scene_plan import (
    build_scenes_from_generated_script,
    decide_plan_status,
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
    GeneratedScript,
    ListWatchlistChannelsResponse,
    ListWatchlistScriptJobsResponse,
    PendingJobRunResultItem,
    ProcessedVideo,
    ProductionJob,
    ProductionJobCreateRequest,
    ReviewGeneratedScriptJobResponse,
    ReviewResultStored,
    RunAutomationCycleResponse,
    RunPendingScriptJobsResponse,
    RunScriptJobResponse,
    ScenePlan,
    ScenePlanGenerateResponse,
    ScenePlanGetResponse,
    ScriptJob,
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
    ProductionJobActionResponse,
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
        try:
            repo.mark_script_job_failed(jid, code, error_code=code)
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
    if job.status not in ("queued", "failed"):
        ws.append(
            "Skip nur für Status „queued“ oder „failed“ vorgesehen "
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
