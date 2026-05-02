"""BA 10.0 — Base connector / Leonardo."""

from app.production_connectors.leonardo_connector import LeonardoProductionConnector


def test_leonardo_valid_payload_builds_request_and_dry_run_success():
    c = LeonardoProductionConnector()
    payload = {"provider_target": "Leonardo", "style_profile": "true_crime", "prompts": ["a", "b"]}
    ok, w, b = c.validate_payload(payload)
    assert ok and not b
    req = c.build_request(payload)
    assert req["operation"] == "image_generation_batch"
    assert req["dry_run"] is True
    res = c.dry_run(payload)
    assert res.execution_status == "dry_run_success"
    assert res.normalized_request
    assert res.normalized_response.get("dry_run") is True


def test_leonardo_invalid_payload_missing_prompts():
    c = LeonardoProductionConnector()
    res = c.dry_run({"style_profile": "x"})
    assert res.execution_status == "invalid_payload"
    assert res.normalized_request == {}
    assert res.blocking_reasons
