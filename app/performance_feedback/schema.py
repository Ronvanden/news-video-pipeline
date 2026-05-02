"""BA 14.0–14.7 — Performance Feedback Loop Schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


KpiIngestStatus = Literal["ready", "partial", "missing"]
KpiSourceType = Literal["manual", "csv", "youtube_api_stub", "unknown"]


class KpiIngestContractResult(BaseModel):
    """BA 14.0 — KPI-Importvertrag ohne Live-API-Pflicht."""

    ingest_version: str = "14.0-v1"
    ingest_status: KpiIngestStatus = "missing"
    source_type: KpiSourceType = "unknown"
    imported_metrics: Dict[str, Any] = Field(default_factory=dict)
    missing_metrics: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class KpiNormalizationResult(BaseModel):
    """BA 14.1 — normalisierte KPI-Werte als SoT."""

    normalization_version: str = "14.1-v1"
    normalized_status: Literal["ready", "partial", "insufficient_data"] = "insufficient_data"
    normalized_ctr: float = Field(default=0.0, ge=0.0)
    normalized_retention: float = Field(default=0.0, ge=0.0)
    normalized_rpm: float = Field(default=0.0)
    normalized_growth: float = Field(default=0.0)
    warnings: List[str] = Field(default_factory=list)


class HookPerformanceResult(BaseModel):
    """BA 14.2 — Hook-Wirkung gegen CTR/Hook-Score."""

    hook_performance_version: str = "14.2-v1"
    hook_performance_status: Literal["strong", "mixed", "weak", "insufficient_data"] = "insufficient_data"
    hook_effectiveness_score: int = Field(default=0, ge=0, le=100)
    hook_ctr_alignment: str = ""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class TemplateEvolutionResult(BaseModel):
    """BA 14.3 — Template-/Narrativ-Outcome-Schicht."""

    evolution_version: str = "14.3-v1"
    template_evolution_status: Literal["scalable", "promising", "needs_iteration", "insufficient_data"] = "insufficient_data"
    template_real_world_score: int = Field(default=0, ge=0, le=100)
    template_scalability: str = ""
    best_use_cases: List[str] = Field(default_factory=list)
    avoid_cases: List[str] = Field(default_factory=list)
    optimization_notes: List[str] = Field(default_factory=list)


class CostRevenueAnalysisResult(BaseModel):
    """BA 14.4 — Kosten-/Erlös-Heuristik."""

    analysis_version: str = "14.4-v1"
    analysis_status: Literal["profitable", "break_even", "loss", "insufficient_data"] = "insufficient_data"
    production_cost: float = Field(default=0.0, ge=0.0)
    revenue: float = Field(default=0.0, ge=0.0)
    roi: Optional[float] = None
    break_even_status: str = ""
    monetization_notes: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class AutoRecommendationUpgradeResult(BaseModel):
    """BA 14.5 — Empfehlungen aus Performance-Signalen."""

    recommendation_version: str = "14.5-v1"
    recommendation_status: Literal["ready", "partial", "insufficient_data"] = "insufficient_data"
    next_best_template: str = ""
    next_best_hook_strategy: str = ""
    provider_adjustment: str = ""
    publishing_adjustment: str = ""
    confidence: int = Field(default=0, ge=0, le=100)


class FounderGrowthIntelligenceResult(BaseModel):
    """BA 14.6 — Founder-Level Growth Intelligence."""

    intelligence_version: str = "14.6-v1"
    intelligence_status: Literal["growth_ready", "watch", "needs_data"] = "needs_data"
    growth_summary: str = ""
    scaling_opportunities: List[str] = Field(default_factory=list)
    major_risks: List[str] = Field(default_factory=list)
    content_strategy_shift: str = ""
    founder_actions: List[str] = Field(default_factory=list)


class MasterFeedbackOrchestratorResult(BaseModel):
    """BA 14.7 — Story → Production → Publishing → Performance → Wachstum."""

    orchestrator_version: str = "14.7-v1"
    orchestrator_status: Literal["growth_ready", "learning", "needs_data"] = "needs_data"
    production_vs_market_fit: str = ""
    hook_vs_market_fit: str = ""
    template_vs_market_fit: str = ""
    scaling_score: int = Field(default=0, ge=0, le=100)
    strategic_direction: str = ""
    final_growth_note: str = ""
