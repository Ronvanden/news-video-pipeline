"""Read-only Visual Plan endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from app.visual_plan.presets import get_visual_prompt_control_options


router = APIRouter(tags=["visual-plan"])


@router.get("/visual-plan/presets")
async def visual_plan_presets() -> Dict[str, Any]:
    """Return the stable visual prompt controls catalog for dashboard clients."""
    return get_visual_prompt_control_options()
