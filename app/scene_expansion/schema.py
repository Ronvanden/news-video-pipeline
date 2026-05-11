"""BA 18.0 — Multi-Scene Asset Expansion (Plan-only, keine Provider-Calls)."""

from __future__ import annotations

from typing import Dict, List, Literal

from pydantic import BaseModel, Field

AssetBeatType = Literal["image", "broll", "establishing", "detail"]


class ExpandedSceneAssetBeat(BaseModel):
    """Ein visueller Beat innerhalb eines Kapitels (Produktions-Prompt, kein Binary)."""

    chapter_index: int = Field(ge=0, description="0-basiert, aligned mit chapter_outline.")
    beat_index: int = Field(ge=0, description="0-basiert innerhalb des Kapitels.")
    visual_prompt: str = Field(default="", description="Bild-/Video-Generierungstext (Founder-editierbar).")
    visual_prompt_raw: str = Field(default="", description="Rohprompt vor finalen Visual Guards.")
    visual_prompt_effective: str = Field(default="", description="Effektiver Prompt inklusive Visual Guards.")
    negative_prompt: str = Field(default="", description="Negative Guards fuer Bild-/Video-Provider.")
    visual_policy_warnings: List[str] = Field(default_factory=list)
    visual_style_profile: str = ""
    prompt_quality_score: int = Field(default=0, ge=0, le=100)
    prompt_risk_flags: List[str] = Field(default_factory=list)
    normalized_controls: Dict[str, str] = Field(default_factory=dict)
    camera_motion_hint: str = Field(default="", description="Kamera/Motion-Heuristik für Schnitt/Gen.")
    duration_seconds: int = Field(default=8, ge=1, le=120, description="Zielsegmentlänge Heuristik.")
    asset_type: AssetBeatType = "image"
    continuity_note: str = Field(default="", description="Bezug zu vorherigem Beat / Kapitel.")
    safety_notes: List[str] = Field(
        default_factory=list,
        description="z. B. keine Gewaltgrafik, keine erfundenen Ortsfakten.",
    )


class SceneExpansionResult(BaseModel):
    """2–3 Beats pro Kapitel — Vorbereitung für 20–40 Assets bei längerem Video."""

    layer_version: str = "18.0-v1"
    plan_only: bool = True
    beats_per_chapter_default: int = Field(default=3, ge=2, le=3)
    expanded_scene_assets: List[ExpandedSceneAssetBeat] = Field(default_factory=list)
    founder_note: str = Field(
        default="",
        description="Kurzhinweis: Beats sind Heuristiken; gegen Quelle und Plattform-Policy prüfen.",
    )
    checked_signals: List[str] = Field(
        default_factory=list,
        description="Welche Plan-Felder für Expansion genutzt wurden.",
    )
