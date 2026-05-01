"""Watchlist-spezifische Request-/Response-Modelle (Phase 5 Watchlist — Jobs, Skript-Persistenz)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Any, Dict, List, Literal, Optional

from app.models import (
    Chapter,
    ReviewIssue,
    ReviewRecommendation,
    ReviewScriptResponse,
    SimilarityFlag,
    TemplateConformanceLevelLiteral,
)

ChannelStatusLiteral = Literal["active", "paused", "error"]
CheckIntervalLiteral = Literal["manual", "hourly", "daily", "weekly"]


class WatchlistChannelCreateRequest(BaseModel):
    channel_url: str = Field(..., min_length=1)
    check_interval: CheckIntervalLiteral = "manual"
    max_results: int = Field(default=5, ge=1, le=50)
    auto_generate_script: bool = False
    auto_review_script: bool = True
    target_language: str = "de"
    duration_minutes: int = Field(default=10, ge=1, le=60)
    min_score: int = Field(default=40, ge=0, le=100)
    ignore_shorts: bool = True
    notes: str = ""
    video_template: str = Field(
        default="generic",
        description="BA 9: Template für spätere Script-Jobs (generic, true_crime, …).",
    )
    template_conformance_level: TemplateConformanceLevelLiteral = Field(
        default="warn",
        description="BA 9.3: Template-Conformance auf Script-Jobs dieses Kanals.",
    )


    @field_validator("channel_url")
    @classmethod
    def channel_url_strip(cls, v: str) -> str:
        s = (v or "").strip()
        return s


class WatchlistChannel(BaseModel):
    id: str
    channel_url: str
    channel_id: str
    channel_name: str
    status: ChannelStatusLiteral = "active"
    check_interval: CheckIntervalLiteral = "manual"
    max_results: int = Field(..., ge=1, le=50)
    auto_generate_script: bool = False
    auto_review_script: bool = True
    target_language: str = "de"
    duration_minutes: int = Field(..., ge=1, le=60)
    min_score: int = Field(..., ge=0, le=100)
    ignore_shorts: bool = True
    created_at: str
    updated_at: str
    last_checked_at: Optional[str] = None
    last_success_at: Optional[str] = None
    last_error: str = ""
    notes: str = ""
    video_template: str = "generic"
    template_conformance_level: TemplateConformanceLevelLiteral = "warn"


class CreateWatchlistChannelResponse(BaseModel):
    channel: Optional[WatchlistChannel] = None
    warnings: List[str] = Field(default_factory=list)


class ListWatchlistChannelsResponse(BaseModel):
    channels: List[WatchlistChannel] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


ProcessedVideoStatusLiteral = Literal["seen", "skipped", "script_generated"]
ChannelCheckItemStatusLiteral = Literal["new", "known", "skipped"]

ScriptJobStatusLiteral = Literal[
    "pending",
    "running",
    "completed",
    "failed",
    "skipped",
    "stuck",
]
SourceTypeYoutubeTranscript = Literal["youtube_transcript"]


class ProcessedVideo(BaseModel):
    id: str
    channel_id: str
    video_id: str
    video_url: str
    title: str
    published_at: str
    first_seen_at: str
    status: ProcessedVideoStatusLiteral
    score: int = 0
    reason: str = ""
    is_short: bool = False
    skip_reason: str = ""
    input_quality_status: str = ""
    script_job_id: Optional[str] = None
    generated_script_id: Optional[str] = None
    review_result_id: Optional[str] = None
    last_error: str = ""


class ChannelCheckVideoItem(BaseModel):
    title: str = ""
    url: str = ""
    video_id: str = ""
    published_at: str = ""
    score: int = 0
    reason: str = ""
    is_short: bool = False
    status: ChannelCheckItemStatusLiteral = "new"
    skip_reason: str = ""
    input_quality_status: str = ""


class ScriptJob(BaseModel):
    id: str
    video_id: str
    channel_id: str
    video_url: str
    status: ScriptJobStatusLiteral
    source_type: SourceTypeYoutubeTranscript = "youtube_transcript"
    target_language: str = "de"
    duration_minutes: int = Field(default=10, ge=1, le=60)
    video_template: str = "generic"
    template_conformance_level: TemplateConformanceLevelLiteral = "warn"
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: str = ""
    error_code: str = ""
    input_quality_status: str = ""
    generated_script_id: Optional[str] = None
    review_result_id: Optional[str] = None
    attempt_count: int = Field(default=0, ge=0)
    last_attempt_at: Optional[str] = None
    pipeline_step_retry_counts: Dict[str, int] = Field(default_factory=dict)


class CreatedScriptJobItem(BaseModel):
    """Kompakte Job-Infos in der Check-Antwort (Schritt 3)."""

    id: str
    video_id: str
    video_url: str
    status: ScriptJobStatusLiteral
    target_language: str = "de"
    duration_minutes: int = 10


class CheckWatchlistChannelResponse(BaseModel):
    channel_id: str
    new_videos: List[ChannelCheckVideoItem] = Field(default_factory=list)
    known_videos: List[ChannelCheckVideoItem] = Field(default_factory=list)
    skipped_videos: List[ChannelCheckVideoItem] = Field(default_factory=list)
    created_processed_videos: int = 0
    created_jobs: List[CreatedScriptJobItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ListWatchlistScriptJobsResponse(BaseModel):
    jobs: List[ScriptJob] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class GeneratedScript(BaseModel):
    """Persistiertes Skript (Firestore ``generated_scripts``; Kern wie ``GenerateScriptResponse`` + Meta)."""

    id: str
    script_job_id: str
    source_url: str
    source_type: SourceTypeYoutubeTranscript = "youtube_transcript"
    title: str
    hook: str
    chapters: List[Chapter] = Field(default_factory=list)
    full_script: str = ""
    sources: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    word_count: int = 0
    video_template: str = "generic"
    hook_type: str = ""
    hook_score: float = Field(default=0.0, ge=0.0, le=10.0)
    opening_style: str = ""
    created_at: str
    template_definition_version: str = ""
    template_conformance_gate: str = ""
    story_structure: Dict[str, Any] = Field(
        default_factory=dict,
        description="BA 9.3.3 Nebenkanal — deterministische Story-Metadaten, nicht Teil des Six-Field-Vertrags.",
    )
    rhythm_hints: Dict[str, Any] = Field(
        default_factory=dict,
        description="BA 9.4 Nebenkanal — Pacing/Rhythm-Hinweise.",
    )
    experiment_id: str = ""
    hook_variant_id: str = ""


class RunScriptJobResponse(BaseModel):
    job: ScriptJob
    script: Optional[GeneratedScript] = None
    warnings: List[str] = Field(default_factory=list)


PendingJobOutcomeLiteral = Literal["completed", "failed", "skipped"]


class PendingJobRunResultItem(BaseModel):
    """Ein Eintrag in der Pending-Runner-Ausführungsliste."""

    job_id: str
    outcome: PendingJobOutcomeLiteral
    warnings: List[str] = Field(default_factory=list)


class RunPendingScriptJobsResponse(BaseModel):
    checked_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    skipped_jobs: int = 0
    results: List[PendingJobRunResultItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class RunAutomationCycleRequest(BaseModel):
    channel_limit: int = Field(default=3, ge=1, le=50)
    job_limit: int = Field(default=3, ge=1, le=10)


class AutomationChannelResultItem(BaseModel):
    channel_id: str
    ok: bool = True
    created_jobs_from_check: int = 0
    new_videos_count: int = 0
    skipped_videos_count: int = 0
    warnings: List[str] = Field(default_factory=list)


class RunAutomationCycleResponse(BaseModel):
    checked_channels: int = 0
    created_jobs: int = 0
    run_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    warnings: List[str] = Field(default_factory=list)
    channel_results: List[AutomationChannelResultItem] = Field(default_factory=list)
    job_results: List[PendingJobRunResultItem] = Field(default_factory=list)


class ReviewGeneratedScriptJobResponse(BaseModel):
    """Antwort zur optionalen Reviewschicht nach erfolgreicher Skripterstellung (bewahrt Job-Status)."""

    job_id: str
    review: Optional[ReviewScriptResponse] = None
    warnings: List[str] = Field(default_factory=list)


class ReviewResultStored(BaseModel):
    """Firestore ``review_results`` — analog ReviewScriptResponse, mit Verknüpfungen."""

    id: str
    script_job_id: str
    generated_script_id: str
    source_url: str = ""
    risk_level: str = ""
    originality_score: int = Field(ge=0, le=100, default=0)
    similarity_flags: List[SimilarityFlag] = Field(default_factory=list)
    issues: List[ReviewIssue] = Field(default_factory=list)
    recommendations: List[ReviewRecommendation] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    created_at: str


ProductionJobStatusLiteral = Literal[
    "queued",
    "planning_ready",
    "assets_ready",
    "voice_ready",
    "editing_ready",
    "upload_ready",
    "published",
    "in_progress",
    "completed",
    "failed",
    "skipped",
    "stuck",
    "retryable",
    "partial_failed",
]


class ProductionJob(BaseModel):
    """Vorbereitungsphase für spätere Videoproduktion (eigene Collection)."""

    id: str
    generated_script_id: str
    script_job_id: str
    status: ProductionJobStatusLiteral = "queued"
    content_category: str = ""
    visual_style: str = ""
    narrator_style: str = ""
    thumbnail_prompt: str = ""
    created_at: str
    updated_at: str
    error: str = ""
    error_code: str = ""
    video_template: str = "generic"
    template_definition_version: str = ""
    pipeline_step_retry_counts: Dict[str, int] = Field(default_factory=dict)


class ProductionJobCreateRequest(BaseModel):
    content_category: str = ""
    visual_style: str = ""
    narrator_style: str = ""
    thumbnail_prompt: str = ""


class CreateProductionJobResponse(BaseModel):
    job: Optional[ProductionJob] = None
    created: bool = True
    warnings: List[str] = Field(default_factory=list)


class ListProductionJobsResponse(BaseModel):
    jobs: List[ProductionJob] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ProductionJobActionResponse(BaseModel):
    """Detail / Aktionen für ``production_jobs`` (kein Rendering)."""

    job: Optional[ProductionJob] = None
    warnings: List[str] = Field(default_factory=list)


SceneAssetTypeLiteral = Literal["generated", "stock", "b_roll"]
ScenePlanStatusLiteral = Literal["draft", "ready", "failed", "superseded"]
SceneMoodLiteral = Literal["neutral", "dramatic", "explainer"]


class Scene(BaseModel):
    """Eine Plan-Szene (BA 6.6), ohne Firestore-Vertragspflicht für Kern-Skript-API."""

    scene_number: int = Field(ge=1)
    title: str
    voiceover_text: str = ""
    visual_summary: str = ""
    duration_seconds: int = Field(default=1, ge=1)
    asset_type: SceneAssetTypeLiteral = "generated"
    mood: SceneMoodLiteral = "neutral"
    source_chapter_title: str = ""
    source_chapter_index: int = Field(default=-1, ge=-1)


class ScenePlan(BaseModel):
    """Firestore ``scene_plans`` — Doc-ID = ``production_job_id``."""

    id: str
    production_job_id: str
    generated_script_id: str
    script_job_id: str
    status: ScenePlanStatusLiteral = "draft"
    plan_version: int = Field(default=1, ge=1)
    source_fingerprint: str = ""
    scenes: List[Scene] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class ScenePlanGenerateResponse(BaseModel):
    """Generate-Endpoint: neuer Plan oder bestehender (idempotent)."""

    scene_plan: Optional[ScenePlan] = None
    warnings: List[str] = Field(default_factory=list)


class ScenePlanGetResponse(BaseModel):
    """GET einzelner Szenenplan."""

    scene_plan: Optional[ScenePlan] = None
    warnings: List[str] = Field(default_factory=list)


SceneAssetStatusLiteral = Literal["draft", "ready", "failed"]
SceneAssetStyleProfileLiteral = Literal[
    "documentary",
    "news",
    "cinematic",
    "faceless_youtube",
    "true_crime",
]


class SceneAssetItem(BaseModel):
    """Eine Szene mit Prompt-Entwürfen (BA 6.7)."""

    scene_number: int = Field(ge=1)
    title: str
    voiceover_chunk: str = ""
    image_prompt: str = ""
    video_prompt: str = ""
    thumbnail_prompt: str = ""
    camera_direction: str = ""
    mood: str = ""
    asset_type: SceneAssetTypeLiteral = "generated"


class SceneAssets(BaseModel):
    """Firestore ``scene_assets`` — Document-ID = ``production_job_id``."""

    id: str
    production_job_id: str
    scene_plan_id: str
    generated_script_id: str
    script_job_id: str
    style_profile: SceneAssetStyleProfileLiteral = "documentary"
    status: SceneAssetStatusLiteral = "draft"
    asset_version: int = Field(default=1, ge=1)
    scenes: List[SceneAssetItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class SceneAssetsGenerateRequest(BaseModel):
    """Optionaler Body für POST …/scene-assets/generate."""

    style_profile: SceneAssetStyleProfileLiteral = "documentary"


class SceneAssetsGenerateResponse(BaseModel):
    scene_assets: Optional[SceneAssets] = None
    warnings: List[str] = Field(default_factory=list)


class SceneAssetsGetResponse(BaseModel):
    scene_assets: Optional[SceneAssets] = None
    warnings: List[str] = Field(default_factory=list)


VoicePlanStatusLiteral = Literal["ready", "failed"]
VoiceProfileLiteral = Literal["documentary", "news", "dramatic", "soft"]
TtsProviderHintLiteral = Literal["elevenlabs", "openai", "google", "generic"]
RenderManifestStatusLiteral = Literal["ready", "incomplete", "failed"]


class VoiceBlock(BaseModel):
    """Strukturierte VO-Zeilen aus einem ``voiceover_chunk`` (Scene-Asset)."""

    scene_number: int = Field(ge=1)
    title: str
    voice_text: str
    estimated_duration_seconds: int = Field(default=1, ge=1)
    speaker_style: str = ""
    pause_after_seconds: float = Field(default=0.25, ge=0.0)
    tts_provider_hint: TtsProviderHintLiteral = "generic"
    pronunciation_notes: str = ""


class VoicePlan(BaseModel):
    """Firestore ``voice_plans`` — Doc-ID = ``production_job_id``."""

    id: str
    production_job_id: str
    scene_assets_id: str
    generated_script_id: str
    script_job_id: str
    voice_profile: VoiceProfileLiteral = "documentary"
    status: VoicePlanStatusLiteral = "ready"
    voice_version: int = Field(default=1, ge=1)
    blocks: List[VoiceBlock] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class VoicePlanGenerateRequest(BaseModel):
    voice_profile: VoiceProfileLiteral = "documentary"


class VoicePlanGenerateResponse(BaseModel):
    voice_plan: Optional[VoicePlan] = None
    warnings: List[str] = Field(default_factory=list)


class VoicePlanGetResponse(BaseModel):
    voice_plan: Optional[VoicePlan] = None
    warnings: List[str] = Field(default_factory=list)


class VoiceSynthPreviewRequest(BaseModel):
    """Phase 7.2 Preview — keine Secrets im Body."""

    dry_run: bool = False
    max_blocks: int = Field(default=1, ge=1, le=5)
    voice: Optional[str] = None


class VoiceSynthPreviewChunk(BaseModel):
    scene_number: int = Field(ge=1)
    byte_length: int = Field(ge=0)
    content_type: str = "audio/mpeg"
    audio_base64: Optional[str] = None


class VoiceSynthPreviewResponse(BaseModel):
    chunks: List[VoiceSynthPreviewChunk] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class VoiceProductionFileRef(BaseModel):
    """Phase 7.7 — Verweis aus ``production_files`` (Typ voice) ins Render-Manifest/Export."""

    production_file_id: str = Field(min_length=1)
    scene_number: int = Field(ge=1)
    production_file_status: ProductionFileRecordStatusLiteral = "planned"
    synthesis_byte_length: int = Field(default=0, ge=0)
    storage_path: str = ""
    provider_name: ProviderNameLiteral = "generic"


class VoiceSynthCommitRequest(BaseModel):
    """Phase 7.3 — Voice-Synthese in ``production_files`` (keine Secrets im Body)."""

    dry_run: bool = False
    max_blocks: int = Field(default=50, ge=1, le=50)
    overwrite: bool = False
    voice: Optional[str] = None


class VoiceSynthCommitSceneResult(BaseModel):
    scene_number: int = Field(ge=1)
    production_file_id: str = ""
    file_status: str = ""
    synthesis_byte_length: int = Field(default=0, ge=0)
    warnings: List[str] = Field(default_factory=list)


class VoiceSynthCommitResponse(BaseModel):
    scenes: List[VoiceSynthCommitSceneResult] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TimelineItem(BaseModel):
    """Zeile in der Produktions-Timeline (BA 6.9)."""

    scene_number: int = Field(ge=1)
    voice_text: str = ""
    image_prompt: str = ""
    video_prompt: str = ""
    camera_direction: str = ""
    duration_seconds: int = Field(default=1, ge=1)
    asset_type: SceneAssetTypeLiteral = "generated"
    transition_hint: str = ""


class RenderManifest(BaseModel):
    """Firestore ``render_manifests`` — Doc-ID = ``production_job_id``."""

    id: str
    production_job_id: str
    production_job: Optional[ProductionJob] = None
    scene_plan: Optional[ScenePlan] = None
    scene_assets: Optional[SceneAssets] = None
    voice_plan: Optional[VoicePlan] = None
    timeline: List[TimelineItem] = Field(default_factory=list)
    #: Phase 7.7 — Metadaten zu persistiertem Voice ohne Audio-Payload.
    voice_production_file_refs: List[VoiceProductionFileRef] = Field(default_factory=list)
    estimated_total_duration_seconds: int = Field(default=0, ge=0)
    export_version: str = "7.1.0"
    status: RenderManifestStatusLiteral = "incomplete"
    warnings: List[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class RenderManifestGenerateResponse(BaseModel):
    render_manifest: Optional[RenderManifest] = None
    warnings: List[str] = Field(default_factory=list)


class RenderManifestGetResponse(BaseModel):
    render_manifest: Optional[RenderManifest] = None
    warnings: List[str] = Field(default_factory=list)


class ConnectorExportMetadata(BaseModel):
    title: str = ""
    description_draft: str = ""
    tags: List[str] = Field(default_factory=list)
    video_template: str = ""
    warnings: List[str] = Field(default_factory=list)


class ConnectorExportPayload(BaseModel):
    """BA 7.0 — reiner JSON-Export, keine Provider-Calls."""

    generic_manifest: dict = Field(default_factory=dict)
    elevenlabs_blocks: List[dict] = Field(default_factory=list)
    kling_prompts: List[dict] = Field(default_factory=list)
    leonardo_prompts: List[dict] = Field(default_factory=list)
    thumbnail_prompt: str = ""
    capcut_timeline_hint: dict = Field(default_factory=dict)
    metadata: ConnectorExportMetadata = Field(default_factory=ConnectorExportMetadata)
    story_pack: dict = Field(
        default_factory=dict,
        description="BA 9.5b — gebündelter Story-Nebenkanal (Hooks, Rhythm, strukturelle Meta).",
    )
    voice_artefakte: List[dict] = Field(
        default_factory=list,
        description="Phase 7.7 — production_files vom Typ voice als dict (read-only).",
    )


class ProductionConnectorExportResponse(BaseModel):
    export: ConnectorExportPayload
    warnings: List[str] = Field(default_factory=list)


ExportDownloadFormatLiteral = Literal["json", "markdown", "csv", "txt"]


class ProductionChecklist(BaseModel):
    """Firestore ``production_checklists`` — Document-ID = ``production_job_id``."""

    id: str
    production_job_id: str
    script_ready: bool = False
    scene_plan_ready: bool = False
    scene_assets_ready: bool = False
    voice_plan_ready: bool = False
    render_manifest_ready: bool = False
    thumbnail_ready: bool = False
    editing_ready: bool = False
    upload_ready: bool = False
    published: bool = False
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""


class ProductionChecklistUpdateRequest(BaseModel):
    """Manuelle Checklisten-Felder (Artefakt-Felder werden serverseitig mit ``True`` ergänzt)."""

    thumbnail_ready: Optional[bool] = None
    editing_ready: Optional[bool] = None
    upload_ready: Optional[bool] = None
    published: Optional[bool] = None
    notes: Optional[str] = None


class ProductionChecklistResponse(BaseModel):
    checklist: Optional[ProductionChecklist] = None
    warnings: List[str] = Field(default_factory=list)


class DevFixtureCompletedScriptJobRequest(BaseModel):
    """Nur aktiv wenn ENABLE_TEST_FIXTURES=true — Endpoint-Doku BA 6.6.1."""

    fixture_id: Optional[str] = Field(
        default=None,
        max_length=80,
        description="Optionaler Suffix; Job-ID wird dev_fixture_<Suffix> oder dev_fixture_<Zufällig>.",
    )
    create_production_job: bool = True

    @field_validator("fixture_id")
    @classmethod
    def fixture_id_safe(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = (v or "").strip()
        if not s:
            return None
        for ch in s:
            if ch.isalnum() or ch in ("_", "-"):
                continue
            raise ValueError("fixture_id: nur ASCII [A-Za-z0-9_-] erlaubt.")
        return s


class DevFixtureCompletedScriptJobResponse(BaseModel):
    """Antwort nach erfolgreicher Dev-Fixture-Erzeugung."""

    job_id: str
    generated_script_id: str
    production_job_id: Optional[str] = None
    production_job_created: bool = False
    warnings: List[str] = Field(default_factory=list)


class WatchlistDashboardHealth(BaseModel):
    last_successful_job_at: Optional[str] = None
    last_run_cycle_at: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class WatchlistDashboardCounts(BaseModel):
    channels_active: int = 0
    channels_paused: int = 0
    channels_error: int = 0
    processed_videos_total: int = 0
    processed_videos_skipped_total: int = 0
    processed_videos_transcript_not_available_total: int = 0
    script_jobs_pending: int = 0
    script_jobs_running: int = 0
    script_jobs_completed: int = 0
    script_jobs_failed: int = 0
    script_jobs_skipped: int = 0
    generated_scripts_total: int = 0


class WatchlistDashboardResponse(BaseModel):
    counts: WatchlistDashboardCounts = Field(default_factory=WatchlistDashboardCounts)
    health: WatchlistDashboardHealth = Field(default_factory=WatchlistDashboardHealth)


class WatchlistErrorCodeSummaryItem(BaseModel):
    error_code: str
    count: int = 0
    sample_job_ids: List[str] = Field(default_factory=list)


class WatchlistSkipReasonSummaryItem(BaseModel):
    skip_reason: str
    count: int = 0
    sample_video_ids: List[str] = Field(default_factory=list)


class WatchlistErrorsSummaryResponse(BaseModel):
    by_error_code: List[WatchlistErrorCodeSummaryItem] = Field(default_factory=list)
    by_skip_reason: List[WatchlistSkipReasonSummaryItem] = Field(
        default_factory=list
    )
    warnings: List[str] = Field(default_factory=list)
    scanned_script_jobs: int = 0
    scanned_processed_videos: int = 0


class WatchlistJobActionResponse(BaseModel):
    job: Optional[ScriptJob] = None
    warnings: List[str] = Field(default_factory=list)


class WatchlistChannelStatusResponse(BaseModel):
    channel: Optional[WatchlistChannel] = None
    warnings: List[str] = Field(default_factory=list)


class WatchlistStuckRunningJobItem(BaseModel):
    job_id: str
    started_at: Optional[str] = None
    channel_id: str = ""
    video_id: str = ""


class WatchlistStuckRunningAnalysisResponse(BaseModel):
    """Analyse hängender ``running``-Jobs — keine automatische Wiederherstellung."""

    threshold_minutes: int = 45
    stuck_jobs: List[WatchlistStuckRunningJobItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# --- BA 7.5–7.7: Daily Cycle, Provider-Readiness, Storage Foundation ---


class RunDailyProductionCycleRequest(BaseModel):
    channel_limit: int = Field(default=3, ge=1, le=50)
    job_limit: int = Field(default=3, ge=1, le=10)
    production_limit: int = Field(default=3, ge=1, le=50)
    dry_run: bool = True


class DailyCycleStepResult(BaseModel):
    """Einzelergebnis im Daily Cycle (Debugging / Transparenz)."""

    step: str = ""
    production_job_id: str = ""
    script_job_id: str = ""
    outcome: str = ""
    detail: str = ""


class RunDailyProductionCycleResponse(BaseModel):
    checked_channels: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    production_jobs_created: int = 0
    scene_plans_created: int = 0
    scene_assets_created: int = 0
    voice_plans_created: int = 0
    render_manifests_created: int = 0
    checklists_initialized: int = 0
    warnings: List[str] = Field(default_factory=list)
    results: List[DailyCycleStepResult] = Field(default_factory=list)


ProviderNameLiteral = Literal[
    "elevenlabs",
    "openai",
    "google",
    "leonardo",
    "kling",
    "runway",
    "generic",
    "voice_default",
    "image_default",
    "render_default",
]
ProviderConfigStatusLiteral = Literal["ready", "disabled", "error"]


class ProviderConfig(BaseModel):
    """Firestore ``provider_configs`` — Konfigurationsstatus ohne Secrets."""

    id: str
    provider_name: ProviderNameLiteral
    enabled: bool = False
    dry_run: bool = True
    monthly_budget_limit: float = Field(default=0.0, ge=0)
    current_month_estimated_cost: float = Field(default=0.0, ge=0)
    status: ProviderConfigStatusLiteral = "disabled"
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""


class ProviderConfigUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: Optional[bool] = None
    dry_run: Optional[bool] = None
    monthly_budget_limit: Optional[float] = Field(default=None, ge=0)
    current_month_estimated_cost: Optional[float] = Field(default=None, ge=0)
    status: Optional[ProviderConfigStatusLiteral] = None
    notes: Optional[str] = None


class ListProviderConfigsResponse(BaseModel):
    configs: List[ProviderConfig] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ProviderStatusItem(BaseModel):
    provider_name: ProviderNameLiteral
    enabled: bool = False
    dry_run: bool = True
    status: ProviderConfigStatusLiteral = "disabled"


class ProviderStatusResponse(BaseModel):
    providers: List[ProviderStatusItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ProviderSeedDefaultsResponse(BaseModel):
    """Antwort nach ``POST /providers/configs/seed-defaults`` (BA 8.6)."""

    created: int = 0
    skipped_existing: int = 0
    seeds: List[ProviderConfig] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


ProductionFileTypeLiteral = Literal[
    "export_json",
    "export_markdown",
    "export_csv",
    "voice",
    "image",
    "video",
    "thumbnail",
    "manifest",
]
ProductionFileRecordStatusLiteral = Literal["planned", "ready", "failed"]


class ProductionFileRecord(BaseModel):
    """Firestore ``production_files`` — geplante Artefakte (ohne echte Blob-Uploads)."""

    id: str
    production_job_id: str
    file_type: ProductionFileTypeLiteral
    storage_path: str = ""
    public_url: str = ""
    status: ProductionFileRecordStatusLiteral = "planned"
    provider_name: ProviderNameLiteral = "generic"
    scene_number: int = Field(default=0, ge=0)
    created_at: str = ""
    updated_at: str = ""
    error: str = ""
    error_code: str = ""
    synthesis_byte_length: int = Field(
        default=0,
        ge=0,
        description="Phase 7.3: bytes der letzten Synthese (Metadata nur, kein Blob).",
    )


class ListProductionFilesResponse(BaseModel):
    files: List[ProductionFileRecord] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class PlanProductionFilesResponse(BaseModel):
    """Antwort nach ``/files/plan`` — neu geplant + bereits vorhanden."""

    files: List[ProductionFileRecord] = Field(default_factory=list)
    planned_new: int = 0
    skipped_existing_planned: int = 0
    warnings: List[str] = Field(default_factory=list)


# --- BA 7.8–7.9: Execution Queue & Budget-Schätzungen (keine echten Provider-Calls) ---


ExecutionJobStatusLiteral = Literal[
    "queued",
    "running",
    "completed",
    "failed",
    "skipped",
]

ExecutionJobTypeLiteral = Literal[
    "voice_generate",
    "image_generate",
    "video_generate",
    "thumbnail_generate",
    "export_package",
]


class ExecutionJob(BaseModel):
    """Firestore ``execution_jobs`` — ausführbare Tasks (Queue), Doc-ID deterministisch."""

    id: str
    production_job_id: str
    production_file_id: Optional[str] = None
    job_type: ExecutionJobTypeLiteral
    provider_name: ProviderNameLiteral = "generic"
    scene_number: Optional[int] = None
    status: ExecutionJobStatusLiteral = "queued"
    priority: int = Field(default=3, ge=1, le=5)
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    output_reference: str = ""
    estimated_cost: float = Field(default=0.0, ge=0.0)
    error: str = ""
    error_code: str = ""
    created_at: str = ""
    updated_at: str = ""


class ExecutionQueueInitResponse(BaseModel):
    """Nach ``POST …/execution/init``."""

    production_job_id: str
    jobs: List[ExecutionJob] = Field(default_factory=list)
    created_new: int = 0
    reused_existing: int = 0
    warnings: List[str] = Field(default_factory=list)


class ExecutionQueueGetResponse(BaseModel):
    jobs: List[ExecutionJob] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ProductionCosts(BaseModel):
    """Firestore ``production_costs`` — Doc-ID = ``production_job_id``."""

    id: str
    production_job_id: str
    estimated_total_cost: float = Field(default=0.0, ge=0.0)
    actual_total_cost: float = Field(default=0.0, ge=0.0)
    currency: str = "EUR"
    voice_cost_estimate: float = Field(default=0.0, ge=0.0)
    image_cost_estimate: float = Field(default=0.0, ge=0.0)
    video_cost_estimate: float = Field(default=0.0, ge=0.0)
    thumbnail_cost_estimate: float = Field(default=0.0, ge=0.0)
    buffer_cost_estimate: float = Field(default=0.0, ge=0.0)
    cost_baseline_expected: float = Field(default=0.0, ge=0.0)
    cost_variance: float = Field(default=0.0)
    over_budget_flag: bool = False
    step_cost_breakdown: Dict[str, float] = Field(default_factory=dict)
    estimated_profitability_hint: str = ""
    warnings: List[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class ProductionCostsCalculateResponse(BaseModel):
    costs: Optional[ProductionCosts] = None
    warnings: List[str] = Field(default_factory=list)


class ProductionCostsGetResponse(BaseModel):
    costs: Optional[ProductionCosts] = None
    warnings: List[str] = Field(default_factory=list)


# --- BA 8.0–8.2: Audit, Recovery, Monitoring ---


PipelineAuditSeverityLiteral = Literal["info", "warning", "critical"]
PipelineAuditStatusLiteral = Literal["open", "resolved", "ignored"]
PipelineRecommendedActionLiteral = Literal[
    "retry",
    "reset",
    "rebuild",
    "retry_scene_plan",
    "retry_scene_assets",
    "retry_voice_plan",
    "retry_voice_synthesize",
    "retry_render_manifest",
    "retry_execution_job",
    "retry_cost_estimate",
    "reset_pipeline_step",
]


RecoveryActionKindLiteral = Literal[
    "retry_scene_plan",
    "retry_scene_assets",
    "retry_voice_plan",
    "retry_render_manifest",
    "retry_execution_job",
    "retry_cost_estimate",
    "retry_production_files",
    "reset_pipeline_step",
    "full_rebuild",
]
RecoveryActionStatusLiteral = Literal["pending", "completed", "failed"]


class PipelineAuditDraft(BaseModel):
    audit_type: str
    severity: PipelineAuditSeverityLiteral
    detected_issue: str = ""
    recommended_action: PipelineRecommendedActionLiteral = "rebuild"
    auto_repairable: bool = False
    production_job_id: Optional[str] = None
    script_job_id: Optional[str] = None
    extra_slug: Optional[str] = None


class PipelineAudit(BaseModel):
    """Firestore ``pipeline_audits``."""

    id: str
    production_job_id: Optional[str] = None
    script_job_id: Optional[str] = None
    audit_type: str = ""
    severity: PipelineAuditSeverityLiteral = "info"
    status: PipelineAuditStatusLiteral = "open"
    detected_issue: str = ""
    recommended_action: PipelineRecommendedActionLiteral = "rebuild"
    auto_repairable: bool = False
    detected_at: str = ""
    resolved_at: Optional[str] = None
    notes: str = ""


class PipelineAuditRunRequest(BaseModel):
    """Optionaler Begrenzer für Smoke-Loads (Firestore)."""

    model_config = ConfigDict(extra="forbid")

    stuck_threshold_minutes: int = Field(default=45, ge=5, le=1440)
    production_job_limit: int = Field(default=80, ge=1, le=250)
    resolve_missing_from_scan_set: bool = Field(
        default=True,
        description="Offene audits für dieselbe Produkt-Jobs-Untermenge ohne Befunde als resolved markieren.",
    )


class PipelineAuditRunResponse(BaseModel):
    scanned_production_jobs: int = 0
    scanned_script_jobs_stuck_candidates: int = 0
    audits_written: int = 0
    audits_resolved: int = 0
    audits: List[PipelineAudit] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ListPipelineAuditsResponse(BaseModel):
    audits: List[PipelineAudit] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ProductionRecoveryRetryRequest(BaseModel):
    """Gezielter Neuaufbau eines Pipeline-Schrittes (unterscheidet sich vom klassischen Produktjob-„retry”)."""

    model_config = ConfigDict(extra="forbid")

    step: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description=(
            "scene_plan | scene_assets | voice_plan | render_manifest | "
            "execution | costs | files | full_rebuild"
        ),
    )


class RecoveryAction(BaseModel):
    """Firestore ``recovery_actions`` — Protokolle."""

    id: str
    production_job_id: str
    action_kind: RecoveryActionKindLiteral
    requested_step_raw: str = ""
    status: RecoveryActionStatusLiteral = "completed"
    detail: str = ""
    warnings: List[str] = Field(default_factory=list)
    created_at: str = ""
    finished_at: str = ""


class ProductionPipelineRecoveryResponse(BaseModel):
    action: RecoveryAction
    warnings: List[str] = Field(default_factory=list)


class PipelineMonitoringSummaryResponse(BaseModel):
    audits_open_critical: int = 0
    audits_open_warning: int = 0
    audits_open_info: int = 0
    audits_recent_resolved_sample: List[PipelineAudit] = Field(default_factory=list)
    recovery_actions_recent: List[RecoveryAction] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# --- BA 8.3: Status-Normalisierung & Eskalationen ---


PipelineEscalationSeverityLiteral = Literal["low", "medium", "high", "critical"]
PipelineEscalationCategoryLiteral = Literal[
    "repeated_failure",
    "provider_failure_cluster",
    "dead_after_recovery",
    "cost_anomaly",
    "repairable_gap",
]


class PipelineEscalation(BaseModel):
    """Firestore ``pipeline_escalations`` — Doc-ID deterministisch (siehe Service)."""

    escalation_id: str
    production_job_id: Optional[str] = None
    script_job_id: Optional[str] = None
    severity: PipelineEscalationSeverityLiteral = "medium"
    category: PipelineEscalationCategoryLiteral
    reason: str = ""
    retry_count: int = Field(default=0, ge=0)
    provider_flag: Optional[str] = None
    created_at: str = ""


class StatusNormalizeRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stuck_running_minutes: int = Field(default=45, ge=5, le=1440)
    queued_stall_minutes: int = Field(default=120, ge=15, le=2880)
    production_job_scan_limit: int = Field(default=120, ge=1, le=250)
    script_job_scan_limit: int = Field(default=200, ge=1, le=600)
    max_step_retries: int = Field(default=3, ge=1, le=50)
    cost_anomaly_ratio: float = Field(default=3.0, ge=1.05, le=100.0)
    provider_failed_cluster_threshold: int = Field(default=3, ge=2, le=500)
    dry_run: bool = False
    retry_reason: str = Field(
        default="status_normalize_run",
        min_length=1,
        max_length=500,
    )


class StatusNormalizeRunResponse(BaseModel):
    orphaned_detected: int = 0
    stuck_normalized: int = 0
    queued_retryable_marked: int = 0
    partial_failed_marked: int = 0
    repairable_gap_escalations: int = 0
    escalations_upserted: int = 0
    hard_fails_retry_cap: int = 0
    actions_log: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ListPipelineEscalationsResponse(BaseModel):
    escalations: List[PipelineEscalation] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# --- BA 8.4 LIGHT: Founder Control Panel (read-only aggregates) ---


class ControlPanelAuditSummary(BaseModel):
    open_critical: int = 0
    open_warning: int = 0
    open_info: int = 0


class ControlPanelEscalationSummary(BaseModel):
    recent_escalations: List[PipelineEscalation] = Field(default_factory=list)
    count_by_severity: Dict[str, int] = Field(default_factory=dict)
    count_by_category: Dict[str, int] = Field(default_factory=dict)


class ControlPanelRecoverySummary(BaseModel):
    recent_actions: List[RecoveryAction] = Field(default_factory=list)


class ControlPanelJobStatusSummary(BaseModel):
    production_jobs_by_status: Dict[str, int] = Field(default_factory=dict)
    script_jobs_by_status: Dict[str, int] = Field(default_factory=dict)
    production_jobs_sampled: int = 0


class ControlPanelProviderSummary(BaseModel):
    total_configs: int = 0
    enabled: int = 0
    disabled: int = 0
    dry_run_true: int = 0
    status_error: int = 0


class ControlPanelCostSummary(BaseModel):
    cost_records_count: int = 0
    estimated_total_eur: float = 0.0
    cost_anomaly_escalations: int = 0
    cost_records_with_warnings: int = 0


class ControlPanelProblemItem(BaseModel):
    kind: Literal["production_job", "script_job"]
    job_id: str
    status: str = ""
    detail: str = ""


class ControlPanelRecentProblemsSummary(BaseModel):
    items: List[ControlPanelProblemItem] = Field(default_factory=list)


class StoryEngineDriftTemplateRow(BaseModel):
    """BA 9.7 — Drift-Signal pro kanonisiertem ``video_template`` (Stichprobe)."""

    template_id: str = ""
    script_count: int = 0
    distinct_template_definition_versions: int = 0
    distinct_nonempty_template_definition_versions: int = 0
    dominant_template_definition_version: str = ""
    definition_version_dispersion_ratio: float = Field(0.0, ge=0.0, le=1.0)
    scripts_with_any_template_conformance_warning: int = 0
    scripts_template_gate_failed: int = 0
    avg_hook_score: float = Field(0.0, ge=0.0, le=10.0)


class StoryEngineTemplateScoresRow(BaseModel):
    """BA 9.7 — Health/Performance-Schätzung ohne externe KPIs."""

    template_id: str = ""
    health_score_0_to_100: float = Field(0.0, ge=0.0, le=100.0)
    internal_performance_score_0_to_100: float = Field(0.0, ge=0.0, le=100.0)


class StoryEngineTemplateOptimizationSummary(BaseModel):
    """BA 9.7 Adaptive Template Optimization (read-only Aggregation)."""

    sample_scripts: int = 0
    min_statistics_sample_met: bool = False
    drift_rows: List[StoryEngineDriftTemplateRow] = Field(default_factory=list)
    scores: List[StoryEngineTemplateScoresRow] = Field(default_factory=list)
    refinement_suggestions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class StoryEngineIntelligenceSummary(BaseModel):
    """BA 9.8 — Empfehlungstexte, kein automatischer Produktions-Umschalter."""

    narrative_recommendations: List[str] = Field(default_factory=list)
    cross_template_summary: List[str] = Field(default_factory=list)
    self_learning_readiness_notes: List[str] = Field(default_factory=list)


class StoryEngineTemplateHealthHttpResponse(BaseModel):
    """BA 9.7/9.8 — READ-Only Antwort für ``GET /story-engine/template-health``."""

    template_optimization: StoryEngineTemplateOptimizationSummary = Field(
        default_factory=StoryEngineTemplateOptimizationSummary,
    )
    story_intelligence: StoryEngineIntelligenceSummary = Field(
        default_factory=StoryEngineIntelligenceSummary,
    )
    warnings: List[str] = Field(default_factory=list)


class ControlPanelStoryEngineSummary(BaseModel):
    sampled_scripts: int = 0
    by_hook_type: Dict[str, int] = Field(default_factory=dict)
    by_video_template: Dict[str, int] = Field(default_factory=dict)
    template_gate_failed_scripts: int = 0
    experiments_by_id: Dict[str, int] = Field(default_factory=dict)
    variants_by_id: Dict[str, int] = Field(default_factory=dict)
    template_optimization: StoryEngineTemplateOptimizationSummary = Field(
        default_factory=StoryEngineTemplateOptimizationSummary,
        description="BA 9.7 — Adaptive Template Optimization (Stichprobe).",
    )
    story_intelligence: StoryEngineIntelligenceSummary = Field(
        default_factory=StoryEngineIntelligenceSummary,
        description="BA 9.8 — Story Intelligence Layer (Hinweise).",
    )


class ControlPanelSummaryResponse(BaseModel):
    audit: ControlPanelAuditSummary = Field(default_factory=ControlPanelAuditSummary)
    escalation: ControlPanelEscalationSummary = Field(
        default_factory=ControlPanelEscalationSummary
    )
    recovery: ControlPanelRecoverySummary = Field(
        default_factory=ControlPanelRecoverySummary
    )
    jobs: ControlPanelJobStatusSummary = Field(default_factory=ControlPanelJobStatusSummary)
    providers: ControlPanelProviderSummary = Field(
        default_factory=ControlPanelProviderSummary
    )
    costs: ControlPanelCostSummary = Field(default_factory=ControlPanelCostSummary)
    recent_problems: ControlPanelRecentProblemsSummary = Field(
        default_factory=ControlPanelRecentProblemsSummary
    )
    story_engine: ControlPanelStoryEngineSummary = Field(
        default_factory=ControlPanelStoryEngineSummary
    )
    warnings: List[str] = Field(default_factory=list)

