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