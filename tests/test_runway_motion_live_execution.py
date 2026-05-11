"""Runway storyboard motion live execution tests (connector mocked)."""

from pathlib import Path

from app.production_connectors.runway_video_connector import RunwayMotionClipResult
from app.storyboard import AssetExecutionResult, AssetGenerationPlan, AssetGenerationTask, AssetTaskExecutionResult
from app.storyboard.runway_motion_live import execute_runway_motion_live_from_asset_plan


def _plan() -> AssetGenerationPlan:
    return AssetGenerationPlan(
        plan_status="planned",
        readiness_status="ready",
        total_tasks=1,
        tasks=[
            AssetGenerationTask(
                task_id="asset_scene_001_video",
                scene_id="scene_001",
                scene_number=1,
                asset_type="video",
                provider_hint="runway",
                prompt="Slow cinematic push-in from the generated keyframe.",
                duration_seconds=5,
                output_path="planned/scene_001/motion.mp4",
            )
        ],
    )


def _image_result(path: Path) -> AssetExecutionResult:
    return _image_result_many([(1, path)])


def _image_result_many(items: list[tuple[int, Path]]) -> AssetExecutionResult:
    return AssetExecutionResult(
        execution_version="openai_image_live_execution_v1",
        execution_status="live_completed",
        dry_run=False,
        task_results=[
            AssetTaskExecutionResult(
                task_id=f"asset_scene_{scene_number:03d}_image",
                asset_type="image",
                provider_hint="openai_image",
                execution_status="live_completed",
                output_path=str(path),
                planned_output_path=str(path),
                output_exists=True,
                scene_id=f"scene_{scene_number:03d}",
                scene_number=scene_number,
                provider="openai_image",
            )
            for scene_number, path in items
        ],
    )


def test_runway_motion_requires_cost_confirmation(tmp_path: Path):
    result = execute_runway_motion_live_from_asset_plan(
        _plan(),
        image_execution_result=_image_result(tmp_path / "image.png"),
        confirm_provider_costs=False,
    )

    assert result.execution_status == "failed"
    assert "confirm_provider_costs_required_for_runway_motion_live" in result.blocking_issues


def test_runway_motion_requires_live_source_image():
    result = execute_runway_motion_live_from_asset_plan(
        _plan(),
        image_execution_result=None,
        confirm_provider_costs=True,
    )

    assert result.execution_status == "failed"
    assert "asset_scene_001_video_execution_failed" in result.blocking_issues
    assert "asset_scene_001_video_runway_source_image_missing" in result.warnings


def test_runway_motion_live_writes_completed_result(tmp_path: Path):
    image = tmp_path / "image.png"
    image.write_bytes(b"png")

    def fake_runner(*, output_path: Path, **_kwargs):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"mp4")
        return RunwayMotionClipResult(ok=True, output_path=output_path, warnings=["runway_mock_ok"])

    result = execute_runway_motion_live_from_asset_plan(
        _plan(),
        image_execution_result=_image_result(image),
        confirm_provider_costs=True,
        run_id="motion test",
        output_root=str(tmp_path / "out"),
        runner=fake_runner,
    )

    assert result.execution_status == "live_completed"
    assert result.estimated_provider_calls == 1
    assert result.task_results[0].execution_status == "live_completed"
    assert result.task_results[0].output_exists is True
    assert result.task_results[0].output_path.endswith("motion.mp4")
    assert "runway_mock_ok" in result.warnings


def test_runway_motion_file_not_found_falls_back_to_image(tmp_path: Path):
    image = tmp_path / "image.png"
    image.write_bytes(b"png")

    def failing_runner(*_args, **_kwargs):
        raise FileNotFoundError("missing motion clip source")

    result = execute_runway_motion_live_from_asset_plan(
        _plan(),
        image_execution_result=_image_result(image),
        confirm_provider_costs=True,
        run_id="motion file missing",
        output_root=str(tmp_path / "out"),
        runner=failing_runner,
    )

    assert result.execution_status == "skipped"
    assert result.blocking_issues == []
    assert "runway_motion_no_clip_fallback_to_image" in result.warnings
    assert result.task_results[0].execution_status == "skipped"


def test_runway_motion_caps_tasks(tmp_path: Path):
    plan = _plan()
    plan.tasks.append(
        AssetGenerationTask(
            task_id="asset_scene_002_video",
            scene_id="scene_002",
            scene_number=2,
            asset_type="video",
            provider_hint="runway",
            prompt="Second motion prompt.",
            output_path="planned/scene_002/motion.mp4",
        )
    )
    image = tmp_path / "image.png"
    image.write_bytes(b"png")

    def fake_runner(*, output_path: Path, **_kwargs):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"mp4")
        return RunwayMotionClipResult(ok=True, output_path=output_path)

    result = execute_runway_motion_live_from_asset_plan(
        plan,
        image_execution_result=_image_result(image),
        confirm_provider_costs=True,
        max_live_motion_tasks=1,
        output_root=str(tmp_path / "out"),
        runner=fake_runner,
    )

    assert len(result.task_results) == 2
    assert result.task_results[1].execution_status == "skipped"
    assert "asset_scene_002_video_skipped_max_live_motion_tasks_1" in result.warnings


def test_runway_motion_live_can_execute_three_capped_clips(tmp_path: Path):
    plan = _plan()
    for scene_number in (2, 3):
        plan.tasks.append(
            AssetGenerationTask(
                task_id=f"asset_scene_{scene_number:03d}_video",
                scene_id=f"scene_{scene_number:03d}",
                scene_number=scene_number,
                asset_type="video",
                provider_hint="runway",
                prompt=f"Motion prompt {scene_number}.",
                output_path=f"planned/scene_{scene_number:03d}/motion.mp4",
            )
        )

    images = []
    for scene_number in (1, 2, 3):
        image = tmp_path / f"scene_{scene_number:03d}.png"
        image.write_bytes(b"png")
        images.append((scene_number, image))

    def fake_runner(*, output_path: Path, **_kwargs):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"mp4")
        return RunwayMotionClipResult(ok=True, output_path=output_path, warnings=["runway_mock_ok"])

    result = execute_runway_motion_live_from_asset_plan(
        plan,
        image_execution_result=_image_result_many(images),
        confirm_provider_costs=True,
        max_live_motion_tasks=3,
        output_root=str(tmp_path / "out"),
        runner=fake_runner,
    )

    assert result.execution_status == "live_completed"
    assert result.estimated_provider_calls == 3
    assert len(result.estimated_outputs) == 3
    assert [task.execution_status for task in result.task_results] == ["live_completed", "live_completed", "live_completed"]
    assert all(task.output_exists is True for task in result.task_results)
