"""Watchlist-Service: Kanal auflösen, Metadaten, Firestore."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Literal, Tuple

from app.youtube.scoring import is_likely_short_video
from app.youtube.service import get_latest_channel_videos
from app.youtube.rss import fetch_channel_feed_entries
from app.youtube.resolver import resolve_channel_id
from app.models import GenerateScriptResponse
from app.utils import (
    WARN_TRANSCRIPT_UNAVAILABLE,
    check_youtube_transcript_available_by_video_id,
    count_words,
    generate_script_from_youtube_video,
)
from app.watchlist.firestore_repo import (
    FirestoreUnavailableError,
    FirestoreWatchlistRepository,
)
from app.watchlist.models import (
    ChannelCheckVideoItem,
    CheckWatchlistChannelResponse,
    CreateWatchlistChannelResponse,
    CreatedScriptJobItem,
    GeneratedScript,
    ListWatchlistChannelsResponse,
    ListWatchlistScriptJobsResponse,
    ProcessedVideo,
    RunScriptJobResponse,
    ScriptJob,
    WatchlistChannel,
    WatchlistChannelCreateRequest,
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
    warn_skip_transcript_unavailable = False
    warn_skip_transcript_check_failed = False
    checker = transcript_checker or check_youtube_transcript_available_by_video_id

    try:
        feed_result = getter(channel.channel_url, channel.max_results)
        merged_warnings.extend(list(feed_result.get("warnings") or []))
        rows = feed_result.get("videos") or []
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            vid = str(raw.get("video_id") or "").strip()
            if not vid:
                continue
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
                continue

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
                continue

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
                continue

            if channel.auto_generate_script:
                ok_tr, _preflight_ws = checker(vid)
                if not ok_tr:
                    if any(
                        WARN_TRANSCRIPT_UNAVAILABLE in (x or "")
                        or "Transcript not available" in (x or "")
                        for x in _preflight_ws
                    ):
                        skip_tr = "transcript_not_available"
                        warn_skip_transcript_unavailable = True
                    else:
                        skip_tr = "transcript_check_failed"
                        warn_skip_transcript_check_failed = True
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
                    continue

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

        created_n = len(new_out) + len(skipped_out)

        if warn_skip_transcript_unavailable:
            merged_warnings.append(
                "Mindestens ein Video wurde ohne Script-Job übersprungen: Transkript nicht verfügbar."
            )
        if warn_skip_transcript_check_failed:
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
