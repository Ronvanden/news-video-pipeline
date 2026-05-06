"""BA 16.0–16.9 — Monetization & Scale Operating System."""

from types import SimpleNamespace

from app.monetization_scale.scale_suite import (
    build_channel_portfolio,
    build_monetization_scale_summary,
    build_opportunity_scanning,
    build_revenue_model,
    build_scale_blueprint,
)
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def _plan():
    return build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))


def test_ba16_pipeline_adds_monetization_scale_results():
    plan = _plan()

    assert plan.revenue_model_result is not None
    assert plan.revenue_model_result.revenue_version == "16.0-v1"
    assert plan.channel_portfolio_result is not None
    assert plan.multi_platform_strategy_result is not None
    assert plan.opportunity_scanning_result is not None
    assert plan.founder_kpi_result is not None
    assert plan.founder_kpi_result.north_star_metric == "repeatable_revenue_per_finished_video"
    assert plan.scale_blueprint_result is not None
    assert plan.sponsorship_readiness_result is not None
    assert plan.content_investment_plan_result is not None
    assert plan.scale_risk_register_result is not None
    assert plan.monetization_scale_summary_result is not None
    assert plan.monetization_scale_summary_result.company_stage == "production_system_to_media_company"


def test_ba16_prompt_plan_dump_exposes_expected_api_fields():
    payload = _plan().model_dump()

    for key in (
        "revenue_model_result",
        "channel_portfolio_result",
        "multi_platform_strategy_result",
        "opportunity_scanning_result",
        "founder_kpi_result",
        "scale_blueprint_result",
        "sponsorship_readiness_result",
        "content_investment_plan_result",
        "scale_risk_register_result",
        "monetization_scale_summary_result",
    ):
        assert key in payload
        assert payload[key] is not None


def test_revenue_model_uses_ba15_readiness_score():
    plan = SimpleNamespace(founder_local_dashboard_result=SimpleNamespace(readiness_score=84))

    result = build_revenue_model(plan)

    assert result.revenue_status == "ready"
    assert result.monetization_readiness_score == 84
    assert "youtube_ad_revenue" in result.primary_revenue_streams
    assert result.warnings == []


def test_opportunity_scanning_combines_hook_and_narrative_scores():
    plan = SimpleNamespace(hook_score=80, narrative_score_result=SimpleNamespace(score=60))

    result = build_opportunity_scanning(plan)

    assert result.scanning_status == "ready"
    assert result.opportunity_score == 70
    assert "test_two_titles" in result.recommended_experiments


def test_scale_blueprint_stays_in_proof_when_components_blocked():
    plan = SimpleNamespace(founder_local_dashboard_result=SimpleNamespace(blocked_components=["demo_video_automation"]))

    result = build_scale_blueprint(plan)

    assert result.blueprint_status == "partial"
    assert result.next_stage == "proof"
    assert result.constraints == ["demo_video_automation"]


def test_channel_portfolio_and_summary_are_media_company_oriented():
    plan = SimpleNamespace(template_type="true_crime", hook_type="open_loop")
    portfolio = build_channel_portfolio(plan)

    assert portfolio.recommended_primary_lane == "flagship_documentary"
    assert any(lane["lane_id"] == "shorts_discovery" for lane in portfolio.channel_lanes)
    summary = build_monetization_scale_summary(
        SimpleNamespace(
            revenue_model_result=SimpleNamespace(monetization_readiness_score=80),
            opportunity_scanning_result=SimpleNamespace(opportunity_score=80),
            scale_blueprint_result=SimpleNamespace(next_stage="repeatability"),
        )
    )
    assert summary.summary_status == "ready"
    assert summary.strategic_focus == "advance_to_repeatability"
