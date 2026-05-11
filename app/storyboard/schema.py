"""Storyboard schema for downstream visual, voice, motion, and render planning."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.prompt_engine.schema import ProductionPromptPlan, TimelineRole


StoryboardAssetType = Literal[
    "hook_card",
    "image_keyframe",
    "image_to_video_candidate",
    "b_roll_sequence",
    "outro_card",
]
StoryboardStatus = Literal["ready", "partial", "blocked"]
StoryboardTransition = Literal["cut", "dissolve", "push_in", "match_cut", "fade_out"]
StoryboardReadinessStatus = Literal["ready", "warning", "blocked"]
AssetGenerationPlanStatus = Literal["planned", "blocked"]
AssetGenerationTaskType = Literal["image", "video", "voice", "thumbnail", "music", "subtitle", "render_hint"]
AssetTaskExecutionStatus = Literal["dry_run", "completed_stub", "live_completed", "skipped", "failed"]
StoryboardRenderTimelineStatus = Literal["ready", "warning", "blocked"]
StoryboardRenderTimelineSegmentStatus = Literal["ready", "image_fallback", "skipped", "missing", "blocked"]
StoryboardLocalRenderPackageStatus = Literal["ready", "warning", "blocked"]
StoryboardVoiceMixdownStatus = Literal["dry_run", "completed", "skipped", "failed"]
StoryboardLocalRenderExecutionStatus = Literal["dry_run", "completed", "failed"]


class StoryboardChapterInput(BaseModel):
    """Minimal script chapter input for storyboard planning."""

    title: str = ""
    content: str = ""
    summary: str = ""


class StoryboardScene(BaseModel):
    """One storyboard scene for later asset generation and render assembly."""

    scene_number: int = Field(ge=1)
    source: Literal["hook", "prompt_plan", "script_chapter"] = "script_chapter"
    chapter_title: str = ""
    timeline_role: TimelineRole
    visual_intent: str = ""
    voice_text: str = ""
    image_prompt: str = ""
    video_prompt: str = ""
    duration_seconds: int = Field(default=0, ge=0)
    transition: StoryboardTransition = "cut"
    asset_type: StoryboardAssetType = "image_keyframe"
    provider_hints: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class StoryboardPlan(BaseModel):
    """Plan-only storyboard contract. No provider calls and no binary assets."""

    storyboard_version: str = "ba32_storyboard_v1"
    status: StoryboardStatus = "blocked"
    source_type: Literal["prompt_plan", "script_chapters"] = "script_chapters"
    video_template: str = "generic"
    total_duration_seconds: int = Field(default=0, ge=0)
    scenes: List[StoryboardScene] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    dashboard_ready: bool = True


class StoryboardBuildRequest(BaseModel):
    """
    Input for the storyboard side-channel.

    Prefer ``prompt_plan`` when available. Otherwise pass script-style chapters.
    ``GenerateScriptResponse`` stays unchanged; this is a separate orchestration contract.
    """

    prompt_plan: Optional[ProductionPromptPlan] = None
    hook: str = ""
    chapters: List[StoryboardChapterInput] = Field(default_factory=list)
    scene_prompts: List[str] = Field(default_factory=list)
    video_template: str = "generic"
    voice_style: str = ""


class StoryboardReadinessSceneResult(BaseModel):
    """Per-scene quality gate result for storyboard plans."""

    scene_number: int = Field(ge=1)
    chapter_title: str = ""
    status: StoryboardReadinessStatus = "blocked"
    score: int = Field(default=0, ge=0, le=100)
    issues: List[str] = Field(default_factory=list)


class StoryboardReadinessResult(BaseModel):
    """Plan-only production gate before provider execution."""

    readiness_version: str = "storyboard_readiness_v1"
    overall_status: StoryboardReadinessStatus = "blocked"
    score: int = Field(default=0, ge=0, le=100)
    blocking_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    scene_results: List[StoryboardReadinessSceneResult] = Field(default_factory=list)
    production_recommendation: str = ""


class StoryboardReadinessRequest(BaseModel):
    """Input for storyboard readiness checks."""

    storyboard_plan: Optional[StoryboardPlan] = None
    build_request: Optional[StoryboardBuildRequest] = None


class AssetGenerationTask(BaseModel):
    """One planned asset-generation task. No provider execution."""

    task_id: str
    scene_id: str = ""
    scene_number: Optional[int] = None
    asset_type: AssetGenerationTaskType
    provider_hint: str = ""
    prompt: str = ""
    duration_seconds: Optional[int] = None
    output_path: str = ""
    status: Literal["planned"] = "planned"
    dependencies: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class AssetGenerationPlan(BaseModel):
    """Plan-only task set for later image, video, voice, subtitle, and render work."""

    plan_version: str = "asset_generation_plan_v1"
    plan_status: AssetGenerationPlanStatus = "blocked"
    storyboard_version: str = ""
    readiness_status: StoryboardReadinessStatus = "blocked"
    total_tasks: int = Field(default=0, ge=0)
    tasks: List[AssetGenerationTask] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)


class AssetGenerationPlanRequest(BaseModel):
    """Input for asset generation planning."""

    storyboard_plan: StoryboardPlan
    readiness_result: Optional[StoryboardReadinessResult] = None


class AssetTaskExecutionResult(BaseModel):
    """Execution-stub result for one planned asset task."""

    task_id: str
    asset_type: AssetGenerationTaskType
    provider_hint: str = ""
    execution_status: AssetTaskExecutionStatus = "dry_run"
    planned_output_path: str = ""
    output_path: str = ""
    output_exists: bool = False
    file_size_bytes: Optional[int] = None
    scene_id: str = ""
    scene_number: Optional[int] = None
    provider: str = ""
    model: str = ""
    warnings: List[str] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)


class AssetExecutionResult(BaseModel):
    """Dry-run/stub execution result for an AssetGenerationPlan."""

    execution_version: str = "asset_execution_stub_v1"
    execution_status: AssetTaskExecutionStatus = "dry_run"
    dry_run: bool = True
    task_results: List[AssetTaskExecutionResult] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)
    estimated_provider_calls: int = Field(default=0, ge=0)
    estimated_outputs: List[str] = Field(default_factory=list)


class AssetExecutionRequest(BaseModel):
    """Input for asset execution stub."""

    asset_generation_plan: AssetGenerationPlan
    dry_run: bool = True


class OpenAIImageLiveExecutionRequest(BaseModel):
    """Input for the first live image execution path."""

    asset_generation_plan: AssetGenerationPlan
    confirm_provider_costs: bool = False
    max_live_image_tasks: int = Field(default=10, ge=0, le=10)
    run_id: str = "storyboard_openai_image_v1"
    output_root: str = "output"
    openai_image_model: str = "gpt-image-2"
    openai_image_size: str = "1024x1024"
    openai_image_timeout_seconds: float = Field(default=120.0, ge=15.0, le=600.0)


class ElevenLabsVoiceLiveExecutionRequest(BaseModel):
    """Input for live ElevenLabs voice execution from storyboard voice tasks."""

    asset_generation_plan: AssetGenerationPlan
    confirm_provider_costs: bool = False
    max_live_voice_tasks: int = Field(default=10, ge=0, le=10)
    run_id: str = "storyboard_elevenlabs_voice_v1"
    output_root: str = "output"
    elevenlabs_voice_id: str = ""
    elevenlabs_model_id: str = "eleven_multilingual_v2"
    elevenlabs_timeout_seconds: float = Field(default=120.0, ge=15.0, le=600.0)


class RunwayMotionLiveExecutionRequest(BaseModel):
    """Input for live Runway motion execution from storyboard video tasks."""

    asset_generation_plan: AssetGenerationPlan
    image_execution_result: Optional[AssetExecutionResult] = None
    confirm_provider_costs: bool = False
    max_live_motion_tasks: int = Field(default=1, ge=0, le=2)
    run_id: str = "storyboard_runway_motion_v1"
    output_root: str = "output"
    runway_duration_seconds: int = Field(default=5, ge=5, le=10)


class StoryboardRenderTimelineSegment(BaseModel):
    """One render-timeline segment derived from storyboard plus generated assets."""

    scene_id: str = ""
    scene_number: int = Field(ge=1)
    title: str = ""
    start_seconds: float = Field(default=0, ge=0)
    end_seconds: float = Field(default=0, ge=0)
    duration_seconds: float = Field(default=0, ge=0)
    status: StoryboardRenderTimelineSegmentStatus = "missing"
    image_path: str = ""
    video_path: str = ""
    voice_path: str = ""
    transition: StoryboardTransition = "cut"
    motion_status: Literal["ready", "skipped", "not_requested", "missing"] = "not_requested"
    render_mode: Literal["image_only", "video_clip", "missing_media"] = "missing_media"
    warnings: List[str] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)


class StoryboardRenderTimelineResult(BaseModel):
    """Plan-only render timeline handoff for later local/worker rendering."""

    timeline_version: str = "storyboard_render_timeline_v1"
    overall_status: StoryboardRenderTimelineStatus = "blocked"
    total_duration_seconds: float = Field(default=0, ge=0)
    segments: List[StoryboardRenderTimelineSegment] = Field(default_factory=list)
    image_segments_ready: int = Field(default=0, ge=0)
    voice_segments_ready: int = Field(default=0, ge=0)
    video_segments_ready: int = Field(default=0, ge=0)
    motion_segments_skipped: int = Field(default=0, ge=0)
    warnings: List[str] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)
    render_recommendation: str = ""


class StoryboardRenderTimelineRequest(BaseModel):
    """Input for storyboard render timeline handoff."""

    storyboard_plan: StoryboardPlan
    asset_generation_plan: Optional[AssetGenerationPlan] = None
    image_execution_result: Optional[AssetExecutionResult] = None
    voice_execution_result: Optional[AssetExecutionResult] = None
    motion_execution_result: Optional[AssetExecutionResult] = None


class StoryboardLocalRenderPackageRequest(BaseModel):
    """Input for creating a local renderer handoff package from a render timeline."""

    render_timeline: StoryboardRenderTimelineResult
    voice_mixdown_result: Optional["StoryboardVoiceMixdownResult"] = None
    run_id: str = "storyboard_local_render_v1"
    output_root: str = "output"


class StoryboardLocalRenderPackageResult(BaseModel):
    """Plan-only local render package. No render is started and no files are written."""

    package_version: str = "storyboard_local_render_package_v1"
    overall_status: StoryboardLocalRenderPackageStatus = "blocked"
    run_id: str = "storyboard_local_render_v1"
    timeline_manifest_path: str = ""
    asset_manifest_path: str = ""
    final_video_path: str = ""
    timeline_manifest: Dict[str, Any] = Field(default_factory=dict)
    asset_manifest: Dict[str, Any] = Field(default_factory=dict)
    render_command_hint: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)
    render_recommendation: str = ""


class StoryboardVoiceMixdownRequest(BaseModel):
    """Input for local voice mixdown from a storyboard render timeline."""

    render_timeline: StoryboardRenderTimelineResult
    run_id: str = "storyboard_voice_mixdown_v1"
    output_root: str = "output"
    dry_run: bool = False


class StoryboardVoiceMixdownResult(BaseModel):
    """Local ffmpeg-backed or dry-run voice mixdown result."""

    mixdown_version: str = "storyboard_voice_mixdown_v1"
    execution_status: StoryboardVoiceMixdownStatus = "failed"
    dry_run: bool = False
    run_id: str = "storyboard_voice_mixdown_v1"
    mixed_audio_path: str = ""
    output_exists: bool = False
    file_size_bytes: Optional[int] = None
    input_voice_paths: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)
    render_recommendation: str = ""


class StoryboardLocalRenderExecutionRequest(BaseModel):
    """Input for local storyboard render execution."""

    local_render_package: StoryboardLocalRenderPackageResult
    run_id: str = "storyboard_local_render_execute_v1"
    output_root: str = "output"
    dry_run: bool = False
    motion_mode: str = "basic"


class StoryboardLocalRenderExecutionResult(BaseModel):
    """Local storyboard render execution result."""

    execution_version: str = "storyboard_local_render_execution_v1"
    execution_status: StoryboardLocalRenderExecutionStatus = "failed"
    dry_run: bool = False
    run_id: str = "storyboard_local_render_execute_v1"
    asset_manifest_path: str = ""
    timeline_manifest_path: str = ""
    final_video_path: str = ""
    render_output_manifest_path: str = ""
    manifest_written: bool = False
    video_created: bool = False
    output_exists: bool = False
    file_size_bytes: Optional[int] = None
    warnings: List[str] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)
    render_recommendation: str = ""
