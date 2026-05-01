from pydantic import BaseModel, Field, model_validator
from typing import Any, Dict, List, Literal, Optional

TemplateConformanceLevelLiteral = Literal["off", "warn", "strict"]


class GenerateScriptRequest(BaseModel):
    url: str
    target_language: str = "de"
    duration_minutes: int = 10
    video_template: str = Field(
        default="generic",
        description="BA 9: generic | true_crime | mystery_explainer | history_deep_dive",
    )
    template_conformance_level: TemplateConformanceLevelLiteral = Field(
        default="warn",
        description=(
            "BA 9.3: off — keine Template-Conformance-Strings in warnings; warn — Hinweise "
            "(Default); strict — gleiche Hinweise plus Gate für Persistenz/Export ([template_strict:…])."
        ),
    )


class YouTubeGenerateScriptRequest(BaseModel):
    video_url: str = Field(..., min_length=1)
    target_language: str = "de"
    duration_minutes: int = 10
    video_template: str = Field(
        default="generic",
        description="BA 9: generic | true_crime | mystery_explainer | history_deep_dive",
    )
    template_conformance_level: TemplateConformanceLevelLiteral = Field(
        default="warn",
        description="BA 9.3 — wie bei /generate-script.",
    )

class Chapter(BaseModel):
    title: str
    content: str

class GenerateScriptResponse(BaseModel):
    title: str
    hook: str
    chapters: List[Chapter]
    full_script: str
    sources: List[str]
    warnings: List[str]


class GenerateHookRequest(BaseModel):
    """BA 9.2 Nebenkanal — kein Teil von GenerateScriptResponse."""

    video_template: str = Field(
        default="generic",
        description="generic | true_crime | mystery_explainer | history_deep_dive",
    )
    topic: str = ""
    title: str = ""
    source_summary: str = ""


class GenerateHookResponse(BaseModel):
    hook_text: str
    hook_type: str
    hook_score: float = Field(ge=0.0, le=10.0)
    rationale: str
    template_match: str
    warnings: List[str] = Field(default_factory=list)


class RhythmHintRequest(BaseModel):
    """BA 9.4 — Nebenkanal; kein Teil von GenerateScriptResponse."""

    video_template: str = Field(default="generic")
    duration_minutes: int = Field(default=10, ge=1, le=180)
    hook: str = ""
    chapters: List[Chapter] = Field(default_factory=list)


class RhythmHintResponse(BaseModel):
    rhythm: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


SceneBlueprintSourceClassLiteral = Literal["synthetic_placeholder", "stock_placeholder"]


class StorySceneBlueprintRequest(BaseModel):
    """Phase 8.1 — read-only Ableitung eines visuellen Szenenplans (Nebenkanal)."""

    video_template: str = Field(default="generic")
    duration_minutes: int = Field(default=10, ge=1, le=180)
    title: str = ""
    hook: str = ""
    chapters: List[Chapter] = Field(default_factory=list)
    full_script: str = Field(
        default="",
        description="Optional Nur-Check Wortzahl vs. chapters; keine inhaltliche Neuerfindung.",
    )
    story_structure: Dict[str, Any] = Field(
        default_factory=dict,
        description="BA 9 Nebenkanal — nur registriert, nicht expandiert.",
    )
    rhythm_hints: Dict[str, Any] = Field(
        default_factory=dict,
        description="BA 9.4 Rhythm-Output — nur lesende pacing_hints je Szene wenn beats vorliegen.",
    )


class SceneBlueprintPromptPack(BaseModel):
    """Strukturierte Prompt-Hülle ohne Anbieter-Call."""

    image_primary: str = ""
    negative_hints: str = ""


class SceneBlueprintContract(BaseModel):
    scene_number: int = Field(ge=1)
    intent: str = ""
    subjects_safe: str = ""
    style_tags: List[str] = Field(default_factory=list)
    source_class: SceneBlueprintSourceClassLiteral = "synthetic_placeholder"
    risk_flags: List[str] = Field(default_factory=list)
    prompt_pack: SceneBlueprintPromptPack = Field(default_factory=SceneBlueprintPromptPack)
    licensing_notes: str = ""
    redaction_warnings: List[str] = Field(default_factory=list)


