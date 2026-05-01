"""Voice TTS‑Provider-Vertrag (Phase 7.2) — herstellerunabhängiges Interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Protocol, runtime_checkable


@dataclass
class VoiceSynthRequest:
    """Ein Synthese‑Segment (MVP: ein VoiceBlock entspricht einem Request)."""

    text: str
    voice: Optional[str] = None
    model: Optional[str] = None


@dataclass
class VoiceSynthChunkResult:
    """Rohe Audiodaten pro Aufruf; bei Fehler bleiben ``audio_bytes`` leer."""

    audio_bytes: bytes = b""
    mime_type: str = "audio/mpeg"
    warnings: List[str] = field(default_factory=list)


@runtime_checkable
class VoiceSynthProvider(Protocol):
    def synthesize(self, request: VoiceSynthRequest) -> VoiceSynthChunkResult:
        ...