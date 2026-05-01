"""OpenAI Speech API (`/v1/audio/speech`) für Phase 7.2 Preview."""

from __future__ import annotations

import logging
from typing import List

import httpx

from app.voice import warning_codes as vw
from app.voice.contracts import VoiceSynthChunkResult, VoiceSynthRequest

logger = logging.getLogger(__name__)

OPENAI_SPEECH_URL = "https://api.openai.com/v1/audio/speech"
# Öffentliche Doku: Eingaben sind begrenzt; konservative Kappe für Preview.
_MAX_INPUT_CHARS = 4096


class OpenAiTtsProvider:
    """Synchroner Minimal‑Adapter — keine Persistenz."""

    def __init__(
        self,
        api_key: str,
        *,
        default_voice: str,
        default_model: str,
        timeout_seconds: float = 60.0,
    ) -> None:
        self._api_key = (api_key or "").strip()
        self._default_voice = (default_voice or "alloy").strip() or "alloy"
        self._default_model = (default_model or "tts-1").strip() or "tts-1"
        self._timeout = timeout_seconds

    def synthesize(self, request: VoiceSynthRequest) -> VoiceSynthChunkResult:
        warns: List[str] = list()
        raw = request.text if request.text is not None else ""
        text = raw.strip()
        if len(text) > _MAX_INPUT_CHARS:
            warns.append(
                f"{vw.W_INPUT_TRUNCATED} "
                f"Voice‑Text auf {_MAX_INPUT_CHARS} Zeichen gekürzt für OpenAI Speech."
            )
            text = text[:_MAX_INPUT_CHARS]

        if not text:
            return VoiceSynthChunkResult(
                audio_bytes=b"",
                mime_type="audio/mpeg",
                warnings=["[voice_synth:empty_text] Kein Voice‑Text nach Trim."],
            )

        if not self._api_key:
            return VoiceSynthChunkResult(
                audio_bytes=b"",
                mime_type="audio/mpeg",
                warnings=[
                    f"{vw.W_MISSING_KEY} OPENAI_API_KEY ist nicht gesetzt (leer)."
                ],
            )

        voice = (request.voice or self._default_voice).strip() or self._default_voice
        model = (request.model or self._default_model).strip() or self._default_model
        payload = {
            "model": model,
            "voice": voice,
            "input": text,
            "response_format": "mp3",
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
        }
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    OPENAI_SPEECH_URL,
                    headers=headers,
                    json=payload,
                )
        except Exception as exc:  # pragma: no cover — httpx-Netzwerk
            logger.warning("OpenAI TTS transport failed type=%s", type(exc).__name__)
            return VoiceSynthChunkResult(
                audio_bytes=b"",
                mime_type="audio/mpeg",
                warnings=[
                    f"{vw.W_TRANSPORT_ERROR} "
                    f"Verbindungsfehler ({type(exc).__name__}); kein Audio."
                ],
            )

        if resp.status_code != 200:
            return VoiceSynthChunkResult(
                audio_bytes=b"",
                mime_type="audio/mpeg",
                warnings=[
                    f"{vw.W_HTTP_ERROR} "
                    f"OpenAI Speech HTTP {resp.status_code} — ohne Response‑Body‑Logging."
                ],
            )

        data = resp.content or b""
        return VoiceSynthChunkResult(audio_bytes=data, mime_type="audio/mpeg", warnings=warns)