class SceneBlueprintPlanResponse(BaseModel):
    policy_profile: str
    plan_version: int = Field(default=1, ge=1)
    status: Literal["draft", "ready", "failed"] = "ready"
    scenes: List[SceneBlueprintContract] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


ImageProviderProfileLiteral = Literal["leonardo", "openai", "kling"]


class ScenePromptsRequest(StorySceneBlueprintRequest):
    """Phase 8.2 — gleicher Eingabekern wie Scene-Plan plus Provider/Continuity (Nebenkanal)."""

    provider_profile: ImageProviderProfileLiteral = Field(
        default="openai",
        description="Platzhalter-Profile ohne echten Provider-Dispatch.",
    )
    continuity_lock: bool = Field(
        default=True,
        description="Wenn true: Szenen 2+ erhalten denselben Kurz-Anker wie Szene 1 im Positivprompt.",
    )


class SceneExpandedPrompt(BaseModel):
    scene_number: int = Field(ge=1)
    positive_expanded: str = ""
    negative_prompt: str = ""
    continuity_token: str = Field(
        default="",
        description="Kurz-Anker aus Szene 1 bei continuity_lock; sonst leer.",
    )


class PromptQualitySceneEntry(BaseModel):
    """BA 10.1 — Heuristische Qualitätscodes je Szene (deterministisch, kein LLM)."""

    scene_number: int = Field(ge=1)
    checks: List[str] = Field(default_factory=list)
    evidence_hints: List[str] = Field(
        default_factory=list,
        description="Kurze Hinweise ohne Geheimnisse (z. B. Längen, Flag-Namen).",
    )


class PromptQualityReport(BaseModel):
    """BA 10.1 — aggregierter Prompt-Quality-Block für Scene-Prompts / Export."""

    policy_profile: str = Field(
        default="prompt_quality_v10_1_20260501",
        description="Versionierter Qualitäts-Profilstring.",
    )
    summary: str = ""
    global_checks: List[str] = Field(default_factory=list)
    scenes: List[PromptQualitySceneEntry] = Field(default_factory=list)


class ScenePromptsResponse(BaseModel):
    """Phase 8.2 — expandierte Prompts, keine Binär- oder Provider-URLs."""

    policy_profile: str
    prompt_engine_version: int = Field(default=1, ge=1)
    provider_profile: str
    continuity_lock_enabled: bool
    continuity_anchor: str = ""
    blueprint_status: Literal["draft", "ready", "failed"] = "ready"
    scenes: List[SceneExpandedPrompt] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    prompt_quality: Optional[PromptQualityReport] = Field(
        default=None,
        description="BA 10.1 — deterministische Qualitätsmetadaten (optional im Typ, in V1 befüllt).",
    )


class ProviderPromptsBundle(BaseModel):
    """BA 10.2 — gleiche Blueprint-Basis, drei Provider-Stub-Formatierungen."""

    leonardo: List[SceneExpandedPrompt] = Field(default_factory=list)
    openai: List[SceneExpandedPrompt] = Field(default_factory=list)
    kling: List[SceneExpandedPrompt] = Field(default_factory=list)


class ExportPackageRequest(ScenePromptsRequest):
    """BA 10.3 — Export-Paket-Eingabe inkl. Hook-Engine-Ankern."""

    topic: str = ""
    source_summary: str = ""


class ExportHookBlock(BaseModel):
    """Hook-Teil im Export-Paket (spiegelt GenerateHookResponse-Kern)."""

    hook_text: str
    hook_type: str
    hook_score: float = Field(ge=0.0, le=10.0)
    rationale: str
    template_match: str
    warnings: List[str] = Field(default_factory=list)


class ExportPackageResponse(BaseModel):
    """BA 10.3 — produktionsnahes Prompt-Paket ohne externe Provider-Calls."""

    hook: ExportHookBlock
    rhythm: Dict[str, Any] = Field(default_factory=dict)
    scene_plan: SceneBlueprintPlanResponse
    scene_prompts: ScenePromptsResponse
    provider_prompts: ProviderPromptsBundle
    thumbnail_prompt: str = ""
    prompt_quality: Optional[PromptQualityReport] = None
    warnings: List[str] = Field(default_factory=list)


ReadinessStatusLiteral = Literal["ready", "partial_ready", "not_ready"]
ThumbnailStrengthLiteral = Literal["low", "medium", "high"]


