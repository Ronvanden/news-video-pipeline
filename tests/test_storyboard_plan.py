"""Storyboard orchestration layer tests (plan-only, no provider calls)."""

from fastapi.testclient import TestClient

from app.main import app
from app.prompt_engine.schema import ChapterOutlineItem, ProductionPromptPlan
from app.storyboard import StoryboardBuildRequest, build_storyboard_plan, build_storyboard_plan_from_prompt_plan


def _plan(**kwargs) -> ProductionPromptPlan:
    defaults = dict(
        template_type="documentary",
        tone="calm",
        hook="A quiet opening line sets up the investigation.",
        chapter_outline=[
            ChapterOutlineItem(title="Setup", summary="The first chapter explains what changed and why it matters."),
            ChapterOutlineItem(title="Turning Point", summary="The second chapter shows the consequence and the stakes."),
        ],
        scene_prompts=[
            "Documentary wide shot of a city street at dawn, grounded realism, no readable text.",
            "Close documentary detail of hands sorting notes on a table, natural light, no readable text.",
        ],
        voice_style="measured documentary narration",
        thumbnail_angle="one clear visual question",
        warnings=[],
        video_template="documentary",
    )
    defaults.update(kwargs)
    return ProductionPromptPlan(**defaults)


def test_storyboard_from_prompt_plan_maps_scene_contract():
    out = build_storyboard_plan_from_prompt_plan(_plan())
    assert out.status == "ready"
    assert out.source_type == "prompt_plan"
    assert out.dashboard_ready is True
    assert len(out.scenes) == 3
    assert out.scenes[0].source == "hook"
    assert out.scenes[1].source == "prompt_plan"
    assert out.scenes[1].asset_type in ("image_keyframe", "image_to_video_candidate")
    assert out.scenes[1].voice_text
    assert out.scenes[1].image_prompt.startswith("Documentary")
    assert "Motion direction:" in out.scenes[1].video_prompt
    assert out.total_duration_seconds == sum(s.duration_seconds for s in out.scenes)


def test_storyboard_from_script_chapters_reuses_scene_prompt_builder():
    req = StoryboardBuildRequest(
        hook="A concise hook.",
        video_template="documentary",
        chapters=[
            {"title": "Chapter One", "content": "Enough narration text for a grounded opening scene. " * 8},
            {"title": "Chapter Two", "content": "More narration text for a second scene with continuity. " * 8},
        ],
    )
    out = build_storyboard_plan(req)
    assert out.source_type == "script_chapters"
    assert len(out.scenes) == 3
    assert out.scenes[1].source == "script_chapter"
    assert out.scenes[1].image_prompt
    assert out.scenes[1].provider_hints == ["image", "video", "voice", "render_timeline"]
    assert not any("provider_call" in w for w in out.warnings)


def test_storyboard_endpoint_accepts_direct_chapters():
    client = TestClient(app)
    r = client.post(
        "/story-engine/storyboard-plan",
        json={
            "hook": "Opening beat.",
            "video_template": "documentary",
            "chapters": [
                {"title": "A", "content": "Narration text for A. " * 10},
                {"title": "B", "content": "Narration text for B. " * 10},
            ],
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["storyboard_version"] == "ba32_storyboard_v1"
    assert data["source_type"] == "script_chapters"
    assert len(data["scenes"]) == 3
    assert {"visual_intent", "voice_text", "image_prompt", "video_prompt", "asset_type"} <= set(
        data["scenes"][1].keys()
    )
