"""BA 16.0–16.9 — Monetization & Scale Operating System."""

from __future__ import annotations

from typing import Any, Dict, List

from app.monetization_scale.schema import (
    ChannelPortfolioResult,
    ContentInvestmentPlanResult,
    FounderKpiResult,
    MonetizationScaleSummaryResult,
    MultiPlatformStrategyResult,
    OpportunityScanningResult,
    RevenueModelResult,
    ScaleBlueprintResult,
    ScaleRiskRegisterResult,
    SponsorshipReadinessResult,
)


def _readiness_score(plan: object) -> int:
    dashboard = getattr(plan, "founder_local_dashboard_result", None)
    score = getattr(dashboard, "readiness_score", 0)
    try:
        return int(score)
    except (TypeError, ValueError):
        return 0


def build_revenue_model(plan: object) -> RevenueModelResult:
    readiness = _readiness_score(plan)
    streams = ["youtube_ad_revenue", "affiliate_links", "sponsorships"]
    secondary = ["newsletter_sponsorship", "licensing", "paid_research_briefings"]
    status = "ready" if readiness >= 70 else "partial"
    warnings = [] if readiness >= 70 else ["production_repeatability_below_revenue_scale_threshold"]
    return RevenueModelResult(
        revenue_status=status,
        primary_revenue_streams=streams,
        secondary_revenue_streams=secondary,
        monetization_readiness_score=min(100, max(25, readiness)),
        warnings=warnings,
    )


def build_channel_portfolio(plan: object) -> ChannelPortfolioResult:
    template = getattr(plan, "template_type", "") or "generic"
    lanes: List[Dict[str, Any]] = [
        {"lane_id": "flagship_documentary", "format": template, "role": "authority_and_watch_time"},
        {"lane_id": "shorts_discovery", "format": "short_open_loop", "role": "top_of_funnel"},
        {"lane_id": "evergreen_explainer", "format": "context_first", "role": "search_and_library"},
    ]
    return ChannelPortfolioResult(
        portfolio_status="ready",
        channel_lanes=lanes,
        recommended_primary_lane="flagship_documentary",
        diversification_notes=["start_with_one_flagship_lane_before_spinning_up_new_channels"],
    )


def build_multi_platform_strategy(plan: object) -> MultiPlatformStrategyResult:
    title = getattr(plan, "hook", "") or getattr(plan, "template_type", "") or "demo_story"
    targets = [
        {"platform": "youtube_longform", "asset": "first_demo_video", "priority": 1},
        {"platform": "youtube_shorts", "asset": "hook_cutdown", "priority": 2},
        {"platform": "tiktok_reels", "asset": "short_vertical_cut", "priority": 3},
        {"platform": "newsletter", "asset": "story_summary", "priority": 4},
    ]
    return MultiPlatformStrategyResult(
        strategy_status="ready",
        platform_targets=targets,
        repurposing_plan=[
            f"convert_hook_to_short_intro:{str(title)[:60]}",
            "extract_three_quote_cards",
            "publish_newsletter_context_summary",
        ],
    )


def build_opportunity_scanning(plan: object) -> OpportunityScanningResult:
    hook_score = int(getattr(plan, "hook_score", 0) or 0)
    narrative = getattr(plan, "narrative_score_result", None)
    narrative_score = int(getattr(narrative, "score", 0) or 0)
    score = max(30, min(100, round((hook_score + narrative_score) / 2)))
    signals = ["hook_strength", "narrative_structure", "template_repeatability"]
    return OpportunityScanningResult(
        scanning_status="ready" if score >= 60 else "partial",
        opportunity_score=score,
        opportunity_signals=signals,
        recommended_experiments=["test_two_titles", "test_thumbnail_contrast", "compare_short_vs_long_hook"],
    )


def build_founder_kpi(plan: object) -> FounderKpiResult:
    revenue = getattr(plan, "revenue_model_result", None)
    readiness = int(getattr(revenue, "monetization_readiness_score", 0) or 0)
    return FounderKpiResult(
        kpi_status="ready",
        north_star_metric="repeatable_revenue_per_finished_video",
        weekly_kpis=[
            {"metric": "videos_completed", "target": 3},
            {"metric": "demo_to_publish_ready_rate", "target": ">=70%"},
            {"metric": "estimated_revenue_per_video", "target": "trend_up"},
        ],
        decision_thresholds=[
            {"if": "readiness_score>=70", "then": "increase_batch_volume"},
            {"if": f"monetization_readiness_score={readiness}", "then": "keep_revenue_tracking_manual_until_real_kpis"},
        ],
    )


