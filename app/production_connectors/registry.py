"""BA 10.0 — Zentrale Connector-Registry (Dry-Run Adapter)."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.production_connectors.base import BaseProductionConnector
from app.production_connectors.kling_connector import KlingProductionConnector
from app.production_connectors.leonardo_connector import LeonardoProductionConnector
from app.production_connectors.render_connector import RenderProductionConnector
from app.production_connectors.thumbnail_connector import ThumbnailProductionConnector
from app.production_connectors.voice_connector import VoiceProductionConnector

_BY_TYPE: Dict[str, BaseProductionConnector] = {
    "image": LeonardoProductionConnector(),
    "video": KlingProductionConnector(),
    "voice": VoiceProductionConnector(),
    "thumbnail": ThumbnailProductionConnector(),
    "render": RenderProductionConnector(),
}

_ALIASES = {
    "leonardo": "image",
    "kling": "video",
    "voice": "voice",
    "openai / elevenlabs (stub)": "voice",
    "thumbnail (stub)": "thumbnail",
    "thumbnail": "thumbnail",
    "render timeline (stub)": "render",
    "render": "render",
}


def get_connector(provider_name: str) -> Optional[BaseProductionConnector]:
    """Liefert Connector nach Rolle oder Provider-Anzeigenamen."""
    key = (provider_name or "").strip().lower()
    if not key:
        return None
    if key in _BY_TYPE:
        return _BY_TYPE[key]
    role = _ALIASES.get(key)
    if role:
        return _BY_TYPE.get(role)
    return None


def list_available_connectors() -> List[Dict[str, str]]:
    seen = set()
    out: List[Dict[str, str]] = []
    for c in _BY_TYPE.values():
        uid = c.provider_type
        if uid in seen:
            continue
        seen.add(uid)
        out.append({"provider_name": c.provider_name, "provider_type": c.provider_type})
    return sorted(out, key=lambda x: x["provider_type"])
