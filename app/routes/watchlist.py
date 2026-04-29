"""Watchlist-Endpunkte (Phase 5: CRUD, Check, Script-Jobs inkl. manueller Run)."""

import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.watchlist.firestore_repo import FirestoreUnavailableError
from app.watchlist.models import (
    CheckWatchlistChannelResponse,
    CreateWatchlistChannelResponse,
    ListWatchlistChannelsResponse,
    ListWatchlistScriptJobsResponse,
    RunScriptJobResponse,
    WatchlistChannelCreateRequest,
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
