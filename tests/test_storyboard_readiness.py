"""Storyboard readiness gate tests (plan-only, no provider calls)."""

from fastapi.testclient import TestClient

from app.main import app
from app.storyboard import StoryboardPlan, StoryboardScene, evaluate_storyboard_readiness


def _scene(**kwargs) -> StoryboardScene:
    data = dict(
        scene_number=1,
        source="script_chapter",
        chapter_title="Scene One",
        timeline_role="setup",
        visual_intent="Show the central situation in grounded documentary style.",
        voice_text="Narration explains the situation with enough context.",
        image_prompt="Documentary image prompt with concrete subject and setting.",
        video_prompt="Subtle push-in over the same grounded scene.",
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
        warnings=[],
    )


def test_ready_storyboard_scores_high():
    result = evaluate_storyboard_readiness(_plan(_scene()))
    assert result.overall_status == "ready"
    assert result.score >= 90
    assert result.blocking_issues == []
    assert result.scene_results[0].status == "ready"


def test_blocked_when_required_text_and_prompts_missing():
    result = evaluate_storyboard_readiness(
        _plan(
            _scene(
                visual_intent="",
                voice_text="",
                image_prompt="",
                video_prompt="",
                duration_seconds=0,
            )
        )
    )
    assert result.overall_status == "blocked"
    assert result.score < 60
    assert "scene_1_voice_text_missing" in result.blocking_issues
    assert "scene_1_image_prompt_missing" in result.blocking_issues
    assert "scene_1_video_prompt_missing" in result.blocking_issues
    assert "scene_1_duration_invalid" in result.blocking_issues


def test_warning_when_provider_hints_missing():
    result = evaluate_storyboard_readiness(_plan(_scene(provider_hints=[])))
    assert result.overall_status == "warning"
    assert "scene_1_provider_hints_missing" in result.warnings
    assert 60 <= result.score < 100


def test_score_penalizes_duplicate_prompts_and_short_scene():
    s1 = _scene(scene_number=1, duration_seconds=4)
    s2 = _scene(scene_number=2, chapter_title="Scene Two")
    result = evaluate_storyboard_readiness(_plan(s1, s2))
    assert result.overall_status == "warning"
    assert result.score < 100
    assert any("duplicate_or_near_duplicate_prompt" in w for w in result.warnings)
    assert "scene_1_duration_too_short" in result.warnings


def test_storyboard_readiness_endpoint_accepts_plan():
    client = TestClient(app)
    plan = _plan(_scene())
    r = client.post("/story-engine/storyboard-readiness", json={"storyboard_plan": plan.model_dump()})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["readiness_version"] == "storyboard_readiness_v1"
    assert data["overall_status"] == "ready"
    assert data["scene_results"][0]["score"] >= 90
