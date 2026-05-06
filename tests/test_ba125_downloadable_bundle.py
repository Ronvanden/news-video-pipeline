"""BA 12.5 — Downloadable Production Bundle."""

from app.production_assembly.downloadable_bundle import build_downloadable_production_bundle
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_download_bundle_id_and_manifest():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    bundle = plan.downloadable_production_bundle_result
    assert bundle is not None
    assert bundle.bundle_id.startswith("prod_bundle_")
    assert bundle.downloadable_manifest["bundle_id"] == bundle.bundle_id
    assert "master_asset_manifest" in bundle.included_components
    assert bundle.local_export_targets


def test_download_bundle_blocked_when_manifest_blocked():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    blocked_manifest = plan.master_asset_manifest_result.model_copy(
        update={"manifest_status": "blocked", "assets": [], "total_assets": 0}
    )
    bundle = build_downloadable_production_bundle(plan.model_copy(update={"master_asset_manifest_result": blocked_manifest}))
    assert bundle.bundle_status == "blocked"
    assert bundle.bundle_id.startswith("prod_bundle_")
