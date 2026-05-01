"""BA 9.x — Story-Engine (Katalog, Hook-Line Nebenkanal)."""

from fastapi import APIRouter, HTTPException

from app.models import (
    GenerateHookRequest,
    GenerateHookResponse,
    RhythmHintRequest,
    RhythmHintResponse,
    SceneBlueprintPlanResponse,
    StorySceneBlueprintRequest,
)
from app.story_engine.hook_engine import generate_hook_v1
from app.story_engine.experiment_registry import public_experiment_registry
from app.story_engine.rhythm_engine import rhythm_hints_v1
from app.story_engine.templates import public_story_template_catalog
from app.watchlist import service as watchlist_service
from app.watchlist.firestore_repo import FirestoreUnavailableError
from app.watchlist.models import StoryEngineTemplateHealthHttpResponse
from app.visual_plan.builder import build_scene_blueprint_plan

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
