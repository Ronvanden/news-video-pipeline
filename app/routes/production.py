"""Production-Jobs — Liste, Detail, Skip/Retry, Szenenplan (BA 6.6), Scene-Assets (BA 6.7); kein Rendering."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.watchlist.firestore_repo import FirestoreUnavailableError
from app.watchlist.models import (
    ListProductionJobsResponse,
    ProductionJobActionResponse,
    SceneAssetsGenerateRequest,
    SceneAssetsGenerateResponse,
    SceneAssetsGetResponse,
    ScenePlanGenerateResponse,
    ScenePlanGetResponse,
)
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


@router.post(
    "/production/jobs/{production_job_id}/scene-plan/generate",
    response_model=ScenePlanGenerateResponse,
)
async def production_generate_scene_plan(production_job_id: str):
    """Deterministischer Szenenplan (Firestore ``scene_plans``), keine externe KI."""
    try:
        out = watchlist_service.generate_scene_plan(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("POST scene-plan/generate failed: Firestore unavailable")
        body = ScenePlanGenerateResponse(scene_plan=None, warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())
    if out.scene_plan is None:
        detail = out.warnings[0] if out.warnings else "Not found."
        raise HTTPException(status_code=404, detail=detail)
    return out


@router.get(
    "/production/jobs/{production_job_id}/scene-plan",
    response_model=ScenePlanGetResponse,
)
async def production_get_scene_plan(production_job_id: str):
    try:
        out = watchlist_service.get_scene_plan_for_production_job(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)
    if out.scene_plan is None:
        detail = out.warnings[0] if out.warnings else "Scene plan not found."
        raise HTTPException(status_code=404, detail=detail)
    return out


@router.post(
    "/production/jobs/{production_job_id}/scene-assets/generate",
    response_model=SceneAssetsGenerateResponse,
)
async def production_generate_scene_assets(
    production_job_id: str,
    body: Optional[SceneAssetsGenerateRequest] = None,
):
    """Prompt-Entwürfe je Szene (Firestore ``scene_assets``); deterministisch, idempotent."""
    try:
        out = watchlist_service.generate_scene_assets(
            production_job_id, body, repo=None
        )
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("POST scene-assets/generate failed: Firestore unavailable")
        body503 = SceneAssetsGenerateResponse(scene_assets=None, warnings=[msg])
        return JSONResponse(status_code=503, content=body503.model_dump())
    if out.scene_assets is None:
        detail = out.warnings[0] if out.warnings else "Not found."
        raise HTTPException(status_code=404, detail=detail)
    return out


@router.get(
    "/production/jobs/{production_job_id}/scene-assets",
    response_model=SceneAssetsGetResponse,
)
async def production_get_scene_assets(production_job_id: str):
    try:
        out = watchlist_service.get_scene_assets_for_production_job(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)
    if out.scene_assets is None:
        detail = out.warnings[0] if out.warnings else "Scene assets not found."
        raise HTTPException(status_code=404, detail=detail)
    return out
