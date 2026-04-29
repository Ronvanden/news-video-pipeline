"""BA 6.8: Voice-Plan aus Scene-Assets (deterministisch, kein TTS)."""

from __future__ import annotations

from typing import List, Tuple

from app.utils import count_words
from app.watchlist.models import (
    ProductionJob,
    SceneAssetItem,
    SceneAssets,
    TtsProviderHintLiteral,
    VoiceBlock,
    VoiceProfileLiteral,
)

_VOICE_WORDS_PER_MINUTE = 140

_TTS_ROTATION: List[TtsProviderHintLiteral] = [
    "elevenlabs",
    "openai",
    "google",
    "generic",
]


def estimate_speech_seconds_from_text(text: str) -> int:
    w = max(0, count_words(text or ""))
    if w == 0:
        return 1
    return max(1, int(round(w * 60.0 / _VOICE_WORDS_PER_MINUTE)))


def speaker_style_for_profile(
    voice_profile: VoiceProfileLiteral,
    narrator_style: str,
) -> str:
    raw = (narrator_style or "").strip()
    if raw:
        return raw[:200]
    if voice_profile == "news":
        return "Klare Nachrichtensprecher-Anmut, moderates Tempo."
    if voice_profile == "dramatic":
        return "Warm, leicht dramatisches Storytelling, klare Zwischenätz."
    if voice_profile == "soft":
        return "Weicher Sprechmodus, keine Überschlagung."
    return "Neutral-dokumentarisch; verständliche Artikulation."


def build_voice_blocks(
    pj: ProductionJob,
    assets: SceneAssets,
    *,
    voice_profile: VoiceProfileLiteral,
) -> Tuple[List[VoiceBlock], List[str]]:
    narrator = pj.narrator_style or ""
    speaker_base = speaker_style_for_profile(voice_profile, narrator)
    warns: List[str] = []
    blocks: List[VoiceBlock] = []
    scenes = sorted(list(assets.scenes or []), key=lambda s: s.scene_number)
    if not scenes:
        warns.append("Scene assets enthalten keine Szenen — Voice Plan leer.")
        return blocks, warns

    for sc in scenes:
        assert isinstance(sc, SceneAssetItem)
        voice_text = (sc.voiceover_chunk or "").strip()
        title = (sc.title or f"Szene {sc.scene_number}").strip()
        if not voice_text:
            voice_text = f"{title}. (Voiceover nicht vorbelegt.)"
            warns.append(f"Szene {sc.scene_number}: voiceover_chunk war leer — Fallback-Titel verwendet.")

        pause = 0.25
        mood = (sc.mood or "").lower()
        if "dramat" in mood:
            pause = 0.45
        elif "explainer" in mood or mood == "neutral":
            pause = 0.35

        tts_hint = _TTS_ROTATION[(max(1, sc.scene_number) - 1) % len(_TTS_ROTATION)]

        pronunciation = ""
        if any(x in voice_text for x in ("EU", "UN", "IMF")):
            pronunciation = "Abkürzungen jeweils buchstabieren wenn unklar."
        speaker = speaker_base
        if voice_profile != "dramatic" and speaker_base.startswith("Neutral") and (
            mood == "dramatic" or "dram" in mood
        ):
            speaker = speaker_base.replace("Neutral-", "Etwas betontes ", 1)

        blocks.append(
            VoiceBlock(
                scene_number=sc.scene_number,
                title=title,
                voice_text=voice_text,
                estimated_duration_seconds=estimate_speech_seconds_from_text(voice_text),
                speaker_style=speaker,
                pause_after_seconds=pause,
                tts_provider_hint=tts_hint,
                pronunciation_notes=pronunciation[:500],
            )
        )

    return blocks, warns


def decide_voice_plan_status(blocks: List[VoiceBlock], assets: SceneAssets) -> str:
    if (assets.status or "") != "ready":
        return "failed"
    if not blocks:
        return "failed"
    empty_chunks = sum(
        1
        for s in assets.scenes or []
        if not (str(getattr(s, "voiceover_chunk", "") or "").strip())
    )
    if empty_chunks == len(assets.scenes or []) and len(assets.scenes or []) > 0:
        return "failed"
    return "ready"
