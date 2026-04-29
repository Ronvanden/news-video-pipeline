"""Watchlist-Endpunkte (Phase 5: CRUD, Check, Script-Jobs inkl. manueller Run)."""

import logging

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import JSONResponse

from app.watchlist.firestore_repo import FirestoreUnavailableError
from app.watchlist.models import (
    CheckWatchlistChannelResponse,
    CreateProductionJobResponse,
    CreateWatchlistChannelResponse,
    ListWatchlistChannelsResponse,
    ListWatchlistScriptJobsResponse,
    ProductionJobCreateRequest,
    ReviewGeneratedScriptJobResponse,
    RunAutomationCycleRequest,
    RunAutomationCycleResponse,
    RunPendingScriptJobsResponse,
    RunScriptJobResponse,
    WatchlistChannelCreateRequest,
    WatchlistChannelStatusResponse,
    WatchlistDashboardHealth,
    WatchlistDashboardResponse,
    WatchlistErrorsSummaryResponse,
    WatchlistJobActionResponse,
)
from app.watchlist import service as watchlist_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/watchlist/channels",
    response_model=CreateWatchlistChannelResponse,
)
async def watchlist_create_channel(req: WatchlistChannelCreateRequest):
    try:
        return watchlist_service.create_channel(req)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore is not reachable."
        logger.warning("watchlist POST /watchlist/channels failed: Firestore unavailable")
        body = CreateWatchlistChannelResponse(channel=None, warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())


