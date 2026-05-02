"""BA 10.0 — Kling Video Connector (Dry-Run, keine API)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.production_connectors.base import BaseProductionConnector


class KlingProductionConnector(BaseProductionConnector):
    provider_name = "Kling"
    provider_type = "video"

    def validate_payload(self, payload: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        warns: List[str] = []
        blockers: List[str] = []
        motion = payload.get("motion_prompts")
        if not isinstance(motion, list) or len(motion) == 0:
            blockers.append("video_payload_missing_motion_prompts")
            return False, warns, blockers
        for i, item in enumerate(motion):
            if not isinstance(item, dict):
                blockers.append(f"motion_prompt_invalid_entry_{i}")
                return False, warns, blockers
            if not (item.get("motion_prompt") or "").strip():
                blockers.append(f"motion_prompt_empty_beat_{i}")
                return False, warns, blockers
        return True, warns, blockers

    def build_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "provider": "Kling",
            "operation": "video_motion_sequence",
            "motion_prompts": list(payload.get("motion_prompts") or []),
            "dry_run": True,
        }
