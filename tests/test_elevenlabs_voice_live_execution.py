"""ElevenLabs storyboard voice live execution tests (connector mocked)."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.storyboard import AssetGenerationPlan, AssetGenerationTask
from app.storyboard.elevenlabs_voice_live import execute_elevenlabs_voice_live_from_asset_plan


def _task(**kwargs) -> AssetGenerationTask:
    data = dict(
        task_id="asset_scene_001_voice",
        scene_id="scene_001",
        scene_number=1,
        asset_type="voice",
        provider_hint="voice",
        prompt="A concise narration line.",
        output_path="planned_assets/scene_001/voice.mp3",
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


def test_cost_confirmation_required_blocks_without_voice_call():
    calls = []

    def fake_runner(*args, **kwargs):
        calls.append((args, kwargs))
        return True, [], {}

    result = execute_elevenlabs_voice_live_from_asset_plan(
        _plan(_task()),
        confirm_provider_costs=False,
        elevenlabs_voice_id="voice_123",
        runner=fake_runner,
    )
    assert result.execution_status == "failed"
    assert result.blocking_issues == ["confirm_provider_costs_required_for_elevenlabs_voice_live"]
    assert calls == []


def test_voice_id_required_before_provider_call():
    calls = []

    def fake_runner(*args, **kwargs):
        calls.append((args, kwargs))
        return True, [], {}

    result = execute_elevenlabs_voice_live_from_asset_plan(
        _plan(_task()),
        confirm_provider_costs=True,
        elevenlabs_voice_id="",
        runner=fake_runner,
    )
    assert result.execution_status == "failed"
    assert result.blocking_issues == ["elevenlabs_voice_id_required"]
    assert calls == []


def test_executes_up_to_ten_voice_tasks(tmp_path):
    calls = []

    def fake_runner(text, dest_mp3: Path, *, api_key, voice_id, model_id, timeout_seconds):
        assert dest_mp3.parent.is_dir()
        assert voice_id == "voice_123"
        assert model_id == "eleven_multilingual_v2"
        calls.append(str(dest_mp3))
        dest_mp3.write_bytes(b"fake-mp3")
        return True, ["elevenlabs_provider:elevenlabs"], {"bytes_written": 8}

    tasks = [_task(task_id=f"asset_scene_{i:03d}_voice", scene_id=f"scene_{i:03d}", scene_number=i) for i in range(1, 12)]
    result = execute_elevenlabs_voice_live_from_asset_plan(
        _plan(*tasks),
        confirm_provider_costs=True,
        max_live_voice_tasks=10,
        run_id="voice_unit",
        output_root=str(tmp_path),
        elevenlabs_voice_id="voice_123",
        runner=fake_runner,
    )
    statuses = {r.task_id: r.execution_status for r in result.task_results}
    assert result.execution_status == "live_completed"
    assert result.estimated_provider_calls == 10
    assert len(result.estimated_outputs) == 10
    assert statuses["asset_scene_010_voice"] == "live_completed"
    assert statuses["asset_scene_011_voice"] == "skipped"
    assert result.task_results[0].output_exists is True
    assert result.task_results[0].file_size_bytes == len(b"fake-mp3")
    assert result.task_results[0].provider == "elevenlabs"
    assert len(calls) == 10


def test_endpoint_missing_cost_confirmation_no_live_call():
    client = TestClient(app)
    r = client.post(
        "/story-engine/elevenlabs-voice-live-execution",
        json={
            "asset_generation_plan": _plan(_task()).model_dump(),
            "confirm_provider_costs": False,
            "elevenlabs_voice_id": "voice_123",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["execution_version"] == "elevenlabs_voice_live_execution_v1"
    assert data["execution_status"] == "failed"
    assert data["blocking_issues"] == ["confirm_provider_costs_required_for_elevenlabs_voice_live"]
