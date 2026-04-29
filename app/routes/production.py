"""Production-Jobs — Liste, Detail, Skip/Retry (kein Rendering, Phase 6.5)."""

import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.watchlist.firestore_repo import FirestoreUnavailableError
from app.watchlist.models import ListProductionJobsResponse, ProductionJobActionResponse
from app.watchlist import service as watchlist_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/production/jobs",
    response_model=ListProductionJobsResponse,
)
async def production_list_jobs(limit: int = Query(50, ge=1, le=200)):
    try:
        return watchlist_service.list_production_jobs(limit=limit)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("GET /production/jobs failed: Firestore unavailable")
        body = ListProductionJobsResponse(jobs=[], warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())


@router.get(
    "/production/jobs/{production_job_id}",
    response_model=ProductionJobActionResponse,
)
async def production_get_job(production_job_id: str):
    try:
        out = watchlist_service.get_production_job_detail(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)
    if out.job is None:
        raise HTTPException(status_code=404, detail="Production job not found.")
    return out


@router.post(
    "/production/jobs/{production_job_id}/skip",
    response_model=ProductionJobActionResponse,
)
async def production_skip_job(production_job_id: str):
    try:
        out = watchlist_service.skip_production_job(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)
    if out.job is None:
        raise HTTPException(status_code=404, detail="Production job not found.")
    return out


@router.post(
    "/production/jobs/{production_job_id}/retry",
    response_model=ProductionJobActionResponse,
)
async def production_retry_job(production_job_id: str):
    try:
        out = watchlist_service.retry_production_job(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)
    if out.job is None:
        raise HTTPException(status_code=404, detail="Production job not found.")
    return out
