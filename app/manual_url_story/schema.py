"""Manual URL Story Execution Engine — additive Ausgabe-Spur (kein Ersatz für BA 15 Acceleration-Felder)."""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field

from app.cash_optimization.schema import CashOptimizationLayerResult

StepStatus = Literal["skipped", "ok", "blocked"]
DemoStepStatus = Literal["skipped", "ready", "blocked"]

UrlQualityStatus = Literal["strong", "moderate", "weak", "blocked"]
RecommendedRewriteMode = Literal["documentary", "emotional", "mystery", "viral"]

DemoExecutionStatus = Literal["ready", "partial", "blocked"]


class UrlQualityGateResult(BaseModel):
    """BA 15.7 — Schneller Gatekeeper nach Extraktion / Rewrite."""

    gate_version: str = "15.7-v1"
    url_quality_status: UrlQualityStatus = "moderate"
    hook_potential_score: int = Field(default=0, ge=0, le=100)
    narrative_density_score: int = Field(default=0, ge=0, le=100)
    emotional_weight_score: int = Field(default=0, ge=0, le=100)
    recommended_mode: RecommendedRewriteMode = "documentary"
    warnings: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)


class ManualUrlDemoExecutionResult(BaseModel):
    """BA 15.5 — Orchestrierungs-Hooks für Leonardo / Voice / First-Demo-Video (ohne Auto-Run)."""

    execution_version: str = "15.5-v1"
    execution_status: DemoExecutionStatus = "partial"
    local_run_summary: str = ""
    leonardo_command_hint: List[str] = Field(default_factory=list)
    voice_command_hint: List[str] = Field(default_factory=list)
    first_demo_video_command_hint: List[str] = Field(default_factory=list)
    asset_handoff_notes: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)


class ManualUrlIntakeStep(BaseModel):
    """15.0 — Manueller URL-Eingang."""

    step_version: str = "15.0-v1"
    status: StepStatus = "skipped"
    source_url_display: str = Field(
        default="",
        description="Nur Host/Pfad — keine Query/Fragment für Logs/API.",
    )


class ManualUrlExtractionStep(BaseModel):
    """15.1 — Quellen-Extraktion (trafilatura / YouTube-Pfad wie utils)."""

    step_version: str = "15.1-v1"
    status: StepStatus = "skipped"
    extracted_char_count: int = Field(default=0, ge=0)
    warnings: List[str] = Field(default_factory=list)


class ManualUrlNarrativeRewriteStep(BaseModel):
    """15.2 — Narrativ-Rewrite (shared Pfad mit build_script_response_from_extracted_text)."""

    step_version: str = "15.2-v1"
    status: StepStatus = "skipped"
    script_title: str = ""
    chapter_count: int = Field(default=0, ge=0)
    full_script_preview: str = Field(
        default="",
        max_length=600,
        description="Gekürzte Vorschau — kein vollständiges Skript im Plan.",
    )
    warnings: List[str] = Field(default_factory=list)


class ManualUrlAssetPromptStep(BaseModel):
    """15.3 — Asset-Prompts aus Kapiteln × Template (scene_prompts)."""

    step_version: str = "15.3-v1"
    status: StepStatus = "skipped"
    scene_prompt_count: int = Field(default=0, ge=0)
    notes: List[str] = Field(default_factory=list)


class ManualUrlDemoVideoStep(BaseModel):
    """15.4 — Demo-Video-Ausführung (lokal, konsistent mit Acceleration BA 15.0)."""

    step_version: str = "15.4-v1"
    status: DemoStepStatus = "skipped"
    command_hint: List[str] = Field(default_factory=list)
    output_path: str = "output/first_demo_video.mp4"
    notes: List[str] = Field(default_factory=list)


class ManualUrlStoryExecutionResult(BaseModel):
    """Gebündelte Spur Manual URL → Extraktion → Rewrite → Asset-Prompts → Demo-Hinweis."""

    execution_version: str = "manual-url-story-v1"
    intake: ManualUrlIntakeStep = Field(default_factory=ManualUrlIntakeStep)
    extraction: ManualUrlExtractionStep = Field(default_factory=ManualUrlExtractionStep)
    narrative_rewrite: ManualUrlNarrativeRewriteStep = Field(
        default_factory=ManualUrlNarrativeRewriteStep
    )
    asset_prompt_build: ManualUrlAssetPromptStep = Field(default_factory=ManualUrlAssetPromptStep)
    demo_video_execution: ManualUrlDemoVideoStep = Field(default_factory=ManualUrlDemoVideoStep)


WatchRecommendedAction = Literal["approve", "review", "skip"]


class BatchUrlItemResult(BaseModel):
    """BA 15.8 — Eine URL aus einem Batch-Lauf (ohne vollen PromptPlan-Suite)."""

    source_url: str
    title: str = ""
    url_quality_status: UrlQualityStatus = "moderate"
    hook_potential_score: int = Field(default=0, ge=0, le=100)
    recommended_mode: RecommendedRewriteMode = "documentary"
    rewrite_summary: str = ""
    local_run_id: str = ""
    cash_layer: CashOptimizationLayerResult | None = Field(
        default=None,
        description="Cash Optimization CO 16.0–16.4 — Profit-Priorität pro URL.",
    )


class BatchUrlRunResult(BaseModel):
    """BA 15.8 — Batch-Analyse + Ranking."""

    batch_version: str = "15.8-v1"
    items: List[BatchUrlItemResult] = Field(default_factory=list)
    ranked_urls: List[str] = Field(default_factory=list)
    profit_ranked_urls: List[str] = Field(
        default_factory=list,
        description="Nach Cash-ROIScore (CO 16.0), höchste zuerst.",
    )
    top_candidates: List[str] = Field(default_factory=list)
    blocked_urls: List[str] = Field(default_factory=list)


class WatchItemVerdict(BaseModel):
    """BA 15.9 — Ein Watch/Radar-Eintrag nach Relevanz-Gate."""

    item_id: str
    source_url: str
    label: str = ""
    relevance_score: int = Field(default=0, ge=0, le=100)
    recommended_action: WatchRecommendedAction = "review"
    url_quality_status: UrlQualityStatus = "moderate"
    hook_potential_score: int = Field(default=0, ge=0, le=100)
    duplicate_of_item_id: str = ""
    notes: List[str] = Field(default_factory=list)
    cash_layer: CashOptimizationLayerResult | None = Field(
        default=None,
        description="Cash Optimization CO 16.0–16.4 — Profit-Priorität für Approval.",
    )


class WatchApprovalResult(BaseModel):
    """BA 15.9 — Radar + Approval-Queues (kein Auto-Video / kein Publish)."""

    layer_version: str = "15.9-v1"
    detected_items: List[WatchItemVerdict] = Field(default_factory=list)
    approval_queue: List[WatchItemVerdict] = Field(default_factory=list)
    rejected_items: List[WatchItemVerdict] = Field(default_factory=list)
