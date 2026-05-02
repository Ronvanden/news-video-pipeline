"""BA 10.0 — Voice Connector Stub (Dry-Run, keine API)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.production_connectors.base import BaseProductionConnector


class VoiceProductionConnector(BaseProductionConnector):
    provider_name = "OpenAI / ElevenLabs (stub)"
    provider_type = "voice"

    def validate_payload(self, payload: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        warns: List[str] = []
        blockers: List[str] = []
        vs = (payload.get("voice_style") or "").strip()
        if not vs:
            blockers.append("voice_payload_missing_voice_style")
            return False, warns, blockers
        blocks = payload.get("chapter_voice_blocks")
        if not isinstance(blocks, list) or len(blocks) == 0:
            blockers.append("voice_payload_missing_chapter_voice_blocks")
            return False, warns, blockers
        return True, warns, blockers

    def build_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "provider": "voice_stub",
            "operation": "tts_chapter_blocks",
            "voice_style": payload.get("voice_style", ""),
            "chapter_voice_blocks": list(payload.get("chapter_voice_blocks") or []),
            "dry_run": True,
        }
