"""Persist an isolated ElevenLabs voice smoke-test response as MP3."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

from app.production_connectors.voice_live_connector import (
    _build_elevenlabs_tts_endpoint,
    _build_voice_generation_payload,
    _voice_id,
)
from app.production_connectors.voice_smoke_test import MINIMAL_VOICE_SMOKE_PAYLOAD

DEFAULT_VOICE_SMOKE_OUTPUT_PATH = Path("output") / "voice_smoke_test_output.mp3"


class VoiceSmokeFileSaveResult(BaseModel):
    """Safe CLI result for a persisted Voice smoke-test MP3."""

    http_status: Optional[int] = None
    file_saved: bool = False
    output_path: str = str(DEFAULT_VOICE_SMOKE_OUTPUT_PATH)
    file_size_bytes: int = 0
    warnings: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)


def run_voice_smoke_test_and_save(
    *,
    output_path: Path | str = DEFAULT_VOICE_SMOKE_OUTPUT_PATH,
    timeout_seconds: float = 25.0,
) -> VoiceSmokeFileSaveResult:
    """Call ElevenLabs TTS once and save the binary response as MP3."""
    target = Path(output_path)
    api_key = (os.getenv("VOICE_API_KEY") or "").strip()
    endpoint_base = (os.getenv("VOICE_API_ENDPOINT") or "").strip()

    warnings: List[str] = []
    if not endpoint_base:
        warnings.append("voice_live_endpoint_missing_no_file_saved")
    if not api_key:
        warnings.append("voice_api_key_missing_no_file_saved")
    if warnings:
        return VoiceSmokeFileSaveResult(
            output_path=str(target),
            warnings=warnings,
            blocking_reasons=["voice_live_env_missing"],
        )

    endpoint = _build_elevenlabs_tts_endpoint(endpoint_base, _voice_id())
    body = json.dumps(_build_voice_generation_payload(MINIMAL_VOICE_SMOKE_PAYLOAD)).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        },
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw_bytes = response.read()
            status = getattr(response, "status", None) or response.getcode()
    except HTTPError as exc:
        return VoiceSmokeFileSaveResult(
            http_status=int(exc.code),
            output_path=str(target),
            warnings=[f"voice_http_error:{exc.code}"],
            blocking_reasons=[],
        )
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        return VoiceSmokeFileSaveResult(
            output_path=str(target),
            warnings=[f"voice_url_error:{reason}"],
            blocking_reasons=[],
        )

    if not raw_bytes:
        return VoiceSmokeFileSaveResult(
            http_status=int(status) if status is not None else None,
            output_path=str(target),
            warnings=["voice_response_empty_no_file_saved"],
            blocking_reasons=["voice_response_empty"],
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw_bytes)
    file_size = target.stat().st_size
    return VoiceSmokeFileSaveResult(
        http_status=int(status) if status is not None else None,
        file_saved=True,
        output_path=str(target),
        file_size_bytes=file_size,
        warnings=[],
        blocking_reasons=[],
    )
