"""BA 10.0 — Render / Timeline Connector Stub (Dry-Run, keine API)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.production_connectors.base import BaseProductionConnector


class RenderProductionConnector(BaseProductionConnector):
    provider_name = "Render timeline (stub)"
    provider_type = "render"

    def validate_payload(self, payload: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        warns: List[str] = []
        blockers: List[str] = []
        tl = payload.get("timeline_skeleton")
        if not isinstance(tl, list) or len(tl) == 0:
            blockers.append("render_payload_missing_timeline_skeleton")
            return False, warns, blockers
        for i, row in enumerate(tl):
            if not isinstance(row, dict):
                blockers.append(f"timeline_row_invalid_{i}")
                return False, warns, blockers
            if not (row.get("chapter_title") or "").strip():
                blockers.append(f"timeline_row_missing_title_{i}")
                return False, warns, blockers
        return True, warns, blockers

    def build_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "provider": "render_stub",
            "operation": "timeline_assemble",
            "timeline_skeleton": list(payload.get("timeline_skeleton") or []),
            "dry_run": True,
        }
