"""BA 12.0–12.6 — Production Asset Assembly Schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


AssemblyAssetType = Literal["image", "video", "audio", "thumbnail", "render"]
AssemblyStatus = Literal["complete", "partial", "blocked"]


class ManifestAsset(BaseModel):
    """BA 12.0 — einzelnes Asset im Master-Manifest."""

    asset_id: str = ""
    provider_name: str = ""
    asset_type: AssemblyAssetType = "image"
    source_status: str = ""
    asset_url: Optional[str] = None
    local_path: Optional[str] = None
    chapter_index: Optional[int] = None
    scene_index: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MasterAssetManifestResult(BaseModel):
    """BA 12.0 — zentrale Asset-Liste aus Live-/Dry-Run-/Persistenz-Ergebnissen."""

    manifest_version: str = "12.0-v1"
    manifest_status: AssemblyStatus = "partial"
    total_assets: int = Field(default=0, ge=0)
    assets: List[ManifestAsset] = Field(default_factory=list)
    missing_asset_types: List[AssemblyAssetType] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class MultiAssetAssemblyResult(BaseModel):
    """BA 12.1 — Gruppierung und Coverage je Asset-Typ."""

    assembly_version: str = "12.1-v1"
    assembly_status: AssemblyStatus = "partial"
    image_assets: List[ManifestAsset] = Field(default_factory=list)
    video_assets: List[ManifestAsset] = Field(default_factory=list)
    voice_assets: List[ManifestAsset] = Field(default_factory=list)
    thumbnail_assets: List[ManifestAsset] = Field(default_factory=list)
    render_assets: List[ManifestAsset] = Field(default_factory=list)
    coverage_score: int = Field(default=0, ge=0, le=100)
    warnings: List[str] = Field(default_factory=list)


class FinalTimelineScene(BaseModel):
    """BA 12.2 — rendernahe Timeline-Szene mit Asset-Links."""

    scene_index: int = Field(ge=0)
    start_time: int = Field(default=0, ge=0)
    end_time: int = Field(default=0, ge=0)
    linked_assets: List[str] = Field(default_factory=list)
    narration_asset: Optional[str] = None
    render_priority: int = Field(default=0, ge=0)


class FinalTimelineResult(BaseModel):
    """BA 12.2 — finale Timeline aus BA-9-Timeline plus Assembly-Assets."""

    timeline_version: str = "12.2-v1"
    timeline_status: AssemblyStatus = "partial"
    final_duration_seconds: int = Field(default=0, ge=0)
    scenes: List[FinalTimelineScene] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class VoiceSceneAlignmentResult(BaseModel):
    """BA 12.3 — grobe Voice-/Scene-Abdeckung."""

    alignment_version: str = "12.3-v1"
    alignment_status: AssemblyStatus = "partial"
    aligned_scenes: List[int] = Field(default_factory=list)
    missing_voice_scenes: List[int] = Field(default_factory=list)
    voice_overflow_warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class RenderInstructionPackageResult(BaseModel):
    """BA 12.4 — Übergabepaket für ein späteres Render-System."""

    render_instruction_version: str = "12.4-v1"
    render_status: AssemblyStatus = "partial"
    render_targets: List[str] = Field(default_factory=list)
    scene_render_map: List[Dict[str, Any]] = Field(default_factory=list)
    voice_track_map: List[Dict[str, Any]] = Field(default_factory=list)
    thumbnail_target: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class DownloadableProductionBundleResult(BaseModel):
    """BA 12.5 — exportierbare Paketstruktur ohne tatsächliches Packen."""

    bundle_version: str = "12.5-v1"
    bundle_status: AssemblyStatus = "partial"
    bundle_id: str = ""
    included_components: List[str] = Field(default_factory=list)
    downloadable_manifest: Dict[str, Any] = Field(default_factory=dict)
    local_export_targets: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


FinalReviewStatus = Literal["ready_for_human_review", "needs_revision", "blocked"]
ReleaseRecommendation = Literal["approve_for_render", "revise_before_render", "hold"]


class HumanFinalReviewPackageResult(BaseModel):
    """BA 12.6 — finales Review-Paket vor Render-Freigabe."""

    review_version: str = "12.6-v1"
    review_status: FinalReviewStatus = "needs_revision"
    final_checklist: List[str] = Field(default_factory=list)
    critical_risks: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    final_summary: str = ""
    release_recommendation: ReleaseRecommendation = "hold"
