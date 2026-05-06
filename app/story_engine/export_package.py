"""BA 10.3 — lokales Export-Paket (Hook, Rhythm, Plan, Prompts) ohne Provider-Calls / Firestore."""

from __future__ import annotations

from typing import List

from app.models import (
    ExportHookBlock,
    ExportPackageRequest,
    ExportPackageResponse,
    ScenePromptsRequest,
    StorySceneBlueprintRequest,
)
from app.story_engine.hook_engine import generate_hook_v1
from app.story_engine.rhythm_engine import rhythm_hints_v1
from app.visual_plan.builder import build_scene_blueprint_plan
from app.visual_plan.policy import SAFETY_NEGATIVE_SEGMENTS_V1
from app.visual_plan.prompt_engine import build_scene_prompts_from_blueprint
from app.visual_plan.provider_formatter import build_all_provider_prompts
from app.visual_plan.visual_no_text import append_no_text_guard


def _dedupe_warnings(ws: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for w in ws or []:
        key = (w or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def build_thumbnail_prompt_v1(req: ExportPackageRequest) -> tuple[str, List[str]]:
    """Deterministischer Platzhalter-Thumbnail-Prompt (kein Bild-API)."""
    tid = (req.video_template or "generic").strip() or "generic"
    title = (req.title or "").strip() or "Video"
    ch1 = ""
    if req.chapters:
        ch1 = ((req.chapters[0].title or "") + " " + (req.chapters[0].content or "")).strip()
        if len(ch1) > 100:
            ch1 = ch1[:97].rsplit(" ", 1)[0] + "…"
    parts = [
        "Thumbnail_stub editorial YouTube key visual",
        f"template={tid}",
        f"title_anchor={title[:120]}",
    ]
    if ch1:
        parts.append(f"first_chapter_hint={ch1}")
    parts.append(
        "constraints: single focal subject, high contrast, no_legible_trademark_text, "
        "no_fake_news_tickers, no_identifiable_real_person_likeness_claims"
    )
    return append_no_text_guard(" | ".join(parts)), []


def build_export_package_v1(req: ExportPackageRequest) -> ExportPackageResponse:
    base = req.model_dump(
        exclude={"provider_profile", "continuity_lock", "topic", "source_summary"},
    )
    blueprint_req = StorySceneBlueprintRequest.model_validate(base)
    blueprint = build_scene_blueprint_plan(blueprint_req)

    hook_r = generate_hook_v1(
        video_template=req.video_template,
        topic=req.topic,
        title=req.title,
        source_summary=req.source_summary,
    )
    hook_block = ExportHookBlock(
        hook_text=hook_r.hook_text,
        hook_type=hook_r.hook_type,
        hook_score=hook_r.hook_score,
        rationale=hook_r.rationale,
        template_match=hook_r.template_match,
        warnings=list(hook_r.warnings or []),
    )

    hook_for_rhythm = (req.hook or "").strip() or hook_r.hook_text
    rhythm_blocks, rhythm_warns = rhythm_hints_v1(
        video_template=req.video_template,
        duration_minutes=req.duration_minutes,
        chapters=[c.model_dump() for c in req.chapters],
        hook=hook_for_rhythm,
    )

    sp_req = ScenePromptsRequest.model_validate(req.model_dump())
    scene_prompts = build_scene_prompts_from_blueprint(sp_req, blueprint)

    provider_prompts = build_all_provider_prompts(
        blueprint,
        bool(req.continuity_lock),
        tuple(SAFETY_NEGATIVE_SEGMENTS_V1),
    )

    thumb, thumb_warns = build_thumbnail_prompt_v1(req)

    merged = _dedupe_warnings(
        list(hook_block.warnings)
        + list(rhythm_warns or [])
        + list(blueprint.warnings or [])
        + list(scene_prompts.warnings or [])
        + list(thumb_warns or [])
    )

    pq = scene_prompts.prompt_quality

    return ExportPackageResponse(
        hook=hook_block,
        rhythm=rhythm_blocks,
        scene_plan=blueprint,
        scene_prompts=scene_prompts,
        provider_prompts=provider_prompts,
        thumbnail_prompt=thumb,
        prompt_quality=pq,
        warnings=merged,
    )
