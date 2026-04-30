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