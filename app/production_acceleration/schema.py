"""BA 15.0–15.9 — First Production Acceleration Suite schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

AccelerationStatus = Literal["ready", "partial", "blocked"]


class DemoVideoAutomationResult(BaseModel):
    """BA 15.0 — reproduzierbarer lokaler Demo-Video-Build-Plan."""

    automation_version: str = "15.0-v1"
    automation_status: AccelerationStatus = "partial"
    output_path: str = "output/first_demo_video.mp4"
    image_source: Optional[str] = None
    audio_source: str = "output/voice_smoke_test_output.mp3"
    command_hint: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)


class AssetDownloaderResult(BaseModel):
    """BA 15.1 — lokaler Download-Plan für Remote-Assets."""

    downloader_version: str = "15.1-v1"
    downloader_status: AccelerationStatus = "partial"
    download_targets: List[Dict[str, Any]] = Field(default_factory=list)
    local_asset_paths: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class VoiceRegistryResult(BaseModel):
    """BA 15.2 — sichere Voice-Registry ohne Secret-Werte."""

    registry_version: str = "15.2-v1"
    registry_status: AccelerationStatus = "partial"
    default_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    configured_voice_id_present: bool = False
    voice_sources: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class SceneStitcherResult(BaseModel):
    """BA 15.3 — einfache Stitching-Map für lokale Szenen."""

    stitcher_version: str = "15.3-v1"
    stitcher_status: AccelerationStatus = "partial"
    scene_count: int = Field(default=0, ge=0)
    stitch_plan: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class SubtitleDraftResult(BaseModel):
    """BA 15.4 — erster Untertitel-Entwurf aus Kapitel-/Szenenstruktur."""

    subtitle_version: str = "15.4-v1"
    subtitle_status: AccelerationStatus = "partial"
    subtitle_format: str = "srt_draft"
    subtitle_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ThumbnailExtractResult(BaseModel):
    """BA 15.5 — lokaler Thumbnail-Extrakt-Plan aus Demo-Video."""

    thumbnail_extract_version: str = "15.5-v1"
    extract_status: AccelerationStatus = "partial"
    video_source: str = "output/first_demo_video.mp4"
    output_path: str = "output/first_demo_thumbnail.jpg"
    command_hint: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class FounderLocalDashboardResult(BaseModel):
    """BA 15.6 — lokaler Founder-Status über Demo-Produktion."""

    dashboard_version: str = "15.6-v1"
    dashboard_status: AccelerationStatus = "partial"
    readiness_score: int = Field(default=0, ge=0, le=100)
    ready_components: List[str] = Field(default_factory=list)
    blocked_components: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)


class BatchTopicRunnerResult(BaseModel):
    """BA 15.7 — reproduzierbarer Batch-Plan für mehrere Demo-Themen."""

    batch_version: str = "15.7-v1"
    batch_status: AccelerationStatus = "partial"
    topic_count: int = Field(default=0, ge=0)
    batch_items: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class CostSnapshotResult(BaseModel):
    """BA 15.8 — lokaler Kosten-Snapshot für Demo-Produktion."""

    snapshot_version: str = "15.8-v1"
    snapshot_status: AccelerationStatus = "partial"
    estimated_cost: float = Field(default=0.0, ge=0.0)
    cost_items: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ViralPrototypePresetsResult(BaseModel):
    """BA 15.9 — schnelle Presets für wiederholbare Demo-Prototypen."""

    presets_version: str = "15.9-v1"
    presets_status: AccelerationStatus = "ready"
    recommended_preset: str = "documentary_proof"
    presets: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

