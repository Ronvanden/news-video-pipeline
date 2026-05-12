"""Storyboard builder: PromptPlan/script chapters -> production orchestration plan."""

from __future__ import annotations

import re
from typing import Iterable, List, Optional, Tuple

from app.models import Chapter, ScenePromptsRequest
from app.prompt_engine.schema import ProductionPromptPlan, TimelineRole
from app.prompt_engine.timeline_builder import build_production_timeline
from app.storyboard.schema import (
    StoryboardAssetType,
    StoryboardBuildRequest,
    StoryboardChapterInput,
    StoryboardPlan,
    StoryboardScene,
    StoryboardTransition,
)
from app.visual_plan.engine_v1 import VisualPromptEngineContext, VisualPromptEngineResult, build_visual_prompt_v1
from app.visual_plan.prompt_anatomy import VisualPromptAnatomy, build_motion_prompt_anatomy
from app.visual_plan.prompt_engine import build_scene_prompts_v1
from app.visual_plan.prompt_formatters import anatomy_to_runway_motion_prompt


_DEFAULT_BODY_DURATION_SECONDS = 34
_HOOK_DURATION_SECONDS = 12
_OUTRO_DURATION_SECONDS = 15
_VOICE_CAP = 900
_PROMPT_CAP = 900
_INTENT_CAP = 320


def _norm(s: str) -> str:
    return " ".join((s or "").split())


def _clip(s: str, cap: int) -> Tuple[str, bool]:
    text = _norm(s)
    if len(text) <= cap:
        return text, False
    cut = text[: max(1, cap - 3)].rsplit(" ", 1)[0].strip()
    return f"{cut}...", True


def _dedupe(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for item in items:
        v = _norm(str(item or ""))
        if not v or v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


def _role_for_index(idx: int, total: int) -> TimelineRole:
    if total <= 1:
        return "outro"
    if idx == 0:
        return "setup"
    if idx == total - 1:
        return "outro"
    if idx == total - 2:
        return "climax"
    return "build" if idx % 2 else "escalation"


def _duration_for_role(role: TimelineRole) -> int:
    if role == "hook":
        return _HOOK_DURATION_SECONDS
    if role == "setup":
        return 28
    if role == "build":
        return 32
    if role == "escalation":
        return 38
    if role == "climax":
        return 45
    return _OUTRO_DURATION_SECONDS


def _transition_for_role(role: TimelineRole) -> StoryboardTransition:
    if role == "hook":
        return "cut"
    if role == "setup":
        return "dissolve"
    if role == "build":
        return "push_in"
    if role in ("escalation", "climax"):
        return "match_cut"
    return "fade_out"


def _asset_type_for_role(role: TimelineRole) -> StoryboardAssetType:
    if role == "hook":
        return "hook_card"
    if role in ("build", "escalation", "climax"):
        return "image_to_video_candidate"
    if role == "outro":
        return "outro_card"
    return "image_keyframe"


def _motion_hint_for_role(role: TimelineRole) -> str:
    return {
        "hook": "fast editorial opener, no generated text overlays",
        "setup": "slow establishing camera move, grounded documentary pacing",
        "build": "subtle push-in, maintain continuity, no readable generated text",
        "escalation": "controlled tension, gentle parallax, no shock imagery",
        "climax": "focused reveal beat, cinematic but factual, no gore",
        "outro": "calm resolving motion, hold for final narration",
    }.get(role, "subtle motion")


def _visual_anatomy_from_engine(result: VisualPromptEngineResult) -> VisualPromptAnatomy:
    raw = dict(result.visual_prompt_anatomy or {})
    allowed = set(VisualPromptAnatomy.__dataclass_fields__.keys())
    payload = {k: v for k, v in raw.items() if k in allowed}
    return VisualPromptAnatomy(**payload)


def _video_prompt(
    image_prompt: str,
    role: TimelineRole,
    engine_result: VisualPromptEngineResult,
    duration_seconds: int,
) -> str:
    motion_hint = _motion_hint_for_role(role)
    visual_anatomy = _visual_anatomy_from_engine(engine_result)
    motion_anatomy = build_motion_prompt_anatomy(
        visual_anatomy,
        normalized_controls=dict(engine_result.normalized_controls or {}),
        motion_hint=motion_hint,
        duration_seconds=duration_seconds,
    )
    prompt = anatomy_to_runway_motion_prompt(
        visual_anatomy,
        motion_anatomy,
        dict(engine_result.normalized_controls or {}),
    )
    if prompt:
        return prompt
    base, _ = _clip(image_prompt, 640)
    return f"{base}. Motion direction: {motion_hint}."


def _visual_engine_result(
    *,
    scene_title: str,
    narration: str,
    video_template: str,
    beat_role: str,
) -> VisualPromptEngineResult:
    return build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title=scene_title,
            narration=narration,
            video_template=video_template,
            beat_role=beat_role,
        )
    )


