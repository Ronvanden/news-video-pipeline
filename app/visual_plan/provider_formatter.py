"""BA 10.2 — Provider-spezifische Prompt-Formatierung (Stubs, kein API-Dispatch)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from app.models import (
    SceneBlueprintPlanResponse,
    SceneExpandedPrompt,
    ProviderPromptsBundle,
)


def _norm_space(s: str) -> str:
    return " ".join((s or "").split())


@dataclass(frozen=True)
class ProviderStub:
    """Konfigurationsstubs — keine echten API-Parameter."""

    positive_prefix: str
    positive_suffix: str
    extra_negative_segments: tuple[str, ...]


PROVIDER_STUBS: Dict[str, ProviderStub] = {
    "leonardo": ProviderStub(
        positive_prefix="Provider_stub Leonardo illustrative still, ",
        positive_suffix=" Clean composition, editorial illustration tone.",
        extra_negative_segments=("style_bleed", "overbusy_background"),
    ),
    "openai": ProviderStub(
        positive_prefix="Provider_stub OpenAI image editorial photograph, ",
        positive_suffix=" Natural lighting, news-documentary framing.",
        extra_negative_segments=("oversaturated_hdr", "cluttered_frame"),
    ),
    "kling": ProviderStub(
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


def expand_scenes_for_provider(
    blueprint: SceneBlueprintPlanResponse,
    provider_key: str,
    continuity_lock: bool,
    safety_segments: tuple[str, ...],
) -> tuple[List[SceneExpandedPrompt], str]:
    """
    Liefert expandierte Szenen für ein Profil plus continuity_anchor (leer wenn lock aus).

    `safety_segments` wird vom Aufrufer (policy) übergeben, um Zyklen mit policy zu vermeiden.
    """
    stub = PROVIDER_STUBS[provider_key]
    if not blueprint.scenes:
        return [], ""

    anchor = ""
    if continuity_lock:
        first = blueprint.scenes[0]
        anchor = _continuity_anchor_from_first_scene(first.subjects_safe, list(first.style_tags or []))

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
            safety_segments,
            tuple(neg_parts),
            stub.extra_negative_segments,
        )

        pos_body = _norm_space(sc.prompt_pack.image_primary or "")
        positive = _norm_space(f"{stub.positive_prefix}{pos_body}{stub.positive_suffix}")

        continuity_tok = ""
        if continuity_lock and anchor:
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
                continuity_token=continuity_tok if continuity_lock else "",
            )
        )

    return scenes_out, (anchor if continuity_lock else "")


def build_all_provider_prompts(
    blueprint: SceneBlueprintPlanResponse,
    continuity_lock: bool,
    safety_segments: tuple[str, ...],
) -> ProviderPromptsBundle:
    """Alle drei Stub-Profile für dieselbe Blueprint-Basis."""
    leo, _ = expand_scenes_for_provider(blueprint, "leonardo", continuity_lock, safety_segments)
    oai, _ = expand_scenes_for_provider(blueprint, "openai", continuity_lock, safety_segments)
    kli, _ = expand_scenes_for_provider(blueprint, "kling", continuity_lock, safety_segments)
    return ProviderPromptsBundle(leonardo=leo, openai=oai, kling=kli)
