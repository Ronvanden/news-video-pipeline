"""BA 13.5 — Publishing Readiness Gate."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest
from app.publishing.publishing_readiness_gate import evaluate_publishing_readiness


def test_publishing_readiness_default_requires_review_not_upload():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    gate = plan.publishing_readiness_gate_result
    assert gate is not None
    assert gate.publishing_status == "ready_for_review"
    assert gate.release_recommendation == "review"
    assert gate.publishing_score > 0
    assert "human_final_review_needs_revision" in gate.warnings


def test_publishing_readiness_holds_when_metadata_missing():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    broken = plan.model_copy(update={"metadata_master_package_result": None})
    gate = evaluate_publishing_readiness(broken)
    assert gate.publishing_status == "not_ready"
    assert gate.release_recommendation == "hold"
    assert "metadata_missing_or_blocked" in gate.blockers
