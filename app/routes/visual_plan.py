"""Read-only Visual Plan endpoints."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.visual_plan.engine_v1 import VisualPromptEngineContext, build_visual_prompt_v1
from app.visual_plan.presets import get_visual_prompt_control_options


router = APIRouter(tags=["visual-plan"])


class VisualPromptPreviewRequest(BaseModel):
    """Preview-only payload for the Visual Prompt Engine."""

    scene_title: str = Field(default="Preview scene")
    narration: str = ""
    video_template: str = ""
    beat_role: str = ""
    visual_preset: str | None = None
    prompt_detail_level: str | None = None
    provider_target: str | None = None
    text_safety_mode: str | None = None
    visual_consistency_mode: str | None = None


class VisualPromptPreviewResponse(BaseModel):
    """Stable response shape for dashboard prompt previews."""

    visual_prompt_raw: str
    visual_prompt_effective: str
    negative_prompt: str
    visual_prompt_anatomy: Dict[str, Any]
    visual_policy_warnings: List[str]
    visual_style_profile: str
    prompt_quality_score: int
    prompt_risk_flags: List[str]
    normalized_controls: Dict[str, str]


@router.get("/visual-plan/presets")
async def visual_plan_presets() -> Dict[str, Any]:
    """Return the stable visual prompt controls catalog for dashboard clients."""
    return get_visual_prompt_control_options()


@router.post("/visual-plan/prompt-preview", response_model=VisualPromptPreviewResponse)
async def visual_plan_prompt_preview(req: VisualPromptPreviewRequest) -> VisualPromptPreviewResponse:
    """Run Visual Prompt Engine V1 without providers, rendering, or persistence."""
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title=req.scene_title,
            narration=req.narration,
            video_template=req.video_template,
            beat_role=req.beat_role,
            visual_preset=req.visual_preset,
            prompt_detail_level=req.prompt_detail_level,
            provider_target=req.provider_target,
            text_safety_mode=req.text_safety_mode,
            visual_consistency_mode=req.visual_consistency_mode,
        )
    )
    return VisualPromptPreviewResponse(**asdict(result))
