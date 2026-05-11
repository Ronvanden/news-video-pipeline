"""OpenAI Image live execution path tests (connector mocked, no real provider calls)."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.storyboard import AssetGenerationPlan, AssetGenerationTask
from app.storyboard.openai_image_live import execute_openai_image_live_from_asset_plan


def _task(**kwargs) -> AssetGenerationTask:
    data = dict(
        task_id="asset_scene_001_image",
        scene_id="scene_001",
        scene_number=1,
        asset_type="image",
        provider_hint="image",
        prompt="A grounded documentary image prompt.",
        output_path="planned_assets/scene_001/image.png",
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


def test_cost_confirmation_required_blocks_without_provider_call():
    calls = []

    def fake_runner(*args, **kwargs):
        calls.append((args, kwargs))
        return True, [], {}

    result = execute_openai_image_live_from_asset_plan(
        _plan(_task()),
        confirm_provider_costs=False,
        runner=fake_runner,
    )
    assert result.execution_status == "failed"
    assert result.blocking_issues == ["confirm_provider_costs_required_for_openai_image_live"]
    assert calls == []


def test_executes_one_image_task_with_openai_options():
    seen = {}

    def fake_runner(prompt, dest_png: Path, *, size, model, timeout_seconds):
        seen["prompt"] = prompt
        seen["dest"] = str(dest_png)
        seen["size"] = size
        seen["model"] = model
        seen["timeout"] = timeout_seconds
        return True, ["openai_image_provider:openai_image"], {"bytes_written": 123}

    result = execute_openai_image_live_from_asset_plan(
        _plan(_task()),
        confirm_provider_costs=True,
        run_id="unit_test_run",
        output_root="output",
        openai_image_model="gpt-image-2",
        openai_image_size="1024x1024",
        runner=fake_runner,
    )
    assert result.execution_status == "live_completed"
    assert result.task_results[0].execution_status == "live_completed"
    assert result.estimated_provider_calls == 1
    assert seen["model"] == "gpt-image-2"
    assert seen["size"] == "1024x1024"
    assert seen["dest"].endswith("output\\storyboard_runs\\unit_test_run\\scene_001\\image.png") or seen[
        "dest"
    ].endswith("output/storyboard_runs/unit_test_run/scene_001/image.png")
    assert result.estimated_outputs


def test_limits_to_one_live_image_task_and_skips_rest():
    result = execute_openai_image_live_from_asset_plan(
        _plan(_task(scene_number=1, scene_id="scene_001"), _task(task_id="asset_scene_002_image", scene_number=2, scene_id="scene_002")),
        confirm_provider_costs=True,
        runner=lambda *args, **kwargs: (True, [], {}),
    )
    statuses = {r.task_id: r.execution_status for r in result.task_results}
    assert statuses["asset_scene_001_image"] == "live_completed"
    assert statuses["asset_scene_002_image"] == "skipped"
    assert result.estimated_provider_calls == 1


def test_blocked_asset_plan_fails_without_provider_call():
    result = execute_openai_image_live_from_asset_plan(
        _plan(plan_status="blocked", total_tasks=0, tasks=[], blocking_issues=["asset_plan_blocked"]),
        confirm_provider_costs=True,
        runner=lambda *args, **kwargs: (True, [], {}),
    )
    assert result.execution_status == "failed"
    assert "openai_image_live_blocked_by_asset_plan" in result.blocking_issues
    assert result.estimated_provider_calls == 0


def test_endpoint_missing_cost_confirmation_no_live_call():
    client = TestClient(app)
    r = client.post(
        "/story-engine/openai-image-live-execution",
        json={"asset_generation_plan": _plan(_task()).model_dump(), "confirm_provider_costs": False},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["execution_version"] == "openai_image_live_execution_v1"
    assert data["execution_status"] == "failed"
    assert data["blocking_issues"] == ["confirm_provider_costs_required_for_openai_image_live"]
