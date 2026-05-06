"""BA 20.3 — Voice & Visual Style Calibration (Founder-lokal, optional)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from app.visual_plan.visual_no_text import append_no_text_guard

# OpenAI TTS: nur dokumentierte Stimmen (tts-1).
VOICE_PRESET_OPENAI: Dict[str, str] = {
    "documentary_de": "onyx",
    "dramatic_documentary_de": "fable",
    "calm_explainer_de": "nova",
}

# ElevenLabs: Stabilität/Similarity — Voice-ID weiter über ELEVENLABS_VOICE_ID / Default.
VOICE_PRESET_ELEVENLABS_SETTINGS: Dict[str, Dict[str, Any]] = {
    "documentary_de": {"stability": 0.45, "similarity_boost": 0.72, "style": 0.0, "use_speaker_boost": True},
    "dramatic_documentary_de": {"stability": 0.32, "similarity_boost": 0.82, "style": 0.15, "use_speaker_boost": True},
    "calm_explainer_de": {"stability": 0.55, "similarity_boost": 0.62, "style": 0.0, "use_speaker_boost": True},
}

VISUAL_STYLE_PREFIX: Dict[str, str] = {
    "documentary_news": (
        "High-end news documentary still, desaturated palette, clear focal subject, "
        "broadcast-safe framing, factual serious atmosphere, no text overlay, no logos. "
        "Scene to illustrate:"
    ),
    "cinematic_explainer": (
        "Cinematic explainer still, soft volumetric light, shallow depth of field, "
        "editorial illustration quality, coherent single subject, no text overlay, no UI. "
        "Scene to illustrate:"
    ),
    "social_media_policy": (
        "Modern social-native visual still (16:9 canvas), strong readable silhouette, "
        "policy-neutral and brand-safe, no logos, no screenshots, no legible text. "
        "Scene to illustrate:"
    ),
}

_MAX_STYLED_PROMPT_CHARS = 3800


def resolve_voice_preset(
    voice_preset_raw: Optional[str],
) -> Tuple[str, Optional[str], Optional[Dict[str, Any]], List[str]]:
    """
    Rückgabe:
      - voice_preset_effective: Anzeige-ID oder "default"
      - openai_voice_override: nur gesetzt, wenn Preset aktiv und OpenAI genutzt werden soll
      - elevenlabs_voice_settings: nur bei bekanntem Preset für ElevenLabs-Body
    Env OPENAI_TTS_VOICE hat Vorrang vor Preset-OpenAI-Stimme (kein Bruch für bestehende Setups).
    """
    warns: List[str] = []
    raw = (voice_preset_raw or "").strip().lower()
    if not raw:
        return "default", None, None, warns

    if raw not in VOICE_PRESET_OPENAI:
        warns.append(f"voice_preset_unknown_defaulting_none:{raw}")
        return "default", None, None, warns

    env_oai = (os.environ.get("OPENAI_TTS_VOICE") or "").strip()
    if env_oai:
        oai = env_oai
        warns.append(f"voice_preset_openai_env_overrides:{raw}")
    else:
        oai = VOICE_PRESET_OPENAI[raw]

    el_set = dict(VOICE_PRESET_ELEVENLABS_SETTINGS[raw])
    return raw, oai, el_set, warns


def resolve_visual_style_preset(visual_style_preset_raw: Optional[str]) -> Tuple[str, List[str]]:
    """Liefert effective Preset-ID oder 'default' plus maximal eine Unknown-Warnung pro Aufruf."""
    warns: List[str] = []
    raw = (visual_style_preset_raw or "").strip().lower()
    if not raw:
        return "default", warns
    if raw not in VISUAL_STYLE_PREFIX:
        warns.append(f"visual_style_preset_unknown_defaulting_none:{raw}")
        return "default", warns
    return raw, warns


def apply_visual_style_to_prompt(visual_prompt: str, visual_style_preset_raw: Optional[str]) -> Tuple[str, List[str]]:
    """Hängt einen Stil-Präfix an den Leonardo-Prompt (bekannte Presets nur)."""
    warns: List[str] = []
    raw = (visual_style_preset_raw or "").strip().lower()
    if not raw or raw not in VISUAL_STYLE_PREFIX:
        return (visual_prompt or "").strip(), warns

    prefix = VISUAL_STYLE_PREFIX[raw].strip()
    vp = (visual_prompt or "").strip()
    combined = f"{prefix}\n\n{vp}" if vp else prefix
    if len(combined) > _MAX_STYLED_PROMPT_CHARS:
        combined = combined[:_MAX_STYLED_PROMPT_CHARS].rsplit(" ", 1)[0] + "…"
        warns.append("visual_style_prompt_truncated_for_leonardo_length")
    return append_no_text_guard(combined), warns
