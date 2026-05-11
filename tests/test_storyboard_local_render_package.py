"""Storyboard local render package tests."""

from fastapi.testclient import TestClient

from app.main import app
from app.storyboard import (
    StoryboardVoiceMixdownResult,
    StoryboardRenderTimelineResult,
    StoryboardRenderTimelineSegment,
    build_storyboard_local_render_package,
)


def _timeline(*segments: StoryboardRenderTimelineSegment) -> StoryboardRenderTimelineResult:
    return StoryboardRenderTimelineResult(
        overall_status="ready",
        total_duration_seconds=sum(s.duration_seconds for s in segments),
        segments=list(segments),
        image_segments_ready=len(segments),
        voice_segments_ready=len([s for s in segments if s.voice_path]),
    )


def _segment(scene_number: int = 1, **kwargs) -> StoryboardRenderTimelineSegment:
    data = dict(
        scene_id=f"scene_{scene_number:03d}",
        scene_number=scene_number,
        title=f"Scene {scene_number}",
        start_seconds=float((scene_number - 1) * 6),
        end_seconds=float(scene_number * 6),
        duration_seconds=6,
        status="ready",
        image_path=f"output/images/scene_{scene_number:03d}.png",
        voice_path="output/audio/final_voice.mp3",
        transition="cut",
        motion_status="not_requested",
        render_mode="image_only",
    )
    data.update(kwargs)
    return StoryboardRenderTimelineSegment(**data)


def test_local_render_package_builds_renderer_manifest_shapes():
    package = build_storyboard_local_render_package(
        _timeline(_segment()),
        run_id="My Render 01",
        output_root="output",
    )

    assert package.overall_status == "ready"
    assert package.run_id == "My_Render_01"
    assert package.timeline_manifest_path.endswith("timeline_manifest.json")
    assert package.asset_manifest_path.endswith("asset_manifest.json")
    assert package.final_video_path.endswith("final_video.mp4")
    assert package.timeline_manifest["total_scenes"] == 1
    assert package.timeline_manifest["audio_path"].endswith("final_voice.mp3")
    assert package.timeline_manifest["scenes"][0]["media_type"] == "image"
    assert package.asset_manifest["assets"][0]["image_path"].endswith("scene_001.png")


def test_multiple_voice_files_warn_that_mixdown_is_required():
    package = build_storyboard_local_render_package(
        _timeline(
            _segment(1, voice_path="output/audio/scene_001.mp3"),
            _segment(2, voice_path="output/audio/scene_002.mp3"),
        )
    )

    assert package.overall_status == "warning"
    assert "storyboard_render_voice_mixdown_required" in package.warnings
    assert package.timeline_manifest["audio_path"] == ""
    assert "Voice-Dateien" in package.render_recommendation


def test_mixdown_result_is_used_as_global_audio_path():
    package = build_storyboard_local_render_package(
        _timeline(
            _segment(1, voice_path="output/audio/scene_001.mp3"),
            _segment(2, voice_path="output/audio/scene_002.mp3"),
        ),
        voice_mixdown_result=StoryboardVoiceMixdownResult(
            execution_status="completed",
            mixed_audio_path="output/audio/storyboard_voice_mixdown.mp3",
            output_exists=True,
        ),
    )

    assert package.timeline_manifest["audio_path"].endswith("storyboard_voice_mixdown.mp3")
    assert "storyboard_render_voice_mixdown_required" not in package.warnings


def test_blocked_render_timeline_blocks_package():
    timeline = StoryboardRenderTimelineResult(
        overall_status="blocked",
        total_duration_seconds=0,
        segments=[],
        blocking_issues=["scene_1_image_missing"],
    )
    package = build_storyboard_local_render_package(timeline)

    assert package.overall_status == "blocked"
    assert "render_timeline_blocked" in package.blocking_issues
    assert "render_timeline_has_no_segments" in package.blocking_issues


def test_endpoint_accepts_render_timeline():
    client = TestClient(app)
    body = {
        "render_timeline": _timeline(_segment()).model_dump(),
        "voice_mixdown_result": StoryboardVoiceMixdownResult(
            execution_status="completed",
            mixed_audio_path="output/audio/storyboard_voice_mixdown.mp3",
            output_exists=True,
        ).model_dump(),
        "run_id": "endpoint render",
        "output_root": "output",
    }
    r = client.post("/story-engine/storyboard-local-render-package", json=body)

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["package_version"] == "storyboard_local_render_package_v1"
    assert data["run_id"] == "endpoint_render"
    assert data["timeline_manifest"]["total_scenes"] == 1
