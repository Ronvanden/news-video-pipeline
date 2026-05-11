"""Storyboard local render execution tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.storyboard import StoryboardLocalRenderPackageResult
from app.storyboard.local_render_execute import execute_storyboard_local_render


def _package(tmp_path: Path) -> StoryboardLocalRenderPackageResult:
    render_dir = tmp_path / "render"
    asset_manifest_path = render_dir / "asset_manifest.json"
    timeline_manifest_path = render_dir / "timeline_manifest.json"
    final_video_path = render_dir / "final_video.mp4"
    return StoryboardLocalRenderPackageResult(
        overall_status="ready",
        run_id="pkg",
        asset_manifest_path=asset_manifest_path.as_posix(),
        timeline_manifest_path=timeline_manifest_path.as_posix(),
        final_video_path=final_video_path.as_posix(),
        asset_manifest={
            "run_id": "pkg",
            "assets": [
                {
                    "scene_number": 1,
                    "image_path": str((tmp_path / "scene_001.png").as_posix()),
                    "duration_seconds": 6,
                }
            ],
        },
        timeline_manifest={
            "run_id": "pkg",
            "asset_manifest_path": asset_manifest_path.as_posix(),
            "assets_directory": render_dir.as_posix(),
            "audio_path": "",
            "total_scenes": 1,
            "estimated_duration_seconds": 6,
            "scene_duration_default_seconds": 6,
            "scenes": [
                {
                    "scene_number": 1,
                    "start_time": 0,
                    "end_time": 6,
                    "duration_seconds": 6,
                    "transition": "cut",
                    "media_type": "image",
                    "image_path": str((tmp_path / "scene_001.png").as_posix()),
                }
            ],
        },
    )


def test_local_render_execute_dry_run_writes_manifests(tmp_path: Path):
    package = _package(tmp_path)
    result = execute_storyboard_local_render(package, output_root=str(tmp_path / "out"), dry_run=True)

    assert result.execution_status == "dry_run"
    assert result.manifest_written is True
    assert Path(result.asset_manifest_path).is_file()
    assert Path(result.timeline_manifest_path).is_file()
    assert result.video_created is False


def test_local_render_execute_runs_renderer_and_returns_output(tmp_path: Path):
    package = _package(tmp_path)

    def fake_render(_timeline_path: Path, *, output_video: Path, **_kw):
        output_video.parent.mkdir(parents=True, exist_ok=True)
        output_video.write_bytes(b"video-bytes")
        manifest = output_video.parent / "render_output_manifest.json"
        manifest.write_text("{}", encoding="utf-8")
        return {
            "video_created": True,
            "render_output_manifest_path": manifest.as_posix(),
            "warnings": [],
            "blocking_reasons": [],
        }

    result = execute_storyboard_local_render(
        package,
        output_root=str(tmp_path / "out"),
        dry_run=False,
        render_fn=fake_render,
    )

    assert result.execution_status == "completed"
    assert result.video_created is True
    assert result.output_exists is True
    assert result.file_size_bytes == len(b"video-bytes")
    assert result.render_output_manifest_path.endswith("render_output_manifest.json")


def test_local_render_execute_fails_for_blocked_package(tmp_path: Path):
    package = _package(tmp_path)
    package.overall_status = "blocked"
    package.blocking_issues = ["storyboard_render_voice_mixdown_required"]

    result = execute_storyboard_local_render(package, dry_run=False)

    assert result.execution_status == "failed"
    assert "storyboard_local_render_package_blocked" in result.blocking_issues


def test_local_render_execute_endpoint_accepts_package(tmp_path: Path):
    client = TestClient(app)
    body = {
        "local_render_package": _package(tmp_path).model_dump(),
        "run_id": "endpoint render execute",
        "output_root": str(tmp_path / "out"),
        "dry_run": True,
        "motion_mode": "basic",
    }
    r = client.post("/story-engine/storyboard-local-render-execute", json=body)

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["execution_version"] == "storyboard_local_render_execution_v1"
    assert data["execution_status"] == "dry_run"