class ProviderProfileFlags(BaseModel):
    """BA 10.4 — grobe Nutzbarkeit je Stub-Profil (Schwellwert-heuristisch)."""

    openai: bool = False
    leonardo: bool = False
    kling: bool = False


class ExportPackagePreviewResponse(BaseModel):
    """BA 10.4 — kompakte Founder-Ansicht aus lokalem Export-Paket."""

    template_id: str
    hook_score: float = Field(ge=0.0, le=10.0)
    hook_type: str
    thumbnail_strength: ThumbnailStrengthLiteral
    prompt_quality_score: int = Field(ge=0, le=100)
    scene_count: int = Field(ge=0)
    provider_profiles: ProviderProfileFlags
    provider_stub_warnings: int = Field(ge=0, description="Aggregierte Qualitätshinweise (Scene-Checks).")
    readiness_status: ReadinessStatusLiteral
    top_warnings: List[str] = Field(default_factory=list)
    export_ready: bool


class TemplateRegistryItem(BaseModel):
    """BA 10.4 — öffentliche Template-Zeile für Template-Selector."""

    template_id: str
    label: str
    style: str
    ideal_use_case: str
    hook_bias: str
    pacing_bias: str


class TemplateSelectorResponse(BaseModel):
    templates: List[TemplateRegistryItem] = Field(default_factory=list)


class ProviderReadinessRequest(ExportPackageRequest):
    """BA 10.4 — gleicher Eingabekörper wie Export-Paket."""


class ProviderReadinessScores(BaseModel):
    leonardo: int = Field(ge=0, le=100)
    kling: int = Field(ge=0, le=100)
    openai: int = Field(ge=0, le=100)


class ProviderReadinessResponse(BaseModel):
    overall_status: ReadinessStatusLiteral
    scores: ProviderReadinessScores
    blocking_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommended_next_step: str = ""


ThumbnailCTREmotionLiteral = Literal[
    "curiosity",
    "shock",
    "urgency",
    "mystery",
    "authority",
    "neutral",
]


class OptimizedProviderScenePrompt(BaseModel):
    """BA 10.5 — Leonardo- / OpenAI-optimierte Bildprompt-Zeile (lokal, deterministisch)."""

    scene_number: int = Field(ge=1)
    positive_optimized: str = ""
    negative_prompt: str = ""
    continuity_token: str = ""


class KlingMotionScenePrompt(BaseModel):
    """BA 10.5 — Kling: Keyframe + Bewegungs-/Kamera-Metadaten pro Szene."""

    scene_number: int = Field(ge=1)
    motion_prompt: str = ""
    camera_path: str = ""
    transition_hint: str = ""
    keyframe_positive: str = ""


class ProviderOptimizedPromptsBundle(BaseModel):
    """BA 10.5 — Aggregat aller Provider-Optimierungen (ohne Bruch zu BA 10.2 Stub-Listen)."""

    leonardo: List[OptimizedProviderScenePrompt] = Field(default_factory=list)
    kling: List[KlingMotionScenePrompt] = Field(default_factory=list)
    openai: List[OptimizedProviderScenePrompt] = Field(default_factory=list)


class ThumbnailVariantSpec(BaseModel):
    """BA 10.5 — Thumbnail-Textvariante für CTR-/Packaging-Pfade."""

    headline: str = ""
    overlay_text: str = ""
    emotion_type: ThumbnailCTREmotionLiteral = "neutral"


class CapCutShotlistRow(BaseModel):
    """BA 10.5 — Shotlist-Zeile (CapCut-orientiert, reines JSON)."""

    scene_number: int = Field(ge=1)
    scene_label: str = ""
    visual_prompt_excerpt: str = ""
    motion_summary: str = ""
    editor_note: str = ""


class CSVShotlistRow(BaseModel):
    """BA 10.5 — CSV-taugliche Shotlist (gleiche Logik wie CapCut, separates Feld für Export-Pfade)."""

    scene_number: int = Field(ge=1)
    scene_label: str = ""
    visual_prompt_excerpt: str = ""
    motion_summary: str = ""
    editor_note: str = ""


