"""Phase 8.2 — Prompt Engine V1 (Expansion, Provider-Stubs, Continuity Lock, Safety-Negative)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from app.models import (
    SceneExpandedPrompt,
    ScenePromptsRequest,
    ScenePromptsResponse,
    StorySceneBlueprintRequest,
)
from app.visual_plan import policy as vp
from app.visual_plan import warning_codes as vw
from app.visual_plan.builder import build_scene_blueprint_plan


def _dedupe_warnings(ws: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for w in ws:
        key = (w or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(w)
    return out


def _norm_space(s: str) -> str:
    return " ".join((s or "").split())


@dataclass(frozen=True)
class _ProviderStub:
    """Konfigurationsstubs — keine echten API-Parameter."""

    positive_prefix: str
    positive_suffix: str
    extra_negative_segments: tuple[str, ...]


_PROVIDER_STUBS: Dict[str, _ProviderStub] = {
    "leonardo": _ProviderStub(
        positive_prefix="Provider_stub Leonardo illustrative still, ",
        positive_suffix=" Clean composition, editorial illustration tone.",
        extra_negative_segments=("style_bleed", "overbusy_background"),
    ),
    "openai": _ProviderStub(
        positive_prefix="Provider_stub OpenAI image editorial photograph, ",
        positive_suffix=" Natural lighting, news-documentary framing.",
        extra_negative_segments=("oversaturated_hdr", "cluttered_frame"),
    ),
    "kling": _ProviderStub(
        positive_prefix="Provider_stub Kling cinematic video keyframe, ",
        positive_suffix=" Stable camera, readable focal subject.",
        extra_negative_segments=("motion_blur_excess", "shaky_cam"),
    ),
}


def _merge_negative_segments(*groups: tuple[str, ...]) -> str:
    parts: List[str] = []
    for g in groups:
        for x in g:
            t = (x or "").strip()
            if t:
                parts.append(t)
    return "; ".join(sorted(set(parts)))


def _continuity_anchor_from_first_scene(subjects_safe: str, style_tags: List[str]) -> str:
    tag_s = ", ".join(sorted({(t or "").strip() for t in (style_tags or []) if (t or "").strip()}))
    base = _norm_space(subjects_safe or "")
    if tag_s:
        chunk = f"{base} | tags: {tag_s}" if base else f"tags: {tag_s}"
    else:
        chunk = base
    if len(chunk) > 160:
        chunk = chunk[:157].rsplit(" ", 1)[0].strip() + " …"
    return chunk


def build_scene_prompts_v1(req: ScenePromptsRequest) -> ScenePromptsResponse:
    """Blueprint (8.1) → expandierte Prompts. Kein Netzwerk, keine Persistenz."""
    provider_key = req.provider_profile
    stub = _PROVIDER_STUBS[provider_key]

    base_data = req.model_dump(exclude={"provider_profile", "continuity_lock"})
    blueprint = build_scene_blueprint_plan(StorySceneBlueprintRequest.model_validate(base_data))

    warns: List[str] = list(blueprint.warnings or [])
    warns.append(vw.W_PROMPT_PROVIDER_PLACEHOLDER)

    if not blueprint.scenes:
        warns.append(vw.W_PROMPT_NO_SCENES)
        return ScenePromptsResponse(
            policy_profile=vp.VISUAL_PROMPT_ENGINE_POLICY_V1,
            prompt_engine_version=1,
            provider_profile=provider_key,
            continuity_lock_enabled=bool(req.continuity_lock),
            continuity_anchor="",
            blueprint_status=blueprint.status,
            scenes=[],
            warnings=_dedupe_warnings(warns),
        )

    anchor = ""
    if req.continuity_lock:
        first = blueprint.scenes[0]
        anchor = _continuity_anchor_from_first_scene(first.subjects_safe, list(first.style_tags or []))

    safety = tuple(vp.SAFETY_NEGATIVE_SEGMENTS_V1)
    scenes_out: List[SceneExpandedPrompt] = []

    for sc in blueprint.scenes:
        sn = int(sc.scene_number)
        neg_scene = (sc.prompt_pack.negative_hints or "").strip()
        neg_parts: List[str] = []
        if neg_scene:
            for piece in neg_scene.replace(",", ";").split(";"):
                p = piece.strip()
                if p:
                    neg_parts.append(p)
        neg_merged = _merge_negative_segments(
            safety,
            tuple(neg_parts),
            stub.extra_negative_segments,
        )

        pos_body = _norm_space(sc.prompt_pack.image_primary or "")
        positive = _norm_space(f"{stub.positive_prefix}{pos_body}{stub.positive_suffix}")

        continuity_tok = ""
        if req.continuity_lock and anchor:
            continuity_tok = anchor
            if sn > 1:
                positive = _norm_space(
                    f"{positive} Continuity_lock: align with scene_1_anchor — {anchor}"
                )

        scenes_out.append(
            SceneExpandedPrompt(
                scene_number=sn,
                positive_expanded=positive,
                negative_prompt=neg_merged,
                continuity_token=continuity_tok if req.continuity_lock else "",
            )
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
    )
