"""Asset execution stub tests (no provider calls, no writes)."""

from fastapi.testclient import TestClient

from app.main import app
from app.storyboard import AssetGenerationPlan, AssetGenerationTask, execute_asset_generation_plan_stub


def _task(**kwargs) -> AssetGenerationTask:
    data = dict(
        task_id="asset_scene_001_image",
        scene_id="scene_001",
        scene_number=1,
        asset_type="image",
        provider_hint="image",
        prompt="Prompt for an image asset.",
        output_path="planned_assets/scene_001/image.png",
        dependencies=[],
        warnings=[],
    )
    data.update(kwargs)
    return AssetGenerationTask(**data)


def _plan(*tasks: AssetGenerationTask, **kwargs) -> AssetGenerationPlan:
    data = dict(
        plan_status="planned",
        storyboard_version="ba32_storyboard_v1",
        readiness_status="ready",
        total_tasks=len(tasks),
        tasks=list(tasks),
        warnings=[],
        blocking_issues=[],
    )
    data.update(kwargs)
    return AssetGenerationPlan(**data)


def test_ready_asset_plan_creates_dry_run_results():
    result = execute_asset_generation_plan_stub(_plan(_task()), dry_run=True)
    assert result.execution_status == "dry_run"
    assert result.task_results[0].execution_status == "dry_run"
    assert result.estimated_provider_calls == 1
    assert result.estimated_outputs == ["planned_assets/scene_001/image.png"]


def test_ready_asset_plan_can_complete_stub_without_provider_execution():
    result = execute_asset_generation_plan_stub(_plan(_task(asset_type="voice", provider_hint="voice")), dry_run=False)
    assert result.execution_status == "completed_stub"
    assert result.task_results[0].execution_status == "completed_stub"
    assert not any("provider_call" in w for w in result.warnings)


def test_blocked_asset_plan_fails_cleanly():
    result = execute_asset_generation_plan_stub(
        _plan(plan_status="blocked", total_tasks=0, tasks=[], blocking_issues=["asset_plan_blocked"])
    )
    assert result.execution_status == "failed"
    assert result.task_results == []
    assert "asset_execution_blocked_by_asset_plan" in result.blocking_issues
    assert result.estimated_provider_calls == 0


def test_missing_prompt_marks_provider_task_failed():
    result = execute_asset_generation_plan_stub(_plan(_task(prompt="")))
    assert result.execution_status == "failed"
    assert result.task_results[0].execution_status == "failed"
    assert "asset_scene_001_image_prompt_missing" in result.warnings
    assert "asset_scene_001_image_execution_failed" in result.blocking_issues


def test_estimated_provider_calls_are_plausible():
    result = execute_asset_generation_plan_stub(
        _plan(
            _task(task_id="asset_scene_001_image", asset_type="image", provider_hint="image"),
            _task(task_id="asset_scene_001_video", asset_type="video", provider_hint="video"),
            _task(task_id="asset_scene_001_render_hint", asset_type="render_hint", provider_hint="render_timeline"),
        )
    )
    assert result.estimated_provider_calls == 2


def test_endpoint_returns_stub_result_without_provider_execution():
    client = TestClient(app)
    plan = _plan(_task())
    r = client.post(
        "/story-engine/asset-execution-stub",
        json={"asset_generation_plan": plan.model_dump(), "dry_run": True},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["execution_version"] == "asset_execution_stub_v1"
    assert data["execution_status"] == "dry_run"
    assert data["estimated_provider_calls"] == 1
    assert not any("provider_call" in str(x).lower() for x in data["task_results"])