def build_scale_blueprint(plan: object) -> ScaleBlueprintResult:
    dashboard = getattr(plan, "founder_local_dashboard_result", None)
    blocked = list(getattr(dashboard, "blocked_components", []) or [])
    stages = [
        {"stage": "proof", "goal": "one_real_watchable_video", "exit": "image_audio_mp4_exists"},
        {"stage": "repeatability", "goal": "three_demo_videos_per_week", "exit": "batch_runner_stable"},
        {"stage": "portfolio", "goal": "two_format_lanes", "exit": "retention_and_ctr_split"},
        {"stage": "monetization", "goal": "revenue_stream_tests", "exit": "sponsor_or_affiliate_signal"},
    ]
    next_stage = "repeatability" if not blocked else "proof"
    return ScaleBlueprintResult(
        blueprint_status="ready" if not blocked else "partial",
        scale_stages=stages,
        next_stage=next_stage,
        constraints=blocked or ["manual_kpi_input_required", "no_auto_publishing_yet"],
    )


def build_sponsorship_readiness(plan: object) -> SponsorshipReadinessResult:
    summary = getattr(plan, "metadata_master_package_result", None)
    category = getattr(summary, "category", "") or "documentary_news"
    return SponsorshipReadinessResult(
        sponsorship_status="partial",
        sponsor_fit_categories=[category, "research_tools", "creator_tools", "education_platforms"],
        media_kit_requirements=["audience_profile", "average_views", "retention_curve", "brand_safety_notes"],
        warnings=["sponsorship_requires_real_audience_metrics"],
    )


def build_content_investment_plan(plan: object) -> ContentInvestmentPlanResult:
    cost = getattr(plan, "cost_snapshot_result", None)
    estimated = float(getattr(cost, "estimated_cost", 0.0) or 0.0)
    return ContentInvestmentPlanResult(
        investment_status="ready",
        reinvestment_priorities=[
            {"priority": 1, "area": "voice_and_image_generation", "reason": "core_asset_quality"},
            {"priority": 2, "area": "thumbnail_testing", "reason": "ctr_leverage"},
            {"priority": 3, "area": "batch_topic_research", "reason": "portfolio_scale"},
        ],
        budget_guardrails=[
            f"keep_demo_cost_baseline_at_or_above:{estimated:.2f}",
            "pause_scale_if_manual_review_backlog_grows",
        ],
        warnings=[] if estimated else ["investment_plan_uses_missing_or_zero_cost_baseline"],
    )


def build_scale_risk_register(_: object) -> ScaleRiskRegisterResult:
    risks = [
        {"risk": "quality_drops_with_batch_volume", "severity": "high"},
        {"risk": "platform_dependency", "severity": "medium"},
        {"risk": "unclear_rights_or_sources", "severity": "high"},
        {"risk": "costs_scale_before_revenue", "severity": "medium"},
    ]
    return ScaleRiskRegisterResult(
        risks=risks,
        mitigation_priorities=["human_review_gate", "multi_platform_distribution", "cost_snapshot_per_batch"],
    )


def build_monetization_scale_summary(plan: object) -> MonetizationScaleSummaryResult:
    revenue = getattr(plan, "revenue_model_result", None)
    opportunity = getattr(plan, "opportunity_scanning_result", None)
    blueprint = getattr(plan, "scale_blueprint_result", None)
    revenue_score = int(getattr(revenue, "monetization_readiness_score", 0) or 0)
    opportunity_score = int(getattr(opportunity, "opportunity_score", 0) or 0)
    readiness = round((revenue_score + opportunity_score) / 2)
    next_stage = getattr(blueprint, "next_stage", "proof")
    return MonetizationScaleSummaryResult(
        summary_status="ready" if readiness >= 70 else "partial",
        company_stage="production_system_to_media_company",
        readiness_score=readiness,
        strategic_focus=f"advance_to_{next_stage}",
        next_actions=[
            "produce_three_repeatable_demo_videos",
            "collect_manual_kpis_per_video",
            "test_one_revenue_stream_before_scaling_channels",
        ],
        warnings=[] if readiness >= 70 else ["scale_requires_more_real_performance_data"],
    )


def apply_monetization_scale_suite(plan: object) -> object:
    """Revenue → portfolio → platforms → opportunity → founder KPI → scale blueprint."""
    p = plan.model_copy(update={"revenue_model_result": build_revenue_model(plan)})
    p = p.model_copy(update={"channel_portfolio_result": build_channel_portfolio(p)})
    p = p.model_copy(update={"multi_platform_strategy_result": build_multi_platform_strategy(p)})
    p = p.model_copy(update={"opportunity_scanning_result": build_opportunity_scanning(p)})
    p = p.model_copy(update={"founder_kpi_result": build_founder_kpi(p)})
    p = p.model_copy(update={"scale_blueprint_result": build_scale_blueprint(p)})
    p = p.model_copy(update={"sponsorship_readiness_result": build_sponsorship_readiness(p)})
    p = p.model_copy(update={"content_investment_plan_result": build_content_investment_plan(p)})
    p = p.model_copy(update={"scale_risk_register_result": build_scale_risk_register(p)})
    p = p.model_copy(update={"monetization_scale_summary_result": build_monetization_scale_summary(p)})
    return p

