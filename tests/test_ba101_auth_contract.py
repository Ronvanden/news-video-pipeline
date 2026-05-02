"""BA 10.1 — Connector auth contract."""

from app.production_connectors.auth_contract import build_connector_auth_contract, build_connector_auth_contracts_result
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_leonardo_mapping():
    r = build_connector_auth_contract("Leonardo")
    assert r.auth_type == "api_key"
    assert "LEONARDO_API_KEY" in r.required_env_vars
    assert r.auth_status == "auth_missing"


def test_thumbnail_no_auth():
    r = build_connector_auth_contract("Thumbnail (stub)")
    assert r.auth_type == "none"
    assert r.auth_status == "auth_not_required"
    assert not r.required_env_vars


def test_unknown_connector_auth_unknown():
    r = build_connector_auth_contract("TotallyUnknownVendor")
    assert r.auth_status == "auth_unknown"
    assert r.auth_type == "unknown"


def test_auth_contracts_result_from_pipeline():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    assert plan.connector_auth_contracts_result is not None
    assert len(plan.connector_auth_contracts_result.contracts) >= 1
