"""BA 10.0 — Leonardo Image Connector (Dry-Run, keine API)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.production_connectors.base import BaseProductionConnector


class LeonardoProductionConnector(BaseProductionConnector):
    provider_name = "Leonardo"
    provider_type = "image"

    def validate_payload(self, payload: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        warns: List[str] = []
        blockers: List[str] = []
        prompts = payload.get("prompts")
        if not isinstance(prompts, list) or len(prompts) == 0:
            blockers.append("image_payload_missing_prompts")
            return False, warns, blockers
        if not all(isinstance(p, str) and p.strip() for p in prompts):
            blockers.append("image_payload_prompts_non_string_or_empty")
            return False, warns, blockers
        if not (payload.get("style_profile") or "").strip():
            warns.append("style_profile_empty_connector_warn")
        return True, warns, blockers

    def build_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "provider": "Leonardo",
            "operation": "image_generation_batch",
            "style_profile": payload.get("style_profile", ""),
            "prompts": list(payload.get("prompts") or []),
            "dry_run": True,
        }
