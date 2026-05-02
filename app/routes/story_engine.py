"""BA 9.x — Story-Engine (Katalog, Hook-Line Nebenkanal)."""

from fastapi import APIRouter, HTTPException

from app.models import (
    ExportFormatsResponse,
    ExportPackagePreviewResponse,
    ExportPackageRequest,
    ExportPackageResponse,
    GenerateHookRequest,
    GenerateHookResponse,
    ProviderPromptOptimizeResponse,
    ProviderReadinessRequest,
    ProviderReadinessResponse,
    RhythmHintRequest,
    RhythmHintResponse,
    SceneBlueprintPlanResponse,
    ScenePromptsRequest,
    ScenePromptsResponse,
    StorySceneBlueprintRequest,
    TemplateSelectorResponse,
    ThumbnailCTRRequest,
    ThumbnailCTRResponse,
)
from app.prompt_engine import build_production_prompt_plan
from app.prompt_engine.schema import ProductionPromptPlan, PromptPlanRequest
from app.story_engine.export_package import build_export_package_v1
from app.story_engine.export_formats import list_export_formats
from app.story_engine.founder_preview import build_export_preview
from app.story_engine.provider_optimizer import optimize_provider_prompts
from app.story_engine.provider_readiness import analyze_provider_readiness
from app.story_engine.thumbnail_ctr import build_thumbnail_ctr_report
from app.story_engine.template_registry import list_templates
from app.story_engine.hook_engine import generate_hook_v1
from app.story_engine.experiment_registry import public_experiment_registry
from app.story_engine.rhythm_engine import rhythm_hints_v1
from app.story_engine.templates import public_story_template_catalog
from app.watchlist import service as watchlist_service
from app.watchlist.firestore_repo import FirestoreUnavailableError
from app.watchlist.models import StoryEngineTemplateHealthHttpResponse
from app.visual_plan.builder import build_scene_blueprint_plan
from app.visual_plan.prompt_engine import build_scene_prompts_v1

router = APIRouter(tags=["story-engine"])


@router.get("/story-engine/templates")
async def list_story_templates():
    """Öffentliche Meta-Infos zu `video_template`-IDs (keine vollständigen Prompts)."""
    return {"templates": public_story_template_catalog()}


@router.post("/story-engine/generate-hook")
async def generate_hook(req: GenerateHookRequest) -> GenerateHookResponse:
    """
    BA 9.2 — Regelbasierte Opening-Line (kein LLM). Ändert nicht `GenerateScriptResponse`.
    """
    r = generate_hook_v1(
        video_template=req.video_template,
        topic=req.topic,
        title=req.title,
        source_summary=req.source_summary,
    )
    return GenerateHookResponse(
        hook_text=r.hook_text,
        hook_type=r.hook_type,
        hook_score=r.hook_score,
        rationale=r.rationale,
        template_match=r.template_match,
        warnings=r.warnings,
    )


