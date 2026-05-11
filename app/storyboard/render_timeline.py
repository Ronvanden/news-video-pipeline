"""Storyboard render timeline handoff builder."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

from app.storyboard.schema import (
    AssetExecutionResult,
    AssetGenerationPlan,
    AssetGenerationTask,
    AssetTaskExecutionResult,
    StoryboardPlan,
    StoryboardRenderTimelineRequest,
    StoryboardRenderTimelineResult,
    StoryboardRenderTimelineSegment,
    StoryboardScene,
)


def _norm(s: str) -> str:
    return " ".join(str(s or "").split()).strip()


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


def _scene_id(scene: StoryboardScene) -> str:
    return f"scene_{int(scene.scene_number):03d}"


def _requires_motion(scene: StoryboardScene) -> bool:
    return scene.asset_type in ("image_to_video_candidate", "b_roll_sequence")


def _tasks_by_scene(plan: Optional[AssetGenerationPlan]) -> Dict[Tuple[int, str], AssetGenerationTask]:
    out: Dict[Tuple[int, str], AssetGenerationTask] = {}
    if not plan:
        return out
    for task in plan.tasks or []:
        if task.scene_number is None:
            continue
        out[(int(task.scene_number), str(task.asset_type))] = task
    return out


def _results_by_scene(*results: Optional[AssetExecutionResult]) -> Dict[Tuple[int, str], AssetTaskExecutionResult]:
    out: Dict[Tuple[int, str], AssetTaskExecutionResult] = {}
    for result in results:
        if not result:
            continue
        for task in result.task_results or []:
            if task.scene_number is None:
                continue
            key = (int(task.scene_number), str(task.asset_type))
            current = out.get(key)
            if current is None or (task.output_exists and not current.output_exists):
                out[key] = task
    return out


def _live_path(result: Optional[AssetTaskExecutionResult]) -> str:
    if not result:
        return ""
    if result.output_exists and result.execution_status == "live_completed":
        return _norm(result.output_path or result.planned_output_path)
    return ""


def _planned_path(task: Optional[AssetGenerationTask]) -> str:
    return _norm(task.output_path if task else "")


def build_storyboard_render_timeline(
    storyboard_plan: StoryboardPlan,
    *,
    asset_generation_plan: Optional[AssetGenerationPlan] = None,
    image_execution_result: Optional[AssetExecutionResult] = None,
    voice_execution_result: Optional[AssetExecutionResult] = None,
    motion_execution_result: Optional[AssetExecutionResult] = None,
) -> StoryboardRenderTimelineResult:
    """Build a deterministic render timeline handoff without rendering or writing files."""
    warnings: List[str] = []
    blockers: List[str] = []
    scenes = list(storyboard_plan.scenes or [])
    if not scenes:
        return StoryboardRenderTimelineResult(
            overall_status="blocked",
            warnings=["storyboard_render_timeline_no_scenes"],
            blocking_issues=["storyboard_scenes_required"],
            render_recommendation="Storyboard zuerst erzeugen.",
        )

    tasks = _tasks_by_scene(asset_generation_plan)
    results = _results_by_scene(image_execution_result, voice_execution_result, motion_execution_result)
    segments: List[StoryboardRenderTimelineSegment] = []
    cursor = 0.0
    image_ready = 0
    voice_ready = 0
    video_ready = 0
    motion_skipped = 0

    for scene in sorted(scenes, key=lambda s: int(s.scene_number)):
        sn = int(scene.scene_number)
        dur = float(scene.duration_seconds or 0)
        if dur <= 0:
            dur = 6.0
            warnings.append(f"scene_{sn}_duration_defaulted_for_render_timeline")

        image_res = results.get((sn, "image"))
        video_res = results.get((sn, "video"))
        voice_res = results.get((sn, "voice"))
        image_task = tasks.get((sn, "image"))
        video_task = tasks.get((sn, "video"))
        voice_task = tasks.get((sn, "voice"))

        image_path = _live_path(image_res) or _planned_path(image_task)
        video_path = _live_path(video_res) or _planned_path(video_task)
        voice_path = _live_path(voice_res) or _planned_path(voice_task)
        tw: List[str] = []
        tb: List[str] = []

        has_live_image = bool(_live_path(image_res))
        has_live_video = bool(_live_path(video_res))
        has_live_voice = bool(_live_path(voice_res))
        if has_live_image:
            image_ready += 1
        if has_live_video:
            video_ready += 1
        if has_live_voice:
            voice_ready += 1

        motion_required = _requires_motion(scene)
        if has_live_video:
            status = "ready"
            motion_status = "ready"
            render_mode = "video_clip"
        elif image_path:
            render_mode = "image_only"
            if motion_required:
                status = "image_fallback"
                motion_status = "skipped"
                motion_skipped += 1
                tw.append("motion_requested_but_no_clip_fallback_to_image")
            else:
                status = "ready"
                motion_status = "not_requested"
        else:
            status = "blocked"
            motion_status = "missing" if motion_required else "not_requested"
            render_mode = "missing_media"
            tb.append(f"scene_{sn}_image_missing")
            blockers.append(f"scene_{sn}_image_missing")

        if scene.voice_text and not voice_path:
            tw.append(f"scene_{sn}_voice_missing_render_may_be_silent")
        elif voice_path and not has_live_voice:
            tw.append(f"scene_{sn}_voice_planned_not_live")
        if image_path and not has_live_image:
            tw.append(f"scene_{sn}_image_planned_not_live")

        segments.append(
            StoryboardRenderTimelineSegment(
                scene_id=_scene_id(scene),
                scene_number=sn,
                title=scene.chapter_title,
                start_seconds=round(cursor, 3),
                end_seconds=round(cursor + dur, 3),
                duration_seconds=round(dur, 3),
                status=status,  # type: ignore[arg-type]
                image_path=image_path,
                video_path=video_path if has_live_video else "",
                voice_path=voice_path,
                transition=scene.transition,
                motion_status=motion_status,  # type: ignore[arg-type]
                render_mode=render_mode,  # type: ignore[arg-type]
                warnings=_dedupe(tw),
                blocking_issues=_dedupe(tb),
            )
        )
        warnings.extend(tw)
        cursor += dur

    overall = "blocked" if blockers else ("warning" if warnings or motion_skipped else "ready")
    recommendation = (
        "Fehlende Bildassets erzeugen, bevor gerendert wird."
        if blockers
        else (
            "Timeline ist renderbar; Motion-Clips ohne Pfad werden als Image-only Fallback behandelt."
            if motion_skipped
            else "Timeline ist bereit fuer den lokalen Render-Handoff."
        )
    )
    return StoryboardRenderTimelineResult(
        overall_status=overall,  # type: ignore[arg-type]
        total_duration_seconds=round(cursor, 3),
        segments=segments,
        image_segments_ready=image_ready,
        voice_segments_ready=voice_ready,
        video_segments_ready=video_ready,
        motion_segments_skipped=motion_skipped,
        warnings=_dedupe(warnings),
        blocking_issues=_dedupe(blockers),
        render_recommendation=recommendation,
    )


def build_storyboard_render_timeline_request(req: StoryboardRenderTimelineRequest) -> StoryboardRenderTimelineResult:
    return build_storyboard_render_timeline(
        req.storyboard_plan,
        asset_generation_plan=req.asset_generation_plan,
        image_execution_result=req.image_execution_result,
        voice_execution_result=req.voice_execution_result,
        motion_execution_result=req.motion_execution_result,
    )
