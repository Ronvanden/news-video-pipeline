"""BA 9.10–9.30 + BA 10–14 — Prompt Planning, Publishing & Feedback."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.production_connectors.schema import (
    APIActivationControlResult,
    AssetPersistenceResult,
    AssetStatusTrackerResult,
    ConnectorAuthContractsResult,
    ExecutionPolicyResult,
    LiveExecutionGuardResult,
    LiveConnectorExecutionResult,
    LiveProviderSafetyResult,
    ProductionConnectorSuiteResult,
    ProductionRunSummaryResult,
    ProviderErrorRecoveryResult,
    ProviderExecutionQueueResult,
    ProviderJobRunnerMockResult,
    RuntimeSecretCheckResult,
)
from app.production_assembly.schema import (
    DownloadableProductionBundleResult,
    FinalTimelineResult,
    HumanFinalReviewPackageResult,
    MasterAssetManifestResult,
    MultiAssetAssemblyResult,
    RenderInstructionPackageResult,
    VoiceSceneAlignmentResult,
)
from app.publishing.schema import (
    FounderPublishingSummaryResult,
    MetadataMasterPackageResult,
    MetadataOptimizerResult,
    PublishingReadinessGateResult,
    SchedulePlanResult,
    ThumbnailVariantPackResult,
    UploadChecklistResult,
)
from app.manual_url_story.schema import (
    ManualUrlDemoExecutionResult,
    ManualUrlStoryExecutionResult,
    UrlQualityGateResult,
)
from app.performance_feedback.schema import (
    AutoRecommendationUpgradeResult,
    CostRevenueAnalysisResult,
    FounderGrowthIntelligenceResult,
    HookPerformanceResult,
    KpiIngestContractResult,
    KpiNormalizationResult,
    MasterFeedbackOrchestratorResult,
    TemplateEvolutionResult,
)
from app.production_acceleration.schema import (
    AssetDownloaderResult,
    BatchTopicRunnerResult,
    CostSnapshotResult,
    DemoVideoAutomationResult,
    FounderLocalDashboardResult,
    SceneStitcherResult,
    SubtitleDraftResult,
    ThumbnailExtractResult,
    ViralPrototypePresetsResult,
    VoiceRegistryResult,
)
from app.cash_optimization.schema import CashOptimizationLayerResult
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


class NarrativeSubscores(BaseModel):
    """BA 9.12 — Teilscores 0–100 (heuristisch)."""

    hook_curiosity_score: int = Field(ge=0, le=100)
    emotional_pull_score: int = Field(ge=0, le=100)
    escalation_score: int = Field(ge=0, le=100)
    chapter_progression_score: int = Field(ge=0, le=100)
    thumbnail_potential_score: int = Field(ge=0, le=100)


class NarrativeScoreResult(BaseModel):
    """BA 9.12 — Erzählerische Zugkraft (regelbasiert, kein LLM)."""

    score: int = Field(ge=0, le=100)
    status: Literal["strong", "moderate", "weak"] = Field(
        ...,
        description='≥80 strong, 50–79 moderate, <50 weak (Aggregat-Score).',
    )
    subscores: NarrativeSubscores
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    checked_dimensions: List[str] = Field(default_factory=list)


class ChapterOutlineItem(BaseModel):
    title: str
    summary: str


class PromptPlanQualityResult(BaseModel):
    """BA 9.11 — Heuristische Produktionsreife eines Prompt-Plans."""

    score: int = Field(ge=0, le=100, description="0–100, aggregiert aus Checks.")
    status: Literal["pass", "warning", "fail"] = Field(
        ...,
        description='Aggregat: "fail" bei Blockern, sonst "warning" bei strukturellen Hinweisen.',
    )
    warnings: List[str] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)
    checked_fields: List[str] = Field(default_factory=list)


class PerformanceRecord(BaseModel):
    """
    BA 9.13 — Logisches „performance_records“-Dokument (V1 ohne Firestore-Pflicht).

    Spätere YouTube-/Produktions-KPIs optional; Identifikation zu Jobs/Videos vorbereitet.
    """

    id: str
    production_job_id: str = ""
    script_job_id: Optional[str] = None
    video_id: Optional[str] = None
    template_type: str = ""
    video_template: Optional[str] = None
    narrative_archetype_id: Optional[str] = None
    hook_type: Optional[str] = None
    hook_score: Optional[float] = None
    quality_score: Optional[int] = None
    quality_status: Optional[str] = None
    narrative_score: Optional[int] = None
    narrative_status: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    youtube_video_id: Optional[str] = None
    impressions: Optional[float] = None
    views: Optional[float] = None
    ctr: Optional[float] = None
    average_view_duration: Optional[float] = None
    retention_percent: Optional[float] = None
    watch_time_minutes: Optional[float] = None
    rpm: Optional[float] = None
    estimated_revenue: Optional[float] = None
    production_cost_estimate: Optional[float] = None
    profit_estimate: Optional[float] = None


class PerformanceSnapshotResult(BaseModel):
    """BA 9.13 — Auswertungs-Snapshot einer Performance-Zeile (heuristisch V1)."""

    status: Literal["pending_data", "partial_data", "ready"] = Field(
        ...,
        description="pending_data — keine KPIs; partial_data — Teilmenge; ready — Kern-KPIs vorhanden.",
    )
    learning_score: Optional[float] = Field(
        default=None,
        description="0–100 sobald ausreichend KPI-Material; sonst None.",
    )
    notes: List[str] = Field(default_factory=list)


class TemplatePerformanceSummary(BaseModel):
    """BA 9.13 — Aggregat je Prompt-Template-Typ (rein rechnerisch)."""

    template_type: str
    record_count: int = Field(ge=0)
    avg_quality_score: Optional[float] = None
    avg_narrative_score: Optional[float] = None
    pending_kpi_count: int = Field(default=0, ge=0)
    avg_learning_score: Optional[float] = None


class PromptPlanReviewGateResult(BaseModel):
    """BA 9.14 — Operative Ampel aus Quality, Narrative und optional Performance-Signalen."""

    decision: Literal["go", "revise", "stop"] = Field(
        ...,
        description="go — weiter; revise — nachbessern; stop — nicht produktionsfähig.",
    )
    confidence: int = Field(ge=0, le=100)
    reasons: List[str] = Field(default_factory=list)
    required_actions: List[str] = Field(default_factory=list)
    checked_signals: List[str] = Field(default_factory=list)


RepairSuggestionCategory = Literal[
    "hook",
    "chapters",
    "scenes",
    "voice",
    "thumbnail",
    "narrative",
    "quality",
    "performance",
]
RepairSuggestionPriority = Literal["high", "medium", "low"]


class PromptRepairSuggestion(BaseModel):
    """BA 9.15 — Einzelner Reparaturhinweis."""

    category: RepairSuggestionCategory
    priority: RepairSuggestionPriority
    issue: str
    suggestion: str


class PromptRepairSuggestionsResult(BaseModel):
    """BA 9.15 — Gesamtbundle konkreter Reparatur-To-dos."""

    status: Literal["not_needed", "suggestions_available"]
    suggestions: List[PromptRepairSuggestion] = Field(default_factory=list)
    summary: str = ""
    checked_sources: List[str] = Field(default_factory=list)


class HumanApprovalState(BaseModel):
    """BA 9.17 — Vorbereitete menschliche Freigabe (read-only V1, keine Persistenz)."""

    status: Literal["pending_review", "approved", "rejected", "needs_revision"]
    recommended_action: Literal["approve", "review", "revise", "reject"]
    approval_required: bool = True
    reasons: List[str] = Field(default_factory=list)
    checklist: List[str] = Field(default_factory=list)
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_reason: Optional[str] = None


class ProductionHandoffPackage(BaseModel):
    """BA 9.18 — Kompaktes Übergabepaket für Downstream-Produktion (ohne Produktionsstart)."""

    template_type: str = ""
    video_template: str = ""
    narrative_archetype_id: str = ""
    hook_type: str = ""
    hook_score: float = Field(default=0.0, ge=0.0, le=10.0)
    quality_status: str = ""
    quality_score: int = Field(default=0, ge=0, le=100)
    narrative_status: str = ""
    narrative_score: int = Field(default=0, ge=0, le=100)
    review_decision: str = ""
    approval_status: str = ""
    hook: str = ""
    chapter_outline: List[ChapterOutlineItem] = Field(default_factory=list)
    scene_prompts: List[str] = Field(default_factory=list)
    voice_style: str = ""
    thumbnail_angle: str = ""


class ProductionHandoffResult(BaseModel):
    """BA 9.18 — Ergebnis der Production-Handoff-Zusammenstellung."""

    handoff_status: Literal["ready", "blocked", "needs_review", "needs_revision"]
    production_ready: bool = False
    summary: str = ""
    package: ProductionHandoffPackage = Field(default_factory=ProductionHandoffPackage)
    warnings: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)
    checked_sources: List[str] = Field(default_factory=list)


class ProductionExportPayload(BaseModel):
    """BA 9.19 — Maschinenlesbarer Export-Inhalt (ohne Secrets, ohne Binärdaten)."""

    prompt_plan_id: Optional[str] = None
    template_type: str = ""
    video_template: str = ""
    narrative_archetype_id: str = ""
    hook_type: str = ""
    hook_score: float = Field(default=0.0, ge=0.0, le=10.0)
    hook: str = ""
    chapter_outline: List[ChapterOutlineItem] = Field(default_factory=list)
    scene_prompts: List[str] = Field(default_factory=list)
    voice_style: str = ""
    thumbnail_angle: str = ""
    quality_result: Optional[PromptPlanQualityResult] = None
    narrative_score_result: Optional[NarrativeScoreResult] = None
    review_gate_result: Optional[PromptPlanReviewGateResult] = None
    human_approval_state: Optional[HumanApprovalState] = None
    production_handoff_result: Optional[ProductionHandoffResult] = None


class ProductionExportContractResult(BaseModel):
    """BA 9.19 — Versionierter Export-Vertrag für Downstream-Produktion."""

    export_contract_version: str = Field(
        default="9.19-v1",
        description="Fixe Vertragsversion für Parser-Kompatibilität.",
    )
    handoff_package_id: str = ""
    export_ready: bool = False
    export_status: Literal["ready", "blocked", "needs_review", "needs_revision"]
    summary: str = ""
    export_payload: ProductionExportPayload = Field(default_factory=ProductionExportPayload)
    warnings: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)
    checked_sources: List[str] = Field(default_factory=list)


ProviderRoleType = Literal["image", "video", "voice", "thumbnail", "render"]
ProviderPackageStatus = Literal["ready", "incomplete", "blocked"]
ProviderPackagingOverallStatus = Literal["ready", "partial", "blocked"]


class ProviderPackage(BaseModel):
    """BA 9.20 — Einzelnes Provider-Mapping (Stub, ohne echte API-Calls)."""

    provider_type: ProviderRoleType
    provider_name: str
    package_status: ProviderPackageStatus
    payload: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class ProviderPackagingResult(BaseModel):
    """BA 9.20 — Gesamtergebnis Provider-Packaging."""

    packaging_status: ProviderPackagingOverallStatus
    packages: List[ProviderPackage] = Field(default_factory=list)
    checked_sources: List[str] = Field(default_factory=list)


class ProviderExportProviders(BaseModel):
    """BA 9.21 — Benannte Provider-Slots im Bundle."""

    image_package: ProviderPackage
    video_package: ProviderPackage
    voice_package: ProviderPackage
    thumbnail_package: ProviderPackage
    render_package: ProviderPackage


class ProviderExportBundleResult(BaseModel):
    """BA 9.21 — Zentrales Multi-Provider-Exportpaket."""

    bundle_version: str = Field(default="9.21-v1")
    bundle_status: ProviderPackagingOverallStatus = "blocked"
    bundle_id: str = ""
    providers: ProviderExportProviders
    export_summary: str = ""
    warnings: List[str] = Field(default_factory=list)


PackageValidationStatus = Literal["pass", "warning", "fail"]
ProductionSafetyLevel = Literal["safe", "review", "unsafe"]


class PackageValidationResult(BaseModel):
    """BA 9.22 — Validierung des Provider-Export-Bundles."""

    validation_status: PackageValidationStatus = "fail"
    production_safety: ProductionSafetyLevel = "unsafe"
    missing_components: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


TimelineRole = Literal["hook", "setup", "build", "escalation", "climax", "outro"]
TimelineOverallStatus = Literal["ready", "partial", "blocked"]
VideoLengthCategory = Literal["short", "medium", "long"]


class TimelineScene(BaseModel):
    """BA 9.23 — Eine Szene auf der Produktionstimeline."""

    scene_index: int = Field(ge=0)
    chapter_title: str = ""
    scene_prompt: str = ""
    estimated_duration_seconds: int = Field(ge=0)
    timeline_role: TimelineRole
    provider_targets: List[str] = Field(default_factory=list)


class ProductionTimelineResult(BaseModel):
    """BA 9.23 — Zeitliche Struktur für Downstream-Render."""

    timeline_status: TimelineOverallStatus = "blocked"
    total_estimated_duration_seconds: int = Field(default=0, ge=0)
    target_video_length_category: VideoLengthCategory = "short"
    scenes: List[TimelineScene] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


CostProjectionStatus = Literal["estimated", "partial", "insufficient_data"]


class ProviderCostEstimate(BaseModel):
    """BA 9.24 — Grobkosten-Schätzung je Provider (EUR, heuristisch)."""

    provider_name: str
    estimated_units: float = Field(ge=0)
    estimated_cost_eur: float = Field(ge=0)
    notes: str = ""


class CostProjectionResult(BaseModel):
    """BA 9.24 — Aggregierte Kostenschätzung."""

    cost_status: CostProjectionStatus = "insufficient_data"
    total_estimated_cost_eur: float = Field(default=0.0, ge=0)
    estimated_cost_per_minute: float = Field(default=0.0, ge=0)
    provider_costs: List[ProviderCostEstimate] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


FinalReadinessDecision = Literal["ready_for_production", "ready_for_review", "not_ready"]


class FinalProductionReadinessResult(BaseModel):
    """BA 9.25 — Finale operative Produktionsfreigabe (ohne Startbefehl)."""

    readiness_decision: FinalReadinessDecision = "not_ready"
    readiness_score: int = Field(default=0, ge=0, le=100)
    production_blockers: List[str] = Field(default_factory=list)
    review_flags: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    summary: str = ""


TemplatePerformanceComparisonStatus = Literal["ready", "insufficient_data"]


class TemplatePerformanceEntry(BaseModel):
    """BA 9.26 — Aggregierte Kennzahl je Template aus PerformanceRecords."""

    template_type: str
    total_records: int = Field(ge=0)
    avg_quality_score: float = Field(default=0.0, ge=0.0, le=100.0)
    avg_narrative_score: float = Field(default=0.0, ge=0.0, le=100.0)
    avg_learning_score: float = Field(default=0.0, ge=0.0, le=100.0)
    overall_template_score: float = Field(default=0.0, ge=0.0, le=100.0)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)


class TemplatePerformanceComparisonResult(BaseModel):
    """BA 9.26 — Vergleich mehrerer Templates über historische Records."""

    comparison_status: TemplatePerformanceComparisonStatus = "insufficient_data"
    best_template_type: Optional[str] = None
    templates: List[TemplatePerformanceEntry] = Field(default_factory=list)
    insights: List[str] = Field(default_factory=list)


TemplateRecommendationBasis = Literal["topic_match", "historical_performance", "narrative_fit"]


class TemplateRecommendationResult(BaseModel):
    """BA 9.27 — Empfohlenes Template aus Topic + optionaler Historie."""

    recommended_template: str = ""
    confidence: int = Field(default=0, ge=0, le=100)
    recommendation_basis: TemplateRecommendationBasis = "topic_match"
    alternatives: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


ProviderStrategyOptimizationStatus = Literal["ready", "partial", "blocked"]
CostPriorityLevel = Literal["low_cost", "balanced", "premium"]


class ProviderStrategyOptimizerResult(BaseModel):
    """BA 9.28 — Heuristische Provider-Rollenwahl (ohne echte APIs)."""

    optimization_status: ProviderStrategyOptimizationStatus = "partial"
    recommended_image_provider: str = "Leonardo"
    recommended_video_provider: str = "Kling"
    recommended_voice_provider: str = "OpenAI / ElevenLabs (stub)"
    recommended_thumbnail_provider: str = "Thumbnail (stub)"
    cost_priority: CostPriorityLevel = "balanced"
    reasoning: List[str] = Field(default_factory=list)


ProductionOSDashboardStatus = Literal["ready", "degraded", "blocked"]


class ProductionOSDashboardResult(BaseModel):
    """BA 9.29 — Kompakte Founder-/Operator-Sicht auf Plan + Ops."""

    dashboard_status: ProductionOSDashboardStatus = "degraded"
    prompt_health_score: int = Field(default=0, ge=0, le=100)
    production_readiness_score: int = Field(default=0, ge=0, le=100)
    estimated_cost: float = Field(default=0.0, ge=0.0)
    recommended_template: str = ""
    recommended_provider_strategy: str = ""
    top_risks: List[str] = Field(default_factory=list)
    top_strengths: List[str] = Field(default_factory=list)
    executive_summary: str = ""


MasterOrchestrationStatus = Literal["ready", "review", "blocked"]
LaunchRecommendation = Literal["proceed", "revise", "hold"]


class MasterOrchestrationResult(BaseModel):
    """BA 9.30 — End-to-End Story-to-Production Zusammenfassung (ohne Startbefehl)."""

    orchestration_status: MasterOrchestrationStatus = "review"
    story_input_summary: str = ""
    prompt_planning_summary: str = ""
    production_summary: str = ""
    provider_summary: str = ""
    risk_summary: str = ""
    launch_recommendation: LaunchRecommendation = "revise"
    final_founder_note: str = ""


class PromptPlanRequest(BaseModel):
    """Topic-getriebene Planung; optional Anker für Hook-Engine (BA 9.2)."""

    topic: str = Field(..., min_length=1)
    title: str = ""
    source_summary: str = ""
    template_override: Optional[str] = Field(
        default=None,
        description="Erzwingt template_key aus prompt_planning JSON (z. B. true_crime, mystery_history).",
    )
    include_performance_record: bool = Field(
        default=False,
        description="BA 9.13 — wenn True, wird ein PerformanceRecord-Entwurf mitgebaut (kein Firestore-Write).",
    )
    production_job_id: str = Field(default="", description="Optional für PerformanceRecord.")
    script_job_id: Optional[str] = Field(default=None, description="Optional für PerformanceRecord.")
    video_id: Optional[str] = Field(default=None, description="Optional für PerformanceRecord.")
    performance_record_id: Optional[str] = Field(
        default=None,
        description="Eigene ID; sonst UUID.",
    )
    allow_live_provider_execution: bool = Field(
        default=False,
        description=(
            "BA 11.x — nur wenn True dürfen Leonardo/Voice echte HTTP-Versuche starten "
            "(Safety + Secrets + Aktivierung vorausgesetzt)."
        ),
    )
    kpi_source_type: Literal["manual", "csv", "youtube_api_stub", "unknown"] = Field(
        default="unknown",
        description="BA 14.x — KPI-Importquelle, V1 ohne verpflichtende Live-API.",
    )
    external_kpi_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="BA 14.x — optionale manuelle/CSV/API-Stub-KPIs.",
    )
    manual_source_url: str = Field(
        default="",
        description=(
            "Manual URL Story Execution — wenn gesetzt: Extraktion + Rewrite wie /generate-script, "
            "gespeist in Kapitel/Hook/Szenen-Prompts (additiv)."
        ),
    )
    manual_url_duration_minutes: int = Field(default=10, ge=1, le=180)
    manual_url_target_language: str = Field(default="de")
    manual_url_video_template: str = Field(
        default="generic",
        description="Story-Template für den gemeinsamen Skriptpfad; bei template_override wird dieses bevorzugt.",
    )
    manual_url_template_conformance_level: str = Field(
        default="warn",
        description="Wie bei /generate-script: off | warn | strict.",
    )
    manual_url_rewrite_mode: str = Field(
        default="",
        description=(
            "BA 15.6 — optional: documentary | emotional | mystery | viral. "
            "Ohne template_override: Preset für Video-Rewrite + Prompt-Template-Zwang; "
            "Hook-Engine nutzt Modus-Tonalität."
        ),
    )


class PromptRepairPreviewResult(BaseModel):
    """BA 9.16 — Vorschau eines reparierten Plans ohne Überschreibung des Originals."""

    status: Literal["not_needed", "preview_available", "not_possible"]
    preview_plan: Optional["ProductionPromptPlan"] = None
    applied_repairs: List[str] = Field(default_factory=list)
    remaining_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ProductionPromptPlan(BaseModel):
    """Deterministisches Produktions-Blueprint — erweiterbar, kein LLM-Pflichtfeld."""

    template_type: str
    tone: str
    hook: str
    chapter_outline: List[ChapterOutlineItem]
    scene_prompts: List[str]
    voice_style: str
    thumbnail_angle: str
    warnings: List[str] = Field(default_factory=list)
    video_template: str = Field(
        default="generic",
        description="Gemappt auf story_engine video_template für Hook-Engine / Downstream.",
    )
    narrative_archetype_id: str = ""
    hook_type: str = ""
    hook_score: float = Field(default=0.0, ge=0.0, le=10.0)
    allow_live_provider_execution: bool = Field(
        default=False,
        description="BA 11.x — Request-Flag für optionale Live-HTTP (Standard aus).",
    )
    kpi_source_type: Literal["manual", "csv", "youtube_api_stub", "unknown"] = Field(
        default="unknown",
        description="BA 14.x — KPI-Importquelle.",
    )
    external_kpi_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="BA 14.x — optionale manuelle/CSV/API-Stub-KPIs.",
    )
    quality_result: Optional[PromptPlanQualityResult] = Field(
        default=None,
        description="BA 9.11 — gesetzt von build_production_prompt_plan / API.",
    )
    narrative_score_result: Optional[NarrativeScoreResult] = Field(
        default=None,
        description="BA 9.12 — Narrative Scoring; gesetzt von build_production_prompt_plan / API.",
    )
    performance_record: Optional[PerformanceRecord] = Field(
        default=None,
        description="BA 9.13 — nur wenn PromptPlanRequest.include_performance_record gesetzt.",
    )
    review_gate_result: Optional[PromptPlanReviewGateResult] = Field(
        default=None,
        description="BA 9.14 — Review Gate; gesetzt von build_production_prompt_plan.",
    )
    repair_suggestions_result: Optional[PromptRepairSuggestionsResult] = Field(
        default=None,
        description="BA 9.15 — Reparaturvorschläge; gesetzt von build_production_prompt_plan.",
    )
    repair_preview_result: Optional[PromptRepairPreviewResult] = Field(
        default=None,
        description="BA 9.16 — deterministische Repair-Vorschau; gesetzt von build_production_prompt_plan.",
    )
    human_approval_state: Optional[HumanApprovalState] = Field(
        default=None,
        description="BA 9.17 — Human-Approval-Vorbereitung; gesetzt von build_production_prompt_plan.",
    )
    production_handoff_result: Optional[ProductionHandoffResult] = Field(
        default=None,
        description="BA 9.18 — Production-Handoff-Paket; gesetzt von build_production_prompt_plan.",
    )
    production_export_contract_result: Optional[ProductionExportContractResult] = Field(
        default=None,
        description="BA 9.19 — Production Export Contract; gesetzt von build_production_prompt_plan.",
    )
    provider_packaging_result: Optional[ProviderPackagingResult] = Field(
        default=None,
        description="BA 9.20 — Provider-Packaging; gesetzt von build_production_prompt_plan.",
    )
    provider_export_bundle_result: Optional[ProviderExportBundleResult] = Field(
        default=None,
        description="BA 9.21 — Multi-Provider Export Bundle; gesetzt von build_production_prompt_plan.",
    )
    package_validation_result: Optional[PackageValidationResult] = Field(
        default=None,
        description="BA 9.22 — Package-Validierung; gesetzt von build_production_prompt_plan.",
    )
    production_timeline_result: Optional[ProductionTimelineResult] = Field(
        default=None,
        description="BA 9.23 — Produktionstimeline; gesetzt von build_production_prompt_plan.",
    )
    cost_projection_result: Optional[CostProjectionResult] = Field(
        default=None,
        description="BA 9.24 — Kostenschätzung; gesetzt von build_production_prompt_plan.",
    )
    final_readiness_gate_result: Optional[FinalProductionReadinessResult] = Field(
        default=None,
        description="BA 9.25 — Finale Readiness; gesetzt von build_production_prompt_plan.",
    )
    template_performance_comparison_result: Optional[TemplatePerformanceComparisonResult] = Field(
        default=None,
        description="BA 9.26 — Template-Vergleich aus optionalen PerformanceRecords.",
    )
    template_recommendation_result: Optional[TemplateRecommendationResult] = Field(
        default=None,
        description="BA 9.27 — Template-Empfehlung; gesetzt von build_production_prompt_plan.",
    )
    provider_strategy_optimizer_result: Optional[ProviderStrategyOptimizerResult] = Field(
        default=None,
        description="BA 9.28 — Provider-Strategie-Heuristik; gesetzt von build_production_prompt_plan.",
    )
    production_os_dashboard_result: Optional[ProductionOSDashboardResult] = Field(
        default=None,
        description="BA 9.29 — Production-OS-Dashboard-Kurzsummary; gesetzt von build_production_prompt_plan.",
    )
    master_orchestration_result: Optional[MasterOrchestrationResult] = Field(
        default=None,
        description="BA 9.30 — Master-Orchestrierung; gesetzt von build_production_prompt_plan.",
    )
    production_connector_suite_result: Optional[ProductionConnectorSuiteResult] = Field(
        default=None,
        description="BA 10.0 — Connector Dry-Run Suite über Export-Bundle; gesetzt von build_production_prompt_plan.",
    )
    connector_auth_contracts_result: Optional[ConnectorAuthContractsResult] = Field(
        default=None,
        description="BA 10.1 — Auth-Contract-Matrix (keine Secret-Werte); gesetzt von build_production_prompt_plan.",
    )
    provider_execution_queue_result: Optional[ProviderExecutionQueueResult] = Field(
        default=None,
        description="BA 10.2 — deterministische Provider-Job-Queue; gesetzt von build_production_prompt_plan.",
    )
    live_execution_guard_result: Optional[LiveExecutionGuardResult] = Field(
        default=None,
        description="BA 10.4 — Live-Execution-Gate; gesetzt von build_production_prompt_plan.",
    )
    api_activation_control_result: Optional[APIActivationControlResult] = Field(
        default=None,
        description="BA 10.5 — API-Aktivierungs-Matrix; gesetzt von build_production_prompt_plan.",
    )
    execution_policy_result: Optional[ExecutionPolicyResult] = Field(
        default=None,
        description="BA 10.6 — Policy / Kill-Switch; gesetzt von build_production_prompt_plan.",
    )
    provider_job_runner_mock_result: Optional[ProviderJobRunnerMockResult] = Field(
        default=None,
        description="BA 10.8 — Mock-Job-Runner; gesetzt von build_production_prompt_plan.",
    )
    asset_status_tracker_result: Optional[AssetStatusTrackerResult] = Field(
        default=None,
        description="BA 10.9 — Asset-Status-Tracker; gesetzt von build_production_prompt_plan.",
    )
    production_run_summary_result: Optional[ProductionRunSummaryResult] = Field(
        default=None,
        description="BA 10.10 — Production-Run-Summary; gesetzt von build_production_prompt_plan.",
    )
    live_provider_safety_result: Optional[LiveProviderSafetyResult] = Field(
        default=None,
        description="BA 11.0 — Live-Provider-Safety; gesetzt von build_production_prompt_plan.",
    )
    runtime_secret_check_result: Optional[RuntimeSecretCheckResult] = Field(
        default=None,
        description="BA 11.1 — ENV-Presence für Provider; gesetzt von build_production_prompt_plan.",
    )
    leonardo_live_result: Optional[LiveConnectorExecutionResult] = Field(
        default=None,
        description="BA 11.2 — optionaler Leonardo-Live-Versuch.",
    )
    voice_live_result: Optional[LiveConnectorExecutionResult] = Field(
        default=None,
        description="BA 11.3 — optionaler Voice-Live-Versuch.",
    )
    asset_persistence_result: Optional[AssetPersistenceResult] = Field(
        default=None,
        description="BA 11.4 — Asset-Persistenz-/Download-Kontrakt.",
    )
    provider_error_recovery_result: Optional[ProviderErrorRecoveryResult] = Field(
        default=None,
        description="BA 11.5 — Recovery-Empfehlung nach Live-Versuchen.",
    )
    master_asset_manifest_result: Optional[MasterAssetManifestResult] = Field(
        default=None,
        description="BA 12.0 — Master-Asset-Manifest; gesetzt von build_production_prompt_plan.",
    )
    multi_asset_assembly_result: Optional[MultiAssetAssemblyResult] = Field(
        default=None,
        description="BA 12.1 — Asset-Gruppierung und Coverage.",
    )
    final_timeline_result: Optional[FinalTimelineResult] = Field(
        default=None,
        description="BA 12.2 — finale Timeline mit Asset-Links.",
    )
    voice_scene_alignment_result: Optional[VoiceSceneAlignmentResult] = Field(
        default=None,
        description="BA 12.3 — Voice-/Scene-Abgleich.",
    )
    render_instruction_package_result: Optional[RenderInstructionPackageResult] = Field(
        default=None,
        description="BA 12.4 — Render-Instructions für Downstream-Systeme.",
    )
    downloadable_production_bundle_result: Optional[DownloadableProductionBundleResult] = Field(
        default=None,
        description="BA 12.5 — downloadbares Production-Bundle als Struktur.",
    )
    human_final_review_package_result: Optional[HumanFinalReviewPackageResult] = Field(
        default=None,
        description="BA 12.6 — finales Human-Review-Paket.",
    )
    metadata_master_package_result: Optional[MetadataMasterPackageResult] = Field(
        default=None,
        description="BA 13.0 — Publishing-Metadaten-SoT.",
    )
    metadata_optimizer_result: Optional[MetadataOptimizerResult] = Field(
        default=None,
        description="BA 13.1 — Titel-/Beschreibung-/Tag-Optimierung.",
    )
    thumbnail_variant_pack_result: Optional[ThumbnailVariantPackResult] = Field(
        default=None,
        description="BA 13.2 — Thumbnail-Variantenpaket.",
    )
    upload_checklist_result: Optional[UploadChecklistResult] = Field(
        default=None,
        description="BA 13.3 — Upload-Readiness-Checkliste ohne Upload.",
    )
    schedule_plan_result: Optional[SchedulePlanResult] = Field(
        default=None,
        description="BA 13.4 — heuristischer Veröffentlichungsplan ohne Scheduler.",
    )
    publishing_readiness_gate_result: Optional[PublishingReadinessGateResult] = Field(
        default=None,
        description="BA 13.5 — Publishing-Readiness-Gate ohne externen Upload.",
    )
    founder_publishing_summary_result: Optional[FounderPublishingSummaryResult] = Field(
        default=None,
        description="BA 13.6 — Founder-/Operator-Publishing-Summary.",
    )
    kpi_ingest_contract_result: Optional[KpiIngestContractResult] = Field(
        default=None,
        description="BA 14.0 — KPI-Importvertrag.",
    )
    kpi_normalization_result: Optional[KpiNormalizationResult] = Field(
        default=None,
        description="BA 14.1 — normalisierte KPI-SoT.",
    )
    hook_performance_result: Optional[HookPerformanceResult] = Field(
        default=None,
        description="BA 14.2 — Hook-Performance-Analyse.",
    )
    template_evolution_result: Optional[TemplateEvolutionResult] = Field(
        default=None,
        description="BA 14.3 — Template-/Narrativ-Evolution.",
    )
    cost_revenue_analysis_result: Optional[CostRevenueAnalysisResult] = Field(
        default=None,
        description="BA 14.4 — Kosten-/Erlös-Analyse.",
    )
    auto_recommendation_upgrade_result: Optional[AutoRecommendationUpgradeResult] = Field(
        default=None,
        description="BA 14.5 — Recommendation Upgrade aus Performance.",
    )
    founder_growth_intelligence_result: Optional[FounderGrowthIntelligenceResult] = Field(
        default=None,
        description="BA 14.6 — Founder Growth Intelligence.",
    )
    master_feedback_orchestrator_result: Optional[MasterFeedbackOrchestratorResult] = Field(
        default=None,
        description="BA 14.7 — Master Feedback Orchestrator.",
    )
    demo_video_automation_result: Optional[DemoVideoAutomationResult] = Field(
        default=None,
        description="BA 15.0 — lokale Demo-Video-Automation.",
    )
    asset_downloader_result: Optional[AssetDownloaderResult] = Field(
        default=None,
        description="BA 15.1 — lokaler Asset-Download-Plan.",
    )
    voice_registry_result: Optional[VoiceRegistryResult] = Field(
        default=None,
        description="BA 15.2 — sichere Voice Registry.",
    )
    scene_stitcher_result: Optional[SceneStitcherResult] = Field(
        default=None,
        description="BA 15.3 — Scene Stitcher für lokale Demo-Produktion.",
    )
    subtitle_draft_result: Optional[SubtitleDraftResult] = Field(
        default=None,
        description="BA 15.4 — Subtitle Draft ohne Burn-in.",
    )
    thumbnail_extract_result: Optional[ThumbnailExtractResult] = Field(
        default=None,
        description="BA 15.5 — Thumbnail-Extract-Plan aus lokalem Demo-Video.",
    )
    founder_local_dashboard_result: Optional[FounderLocalDashboardResult] = Field(
        default=None,
        description="BA 15.6 — lokales Founder-Dashboard.",
    )
    batch_topic_runner_result: Optional[BatchTopicRunnerResult] = Field(
        default=None,
        description="BA 15.7 — Batch Topic Runner für Demo-Produktion.",
    )
    cost_snapshot_result: Optional[CostSnapshotResult] = Field(
        default=None,
        description="BA 15.8 — Kosten-Snapshot für Demo-Produktion.",
    )
    viral_prototype_presets_result: Optional[ViralPrototypePresetsResult] = Field(
        default=None,
        description="BA 15.9 — Viral Prototype Presets.",
    )
    revenue_model_result: Optional[RevenueModelResult] = Field(
        default=None,
        description="BA 16.0 — Revenue Model.",
    )
    channel_portfolio_result: Optional[ChannelPortfolioResult] = Field(
        default=None,
        description="BA 16.1 — Channel Portfolio.",
    )
    multi_platform_strategy_result: Optional[MultiPlatformStrategyResult] = Field(
        default=None,
        description="BA 16.2 — Multi-Platform Strategy.",
    )
    opportunity_scanning_result: Optional[OpportunityScanningResult] = Field(
        default=None,
        description="BA 16.3 — Opportunity Scanning.",
    )
    founder_kpi_result: Optional[FounderKpiResult] = Field(
        default=None,
        description="BA 16.4 — Founder KPI.",
    )
    scale_blueprint_result: Optional[ScaleBlueprintResult] = Field(
        default=None,
        description="BA 16.5 — Scale Blueprint.",
    )
    sponsorship_readiness_result: Optional[SponsorshipReadinessResult] = Field(
        default=None,
        description="BA 16.6 — Sponsorship Readiness.",
    )
    content_investment_plan_result: Optional[ContentInvestmentPlanResult] = Field(
        default=None,
        description="BA 16.7 — Content Investment Plan.",
    )
    scale_risk_register_result: Optional[ScaleRiskRegisterResult] = Field(
        default=None,
        description="BA 16.8 — Scale Risk Register.",
    )
    monetization_scale_summary_result: Optional[MonetizationScaleSummaryResult] = Field(
        default=None,
        description="BA 16.9 — Monetization & Scale Summary.",
    )
    manual_url_story_execution_result: Optional[ManualUrlStoryExecutionResult] = Field(
        default=None,
        description=(
            "Manual URL Story Execution V1 — Kernpfad 15.0–15.4 (Intake, Extraktion, Rewrite, Asset-Prompts, Demo-Hinweis); "
            "nicht identisch mit BA 15.0–15.9 Production Acceleration Feldern."
        ),
    )
    manual_url_quality_gate_result: Optional[UrlQualityGateResult] = Field(
        default=None,
        description="BA 15.7 — heuristisches URL-Quality-Gate bei manual_source_url.",
    )
    manual_url_demo_execution_result: Optional[ManualUrlDemoExecutionResult] = Field(
        default=None,
        description="BA 15.5 — Leonardo/Voice/First-Demo Kommando-Hooks ohne Auto-Run.",
    )
    cash_optimization_layer_result: Optional[CashOptimizationLayerResult] = Field(
        default=None,
        description=(
            "Cash Optimization CO 16.0–16.4 — Founder Profit Filter bei manual_source_url; "
            "nicht identisch mit monetization_scale BA 16.0–16.9."
        ),
    )