@router.post(
    "/story-engine/prompt-plan",
    response_model=ProductionPromptPlan,
)
async def story_engine_prompt_plan(req: PromptPlanRequest) -> ProductionPromptPlan:
    """
    BA 9.10–9.30 & BA 10.0–10.10 & Connector BA 11.0–11.5 & BA 12–13 — Prompt Planning inkl. Quality (9.11), Narrative (9.12), optional
    ``performance_record`` (9.13), Review Gate (9.14), ``repair_suggestions_result`` (9.15),
    ``repair_preview_result`` (9.16), ``human_approval_state`` (9.17),
    ``production_handoff_result`` (9.18), ``production_export_contract_result`` (9.19),
    ``provider_packaging_result`` (9.20), ``provider_export_bundle_result`` (9.21),
    ``package_validation_result`` (9.22), ``production_connector_suite_result`` (10.0 Dry-Run),
    ``connector_auth_contracts_result`` (10.1 Auth-Contract), ``provider_execution_queue_result`` (10.2 Queue),
    ``production_timeline_result`` (9.23),
    ``cost_projection_result`` (9.24), ``final_readiness_gate_result`` (9.25),
    ``template_performance_comparison_result`` (9.26), ``template_recommendation_result`` (9.27),
    ``provider_strategy_optimizer_result`` (9.28), ``production_os_dashboard_result`` (9.29),
    ``master_orchestration_result`` (9.30); nach ``plan_readiness`` additiv
    ``live_execution_guard_result`` (10.4), ``api_activation_control_result`` (10.5),
    ``execution_policy_result`` (10.6 Policy/Kill-Switch), ``provider_job_runner_mock_result`` (10.8),
    ``asset_status_tracker_result`` (10.9), ``production_run_summary_result`` (10.10); danach
    **Connector BA 11.0–11.5** ``live_provider_safety_result``, ``runtime_secret_check_result``,
    ``leonardo_live_result``, ``voice_live_result``, ``asset_persistence_result``,
    ``provider_error_recovery_result`` (optional echtes HTTP nur mit Safety + Secrets + Request-Flag);
    danach **BA 12.0–12.6 Production Assembly** ``master_asset_manifest_result``,
    ``multi_asset_assembly_result``, ``final_timeline_result``, ``voice_scene_alignment_result``,
    ``render_instruction_package_result``, ``downloadable_production_bundle_result``,
    ``human_final_review_package_result``; danach **BA 13.0–13.6 Publishing Preparation**
    ``metadata_master_package_result``, ``metadata_optimizer_result``, ``thumbnail_variant_pack_result``,
    ``upload_checklist_result``, ``schedule_plan_result``, ``publishing_readiness_gate_result``,
    ``founder_publishing_summary_result``; danach **BA 14.0–14.7 Performance Feedback**
    ``kpi_ingest_contract_result``, ``kpi_normalization_result``, ``hook_performance_result``,
    ``template_evolution_result``, ``cost_revenue_analysis_result``, ``auto_recommendation_upgrade_result``,
    ``founder_growth_intelligence_result``, ``master_feedback_orchestrator_result`` — keine verpflichtende
    YouTube-Live-API, keine Auto-Monetization.
    Schema-Layer: ``result_store_schema`` (10.7), **ohne** DB-Write.

    Deterministisch, JSON-getrieben unter ``app/templates/prompt_planning/``; **kein** Teil von
    ``GenerateScriptResponse``.
    """
    try:
        return build_production_prompt_plan(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/story-engine/rhythm-hint")
async def rhythm_hint(req: RhythmHintRequest) -> RhythmHintResponse:
    """BA 9.4 Nebenkanal — ändert nicht den Live-`/generate-script`-Vertrag."""
    blocks, warns = rhythm_hints_v1(
        video_template=req.video_template,
        duration_minutes=req.duration_minutes,
        chapters=[c.model_dump() for c in req.chapters],
        hook=req.hook or "",
    )
    return RhythmHintResponse(rhythm=blocks, warnings=warns)


@router.post(
    "/story-engine/scene-plan",
    response_model=SceneBlueprintPlanResponse,
)
async def story_engine_scene_blueprint(req: StorySceneBlueprintRequest):
    """
    Makro‑Phase 8.1 — Scene Blueprint Contract (deterministisch).

    Nur lesend aus übergebenem Skript-/Kapitelteil; **kein** Bildgenerator, **keine**
    Persistenz. Verändert **`GenerateScriptResponse`** nicht.
    """
    return build_scene_blueprint_plan(req)


@router.post(
    "/story-engine/scene-prompts",
    response_model=ScenePromptsResponse,
)
async def story_engine_scene_prompts(req: ScenePromptsRequest):
    """
    Makro‑Phase 8.2 — Prompt Engine V1 (Expansion, Provider-Stubs, Continuity).

    Baut auf **`/story-engine/scene-plan`** (8.1) auf; **keine** Bildgenerierung, **keine** Persistenz.
    **`GenerateScriptResponse`** unverändert.
    """
    return build_scene_prompts_v1(req)


@router.post(
    "/story-engine/export-package",
    response_model=ExportPackageResponse,
)
async def story_engine_export_package(req: ExportPackageRequest) -> ExportPackageResponse:
    """
    BA 10.3 — Prompt-to-Production Export V1 (lokal, kein Bild-API, kein Firestore-Write).

    Aggregiert Hook, Rhythm, Scene-Plan, Scene-Prompts, alle Provider-Stub-Varianten,
    Thumbnail-Platzhalter-Prompt, `prompt_quality` und gemergte Warnings.
    """
    return build_export_package_v1(req)


@router.post(
    "/story-engine/export-package/preview",
    response_model=ExportPackagePreviewResponse,
)
async def story_engine_export_package_preview(
    req: ExportPackageRequest,
) -> ExportPackagePreviewResponse:
    """
    BA 10.4 — Kompakte Founder-Ansicht (Hook, Qualität, Provider-Flags, Readiness).

    Nutzt dieselbe Eingabe wie `/story-engine/export-package`; **keine** externen Provider-Calls,
    **keine** Persistenz.
    """
    return build_export_preview(req)


@router.get(
    "/story-engine/template-selector",
    response_model=TemplateSelectorResponse,
)
async def story_engine_template_selector() -> TemplateSelectorResponse:
    """BA 10.4 — Öffentliche Template-Übersicht für Format- und Hook-Vergleiche."""
    return TemplateSelectorResponse(templates=list_templates())


@router.post(
    "/story-engine/provider-readiness",
    response_model=ProviderReadinessResponse,
)
async def story_engine_provider_readiness(
    req: ProviderReadinessRequest,
) -> ProviderReadinessResponse:
    """
    BA 10.4 — Heuristische Produktions-Readiness je Stub-Profil (Leonardo, Kling, OpenAI).

    Baut intern das Export-Paket wie BA 10.3; **keine** Bild-/Video-APIs.
    """
    pkg = build_export_package_v1(req)
    return analyze_provider_readiness(pkg)


@router.post(
    "/story-engine/provider-prompts/optimize",
    response_model=ProviderPromptOptimizeResponse,
)
async def story_engine_provider_prompts_optimize(
    req: ExportPackageRequest,
) -> ProviderPromptOptimizeResponse:
    """
    BA 10.5 — Leonardo-/Kling-/OpenAI-optimierte Prompts, Shotlists und Thumbnail-Varianten.

    Eingabe wie Export-Paket; **keine** externen Provider-Calls, **keine** Persistenz.
    """
    return optimize_provider_prompts(req)


@router.post(
    "/story-engine/thumbnail-ctr",
    response_model=ThumbnailCTRResponse,
)
async def story_engine_thumbnail_ctr(req: ThumbnailCTRRequest) -> ThumbnailCTRResponse:
    """BA 10.5 — Heuristischer CTR-Score und Thumbnail-Textvarianten (ohne Bildanalyse)."""
    return build_thumbnail_ctr_report(req)


@router.get(
    "/story-engine/export-formats",
    response_model=ExportFormatsResponse,
)
async def story_engine_export_formats() -> ExportFormatsResponse:
    """BA 10.5 — Read-only Registry der Export- und Produktionsartefakte."""
    return list_export_formats()


@router.get("/story-engine/experiment-registry")
async def hook_experiment_registry():
    """BA 9.6 — öffentlicher Katalog lokaler Experiment-/Variant-Meta."""
    return public_experiment_registry()


@router.get(
    "/story-engine/template-health",
    response_model=StoryEngineTemplateHealthHttpResponse,
)
async def template_health_story_engine():
    """
    BA 9.7 (Optimization) und BA 9.8 (Intelligence) aus ``generated_scripts``-Stichprobe.
    Ändert nicht ``GenerateScriptResponse``.
    """
    try:
        return watchlist_service.get_story_engine_template_health_service()
    except FirestoreUnavailableError as e:
        msg = str(e) if str(e) else "Firestore ist nicht erreichbar."
        raise HTTPException(status_code=503, detail=msg)
