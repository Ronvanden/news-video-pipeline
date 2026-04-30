"""BA 9.1 — Read-only Story-Engine-Katalog."""

from fastapi import APIRouter

from app.story_engine.templates import public_story_template_catalog

router = APIRouter(tags=["story-engine"])


@router.get("/story-engine/templates")
async def list_story_templates():
    """Öffentliche Meta-Infos zu `video_template`-IDs (keine vollständigen Prompts)."""
    return {"templates": public_story_template_catalog()}
