"""BA 13.6 — Founder Publishing Summary."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest
from app.publishing.founder_publishing_summary import build_founder_publishing_summary


def test_founder_publishing_summary_present():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    summary = plan.founder_publishing_summary_result
    assert summary is not None
    assert summary.content_summary
    assert summary.marketability_summary
    assert summary.seo_summary
    assert summary.publishing_risk_summary
    assert summary.release_strategy
    assert summary.final_founder_note


def test_founder_summary_reflects_hold_signal():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    hold_gate = plan.publishing_readiness_gate_result.model_copy(
        update={"publishing_status": "not_ready", "release_recommendation": "hold", "blockers": ["x"]}
    )
    summary = build_founder_publishing_summary(plan.model_copy(update={"publishing_readiness_gate_result": hold_gate}))
    assert "Hold or review" in summary.final_founder_note
    assert summary.supporting_signals["release_recommendation"] == "hold"
