"""Asset generation plan tests (plan-only, no provider calls)."""

from fastapi.testclient import TestClient

from app.main import app
from app.storyboard import StoryboardPlan, StoryboardReadinessResult, StoryboardScene, build_asset_generation_plan


def _scene(**kwargs) -> StoryboardScene:
    data = dict(
        scene_number=1,
        source="script_chapter",
        chapter_title="Scene One",
        timeline_role="setup",
        visual_intent="Grounded documentary scene intent.",
        voice_text="Narration for the scene.",
        image_prompt="Image prompt for the scene.",
        video_prompt="Video prompt for the scene.",
        duration_seconds=24,
        transition="dissolve",
        asset_type="image_to_video_candidate",
        provider_hints=["image", "video", "voice", "render_timeline"],
    )
    data.update(kwargs)
    return StoryboardScene(**data)


def _plan(*scenes: StoryboardScene) -> StoryboardPlan:
    return StoryboardPlan(
        status="ready",
        source_type="script_chapters",
        video_template="documentary",
        total_duration_seconds=sum(s.duration_seconds for s in scenes),
        scenes=list(scenes),
    )


def test_ready_storyboard_creates_image_video_voice_tasks():
    plan = build_asset_generation_plan(_plan(_scene()))
    ids = {t.task_id for t in plan.tasks}
    assert plan.plan_status == "planned"
    assert "asset_scene_001_image" in ids
    assert "asset_scene_001_video" in ids
    assert "asset_scene_001_voice" in ids
    assert "asset_scene_001_render_hint" in ids


def test_hybrid_scene_creates_image_and_video_with_dependency():
    plan = build_asset_generation_plan(
        _plan(
            _scene(
                asset_type="image_to_video_candidate",
                video_prompt="Animate the provided image as a realistic short documentary clip. Camera movement: slow controlled push-in.",
            )
        )
    )
    video = next(t for t in plan.tasks if t.task_id == "asset_scene_001_video")
    assert "asset_scene_001_image" in video.dependencies
    assert video.output_path == "planned_assets/scene_001/video.mp4"
    assert video.provider_hint == "video"
    assert video.prompt.startswith("Animate the provided image")


def test_blocked_readiness_blocks_normal_asset_plan():
    blocked = StoryboardReadinessResult(
        overall_status="blocked",
        score=0,
        blocking_issues=["scene_1_voice_text_missing"],
        production_recommendation="Fix storyboard.",
    )
    plan = build_asset_generation_plan(_plan(_scene()), blocked)
    assert plan.plan_status == "blocked"
    assert plan.tasks == []
    assert "scene_1_voice_text_missing" in plan.blocking_issues
    assert "asset_plan_blocked_by_storyboard_readiness" in plan.warnings


def test_task_ids_and_output_paths_are_deterministic():
    plan = build_asset_generation_plan(_plan(_scene(scene_number=7)))
    image = next(t for t in plan.tasks if t.asset_type == "image")
    voice = next(t for t in plan.tasks if t.asset_type == "voice")
    thumb = next(t for t in plan.tasks if t.asset_type == "thumbnail")
    assert image.task_id == "asset_scene_007_image"
    assert image.output_path == "planned_assets/scene_007/image.png"
    assert voice.output_path == "planned_assets/scene_007/voice.wav"
    assert thumb.task_id == "asset_global_thumbnail"
    assert thumb.output_path == "planned_assets/global/thumbnail.png"


def test_endpoint_returns_plan_without_provider_execution():
    client = TestClient(app)
    storyboard = _plan(_scene())
    r = client.post("/story-engine/asset-generation-plan", json={"storyboard_plan": storyboard.model_dump()})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["plan_version"] == "asset_generation_plan_v1"
    assert data["plan_status"] == "planned"
    assert data["total_tasks"] == len(data["tasks"])
    assert not any("provider_call" in str(t).lower() for t in data["tasks"])
