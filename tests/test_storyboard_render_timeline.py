"""Storyboard render timeline handoff tests."""

from fastapi.testclient import TestClient

from app.main import app
from app.storyboard import (
    AssetExecutionResult,
    AssetGenerationPlan,
    AssetGenerationTask,
    AssetTaskExecutionResult,
    StoryboardPlan,
    StoryboardScene,
    build_storyboard_render_timeline,
)


def _scene(**kwargs) -> StoryboardScene:
    data = dict(
        scene_number=1,
        chapter_title="Scene One",
        timeline_role="setup",
        visual_intent="A strong documentary visual.",
        voice_text="Narration text.",
        image_prompt="Image prompt.",
        video_prompt="Video prompt.",
        duration_seconds=8,
        transition="cut",
        asset_type="image_keyframe",
        provider_hints=["image", "voice", "render_timeline"],
    )
    data.update(kwargs)
    return StoryboardScene(**data)


def _plan(*scenes: StoryboardScene) -> StoryboardPlan:
    return StoryboardPlan(status="ready", total_duration_seconds=sum(s.duration_seconds for s in scenes), scenes=list(scenes))


def _asset_task(scene_number: int, kind: str, path: str) -> AssetGenerationTask:
    return AssetGenerationTask(
        task_id=f"asset_scene_{scene_number:03d}_{kind}",
        scene_id=f"scene_{scene_number:03d}",
        scene_number=scene_number,
        asset_type=kind,  # type: ignore[arg-type]
        provider_hint=kind,
        prompt=f"{kind} prompt",
        output_path=path,
    )


def _exec_result(scene_number: int, kind: str, path: str, exists: bool = True) -> AssetExecutionResult:
    return AssetExecutionResult(
        execution_version=f"{kind}_live",
        execution_status="live_completed",
        dry_run=False,
        task_results=[
            AssetTaskExecutionResult(
                task_id=f"asset_scene_{scene_number:03d}_{kind}",
                asset_type=kind,  # type: ignore[arg-type]
                execution_status="live_completed",
                output_path=path,
                planned_output_path=path,
                output_exists=exists,
                scene_id=f"scene_{scene_number:03d}",
                scene_number=scene_number,
                provider=kind,
            )
        ],
        estimated_outputs=[path] if exists else [],
    )


def test_render_timeline_uses_live_image_and_voice_paths():
    plan = _plan(_scene())
    out = build_storyboard_render_timeline(
        plan,
        image_execution_result=_exec_result(1, "image", "output/scene_001/image.png"),
        voice_execution_result=_exec_result(1, "voice", "output/scene_001/voice.mp3"),
    )
    assert out.overall_status == "ready"
    assert out.total_duration_seconds == 8
    assert out.image_segments_ready == 1
    assert out.voice_segments_ready == 1
    assert out.segments[0].render_mode == "image_only"
    assert out.segments[0].image_path.endswith("image.png")
    assert out.segments[0].voice_path.endswith("voice.mp3")


def test_motion_requested_without_clip_is_image_fallback_not_placeholder():
    scene = _scene(asset_type="image_to_video_candidate", provider_hints=["image", "video", "voice", "render_timeline"])
    out = build_storyboard_render_timeline(
        _plan(scene),
        image_execution_result=_exec_result(1, "image", "output/scene_001/image.png"),
        voice_execution_result=_exec_result(1, "voice", "output/scene_001/voice.mp3"),
    )
    assert out.overall_status == "warning"
    assert out.motion_segments_skipped == 1
    assert out.segments[0].status == "image_fallback"
    assert out.segments[0].motion_status == "skipped"
    assert "motion_requested_but_no_clip_fallback_to_image" in out.warnings


def test_missing_image_blocks_render_timeline():
    out = build_storyboard_render_timeline(_plan(_scene()))
    assert out.overall_status == "blocked"
    assert "scene_1_image_missing" in out.blocking_issues


def test_planned_paths_are_warning_but_timeline_shape_exists():
    scene = _scene()
    asset_plan = AssetGenerationPlan(
        plan_status="planned",
        readiness_status="ready",
        total_tasks=2,
        tasks=[
            _asset_task(1, "image", "planned_assets/scene_001/image.png"),
            _asset_task(1, "voice", "planned_assets/scene_001/voice.wav"),
        ],
    )
    out = build_storyboard_render_timeline(_plan(scene), asset_generation_plan=asset_plan)
    assert out.overall_status == "warning"
    assert out.segments[0].image_path.endswith("image.png")
    assert "scene_1_image_planned_not_live" in out.warnings


def test_endpoint_accepts_storyboard_plan():
    client = TestClient(app)
    r = client.post("/story-engine/storyboard-render-timeline", json={"storyboard_plan": _plan(_scene()).model_dump()})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["timeline_version"] == "storyboard_render_timeline_v1"
    assert data["overall_status"] == "blocked"
