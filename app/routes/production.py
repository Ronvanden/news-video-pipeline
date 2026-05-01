"""Production-Jobs — Liste, Detail, Skip/Retry, Szenenplan (BA 6.6), Scene-Assets (BA 6.7),
Voice-Plan (BA 6.8), Render-Manifest (BA 6.9), Connector-Export (BA 7.0),
Production OS: Export-Download & Provider-Templates (BA 7.1–7.2), Checkliste (BA 7.3),
Status-Workflow (BA 7.4), Execution Queue & Budget (BA 7.8–7.9); Audit / Recovery / Monitoring (BA 8.0–8.2);
Status-Normalisierung & Eskalationen (BA 8.3); Phase 7.2: TTS‑Preview ohne Audio-Persistenz
(``POST …/voice/synthesize-preview``, ``POST …/voice/synthesize``); kein FFmpeg/Voll‑Rendering hier."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse, Response

from app.watchlist.firestore_repo import FirestoreUnavailableError
from app.watchlist.models import (
    ExecutionQueueGetResponse,
    ExecutionQueueInitResponse,
    ListPipelineAuditsResponse,
    PipelineAuditRunRequest,
    PipelineAuditRunResponse,
    PipelineMonitoringSummaryResponse,
    StatusNormalizeRunRequest,
    StatusNormalizeRunResponse,
    ListPipelineEscalationsResponse,
    ControlPanelSummaryResponse,
    ProductionCostsCalculateResponse,
    ProductionCostsGetResponse,
    ProductionPipelineRecoveryResponse,
    ProductionRecoveryRetryRequest,
    ListProductionJobsResponse,
    ListProductionFilesResponse,
    PlanProductionFilesResponse,
    ProductionChecklistResponse,
    ProductionChecklistUpdateRequest,
    ProductionJobActionResponse,
    RunDailyProductionCycleRequest,
    RunDailyProductionCycleResponse,
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
    VoiceSynthCommitRequest,
    VoiceSynthCommitResponse,
    VoiceSynthPreviewRequest,
    VoiceSynthPreviewResponse,
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
    "/production/jobs/{production_job_id}/voice/synthesize-preview",
    response_model=VoiceSynthPreviewResponse,
)
async def production_voice_synthesize_preview(
    production_job_id: str,
    body: Optional[VoiceSynthPreviewRequest] = None,
):
    """Phase 7.2 — OpenAI Speech Preview aus ``voice_plans`` (optional ``dry_run``); keine Persistenz."""
    req = body or VoiceSynthPreviewRequest()
    try:
        out, status_code = watchlist_service.synthesize_voice_plan_preview(
            production_job_id, req, repo=None, provider=None
        )
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("POST voice/synthesize-preview failed: Firestore unavailable")
        body503 = VoiceSynthPreviewResponse(chunks=[], warnings=[msg])
        return JSONResponse(status_code=503, content=body503.model_dump(mode="json"))
    if status_code != 200:
        return JSONResponse(
            status_code=status_code, content=out.model_dump(mode="json")
        )
    return out


@router.post(
    "/production/jobs/{production_job_id}/voice/synthesize",
    response_model=VoiceSynthCommitResponse,
)
async def production_voice_synthesize(
    production_job_id: str,
    body: Optional[VoiceSynthCommitRequest] = None,
):
    """Phase 7.3 — TTS-Commit: Metadaten in ``production_files`` (Typ ``voice``), keine Blobs."""
    req = body or VoiceSynthCommitRequest()
    try:
        out, status_code = watchlist_service.synthesize_voice_commit(
            production_job_id, req, repo=None, provider=None
        )
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("POST voice/synthesize failed: Firestore unavailable")
        body503 = VoiceSynthCommitResponse(scenes=[], warnings=[msg])
        return JSONResponse(status_code=503, content=body503.model_dump(mode="json"))
    if status_code != 200:
        return JSONResponse(
            status_code=status_code, content=out.model_dump(mode="json")
        )
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


@router.post(
    "/production/automation/run-daily-cycle",
    response_model=RunDailyProductionCycleResponse,
)
async def production_run_daily_cycle(
    req: RunDailyProductionCycleRequest = Body(...),
):
    """BA 7.5 — Watchlist-Zyklus, Pending-Jobs, Production-Artefakte; dry_run ohne Schreibzugriffe."""
    try:
        return watchlist_service.run_daily_production_cycle(
            channel_limit=req.channel_limit,
            job_limit=req.job_limit,
            production_limit=req.production_limit,
            dry_run=req.dry_run,
        )
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning(
            "POST /production/automation/run-daily-cycle failed: Firestore unavailable"
        )
        body = RunDailyProductionCycleResponse(warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())


@router.post(
    "/production/jobs/{production_job_id}/files/plan",
    response_model=PlanProductionFilesResponse,
)
async def production_files_plan(production_job_id: str):
    """BA 7.7 — geplante Storage-Pfade persistieren (``planned``, idempotent)."""
    try:
        out = watchlist_service.plan_production_files_service(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("POST files/plan failed: Firestore unavailable")
        body = PlanProductionFilesResponse(
            files=[], planned_new=0, skipped_existing_planned=0, warnings=[msg]
        )
        return JSONResponse(status_code=503, content=body.model_dump())
    if any(w == "not found" for w in (out.warnings or [])):
        raise HTTPException(status_code=404, detail="Production job not found.")
    return out


@router.get(
    "/production/jobs/{production_job_id}/files",
    response_model=ListProductionFilesResponse,
)
async def production_files_list(production_job_id: str):
    """BA 7.7 — Artefakt-Metadaten für einen Production Job."""
    try:
        dj = watchlist_service.get_production_job_detail(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)
    if dj.job is None:
        raise HTTPException(status_code=404, detail="Production job not found.")
    try:
        return watchlist_service.list_production_files_service(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)


@router.post(
    "/production/jobs/{production_job_id}/execution/init",
    response_model=ExecutionQueueInitResponse,
)
async def production_execution_queue_init(production_job_id: str):
    """BA 7.8 — Aus ``production_files`` werden ``execution_jobs`` aufgebaut (idempotent)."""
    try:
        out = watchlist_service.init_execution_queue_service(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("POST execution/init failed: Firestore unavailable")
        body = ExecutionQueueInitResponse(
            production_job_id=production_job_id,
            jobs=[],
            created_new=0,
            reused_existing=0,
            warnings=[msg],
        )
        return JSONResponse(status_code=503, content=body.model_dump())
    if any(w == "not found" for w in (out.warnings or [])):
        raise HTTPException(status_code=404, detail="Production job not found.")
    return out


@router.get(
    "/production/jobs/{production_job_id}/execution",
    response_model=ExecutionQueueGetResponse,
)
async def production_execution_queue_get(production_job_id: str):
    try:
        out = watchlist_service.list_execution_jobs_service(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)
    if any(w == "not found" for w in (out.warnings or [])):
        raise HTTPException(status_code=404, detail="Production job not found.")
    return out


@router.post(
    "/production/jobs/{production_job_id}/costs/calculate",
    response_model=ProductionCostsCalculateResponse,
)
async def production_costs_calculate(production_job_id: str):
    """BA 7.9 — Kosten-Schätzung (EUR) berechnen und in ``production_costs`` persistieren."""
    try:
        out = watchlist_service.calculate_production_costs_service(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("POST costs/calculate failed: Firestore unavailable")
        body = ProductionCostsCalculateResponse(costs=None, warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())
    if any(w == "not found" for w in (out.warnings or [])):
        raise HTTPException(status_code=404, detail="Production job not found.")
    return out


@router.get(
    "/production/jobs/{production_job_id}/costs",
    response_model=ProductionCostsGetResponse,
)
async def production_costs_get(production_job_id: str):
    try:
        out = watchlist_service.get_production_costs_service(production_job_id)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)
    if any(w == "not found" for w in (out.warnings or [])):
        raise HTTPException(status_code=404, detail="Production job not found.")
    return out


@router.post(
    "/production/audit/run",
    response_model=PipelineAuditRunResponse,
)
async def production_audit_run(body: PipelineAuditRunRequest):
    """BA 8.0 — Audit-Funde persistieren."""
    try:
        return watchlist_service.run_pipeline_audit_service(body=body)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("POST /production/audit/run failed")
        fb = PipelineAuditRunResponse(warnings=[msg])
        return JSONResponse(status_code=503, content=fb.model_dump())


@router.get(
    "/production/audit",
    response_model=ListPipelineAuditsResponse,
)
async def production_audit_list(
    limit: int = Query(150, ge=1, le=500),
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
):
    try:
        return watchlist_service.list_pipeline_audits_service(
            limit=limit,
            status=status_filter,
            severity=severity,
        )
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)


@router.post(
    "/production/jobs/{production_job_id}/recovery/retry",
    response_model=ProductionPipelineRecoveryResponse,
)
async def production_pipeline_recovery_retry(
    production_job_id: str,
    body: ProductionRecoveryRetryRequest,
):
    """BA 8.1 — Schritt-gezielt erneut (nicht Produktjobs-„retry„)."""
    try:
        return watchlist_service.retry_production_pipeline_step_service(
            production_job_id,
            body,
        )
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)


@router.get(
    "/production/monitoring/summary",
    response_model=PipelineMonitoringSummaryResponse,
)
async def production_monitoring_summary():
    """BA 8.2 — Kennzahlen Audits / Recovery-Protokolle."""
    try:
        return watchlist_service.pipeline_monitoring_summary_service()
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)


@router.post(
    "/production/status/normalize/run",
    response_model=StatusNormalizeRunResponse,
)
async def production_status_normalize_run(body: StatusNormalizeRunRequest):
    """BA 8.3 — Pipeline-Status stabilisieren, Eskalationen persistieren."""
    try:
        return watchlist_service.run_status_normalization_service(body=body)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("POST /production/status/normalize/run failed")
        fb = StatusNormalizeRunResponse(warnings=[msg])
        return JSONResponse(status_code=503, content=fb.model_dump())


@router.get(
    "/production/status/escalations",
    response_model=ListPipelineEscalationsResponse,
)
async def production_status_escalations(limit: int = Query(120, ge=1, le=400)):
    """BA 8.3 — letzte Einträge in ``pipeline_escalations``."""
    try:
        return watchlist_service.list_pipeline_escalations_service(limit=limit)
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)


@router.get(
    "/production/control-panel/summary",
    response_model=ControlPanelSummaryResponse,
)
async def production_control_panel_summary():
    """BA 8.4 LIGHT — Founder Control Panel (Audits, Eskalationen, Jobs, Provider, Kosten)."""
    try:
        return watchlist_service.get_control_panel_summary_service()
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        logger.warning("GET /production/control-panel/summary failed: Firestore unavailable")
        body = ControlPanelSummaryResponse(warnings=[msg])
        return JSONResponse(status_code=503, content=body.model_dump())
