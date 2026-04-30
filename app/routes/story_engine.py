"""BA 9.x — Story-Engine (Katalog, Hook-Line Nebenkanal)."""

from fastapi import APIRouter

from app.models import (
    GenerateHookRequest,
    GenerateHookResponse,
    RhythmHintRequest,
    RhythmHintResponse,
)
from app.story_engine.hook_engine import generate_hook_v1
from app.story_engine.experiment_registry import public_experiment_registry
from app.story_engine.rhythm_engine import rhythm_hints_v1
from app.story_engine.templates import public_story_template_catalog

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


@router.get("/story-engine/experiment-registry")
async def hook_experiment_registry():
    """BA 9.6 — öffentlicher Katalog lokaler Experiment-/Variant-Meta."""
    return public_experiment_registry()
