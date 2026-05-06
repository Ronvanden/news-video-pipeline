"""Phase 8.2 — Prompt Engine V1 (Expansion, Provider-Stubs, Continuity Lock, Safety-Negative)."""

from __future__ import annotations

from typing import List

from app.models import (
    SceneBlueprintPlanResponse,
    SceneExpandedPrompt,
    ScenePromptsRequest,
    ScenePromptsResponse,
    StorySceneBlueprintRequest,
)
from app.visual_plan import policy as vp
from app.visual_plan import warning_codes as vw
from app.visual_plan.builder import build_scene_blueprint_plan
from app.visual_plan.prompt_quality import build_prompt_quality
from app.visual_plan.provider_formatter import expand_scenes_for_provider


def _dedupe_warnings(ws: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for w in ws:
        key = (w or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def build_scene_prompts_from_blueprint(
    req: ScenePromptsRequest,
    blueprint: SceneBlueprintPlanResponse,
) -> ScenePromptsResponse:
    """Blueprint → expandierte Prompts inkl. BA 10.1 Quality (kein zweites Blueprint-Lesen nötig)."""
    provider_key = req.provider_profile
    warns: List[str] = list(blueprint.warnings or [])
    warns.append(vw.W_PROMPT_PROVIDER_PLACEHOLDER)

    safety = tuple(vp.SAFETY_NEGATIVE_SEGMENTS_V1)

    if not blueprint.scenes:
        warns.append(vw.W_PROMPT_NO_SCENES)
        scenes_out: List[SceneExpandedPrompt] = []
        quality = build_prompt_quality(
            blueprint,
            scenes_out,
            continuity_lock=bool(req.continuity_lock),
        )
        return ScenePromptsResponse(
            policy_profile=vp.VISUAL_PROMPT_ENGINE_POLICY_V1,
            prompt_engine_version=1,
            provider_profile=provider_key,
            continuity_lock_enabled=bool(req.continuity_lock),
            continuity_anchor="",
            blueprint_status=blueprint.status,
            scenes=scenes_out,
            warnings=_dedupe_warnings(warns),
            prompt_quality=quality,
        )

    scenes_out, anchor = expand_scenes_for_provider(
        blueprint,
        provider_key,
        bool(req.continuity_lock),
        safety,
    )
    quality = build_prompt_quality(
        blueprint,
        scenes_out,
        continuity_lock=bool(req.continuity_lock),
    )

    return ScenePromptsResponse(
        policy_profile=vp.VISUAL_PROMPT_ENGINE_POLICY_V1,
        prompt_engine_version=1,
        provider_profile=provider_key,
        continuity_lock_enabled=bool(req.continuity_lock),
        continuity_anchor=anchor if req.continuity_lock else "",
        blueprint_status=blueprint.status,
        scenes=scenes_out,
        warnings=_dedupe_warnings(warns),
        prompt_quality=quality,
    )


def build_scene_prompts_v1(req: ScenePromptsRequest) -> ScenePromptsResponse:
    """Blueprint (8.1) → expandierte Prompts. Kein Netzwerk, keine Persistenz."""
    base_data = req.model_dump(exclude={"provider_profile", "continuity_lock"})
    blueprint = build_scene_blueprint_plan(StorySceneBlueprintRequest.model_validate(base_data))
    return build_scene_prompts_from_blueprint(req, blueprint)
