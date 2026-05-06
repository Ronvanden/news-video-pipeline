"""BA 10.5 — Export-Format-Registry (read-only, ohne Persistenz)."""

from __future__ import annotations

from typing import List

from app.models import ExportFormatDescriptor, ExportFormatsResponse


def _dedupe_warnings(ws: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for w in ws or []:
        key = (w or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def list_export_formats() -> ExportFormatsResponse:
    """Statische Registry — Hinweise auf bestehende BA-10.x Endpunkte."""
    warns = _dedupe_warnings(
        [
            "[export_formats] Registry V1 — Felder beschreiben logische Artefakte; "
            "konkrete Bytes entstehen über die genannten Producer-Endpunkte.",
        ]
    )
    return ExportFormatsResponse(
        json_export=ExportFormatDescriptor(
            id="json_export",
            label="JSON Export-Paket",
            description="Vollständiges Prompt-Paket inkl. Hook, Rhythm, Scene-Plan, Provider-Stubs.",
            content_type="application/json",
            source_endpoint="POST /story-engine/export-package",
        ),
        capcut_shotlist=ExportFormatDescriptor(
            id="capcut_shotlist",
            label="CapCut Shotlist (JSON-Zeilen)",
            description="Szenenweise Editor-Notizen und Motion-Kurzfassung als JSON-Array.",
            content_type="application/json",
            source_endpoint="POST /story-engine/provider-prompts/optimize",
        ),
        csv_shotlist=ExportFormatDescriptor(
            id="csv_shotlist",
            label="CSV Shotlist (logisch)",
            description="Tabellarische Shotlist-Spalten (scene, label, visual, motion, note) — Client-CSV aus JSON.",
            content_type="text/csv",
            source_endpoint="POST /story-engine/provider-prompts/optimize",
        ),
        thumbnail_variants=ExportFormatDescriptor(
            id="thumbnail_variants",
            label="Thumbnail Textvarianten",
            description="Headline/Overlay/Emotion-Tags für CTR- und Design-Pfade.",
            content_type="application/json",
            source_endpoint="POST /story-engine/thumbnail-ctr",
        ),
        provider_prompt_bundle=ExportFormatDescriptor(
            id="provider_prompt_bundle",
            label="Provider Prompt Bundle",
            description="Aggregierte optimierte Prompts je Profil (Leonardo/Kling/OpenAI).",
            content_type="application/json",
            source_endpoint="POST /story-engine/provider-prompts/optimize",
        ),
        warnings=warns,
    )
