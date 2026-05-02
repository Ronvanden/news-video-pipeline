"""BA 16.0–16.9 — Monetization & Scale Operating System schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field

ScaleStatus = Literal["ready", "partial", "needs_data"]


class RevenueModelResult(BaseModel):
    """BA 16.0 — Revenue-Modell für Medienunternehmen-Pfad."""

    revenue_version: str = "16.0-v1"
    revenue_status: ScaleStatus = "partial"
    primary_revenue_streams: List[str] = Field(default_factory=list)
    secondary_revenue_streams: List[str] = Field(default_factory=list)
    monetization_readiness_score: int = Field(default=0, ge=0, le=100)
    warnings: List[str] = Field(default_factory=list)


class ChannelPortfolioResult(BaseModel):
    """BA 16.1 — Channel-Portfolio-Architektur."""

    portfolio_version: str = "16.1-v1"
    portfolio_status: ScaleStatus = "partial"
    channel_lanes: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_primary_lane: str = ""
    diversification_notes: List[str] = Field(default_factory=list)


class MultiPlatformStrategyResult(BaseModel):
    """BA 16.2 — Multi-Platform-Ausspielstrategie ohne Upload."""

    strategy_version: str = "16.2-v1"
    strategy_status: ScaleStatus = "partial"
    platform_targets: List[Dict[str, Any]] = Field(default_factory=list)
    repurposing_plan: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class OpportunityScanningResult(BaseModel):
    """BA 16.3 — Opportunity Radar für Themen- und Format-Chancen."""

    scanning_version: str = "16.3-v1"
    scanning_status: ScaleStatus = "partial"
    opportunity_score: int = Field(default=0, ge=0, le=100)
    opportunity_signals: List[str] = Field(default_factory=list)
    recommended_experiments: List[str] = Field(default_factory=list)


class FounderKpiResult(BaseModel):
    """BA 16.4 — Founder-KPIs für Wachstum und Monetarisierung."""

    kpi_version: str = "16.4-v1"
    kpi_status: ScaleStatus = "partial"
    north_star_metric: str = ""
    weekly_kpis: List[Dict[str, Any]] = Field(default_factory=list)
    decision_thresholds: List[Dict[str, Any]] = Field(default_factory=list)


class ScaleBlueprintResult(BaseModel):
    """BA 16.5 — Skalierungs-Blueprint von Demo zu Medienunternehmen."""

    blueprint_version: str = "16.5-v1"
    blueprint_status: ScaleStatus = "partial"
    scale_stages: List[Dict[str, Any]] = Field(default_factory=list)
    next_stage: str = ""
    constraints: List[str] = Field(default_factory=list)


class SponsorshipReadinessResult(BaseModel):
    """BA 16.6 — Sponsor-/Brand-Readiness ohne Outreach."""

    sponsorship_version: str = "16.6-v1"
    sponsorship_status: ScaleStatus = "needs_data"
    sponsor_fit_categories: List[str] = Field(default_factory=list)
    media_kit_requirements: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ContentInvestmentPlanResult(BaseModel):
    """BA 16.7 — Investitionsplan für wiederholbare Content-Produktion."""

    investment_version: str = "16.7-v1"
    investment_status: ScaleStatus = "partial"
    reinvestment_priorities: List[Dict[str, Any]] = Field(default_factory=list)
    budget_guardrails: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ScaleRiskRegisterResult(BaseModel):
    """BA 16.8 — Risiko-Register für Skalierung."""

    risk_version: str = "16.8-v1"
    risk_status: ScaleStatus = "ready"
    risks: List[Dict[str, Any]] = Field(default_factory=list)
    mitigation_priorities: List[str] = Field(default_factory=list)


class MonetizationScaleSummaryResult(BaseModel):
    """BA 16.9 — Founder-Level Monetization & Scale Summary."""

    summary_version: str = "16.9-v1"
    summary_status: ScaleStatus = "partial"
    company_stage: str = ""
    readiness_score: int = Field(default=0, ge=0, le=100)
    strategic_focus: str = ""
    next_actions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

