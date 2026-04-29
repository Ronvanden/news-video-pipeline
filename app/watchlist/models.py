"""Watchlist-spezifische Request-/Response-Modelle (Phase 5 Watchlist — Jobs, Skript-Persistenz)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional

from app.models import Chapter, ReviewIssue, ReviewRecommendation, ReviewScriptResponse, SimilarityFlag

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


class CreateWatchlistChannelResponse(BaseModel):
    channel: Optional[WatchlistChannel] = None
    warnings: List[str] = Field(default_factory=list)


class ListWatchlistChannelsResponse(BaseModel):
    channels: List[WatchlistChannel] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


ProcessedVideoStatusLiteral = Literal["seen", "skipped", "script_generated"]
ChannelCheckItemStatusLiteral = Literal["new", "known", "skipped"]

ScriptJobStatusLiteral = Literal["pending", "running", "completed", "failed", "skipped"]
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


class ScriptJob(BaseModel):
    id: str
    video_id: str
    channel_id: str
    video_url: str
    status: ScriptJobStatusLiteral
    source_type: SourceTypeYoutubeTranscript = "youtube_transcript"
    target_language: str = "de"
    duration_minutes: int = Field(default=10, ge=1, le=60)
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: str = ""
    error_code: str = ""
    generated_script_id: Optional[str] = None
    review_result_id: Optional[str] = None
    attempt_count: int = Field(default=0, ge=0)
    last_attempt_at: Optional[str] = None


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
    """Persistiertes Skript (Firestore ``generated_scripts``, Vertrag analog ``GenerateScriptResponse``)."""

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
    created_at: str


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
    "queued", "in_progress", "completed", "failed", "skipped"
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
