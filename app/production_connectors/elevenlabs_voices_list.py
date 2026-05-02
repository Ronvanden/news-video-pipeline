"""List ElevenLabs voices with safe output only."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

ELEVENLABS_VOICES_ENDPOINT = "https://api.elevenlabs.io/v1/voices"


class ElevenLabsVoiceInfo(BaseModel):
    """Safe subset of one ElevenLabs voice row."""

    voice_id: str = ""
    name: str = ""
    category: Optional[str] = None
    labels: Optional[Dict[str, Any]] = None


class ElevenLabsVoicesListResult(BaseModel):
    """Internal result with safe diagnostics kept separate from CLI rows."""

    voices: List[ElevenLabsVoiceInfo] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    def safe_output(self) -> List[Dict[str, Any]]:
        return [voice.model_dump(exclude_none=True) for voice in self.voices]


def _safe_voice(row: Any) -> Optional[ElevenLabsVoiceInfo]:
    if not isinstance(row, dict):
        return None
    voice_id = row.get("voice_id")
    name = row.get("name")
    if not isinstance(voice_id, str) or not voice_id.strip():
        return None
    if not isinstance(name, str) or not name.strip():
        return None
    category = row.get("category")
    labels = row.get("labels")
    return ElevenLabsVoiceInfo(
        voice_id=voice_id.strip(),
        name=name.strip(),
        category=category.strip() if isinstance(category, str) and category.strip() else None,
        labels=labels if isinstance(labels, dict) and labels else None,
    )


def list_elevenlabs_voices(*, timeout_seconds: float = 20.0) -> ElevenLabsVoicesListResult:
    """Fetch ElevenLabs voices and return only non-secret metadata."""
    api_key = (os.getenv("VOICE_API_KEY") or "").strip()
    if not api_key:
        return ElevenLabsVoicesListResult(warnings=["voice_api_key_missing_no_http_attempt"])

    request = Request(
        ELEVENLABS_VOICES_ENDPOINT,
        method="GET",
        headers={
            "xi-api-key": api_key,
            "accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
    except HTTPError as exc:
        return ElevenLabsVoicesListResult(warnings=[f"elevenlabs_voices_http_error:{exc.code}"])
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        return ElevenLabsVoicesListResult(warnings=[f"elevenlabs_voices_url_error:{reason}"])

    try:
        parsed = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return ElevenLabsVoicesListResult(warnings=["elevenlabs_voices_response_not_json"])
    if not isinstance(parsed, dict):
        return ElevenLabsVoicesListResult(warnings=["elevenlabs_voices_response_not_object"])

    rows = parsed.get("voices")
    if not isinstance(rows, list):
        return ElevenLabsVoicesListResult(warnings=["elevenlabs_voices_missing_voices_list"])

    voices = [voice for row in rows if (voice := _safe_voice(row)) is not None]
    warnings: List[str] = []
    if len(voices) != len(rows):
        warnings.append("elevenlabs_voices_skipped_invalid_rows")
    return ElevenLabsVoicesListResult(voices=voices, warnings=warnings)
