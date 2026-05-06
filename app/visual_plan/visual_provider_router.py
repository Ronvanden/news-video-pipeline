"""BA 26.4b — Zentraler Visual-Provider-Router (Disposition, keine API-Calls)."""

from __future__ import annotations

from typing import Any, Dict

VisualAssetKindNormalized = str

_OVERLAY_KINDS = frozenset(
    {
        "final_text_overlay",
        "subtitle",
        "lower_third",
        "title_card",
        "label",
    }
)

_KNOWN_KIND_ALIASES: Dict[str, VisualAssetKindNormalized] = {
    "b_roll": "cinematic_broll",
    "broll": "cinematic_broll",
    "atmospheric_still": "atmosphere_still",
    "atmosphere": "atmosphere_still",
    "motion": "motion_clip",
    "video": "motion_clip",
    "video_clip": "motion_clip",
    "thumb": "thumbnail_base",
    "thumbnail": "thumbnail_base",
}


def normalize_visual_asset_kind(kind: str) -> VisualAssetKindNormalized:
    k = (kind or "").strip().lower().replace("-", "_")
    return _KNOWN_KIND_ALIASES.get(k, k)


def route_visual_provider(
    asset_kind: str,
    *,
    text_sensitive: bool = False,
) -> Dict[str, Any]:
    """
    Liefert dispositionierte Provider-IDs für Bild-/Motion-Pfade.

    Semantik (Projektregel BA 26.4b):
    - text_sensitive → openai_images (Kompositions-/Keyframe-Pfad)
    - cinematic_broll / atmosphere_still → leonardo
    - motion_clip → runway
    - thumbnail_base → openai_images
    - Overlay-Arten → render_layer (+ image_provider für Basis-Still)
    """
    k = normalize_visual_asset_kind(asset_kind)

    if k in _OVERLAY_KINDS:
        img = "openai_images" if text_sensitive else "leonardo"
        return {"provider": "render_layer", "image_provider": img}

    if text_sensitive:
        return {"provider": "openai_images", "image_provider": ""}

    if k in ("cinematic_broll", "atmosphere_still"):
        return {"provider": "leonardo", "image_provider": ""}

    if k in ("motion_clip",):
        return {"provider": "runway", "image_provider": ""}

    if k in ("thumbnail_base", "keyframe_still", "keyframe"):
        return {"provider": "openai_images", "image_provider": ""}

    # konservativer Default: stimmungsvolle B-Roll-Pfade
    return {"provider": "leonardo", "image_provider": ""}
