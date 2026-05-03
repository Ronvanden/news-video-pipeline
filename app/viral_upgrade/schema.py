"""BA 17.0 — Viral Upgrade Layer (Founder-only, advisory, kein API)."""

from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field

EmotionalDriver = Literal[
    "curiosity",
    "urgency",
    "hope",
    "concern",
    "surprise",
    "neutral",
]
AudienceMode = Literal[
    "general_public",
    "news_literate",
    "niche_insider",
    "mixed",
]


class ViralUpgradeLayerResult(BaseModel):
    """Nur Verpackungsvorschläge — überschreibt kein Skript, kein Auto-Publish."""

    layer_version: str = "17.0-v1"
    advisory_only: bool = True
    viral_title_variants: List[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Drei CTR-orientierte Titel-Ideen; redaktionell prüfen.",
    )
    hook_intensity_score: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Heuristik 0–100 aus Hook-Länge, Satzzeichen, plan.hook_score.",
    )
    thumbnail_angle_variants: List[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Drei Thumbnail-Winkel als Textprompts für Founder/Designer.",
    )
    emotional_driver: EmotionalDriver = "neutral"
    audience_mode: AudienceMode = "mixed"
    caution_flags: List[str] = Field(
        default_factory=list,
        description="Risiko-Hinweise (z. B. Sensationalismus, absolute Claims).",
    )
    founder_note: str = Field(
        default="",
        description="Kurzempfehlung: Vorschläge sind heuristisch, Fakten nicht verschärfen.",
    )
    checked_signals: List[str] = Field(
        default_factory=list,
        description="Welche Plan-/Story-Signale die Heuristik genutzt hat.",
    )
