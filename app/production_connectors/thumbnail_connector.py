"""BA 10.0 — Thumbnail Connector Stub (Dry-Run, keine API)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.production_connectors.base import BaseProductionConnector


class ThumbnailProductionConnector(BaseProductionConnector):
    provider_name = "Thumbnail (stub)"
    provider_type = "thumbnail"

    def validate_payload(self, payload: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        warns: List[str] = []
        blockers: List[str] = []
        hk = (payload.get("hook") or "").strip()
        ta = (payload.get("thumbnail_angle") or "").strip()
        if not hk:
            blockers.append("thumbnail_payload_missing_hook")
            return False, warns, blockers
        if not ta:
            blockers.append("thumbnail_payload_missing_thumbnail_angle")
            return False, warns, blockers
        return True, warns, blockers

    def build_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "provider": "thumbnail_stub",
            "operation": "composite_thumbnail",
            "hook": payload.get("hook", ""),
            "thumbnail_angle": payload.get("thumbnail_angle", ""),
            "composite_prompt": payload.get("composite_prompt", ""),
            "dry_run": True,
        }
