"""Real KPI Feedback Loop V1 — manuelle Performance-Daten, kein API-Zwang."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

CaptureStatus = Literal["ok", "partial", "invalid"]
FeedbackStatus = Literal["ok", "partial", "blocked"]
PerformanceLabel = Literal["winner", "promising", "neutral", "loser"]
FounderDecision = Literal[
    "repeat_format",
    "modify_hook",
    "change_niche",
    "kill_topic",
    "test_again",
]
DecisionPriority = Literal["high", "medium", "low"]


class RealKpiCaptureInput(BaseModel):
    """JSON-/CLI-Eingabe nach Publish (V1 manuell)."""

    video_id: str = ""
    source_url: str = Field(..., min_length=4)
    views: int = Field(default=0, ge=0)
    impressions: int = Field(default=0, ge=0)
    ctr: float = Field(default=0.0, ge=0.0, description="Anteil 0–1 oder Prozent bis 100")
    watch_time_minutes: float = Field(default=0.0, ge=0.0)
    avg_view_duration_seconds: float = Field(default=0.0, ge=0.0)
    subscribers_gained: int = Field(default=0)
    revenue_eur: Optional[float] = Field(default=None, ge=0.0)
    upload_date: str = ""


class RealKpiCaptureResult(BaseModel):
    """BA CF 16.5 — Normalisierte KPI-Erfassung."""

    capture_version: str = "cf-16.5-v1"
    capture_status: CaptureStatus = "partial"
    normalized_metrics: Dict[str, Any] = Field(default_factory=dict)
    missing_metrics: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class PerformanceClassificationResult(BaseModel):
    """BA CF 16.6 — Winner/Loser aus echten Signalen."""

    classify_version: str = "cf-16.6-v1"
    performance_label: PerformanceLabel = "neutral"
    confidence: int = Field(default=50, ge=0, le=100)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    repeat_recommendation: str = ""


class PredictionRealityResult(BaseModel):
    """BA CF 16.7 — Cash-Prognose vs. Realität."""

    compare_version: str = "cf-16.7-v1"
    prediction_accuracy: int = Field(default=0, ge=0, le=100)
    overestimated_signals: List[str] = Field(default_factory=list)
    underestimated_signals: List[str] = Field(default_factory=list)
    calibration_notes: List[str] = Field(default_factory=list)


class FounderPerformanceDecisionResult(BaseModel):
    """BA CF 16.8 — Founder-Entscheidungs-Vorschlag."""

    decide_version: str = "cf-16.8-v1"
    decision: FounderDecision = "test_again"
    reason: str = ""
    next_action: str = ""
    priority: DecisionPriority = "medium"


class KpiFeedbackSummaryResult(BaseModel):
    """BA CF 16.9 — kompakter Reality-Report."""

    summary_version: str = "cf-16.9-v1"
    feedback_status: FeedbackStatus = "partial"
    cash_result_summary: str = ""
    performance_summary: str = ""
    learning_summary: str = ""
    next_best_action: str = ""


class RealKpiFeedbackLoopResult(BaseModel):
    """Voller Loop 16.5–16.9 in einem Objekt (ohne Runtime-Pflicht)."""

    loop_version: str = "cf-loop-v1"
    capture: RealKpiCaptureResult
    classification: PerformanceClassificationResult
    prediction_reality: Optional[PredictionRealityResult] = None
    decision: FounderPerformanceDecisionResult
    summary: KpiFeedbackSummaryResult
