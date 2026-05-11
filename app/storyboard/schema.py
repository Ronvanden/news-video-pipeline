"""Storyboard schema for downstream visual, voice, motion, and render planning."""

from __future__ import annotations

from typing import List, Literal, Optional

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
    max_live_image_tasks: int = Field(default=1, ge=0, le=1)
    run_id: str = "storyboard_openai_image_v1"
    output_root: str = "output"
    openai_image_model: str = "gpt-image-2"
    openai_image_size: str = "1024x1024"
    openai_image_timeout_seconds: float = Field(default=120.0, ge=15.0, le=600.0)
