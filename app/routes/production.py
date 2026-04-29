"""Production-Jobs — Liste, Detail, Skip/Retry, Szenenplan (BA 6.6), Scene-Assets (BA 6.7),
Voice-Plan (BA 6.8), Render-Manifest (BA 6.9), Connector-Export (BA 7.0),
Production OS: Export-Download & Provider-Templates (BA 7.1–7.2), Checkliste (BA 7.3),
Status-Workflow (BA 7.4); kein Rendering/TTS."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, Response

from app.watchlist.firestore_repo import FirestoreUnavailableError
from app.watchlist.models import (
    ListProductionJobsResponse,
    ProductionChecklistResponse,
    ProductionChecklistUpdateRequest,
    ProductionJobActionResponse,
    ProductionConnectorExportResponse,
    RenderManifestGenerateResponse,
    RenderManifestGetResponse,
    SceneAssetsGenerateRequest,
    SceneAssetsGenerateResponse,
    SceneAssetsGetResponse,
    ScenePlanGenerateResponse,
    ScenePlanGetResponse,
    VoicePlanGenerateRequest,
    VoicePlanGenerateResponse,
    VoicePlanGetResponse,
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


@router.post(
    "/production/jobs/{production_job_id}/voice-plan/generate",
    response_model=VoicePlanGenerateResponse,
)
async def production_generate_voice_plan(
    production_job_id: str,
    body: Optional[VoicePlanGenerateRequest] = None,
):
    """Strukturierter Voice-Plan (Firestore ``voice_plans``), kein TTS."""
    try:
        out = watchlist_service.generate_voice_plan(
            production_job_id, body or VoicePlanGenerateRequest(), repo=None
        )
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("POST voice-plan/generate failed: Firestore unavailable")
        body503 = VoicePlanGenerateResponse(voice_plan=None, warnings=[msg])
        return JSONResponse(status_code=503, content=body503.model_dump())
    if out.voice_plan is None:
        detail = out.warnings[0] if out.warnings else "Not found."
        raise HTTPException(status_code=404, detail=detail)
    return out


@router.get(
    "/production/jobs/{production_job_id}/voice-plan",
    response_model=VoicePlanGetResponse,
)
async def production_get_voice_plan(production_job_id: str):
    try:
        out = watchlist_service.get_voice_plan_for_production_job(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)
    if out.voice_plan is None:
        detail = out.warnings[0] if out.warnings else "Voice plan not found."
        raise HTTPException(status_code=404, detail=detail)
    return out


@router.post(
    "/production/jobs/{production_job_id}/render-manifest/generate",
    response_model=RenderManifestGenerateResponse,
)
async def production_generate_render_manifest(production_job_id: str):
    """Produktions-Manifest (Firestore ``render_manifests``)."""
    try:
        out = watchlist_service.generate_render_manifest(production_job_id, repo=None)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("POST render-manifest/generate failed: Firestore unavailable")
        body503 = RenderManifestGenerateResponse(render_manifest=None, warnings=[msg])
        return JSONResponse(status_code=503, content=body503.model_dump())
    if out.render_manifest is None:
        detail = out.warnings[0] if out.warnings else "Not found."
        raise HTTPException(status_code=404, detail=detail)
    return out


@router.get(
    "/production/jobs/{production_job_id}/render-manifest",
    response_model=RenderManifestGetResponse,
)
async def production_get_render_manifest(production_job_id: str):
    try:
        out = watchlist_service.get_render_manifest_for_production_job(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)
    if out.render_manifest is None:
        detail = out.warnings[0] if out.warnings else "Render manifest not found."
        raise HTTPException(status_code=404, detail=detail)
    return out


@router.get(
    "/production/jobs/{production_job_id}/export",
    response_model=ProductionConnectorExportResponse,
)
async def production_connector_export(production_job_id: str):
    """Connector-JSON (ElevenLabs/Kling/Leo-Stubs — keine Provider-Aufrufe)."""
    try:
        return watchlist_service.get_production_connector_export(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)


@router.get(
    "/production/jobs/{production_job_id}/export/download",
)
async def production_export_download(
    production_job_id: str,
    export_format: str = Query(
        "json",
        alias="format",
        description="json | markdown | csv | txt",
    ),
):
    """BA 7.1 — Manifest + Provider-Templates als Download (read-only)."""
    fmt = (export_format or "json").strip().lower()
    if fmt not in ("json", "markdown", "csv", "txt"):
        raise HTTPException(
            status_code=422,
            detail="Unsupported format; use json, markdown, csv, or txt.",
        )
    try:
        body, media_type, filename, warns = watchlist_service.generate_export_download(
            production_job_id, fmt
        )
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)
    if body is None:
        detail = warns[0] if warns else "Export nicht möglich."
        raise HTTPException(status_code=404, detail=detail)
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(content=body, media_type=media_type, headers=headers)


@router.post(
    "/production/jobs/{production_job_id}/checklist/init",
    response_model=ProductionChecklistResponse,
)
async def production_checklist_init(production_job_id: str):
    """BA 7.3 — Checkliste anlegen oder bestehende mit Auto-Flags zurückgeben."""
    try:
        out = watchlist_service.initialize_checklist(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("POST checklist/init failed: Firestore unavailable")
        body = ProductionChecklistResponse(checklist=None, warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())
    if out.checklist is None:
        raise HTTPException(
            status_code=404,
            detail=out.warnings[0] if out.warnings else "Production job not found.",
        )
    return out


@router.get(
    "/production/jobs/{production_job_id}/checklist",
    response_model=ProductionChecklistResponse,
)
async def production_checklist_get(production_job_id: str):
    try:
        out = watchlist_service.get_production_checklist_for_job(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)
    if out.checklist is None:
        raise HTTPException(
            status_code=404,
            detail=out.warnings[0] if out.warnings else "Checklist not found.",
        )
    return out


@router.post(
    "/production/jobs/{production_job_id}/checklist/update",
    response_model=ProductionChecklistResponse,
)
async def production_checklist_update(
    production_job_id: str,
    body: ProductionChecklistUpdateRequest,
):
    try:
        out = watchlist_service.update_checklist(production_job_id, body)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("POST checklist/update failed: Firestore unavailable")
        resp = ProductionChecklistResponse(checklist=None, warnings=[msg])
        return JSONResponse(status_code=503, content=resp.model_dump())
    if out.checklist is None:
        raise HTTPException(
            status_code=404,
            detail=out.warnings[0] if out.warnings else "Checklist not found.",
        )
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