class ProviderPromptOptimizeResponse(BaseModel):
    """BA 10.5 — Produktionsnahe Provider-Artefakte aus Export-Paket + Optimierern."""

    provider_profile: str = ""
    optimized_prompts: ProviderOptimizedPromptsBundle = Field(
        default_factory=ProviderOptimizedPromptsBundle
    )
    thumbnail_variants: List[ThumbnailVariantSpec] = Field(default_factory=list)
    capcut_shotlist: List[CapCutShotlistRow] = Field(default_factory=list)
    csv_shotlist: List[CSVShotlistRow] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ThumbnailCTRRequest(BaseModel):
    """BA 10.5 — Heuristische CTR-Schätzung ohne Bildanalyse."""

    title: str = ""
    hook: str = ""
    video_template: str = Field(default="generic")
    thumbnail_prompt: str = ""
    chapters: List[Chapter] = Field(default_factory=list)


class ThumbnailCTRResponse(BaseModel):
    ctr_score: int = Field(ge=0, le=100, default=0)
    thumbnail_variants: List[ThumbnailVariantSpec] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ExportFormatDescriptor(BaseModel):
    """BA 10.5 — Eintrag im Export-Format-Registry."""

    id: str
    label: str = ""
    description: str = ""
    content_type: str = Field(default="application/json", description="MIME oder text/csv")
    source_endpoint: str = Field(
        default="",
        description="Hinweis z. B. POST /story-engine/export-package — nur Dokumentation.",
    )


class ExportFormatsResponse(BaseModel):
    """BA 10.5 — Registry der unterstützten Export-/Produktionspfade (read-only)."""

    json_export: ExportFormatDescriptor
    capcut_shotlist: ExportFormatDescriptor
    csv_shotlist: ExportFormatDescriptor
    thumbnail_variants: ExportFormatDescriptor
    provider_prompt_bundle: ExportFormatDescriptor
    warnings: List[str] = Field(default_factory=list)


class LatestVideosRequest(BaseModel):
    channel_url: str = Field(..., min_length=1)
    max_results: int = Field(5, ge=1, le=50)


class LatestVideoItem(BaseModel):
    title: str
    url: str
    video_id: str
    published_at: str
    summary: str
    score: int
    reason: str


class LatestVideosResponse(BaseModel):
    channel: str
    videos: List[LatestVideoItem]
    warnings: List[str]


SourceTypeLiteral = Literal["youtube_transcript", "news_article", "unknown"]
SeverityLiteral = Literal["info", "warning", "critical"]
RiskLevelLiteral = Literal["low", "medium", "high"]
RecPriorityLiteral = Literal["low", "medium", "high"]


class ReviewScriptRequest(BaseModel):
    source_url: str = ""
    source_type: SourceTypeLiteral = "unknown"
    source_text: str = ""
    generated_script: str = ""
    target_language: str = "de"
    prior_warnings: List[str] = Field(default_factory=list)
    video_template: str = Field(
        default="generic",
        description=(
            "BA 9.1: optional; gleiche Template-IDs wie Generate — "
            "beeinflusst zusätzliche Review-Hinweise, nicht den Heuristik-Kern."
        ),
    )
    hook_text: str = Field(
        default="",
        description="BA 9.2: optional; Opening-Zeile zur Template-Passung (sonst erste Zeile des Skripts).",
    )
    hook_type: str = Field(
        default="",
        description="BA 9.2: optional; z. B. shock_reveal — Abgleich mit Heuristik.",
    )

    @model_validator(mode="after")
    def at_least_one_text_field(self):
        if not (self.source_text or "").strip() and not (self.generated_script or "").strip():
            raise ValueError(
                "At least one of source_text or generated_script must be non-empty."
            )
        return self


class SimilarityFlag(BaseModel):
    flag_type: str
    severity: SeverityLiteral
    detail: str
    evidence_hint: Optional[str] = None


class ReviewIssue(BaseModel):
    severity: SeverityLiteral
    code: str
    message: str
    evidence_hint: Optional[str] = None


class ReviewRecommendation(BaseModel):
    priority: RecPriorityLiteral
    action: str
    rationale: str


class ReviewScriptResponse(BaseModel):
    risk_level: RiskLevelLiteral
    originality_score: int = Field(ge=0, le=100)
    similarity_flags: List[SimilarityFlag]
    issues: List[ReviewIssue]
    recommendations: List[ReviewRecommendation]
    warnings: List[str]