def _visual_engine_fields(result: VisualPromptEngineResult) -> dict:
    return {
        "visual_prompt_raw": result.visual_prompt_raw,
        "visual_prompt_effective": result.visual_prompt_effective,
        "negative_prompt": result.negative_prompt,
        "visual_policy_warnings": list(result.visual_policy_warnings or []),
        "visual_style_profile": result.visual_style_profile,
        "prompt_quality_score": result.prompt_quality_score,
        "prompt_risk_flags": list(result.prompt_risk_flags or []),
        "normalized_controls": dict(result.normalized_controls or {}),
    }


def _chapter_to_model(ch: StoryboardChapterInput) -> Chapter:
    content = ch.content or ch.summary
    return Chapter(title=ch.title, content=content)


def _scene_prompts_for_chapters(
    *,
    hook: str,
    chapters: List[StoryboardChapterInput],
    video_template: str,
) -> Tuple[List[str], List[str]]:
    if not chapters:
        return [], ["storyboard_no_chapters"]
    req = ScenePromptsRequest(
        video_template=video_template or "generic",
        hook=hook or "",
        chapters=[_chapter_to_model(ch) for ch in chapters],
        provider_profile="kling",
        continuity_lock=True,
    )
    resp = build_scene_prompts_v1(req)
    prompts = [s.positive_expanded for s in resp.scenes]
    return prompts, list(resp.warnings or [])


def _chapter_voice_text(ch: StoryboardChapterInput) -> str:
    raw = ch.content or ch.summary or ch.title
    text, _ = _clip(raw, _VOICE_CAP)
    return text


def _chapter_intent(ch: StoryboardChapterInput, scene_prompt: str) -> str:
    raw = f"{ch.title}. {ch.summary or ch.content or scene_prompt}"
    text, _ = _clip(raw, _INTENT_CAP)
    return text


def build_storyboard_plan_from_prompt_plan(plan: ProductionPromptPlan) -> StoryboardPlan:
    chapters = [
        StoryboardChapterInput(title=c.title, summary=c.summary, content=c.summary)
        for c in (plan.chapter_outline or [])
    ]
    req = StoryboardBuildRequest(
        prompt_plan=plan,
        hook=plan.hook,
        chapters=chapters,
        scene_prompts=list(plan.scene_prompts or []),
        video_template=plan.video_template or plan.template_type or "generic",
        voice_style=plan.voice_style,
    )
    return build_storyboard_plan(req)


