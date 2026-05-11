"""Plan-only asset task planning from a readiness-checked storyboard."""

from __future__ import annotations

from typing import Iterable, List, Optional

from app.storyboard.readiness import evaluate_storyboard_readiness
from app.storyboard.schema import (
    AssetGenerationPlan,
    AssetGenerationPlanRequest,
    AssetGenerationTask,
    StoryboardPlan,
    StoryboardReadinessResult,
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


def _task_id(scene: StoryboardScene, kind: str) -> str:
    return f"asset_scene_{int(scene.scene_number):03d}_{kind}"


def _output_path(scene: Optional[StoryboardScene], kind: str, ext: str) -> str:
    if scene is None:
        return f"planned_assets/global/{kind}.{ext}"
    return f"planned_assets/{_scene_id(scene)}/{kind}.{ext}"


def _provider_hint(scene: StoryboardScene, kind: str) -> str:
    hints = [str(x).strip().lower() for x in (scene.provider_hints or []) if str(x).strip()]
    if kind == "image":
        if "openai" in hints or "openai_image" in hints:
            return "openai_image"
        return "image"
    if kind == "video":
        if "runway" in hints:
            return "runway"
        if "kling" in hints:
            return "kling"
        return "video"
    if kind == "voice":
        if "elevenlabs" in hints:
            return "elevenlabs"
        return "voice"
    return kind


def _requires_image(scene: StoryboardScene) -> bool:
    return scene.asset_type in ("hook_card", "image_keyframe", "image_to_video_candidate", "outro_card")


def _requires_video(scene: StoryboardScene) -> bool:
    return scene.asset_type in ("image_to_video_candidate", "b_roll_sequence")


def _task(
    *,
    task_id: str,
    scene: Optional[StoryboardScene],
    asset_type: str,
    provider_hint: str,
    prompt: str,
    output_path: str,
    duration_seconds: Optional[int] = None,
    dependencies: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
) -> AssetGenerationTask:
    return AssetGenerationTask(
        task_id=task_id,
        scene_id=_scene_id(scene) if scene is not None else "",
        scene_number=scene.scene_number if scene is not None else None,
        asset_type=asset_type,  # type: ignore[arg-type]
        provider_hint=provider_hint,
        prompt=prompt,
        duration_seconds=duration_seconds,
        output_path=output_path,
        dependencies=list(dependencies or []),
        warnings=list(warnings or []),
    )


def build_asset_generation_plan(
    storyboard_plan: StoryboardPlan,
    readiness_result: Optional[StoryboardReadinessResult] = None,
) -> AssetGenerationPlan:
    """Create deterministic asset tasks without calling providers or writing files."""
    readiness = readiness_result or evaluate_storyboard_readiness(storyboard_plan)
    if readiness.overall_status == "blocked":
        return AssetGenerationPlan(
            plan_status="blocked",
            storyboard_version=storyboard_plan.storyboard_version,
            readiness_status=readiness.overall_status,
            tasks=[],
            total_tasks=0,
            warnings=_dedupe(readiness.warnings + ["asset_plan_blocked_by_storyboard_readiness"]),
            blocking_issues=_dedupe(readiness.blocking_issues),
        )

    tasks: List[AssetGenerationTask] = []
    scenes = list(storyboard_plan.scenes or [])
    for scene in scenes:
        scene_warnings: List[str] = []
        if not scene.provider_hints:
            scene_warnings.append("provider_hints_missing")

        image_task_id = _task_id(scene, "image")
        if _requires_image(scene):
            tasks.append(
                _task(
                    task_id=image_task_id,
                    scene=scene,
                    asset_type="image",
                    provider_hint=_provider_hint(scene, "image"),
                    prompt=scene.image_prompt or scene.visual_intent,
                    output_path=_output_path(scene, "image", "png"),
                    warnings=scene_warnings,
                )
            )

        if _requires_video(scene):
            deps = [image_task_id] if _requires_image(scene) else []
            tasks.append(
                _task(
                    task_id=_task_id(scene, "video"),
                    scene=scene,
                    asset_type="video",
                    provider_hint=_provider_hint(scene, "video"),
                    prompt=scene.video_prompt or scene.image_prompt or scene.visual_intent,
                    duration_seconds=scene.duration_seconds,
                    output_path=_output_path(scene, "video", "mp4"),
                    dependencies=deps,
                    warnings=scene_warnings,
                )
            )

        if _norm(scene.voice_text):
            tasks.append(
                _task(
                    task_id=_task_id(scene, "voice"),
                    scene=scene,
                    asset_type="voice",
                    provider_hint=_provider_hint(scene, "voice"),
                    prompt=scene.voice_text,
                    duration_seconds=scene.duration_seconds,
                    output_path=_output_path(scene, "voice", "wav"),
                    warnings=scene_warnings,
                )
            )

        tasks.append(
            _task(
                task_id=_task_id(scene, "subtitle"),
                scene=scene,
                asset_type="subtitle",
                provider_hint="subtitle",
                prompt=scene.voice_text,
                duration_seconds=scene.duration_seconds,
                output_path=_output_path(scene, "subtitle", "srt"),
                dependencies=[_task_id(scene, "voice")] if _norm(scene.voice_text) else [],
                warnings=scene_warnings,
            )
        )
        tasks.append(
            _task(
                task_id=_task_id(scene, "render_hint"),
                scene=scene,
                asset_type="render_hint",
                provider_hint="render_timeline",
                prompt=f"{scene.transition}; {scene.asset_type}; {scene.visual_intent}",
                duration_seconds=scene.duration_seconds,
                output_path=_output_path(scene, "render_hint", "json"),
                dependencies=[t.task_id for t in tasks if t.scene_number == scene.scene_number],
                warnings=scene_warnings,
            )
        )

    if scenes:
        first = scenes[0]
        deps = [_task_id(first, "image")] if _requires_image(first) else []
        tasks.append(
            _task(
                task_id="asset_global_thumbnail",
                scene=first,
                asset_type="thumbnail",
                provider_hint="image",
                prompt=first.image_prompt or first.visual_intent,
                output_path=_output_path(None, "thumbnail", "png"),
                dependencies=deps,
            )
        )

    return AssetGenerationPlan(
        plan_status="planned",
        storyboard_version=storyboard_plan.storyboard_version,
        readiness_status=readiness.overall_status,
        total_tasks=len(tasks),
        tasks=tasks,
        warnings=_dedupe(readiness.warnings),
        blocking_issues=[],
    )


def build_asset_generation_plan_request(req: AssetGenerationPlanRequest) -> AssetGenerationPlan:
    return build_asset_generation_plan(req.storyboard_plan, req.readiness_result)
