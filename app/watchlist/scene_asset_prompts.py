"""BA 6.7: deterministische Prompt-Entwürfe pro Szene (kein externer Generator)."""

from __future__ import annotations

from typing import List, Tuple

from app.watchlist.models import Scene, SceneAssetItem, SceneAssetStyleProfileLiteral


def _style_image_prefix(style: SceneAssetStyleProfileLiteral) -> str:
    if style == "documentary":
        return (
            "Documentary still, natural lighting, authentic B-roll feel, no readable text, "
            "no logos, no identifiable faces unless generic silhouette: "
        )
    if style == "news":
        return (
            "News broadcast visual, clean composition, professional, neutral palette, "
            "no readable logos or text, modern information graphics style hint: "
        )
    if style == "cinematic":
        return (
            "Cinematic wide shot mood, shallow depth of field, dramatic but tasteful grade, "
            "filmic lighting, no readable text, no specific real persons: "
        )
    if style == "faceless_youtube":
        return (
            "Faceless YouTube aesthetic, dynamic motion graphics friendly backdrop, "
            "bold shapes, no faces, no readable brand text, editorial illustration vibe: "
        )
    if style == "true_crime":
        return (
            "True-crime documentary tone, muted contrast, somber mood, archival reenactment "
            "suggestion without gore, silhouettes or symbolic objects only, no readable text: "
        )
    return ""


def _style_video_motion(style: SceneAssetStyleProfileLiteral) -> str:
    if style == "documentary":
        return "Slow tripod pan; subtle zoom; calm pacing."
    if style == "news":
        return "Steady lock-off with gentle push-in; crisp cuts implied."
    if style == "cinematic":
        return "Slow dolly-in; shallow focus pull; restrained camera move."
    if style == "faceless_youtube":
        return "Energetic but clean push transitions; graphic-friendly negative space."
    if style == "true_crime":
        return "Slow creep-in; low-key handheld micro-movement; restrained tension."
    return "Subtle camera move; match editorial tone."


def _style_camera_direction(style: SceneAssetStyleProfileLiteral, mood: str) -> str:
    base = _style_video_motion(style)
    m = (mood or "").lower()
    if "dramatic" in m:
        return f"{base} Emphasize contrast and restraint."
    if "explainer" in m:
        return f"{base} Keep frame balanced for overlay graphics."
    return base


def _thumbnail_hint(style: SceneAssetStyleProfileLiteral, title: str) -> str:
    t = (title or "").strip()[:80]
    if style == "documentary":
        return f"YouTube thumbnail concept, bold readable title area reserved (no real text rendered), subject: {t!s}, documentary tabloid-safe."
    if style == "news":
        return f"News-style thumbnail, high clarity, lower-third friendly, topic: {t!s}, avoid fake logos."
    if style == "cinematic":
        return f"Cinematic thumbnail still, strong silhouette or symbolic object, topic hint: {t!s}, no faces."
    if style == "faceless_youtube":
        return f"High-retention faceless thumbnail, strong central shape, topic: {t!s}, vibrant but not noisy."
    if style == "true_crime":
        return f"Moody true-crime thumbnail, foggy or low-key, abstract motif, topic: {t!s}, non-graphic."
    return f"Editorial thumbnail, clear focal point, topic: {t!s}."


def build_scene_asset_items(
    scenes: List[Scene],
    *,
    style_profile: SceneAssetStyleProfileLiteral,
) -> Tuple[List[SceneAssetItem], List[str]]:
    """Erzeugt Listen von Szenen-Assets; Warnungen nur bei Datenlücken."""
    warnings: List[str] = []
    items: List[SceneAssetItem] = []
    if not scenes:
        return [], ["Keine Szenen im Szenenplan — keine Asset-Prompts erzeugt."]

    for sc in scenes:
        vo = (sc.voiceover_text or "").strip()
        if not vo:
            warnings.append(
                f"Szene {sc.scene_number}: leerer Voiceover — Platzhalter-Prompts."
            )
        vis = (sc.visual_summary or "").strip() or vo[:300]

        img = _style_image_prefix(style_profile) + vis
        vid = (
            f"{_style_video_motion(style_profile)} Visual idea: {vis[:400]}. "
            f"Sync to voiceover pacing; no on-screen readable quotes."
        )
        thumb = _thumbnail_hint(style_profile, sc.title)
        cam = _style_camera_direction(style_profile, str(sc.mood))

        items.append(
            SceneAssetItem(
                scene_number=sc.scene_number,
                title=sc.title,
                voiceover_chunk=vo or "(voiceover empty)",
                image_prompt=img[:8000],
                video_prompt=vid[:8000],
                thumbnail_prompt=thumb[:8000],
                camera_direction=cam[:2000],
                mood=str(sc.mood),
                asset_type=sc.asset_type,
            )
        )

    return items, warnings