def build_storyboard_plan(req: StoryboardBuildRequest) -> StoryboardPlan:
    """Build a deterministic storyboard. No network, no persistence, no provider calls."""
    if req.prompt_plan is not None:
        plan = req.prompt_plan
        hook = plan.hook or req.hook
        video_template = plan.video_template or plan.template_type or req.video_template or "generic"
        chapters = [
            StoryboardChapterInput(title=c.title, summary=c.summary, content=c.summary)
            for c in (plan.chapter_outline or [])
        ]
        provided_scene_prompts = list(plan.scene_prompts or [])
        source_type = "prompt_plan"
        timeline = build_production_timeline(plan)
    else:
        hook = req.hook
        video_template = req.video_template or "generic"
        chapters = list(req.chapters or [])
        provided_scene_prompts = list(req.scene_prompts or [])
        source_type = "script_chapters"
        timeline = None

    warnings: List[str] = []
    if not chapters and not _norm(hook):
        return StoryboardPlan(
            status="blocked",
            source_type=source_type,
            video_template=video_template,
            warnings=["storyboard_no_hook_or_chapters"],
            scenes=[],
            total_duration_seconds=0,
        )

    built_scene_prompts: List[str] = []
    if len(provided_scene_prompts) < len(chapters):
        built_scene_prompts, prompt_warnings = _scene_prompts_for_chapters(
            hook=hook,
            chapters=chapters,
            video_template=video_template,
        )
        warnings.extend(prompt_warnings)

    scene_prompts = []
    for idx in range(len(chapters)):
        if idx < len(provided_scene_prompts) and _norm(provided_scene_prompts[idx]):
            scene_prompts.append(provided_scene_prompts[idx])
        elif idx < len(built_scene_prompts):
            scene_prompts.append(built_scene_prompts[idx])
        else:
            scene_prompts.append("")
            warnings.append(f"storyboard_scene_prompt_missing:{idx + 1}")

    if len(provided_scene_prompts) > len(chapters):
        warnings.append("storyboard_extra_scene_prompts_ignored")

    out: List[StoryboardScene] = []
    scene_no = 1
    if _norm(hook):
        hook_engine = _visual_engine_result(
            scene_title="Hook",
            narration=hook,
            video_template=video_template,
            beat_role="hook",
        )
        hook_prompt, hook_truncated = _clip(hook_engine.visual_prompt_effective, _PROMPT_CAP)
        if hook_truncated:
            warnings.append("storyboard_hook_prompt_truncated")
        out.append(
            StoryboardScene(
                scene_number=scene_no,
                source="hook",
                chapter_title="Hook",
                timeline_role="hook",
                visual_intent=_clip(hook, _INTENT_CAP)[0],
                voice_text=_clip(hook, _VOICE_CAP)[0],
                image_prompt=hook_prompt,
                video_prompt=_video_prompt(hook_prompt, "hook", hook_engine, _duration_for_role("hook")),
                **_visual_engine_fields(hook_engine),
                duration_seconds=_duration_for_role("hook"),
                transition=_transition_for_role("hook"),
                asset_type=_asset_type_for_role("hook"),
                provider_hints=["image", "render_layer"],
            )
        )
        scene_no += 1

    timeline_by_title = {}
    if timeline is not None and timeline.timeline_status != "blocked":
        warnings.extend(timeline.warnings or [])
        for ts in timeline.scenes:
            timeline_by_title.setdefault(_norm(ts.chapter_title).lower(), ts)

    total_chapters = len(chapters)
    for idx, ch in enumerate(chapters):
        role = _role_for_index(idx, total_chapters)
        duration = _duration_for_role(role)
        key = _norm(ch.title).lower()
        ts = timeline_by_title.get(key)
        if ts is not None:
            role = ts.timeline_role
            duration = int(ts.estimated_duration_seconds)

        image_prompt = scene_prompts[idx] if idx < len(scene_prompts) else ""
        if not _norm(image_prompt):
            image_prompt = f"Grounded editorial scene for chapter: {_norm(ch.title)}"
        image_prompt, prompt_truncated = _clip(image_prompt, _PROMPT_CAP)
        scene_warnings: List[str] = []
        if prompt_truncated:
            scene_warnings.append("storyboard_image_prompt_truncated")

        voice_text = _chapter_voice_text(ch)
        scene_engine = _visual_engine_result(
            scene_title=ch.title or f"Scene {scene_no}",
            narration=image_prompt or voice_text,
            video_template=video_template,
            beat_role=role,
        )
        if not voice_text:
            scene_warnings.append("storyboard_voice_text_missing")
            warnings.append(f"storyboard_voice_text_missing:{idx + 1}")

        out.append(
            StoryboardScene(
                scene_number=scene_no,
                source=source_type[:-1] if source_type == "script_chapters" else "prompt_plan",
                chapter_title=ch.title or f"Scene {scene_no}",
                timeline_role=role,
                visual_intent=_chapter_intent(ch, image_prompt),
                voice_text=voice_text,
                image_prompt=image_prompt,
                video_prompt=_video_prompt(image_prompt, role, scene_engine, duration),
                **_visual_engine_fields(scene_engine),
                duration_seconds=duration,
                transition=_transition_for_role(role),
                asset_type=_asset_type_for_role(role),
                provider_hints=["image", "video", "voice", "render_timeline"],
                warnings=scene_warnings,
            )
        )
        scene_no += 1

    status = "ready"
    if warnings or any(s.warnings for s in out):
        status = "partial"
    if not out:
        status = "blocked"

    total_duration = sum(s.duration_seconds for s in out)
    return StoryboardPlan(
        status=status,
        source_type=source_type,
        video_template=video_template,
        total_duration_seconds=total_duration,
        scenes=out,
        warnings=_dedupe(warnings),
        dashboard_ready=True,
    )
