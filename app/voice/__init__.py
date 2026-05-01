"""Phase 7.2 — TTS Provider Contract + OpenAI Speech Adapter."""

from app.voice.contracts import (
    VoiceSynthChunkResult,
    VoiceSynthProvider,
    VoiceSynthRequest,
)
from app.voice.openai_tts import OpenAiTtsProvider

__all__ = [
    "VoiceSynthChunkResult",
    "VoiceSynthProvider",
    "VoiceSynthRequest",
    "OpenAiTtsProvider",
]
