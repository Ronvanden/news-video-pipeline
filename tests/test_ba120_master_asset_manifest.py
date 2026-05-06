"""BA 12.0 — Master Asset Manifest."""

from app.production_assembly.master_asset_manifest import build_master_asset_manifest
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def _plan():
    return build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))


def test_manifest_complete_from_default_mock_and_live_outputs():
    plan = _plan()
    manifest = plan.master_asset_manifest_result
    assert manifest is not None
    assert manifest.manifest_version == "12.0-v1"
    assert manifest.manifest_status == "complete"
    assert manifest.total_assets >= 5
    assert set(manifest.missing_asset_types) == set()


def test_manifest_partial_when_only_image_asset_present():
    plan = _plan().model_copy(
        update={
            "voice_live_result": None,
            "provider_job_runner_mock_result": None,
            "asset_persistence_result": None,
        }
    )
    manifest = build_master_asset_manifest(plan)
    assert manifest.manifest_status == "partial"
    assert "audio" in manifest.missing_asset_types
    assert manifest.total_assets >= 1
