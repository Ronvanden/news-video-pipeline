"""BA 11.4 — Asset Persistence Contract."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest
from app.production_connectors.asset_persistence import build_asset_persistence_contract
from app.production_connectors.live_provider_suite import apply_live_provider_suite


def test_manifest_structure_after_suite():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    p2 = apply_live_provider_suite(plan)
    ap = build_asset_persistence_contract(p2)
    assert ap.persistence_status in ("metadata_only", "persist_ready", "blocked")
    assert "assets" in ap.metadata_manifest
    assert isinstance(ap.local_storage_targets, list)
    assert ap.metadata_manifest.get("run_key")
