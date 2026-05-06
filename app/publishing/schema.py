"""BA 13.0–13.6 — Publishing Preparation Schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


PublishingComponentStatus = Literal["complete", "partial", "blocked"]


class MetadataMasterPackageResult(BaseModel):
    """BA 13.0 — zentrale Metadatenquelle für Publishing."""

    metadata_version: str = "13.0-v1"
    metadata_status: PublishingComponentStatus = "partial"
    platform_target: str = "youtube"
    canonical_title: str = ""
    canonical_description: str = ""
    canonical_tags: List[str] = Field(default_factory=list)
    category: str = "News & Politics"
    audience_flags: List[str] = Field(default_factory=list)
    compliance_warnings: List[str] = Field(default_factory=list)


class MetadataOptimizerResult(BaseModel):
    """BA 13.1 — Titel-, Description- und Tag-Varianten."""

    optimizer_version: str = "13.1-v1"
    optimized_titles: List[str] = Field(default_factory=list)
    optimized_descriptions: List[str] = Field(default_factory=list)
    optimized_tags: List[str] = Field(default_factory=list)
    seo_score: int = Field(default=0, ge=0, le=100)
    click_potential_score: int = Field(default=0, ge=0, le=100)
    warnings: List[str] = Field(default_factory=list)


class ThumbnailVariant(BaseModel):
    """BA 13.2 — einzelne Thumbnail-Idee."""

    variant_id: str = ""
    angle: str = ""
    headline_text: str = ""
    visual_direction: str = ""
    emotional_trigger: str = ""


class ThumbnailVariantPackResult(BaseModel):
    """BA 13.2 — Thumbnail-Variantenpaket ohne Bildgenerierung."""

    variant_version: str = "13.2-v1"
    variant_status: PublishingComponentStatus = "partial"
    variants: List[ThumbnailVariant] = Field(default_factory=list)
    recommended_primary: str = ""
    visual_hooks: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class UploadChecklistResult(BaseModel):
    """BA 13.3 — Upload-Readiness-Check ohne Upload."""

    checklist_version: str = "13.3-v1"
    checklist_status: PublishingComponentStatus = "partial"
    required_items: List[str] = Field(default_factory=list)
    completed_items: List[str] = Field(default_factory=list)
    missing_items: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)


SuggestedPublishMode = Literal["immediate", "scheduled", "hold"]


class SchedulePlanResult(BaseModel):
    """BA 13.4 — heuristischer Veröffentlichungsplan ohne Scheduler."""

    schedule_version: str = "13.4-v1"
    suggested_publish_mode: SuggestedPublishMode = "hold"
    recommended_publish_windows: List[str] = Field(default_factory=list)
    timezone_notes: List[str] = Field(default_factory=list)
    strategic_notes: List[str] = Field(default_factory=list)


PublishingStatus = Literal["ready_to_publish", "ready_for_review", "not_ready"]
PublishingReleaseRecommendation = Literal["publish", "review", "hold"]


class PublishingReadinessGateResult(BaseModel):
    """BA 13.5 — finales Publishing-Gate ohne externen Upload."""

    readiness_version: str = "13.5-v1"
    publishing_status: PublishingStatus = "not_ready"
    publishing_score: int = Field(default=0, ge=0, le=100)
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    release_recommendation: PublishingReleaseRecommendation = "hold"


class FounderPublishingSummaryResult(BaseModel):
    """BA 13.6 — Executive Publishing Summary."""

    summary_version: str = "13.6-v1"
    content_summary: str = ""
    marketability_summary: str = ""
    seo_summary: str = ""
    publishing_risk_summary: str = ""
    release_strategy: str = ""
    final_founder_note: str = ""
    supporting_signals: Dict[str, Any] = Field(default_factory=dict)
