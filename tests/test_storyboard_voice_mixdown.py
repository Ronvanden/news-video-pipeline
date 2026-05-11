"""Storyboard voice mixdown tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.storyboard import (
    StoryboardRenderTimelineResult,
    StoryboardRenderTimelineSegment,
)
from app.storyboard.voice_mixdown import execute_storyboard_voice_mixdown


def _timeline(*segments: StoryboardRenderTimelineSegment) -> StoryboardRenderTimelineResult:
    return StoryboardRenderTimelineResult(
        overall_status="ready",
        total_duration_seconds=sum(s.duration_seconds for s in segments),
        segments=list(segments),
        voice_segments_ready=len([s for s in segments if s.voice_path]),
    )


def _segment(scene_number: int = 1, voice_path: str = "") -> StoryboardRenderTimelineSegment:
    return StoryboardRenderTimelineSegment(
        scene_id=f"scene_{scene_number:03d}",
        scene_number=scene_number,
        title=f"Scene {scene_number}",
        start_seconds=float((scene_number - 1) * 6),
        end_seconds=float(scene_number * 6),
        duration_seconds=6,
        status="ready",
        image_path=f"output/images/scene_{scene_number:03d}.png",
        voice_path=voice_path,
        transition="cut",
        motion_status="not_requested",
        render_mode="image_only",
    )


def test_voice_mixdown_dry_run_plans_output_path(tmp_path: Path):
    one = tmp_path / "scene_001.mp3"
    two = tmp_path / "scene_002.mp3"
    result = execute_storyboard_voice_mixdown(
        _timeline(_segment(1, str(one)), _segment(2, str(two))),
        run_id="mixdown dry",
        output_root=str(tmp_path / "out"),
        dry_run=True,
    )

    assert result.execution_status == "dry_run"
    assert result.output_exists is False
    assert result.mixed_audio_path.endswith("storyboard_voice_mixdown.mp3")
    assert len(result.input_voice_paths) == 2


def test_voice_mixdown_concats_multiple_files(tmp_path: Path):
    one = tmp_path / "scene_001.mp3"
    two = tmp_path / "scene_002.mp3"
    one.write_bytes(b"one")
    two.write_bytes(b"two")

    def fake_run(cmd, check, capture_output, text):
        Path(cmd[-1]).write_bytes(b"joined-audio")
        class _Done:
            returncode = 0
        return _Done()

    result = execute_storyboard_voice_mixdown(
        _timeline(_segment(1, str(one)), _segment(2, str(two))),
        run_id="mixdown live",
        output_root=str(tmp_path / "out"),
        dry_run=False,
        ffmpeg_bin="ffmpeg_mock",
        run_fn=fake_run,
    )

    assert result.execution_status == "completed"
    assert result.output_exists is True
    assert result.file_size_bytes == len(b"joined-audio")
    assert Path(result.mixed_audio_path).is_file()


def test_voice_mixdown_fails_on_missing_input(tmp_path: Path):
    result = execute_storyboard_voice_mixdown(
        _timeline(_segment(1, str(tmp_path / "missing.mp3"))),
        output_root=str(tmp_path / "out"),
        dry_run=False,
    )

    assert result.execution_status == "failed"
    assert "storyboard_voice_mixdown_inputs_missing" in result.blocking_issues


def test_voice_mixdown_single_voice_passthrough(tmp_path: Path):
    one = tmp_path / "scene_001.mp3"
    one.write_bytes(b"solo")
    result = execute_storyboard_voice_mixdown(
        _timeline(_segment(1, str(one))),
        output_root=str(tmp_path / "out"),
        dry_run=False,
    )

    assert result.execution_status == "completed"
    assert result.output_exists is True
    assert "storyboard_voice_mixdown_single_voice_passthrough" in result.warnings


def test_voice_mixdown_endpoint_accepts_render_timeline(tmp_path: Path):
    one = tmp_path / "scene_001.mp3"
    one.write_bytes(b"solo")
    client = TestClient(app)
    body = {
        "render_timeline": _timeline(_segment(1, str(one))).model_dump(),
        "run_id": "endpoint mixdown",
        "output_root": str(tmp_path / "out"),
        "dry_run": True,
    }
    r = client.post("/story-engine/storyboard-voice-mixdown", json=body)

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["mixdown_version"] == "storyboard_voice_mixdown_v1"
    assert data["execution_status"] == "dry_run"
