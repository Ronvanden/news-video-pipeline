"""BA 15.0–15.9 — First Production Acceleration Suite."""

from types import SimpleNamespace

from app.production_acceleration.acceleration_suite import (
    build_asset_downloader,
    build_demo_video_automation,
    build_founder_local_dashboard,
)
from app.production_connectors.voice_live_connector import DEFAULT_ELEVENLABS_TEST_VOICE_ID
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def _plan():
    return build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))


def test_ba15_pipeline_adds_acceleration_results():
    plan = _plan()

    assert plan.demo_video_automation_result is not None
    assert plan.demo_video_automation_result.automation_version == "15.0-v1"
    assert plan.asset_downloader_result is not None
    assert plan.voice_registry_result is not None
    assert plan.voice_registry_result.default_voice_id == DEFAULT_ELEVENLABS_TEST_VOICE_ID
    assert plan.scene_stitcher_result is not None
    assert plan.subtitle_draft_result is not None
    assert plan.thumbnail_extract_result is not None
    assert plan.founder_local_dashboard_result is not None
    assert plan.batch_topic_runner_result is not None
    assert plan.batch_topic_runner_result.topic_count == 1
    assert plan.cost_snapshot_result is not None
    assert plan.viral_prototype_presets_result is not None
    assert plan.viral_prototype_presets_result.presets_status == "ready"


def test_ba15_prompt_plan_dump_exposes_expected_api_fields():
    payload = _plan().model_dump()

    for key in (
        "demo_video_automation_result",
        "asset_downloader_result",
        "voice_registry_result",
        "scene_stitcher_result",
        "subtitle_draft_result",
        "thumbnail_extract_result",
        "founder_local_dashboard_result",
        "batch_topic_runner_result",
        "cost_snapshot_result",
        "viral_prototype_presets_result",
    ):
        assert key in payload
        assert payload[key] is not None


def test_demo_video_automation_ready_with_real_image_asset():
    plan = SimpleNamespace(
        master_asset_manifest_result=SimpleNamespace(
            assets=[
                SimpleNamespace(
                    asset_type="image",
                    asset_url="https://cdn.example.test/leonardo/image.png",
                    local_path=None,
                    provider_name="Leonardo",
                )
            ]
        ),
        leonardo_live_result=None,
    )

    result = build_demo_video_automation(plan)

    assert result.automation_status == "ready"
    assert result.image_source == "https://cdn.example.test/leonardo/image.png"
    assert result.output_path == "output/first_demo_video.mp4"
    assert result.audio_source == "output/voice_smoke_test_output.mp3"
    assert result.blocking_reasons == []
    assert result.command_hint == [
        "python",
        "scripts/build_first_demo_video.py",
        "https://cdn.example.test/leonardo/image.png",
    ]


def test_asset_downloader_collects_remote_and_local_assets():
    plan = SimpleNamespace(
        master_asset_manifest_result=SimpleNamespace(
            assets=[
                SimpleNamespace(
                    asset_type="image",
                    asset_url="https://cdn.example.test/image.png",
                    local_path=None,
                    provider_name="Leonardo",
                ),
                SimpleNamespace(
                    asset_type="audio",
                    asset_url=None,
                    local_path="output/voice_smoke_test_output.mp3",
                    provider_name="ElevenLabs",
                ),
            ]
        )
    )

    result = build_asset_downloader(plan)

    assert result.downloader_status == "ready"
    assert result.download_targets == [
        {
            "asset_type": "image",
            "provider_name": "Leonardo",
            "asset_url": "https://cdn.example.test/image.png",
        }
    ]
    assert result.local_asset_paths == ["output/voice_smoke_test_output.mp3"]


def test_founder_local_dashboard_marks_blocked_components():
    plan = SimpleNamespace(
        demo_video_automation_result=SimpleNamespace(automation_status="blocked"),
        asset_downloader_result=SimpleNamespace(downloader_status="ready"),
        voice_registry_result=SimpleNamespace(registry_status="ready"),
        scene_stitcher_result=SimpleNamespace(stitcher_status="partial"),
        subtitle_draft_result=SimpleNamespace(subtitle_status="ready"),
        thumbnail_extract_result=SimpleNamespace(extract_status="ready"),
    )

    result = build_founder_local_dashboard(plan)

    assert result.dashboard_status == "partial"
    assert result.readiness_score == 83
    assert result.blocked_components == ["demo_video_automation"]
    assert result.next_actions[0] == "provide_real_image_and_audio_assets"
