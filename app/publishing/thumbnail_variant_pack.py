"""BA 13.2 — Thumbnail Variant Pack."""

from __future__ import annotations

from typing import List

from app.publishing.schema import ThumbnailVariant, ThumbnailVariantPackResult


def _short_headline(text: str, fallback: str) -> str:
    cleaned = " ".join((text or fallback).split())
    return cleaned[:42].rstrip()


def build_thumbnail_variant_pack(plan: object) -> ThumbnailVariantPackResult:
    warnings: List[str] = []
    base_angle = (getattr(plan, "thumbnail_angle", "") or "").strip()
    hook = getattr(plan, "hook", "") or "Diese Story wirft Fragen auf"
    title = _short_headline(hook, "Was steckt dahinter?")

    angles = [
        ("curiosity", "Die offene Frage", "Kontrastreiches Motiv mit Frage-Fokus"),
        ("urgency", "Warum jetzt?", "Dramatische Nahaufnahme, klare Zeitmarke"),
        ("authority", "Die Faktenlage", "Seriöse Doku-Optik, Quellen-/Akten-Anmutung"),
        ("emotional", "Der menschliche Kern", "Gesicht/Ort im Mittelpunkt, emotionale Spannung"),
    ]
    variants = [
        ThumbnailVariant(
            variant_id=f"thumb_{idx}_{key}",
            angle=key if not base_angle else f"{key}:{base_angle}",
            headline_text=_short_headline(f"{headline}: {title}", headline),
            visual_direction=direction,
            emotional_trigger=key,
        )
        for idx, (key, headline, direction) in enumerate(angles, start=1)
    ]

    if not base_angle:
        warnings.append("thumbnail_angle_missing_using_generic_variants")

    return ThumbnailVariantPackResult(
        variant_status="complete" if variants else "blocked",
        variants=variants,
        recommended_primary=variants[0].variant_id if variants else "",
        visual_hooks=[v.headline_text for v in variants],
        warnings=warnings,
    )
