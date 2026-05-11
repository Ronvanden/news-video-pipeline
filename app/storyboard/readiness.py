"""Plan-only storyboard readiness gate before provider execution."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Iterable, List, Tuple

from app.storyboard.builder import build_storyboard_plan
from app.storyboard.schema import (
    StoryboardPlan,
    StoryboardReadinessRequest,
    StoryboardReadinessResult,
    StoryboardReadinessSceneResult,
    StoryboardReadinessStatus,
    StoryboardScene,
)


_MIN_SCENE_SECONDS = 5
_MAX_SCENE_SECONDS = 90
_SIMILARITY_THRESHOLD = 0.93


def _norm(s: str) -> str:
    return " ".join(str(s or "").split()).strip()


def _prompt_key(s: str) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", str(s or "").lower())
    return " ".join(text.split())


def _dedupe(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for item in items:
        v = _norm(item)
        if not v or v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


def _asset_requires_image(scene: StoryboardScene) -> bool:
    return scene.asset_type in ("hook_card", "image_keyframe", "image_to_video_candidate", "outro_card")


def _asset_requires_video(scene: StoryboardScene) -> bool:
    return scene.asset_type in ("image_to_video_candidate", "b_roll_sequence")


def _score_scene(blockers: List[str], warnings: List[str]) -> int:
    score = 100 - len(blockers) * 34 - len(warnings) * 10
    return max(0, min(100, score))


def _status(blockers: List[str], warnings: List[str]) -> StoryboardReadinessStatus:
    if blockers:
        return "blocked"
    if warnings:
        return "warning"
    return "ready"


def _similar_prompt_warnings(scenes: List[StoryboardScene]) -> List[Tuple[int, int, str]]:
    warnings: List[Tuple[int, int, str]] = []
    keyed = [(s.scene_number, _prompt_key(f"{s.image_prompt} {s.video_prompt}")) for s in scenes]
    for i in range(len(keyed)):
        n1, p1 = keyed[i]
        if len(p1) < 24:
            continue
        for j in range(i + 1, len(keyed)):
            n2, p2 = keyed[j]
            if len(p2) < 24:
                continue
            if p1 == p2 or SequenceMatcher(None, p1, p2).ratio() >= _SIMILARITY_THRESHOLD:
                warnings.append((n1, n2, f"storyboard_duplicate_or_near_duplicate_prompt:{n1}:{n2}"))
    return warnings


def evaluate_storyboard_readiness(plan: StoryboardPlan) -> StoryboardReadinessResult:
    """Evaluate a storyboard plan without calling providers or writing state."""
    global_blockers: List[str] = []
    global_warnings: List[str] = []
    scenes = list(plan.scenes or [])

    if not scenes:
        global_blockers.append("storyboard_no_scenes")
    if int(plan.total_duration_seconds or 0) <= 0:
        global_blockers.append("storyboard_total_duration_zero")

    duplicate_warnings = _similar_prompt_warnings(scenes)
    duplicate_by_scene: dict[int, List[str]] = {}
    for a, b, msg in duplicate_warnings:
        global_warnings.append(msg)
        duplicate_by_scene.setdefault(a, []).append(msg)
        duplicate_by_scene.setdefault(b, []).append(msg)

    scene_results: List[StoryboardReadinessSceneResult] = []
    for scene in scenes:
        blockers: List[str] = []
        warnings: List[str] = []
        prefix = f"scene_{scene.scene_number}"
        if not _norm(scene.visual_intent):
            blockers.append(f"{prefix}_visual_intent_missing")
        if not _norm(scene.voice_text):
            blockers.append(f"{prefix}_voice_text_missing")
        if _asset_requires_image(scene) and not _norm(scene.image_prompt):
            blockers.append(f"{prefix}_image_prompt_missing")
        if _asset_requires_video(scene) and not _norm(scene.video_prompt):
            blockers.append(f"{prefix}_video_prompt_missing")
        duration = int(scene.duration_seconds or 0)
        if duration <= 0:
            blockers.append(f"{prefix}_duration_invalid")
        elif duration < _MIN_SCENE_SECONDS:
            warnings.append(f"{prefix}_duration_too_short")
        elif duration > _MAX_SCENE_SECONDS:
            warnings.append(f"{prefix}_duration_too_long")
        if not scene.provider_hints:
            warnings.append(f"{prefix}_provider_hints_missing")
        warnings.extend(duplicate_by_scene.get(scene.scene_number, []))

        scene_results.append(
            StoryboardReadinessSceneResult(
                scene_number=scene.scene_number,
                chapter_title=scene.chapter_title,
                status=_status(blockers, warnings),
                score=_score_scene(blockers, warnings),
                issues=_dedupe(blockers + warnings),
            )
        )
        global_blockers.extend(blockers)
        global_warnings.extend(warnings)

    if scene_results:
        score = round(sum(s.score for s in scene_results) / len(scene_results))
        if global_blockers:
            score = min(score, 59)
        elif global_warnings:
            score = min(score, 89)
    else:
        score = 0

    overall = _status(global_blockers, global_warnings)
    if overall == "blocked":
        rec = "Storyboard korrigieren: fehlende Pflichtfelder, Prompts oder Dauerwerte ergänzen, dann erneut prüfen."
    elif overall == "warning":
        rec = "Storyboard ist nutzbar, aber Warnungen vor echten Provider-Calls prüfen."
    else:
        rec = "Storyboard ist bereit für den nächsten plan-only oder Provider-Vorbereitungsschritt."

    return StoryboardReadinessResult(
        overall_status=overall,
        score=score,
        blocking_issues=_dedupe(global_blockers),
        warnings=_dedupe(global_warnings),
        scene_results=scene_results,
        production_recommendation=rec,
    )


def evaluate_storyboard_readiness_request(req: StoryboardReadinessRequest) -> StoryboardReadinessResult:
    """Evaluate a provided StoryboardPlan or build one from a supplied build request first."""
    plan = req.storyboard_plan
    if plan is None and req.build_request is not None:
        plan = build_storyboard_plan(req.build_request)
    if plan is None:
        return StoryboardReadinessResult(
            overall_status="blocked",
            score=0,
            blocking_issues=["storyboard_plan_missing"],
            production_recommendation="Storyboard Plan erzeugen und dann Readiness erneut prüfen.",
        )
    return evaluate_storyboard_readiness(plan)