@router.post(
    "/watchlist/channels/{channel_id}/check",
    response_model=CheckWatchlistChannelResponse,
)
async def watchlist_check_channel(channel_id: str):
    try:
        return watchlist_service.check_channel(channel_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore is not reachable."
        logger.warning("watchlist POST channel check failed: Firestore unavailable")
        body = CheckWatchlistChannelResponse(
            channel_id=channel_id,
            created_jobs=[],
            warnings=[msg],
        )
        return JSONResponse(status_code=503, content=body.model_dump())


@router.get(
    "/watchlist/jobs",
    response_model=ListWatchlistScriptJobsResponse,
)
async def watchlist_list_script_jobs(limit: int = Query(50, ge=1, le=200)):
    try:
        return watchlist_service.list_script_jobs(limit=limit)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore is not reachable."
        logger.warning("watchlist GET /watchlist/jobs failed: Firestore unavailable")
        body = ListWatchlistScriptJobsResponse(jobs=[], warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())


@router.post(
    "/watchlist/jobs/{job_id}/run",
    response_model=RunScriptJobResponse,
)
async def watchlist_run_script_job(job_id: str):
    """Pending/failed Script-Job ausführen: YouTube-to-Script, Speicherung unter ``generated_scripts``."""
    try:
        return watchlist_service.run_script_job(job_id)
    except watchlist_service.ScriptJobNotFoundError:
        raise HTTPException(status_code=404, detail="Script job not found.")
    except watchlist_service.ScriptJobConflictError as e:
        raise HTTPException(status_code=409, detail=e.detail)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore is not reachable."
        logger.warning("watchlist POST /watchlist/jobs/run failed: Firestore unavailable")
        raise HTTPException(status_code=503, detail=msg)


@router.post(
    "/watchlist/channels/{channel_id}/recheck-video/{video_id}",
    response_model=CheckWatchlistChannelResponse,
)
async def watchlist_recheck_video(channel_id: str, video_id: str):
    """Dev/Test: eine video_id neu klassifizieren (optional ein Dokument aus ``processed_videos`` entfernen)."""
    try:
        return watchlist_service.recheck_video(channel_id, video_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore is not reachable."
        logger.warning(
            "watchlist POST recheck-video failed: Firestore unavailable"
        )
        body = CheckWatchlistChannelResponse(
            channel_id=channel_id,
            warnings=[msg],
            created_jobs=[],
        )
        return JSONResponse(status_code=503, content=body.model_dump())


@router.post(
    "/watchlist/jobs/run-pending",
    response_model=RunPendingScriptJobsResponse,
)
async def watchlist_run_pending_jobs(limit: int = Query(3, ge=1, le=10)):
    """Pending Jobs nacheinander ausführen (Batch toleriert Einzelfehler)."""
    try:
        return watchlist_service.run_pending_script_jobs(limit=limit)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore is not reachable."
        logger.warning(
            "watchlist POST /watchlist/jobs/run-pending failed: Firestore unavailable"
        )
        body = RunPendingScriptJobsResponse(
            warnings=[msg],
        )
        return JSONResponse(status_code=503, content=body.model_dump())


@router.post(
    "/watchlist/automation/run-cycle",
    response_model=RunAutomationCycleResponse,
)
async def watchlist_automation_run_cycle(
    req: RunAutomationCycleRequest = Body(...),
):
    """Ein Scheduler-Zyklus vorbereiten: aktive Kanäle prüfen, danach pending Jobs (ohne GCP Cloud Scheduler)."""
    try:
        return watchlist_service.run_automation_cycle(
            channel_limit=req.channel_limit,
            job_limit=req.job_limit,
        )
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore is not reachable."
        logger.warning(
            "watchlist POST automation run-cycle failed: Firestore unavailable"
        )
        body = RunAutomationCycleResponse(warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())


@router.post(
    "/watchlist/jobs/{job_id}/review",
    response_model=ReviewGeneratedScriptJobResponse,
)
async def watchlist_review_generated_script(job_id: str):
    """Originalitäts-Review wie ``POST /review-script``, ohne Job-Status anzufassen."""
    try:
        return watchlist_service.review_generated_script_for_job(job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore is not reachable."
        logger.warning(
            "watchlist POST jobs review failed: Firestore unavailable"
        )
        body = ReviewGeneratedScriptJobResponse(job_id=job_id, warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())


@router.get(
    "/watchlist/dashboard",
    response_model=WatchlistDashboardResponse,
)
async def watchlist_dashboard():
    try:
        return watchlist_service.get_watchlist_dashboard()
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore nicht erreichbar."
        logger.warning("watchlist GET dashboard failed: Firestore unavailable")
        return JSONResponse(
            status_code=503,
            content=WatchlistDashboardResponse(
                health=WatchlistDashboardHealth(warnings=[msg])
            ).model_dump(),
        )


@router.get(
    "/watchlist/errors/summary",
    response_model=WatchlistErrorsSummaryResponse,
)
async def watchlist_errors_summary(max_docs: int = Query(500, ge=50, le=2000)):
    try:
        return watchlist_service.get_watchlist_errors_summary(max_docs=max_docs)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore nicht erreichbar."
        logger.warning("watchlist GET errors/summary failed: Firestore unavailable")
        body = WatchlistErrorsSummaryResponse(warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())


@router.post(
    "/watchlist/jobs/{job_id}/retry",
    response_model=WatchlistJobActionResponse,
)
async def watchlist_retry_job(job_id: str):
    try:
        return watchlist_service.retry_script_job(job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)


@router.post(
    "/watchlist/jobs/{job_id}/skip",
    response_model=WatchlistJobActionResponse,
)
async def watchlist_skip_job(job_id: str):
    try:
        return watchlist_service.skip_script_job_manually(job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)


@router.post(
    "/watchlist/channels/{channel_id}/pause",
    response_model=WatchlistChannelStatusResponse,
)
async def watchlist_pause_channel(channel_id: str):
    try:
        return watchlist_service.pause_watchlist_channel(channel_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)


@router.post(
    "/watchlist/channels/{channel_id}/resume",
    response_model=WatchlistChannelStatusResponse,
)
async def watchlist_resume_channel(channel_id: str):
    try:
        return watchlist_service.resume_watchlist_channel(channel_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)


@router.post(
    "/watchlist/jobs/{job_id}/create-production-job",
    response_model=CreateProductionJobResponse,
)
async def watchlist_create_production_job(
    job_id: str,
    req: ProductionJobCreateRequest | None = Body(None),
):
    try:
        return watchlist_service.create_production_job_from_script_job(
            job_id, req
        )
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)


@router.get(
    "/watchlist/channels",
    response_model=ListWatchlistChannelsResponse,
)
async def watchlist_list_channels():
    try:
        return watchlist_service.list_channels()
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore is not reachable."
        logger.warning("watchlist GET failed: FirestoreUnavailableError")
        body = ListWatchlistChannelsResponse(channels=[], warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())
