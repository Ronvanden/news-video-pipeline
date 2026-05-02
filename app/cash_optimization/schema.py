"""Cash Optimization Layer V1 — Founder Profit Filter (heuristisch, kein ML)."""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field

ConfidenceLevel = Literal["high", "medium", "low"]
PriorityLevel = Literal["high", "medium", "low"]
RpmCategory = Literal["high", "medium", "low"]
ProductionCostTier = Literal["lean", "standard", "heavy"]
ComplexityLabel = Literal["low", "medium", "high"]
FactRiskLabel = Literal["low", "medium", "high"]
VisualDifficultyLabel = Literal["low", "medium", "high"]


class EstimatedRpmResult(BaseModel):
    """BA 16.1 — Heuristische RPM-/Nischen-Kategorie."""

    rpm_version: str = "16.1-v1"
    estimated_rpm_category: RpmCategory = "medium"
    estimated_rpm_confidence: int = Field(default=50, ge=0, le=100)
    niche_reasoning: str = ""


class ProductionCostSnapshotResult(BaseModel):
    """BA 16.2 — Produktions-Aufwand."""

    cost_snapshot_version: str = "16.2-v1"
    estimated_asset_complexity: ComplexityLabel = "medium"
    likely_scene_count: int = Field(default=4, ge=0, le=64)
    likely_fact_check_risk: FactRiskLabel = "medium"
    likely_visual_difficulty: VisualDifficultyLabel = "medium"
    production_cost_tier: ProductionCostTier = "standard"


class ViralHookScoreResult(BaseModel):
    """BA 16.3 — Virale Hook-Dimensionen (Keyword-heuristisch)."""

    viral_hook_version: str = "16.3-v1"
    viral_hook_score: int = Field(default=0, ge=0, le=100)
    dominant_hook_type: str = "none"
    hook_risk_warning: str = ""


class WinnerRepeatResult(BaseModel):
    """BA 16.4 — Gewinner-Cluster / Repeatability."""

    winner_version: str = "16.4-v1"
    winner_cluster: str = "none"
    repeatability_score: int = Field(default=0, ge=0, le=100)
    format_scaling_potential: str = ""


class CandidateRoiScoreResult(BaseModel):
    """BA 16.0 — Aggregiertes Profit-Signal."""

    roi_version: str = "16.0-v1"
    candidate_roi_score: int = Field(default=0, ge=0, le=100)
    hook_power_score: int = Field(default=0, ge=0, le=100)
    narrative_strength_score: int = Field(default=0, ge=0, le=100)
    niche_value_score: int = Field(default=0, ge=0, le=100)
    production_efficiency_score: int = Field(default=50, ge=0, le=100)
    confidence_level: ConfidenceLevel = "medium"
    recommended_priority: PriorityLevel = "medium"
    warnings: List[str] = Field(default_factory=list)


class CashOptimizationLayerResult(BaseModel):
    """Gebündelte Ausgabe 16.0–16.4 für PromptPlan / Batch / Watch."""

    layer_version: str = "cash-opt-v1"
    roi: CandidateRoiScoreResult
    estimated_rpm: EstimatedRpmResult
    production_cost: ProductionCostSnapshotResult
    viral_hook: ViralHookScoreResult
    winner_repeat: WinnerRepeatResult
