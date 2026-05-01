"""BA 7.1–7.2: Download-Formate und Provider-Templates aus Render-Manifest (read-only, keine APIs)."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List, Optional, Tuple

from app.watchlist.models import GeneratedScript, ProductionJob, RenderManifest, VoicePlan
from app.watchlist.connector_export import build_story_pack_dict


def build_provider_templates(
    *,
    manifest: Optional[RenderManifest],
    voice_plan: Optional[VoicePlan],
    production_job: Optional[ProductionJob],
    generated_script: Optional[GeneratedScript],
    voice_artefakte: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """BA 7.2 — strukturierte Blöcke für ElevenLabs, Kling, Leonardo, CapCut, YouTube."""
    elevenlabs_ready: List[Dict[str, Any]] = []
    if voice_plan is not None:
        for b in voice_plan.blocks or []:
            elevenlabs_ready.append(
                {
                    "scene_number": b.scene_number,
                    "text": b.voice_text or "",
                    "voice_style": (b.speaker_style or "").strip()
                    or str(voice_plan.voice_profile or ""),
                }
            )

    kling_ready: List[Dict[str, Any]] = []
    leonardo_ready: List[Dict[str, Any]] = []
    timeline_order: List[int] = []
    duration_total = 0

    if manifest is not None:
        duration_total = int(manifest.estimated_total_duration_seconds or 0)
        for t in manifest.timeline or []:
            kling_ready.append(
                {"scene_number": t.scene_number, "prompt": t.video_prompt or ""}
            )
            leonardo_ready.append(
                {"scene_number": t.scene_number, "prompt": t.image_prompt or ""}
            )
            timeline_order.append(int(t.scene_number))

    capcut_ready: Dict[str, Any] = {
        "timeline_order": timeline_order,
        "duration_total": duration_total,
    }

    title = ""
    description = ""
    tags: List[str] = []
    if generated_script is not None:
        title = (generated_script.title or "").strip()
        description = (generated_script.hook or "").strip()
        if generated_script.chapters:
            tags = [
                (c.title or "").strip()
                for c in generated_script.chapters[:16]
                if (c.title or "").strip()
            ]
    if not title and production_job is not None:
        title = (
            (production_job.thumbnail_prompt or "")[:120].strip()
            or f"Production {production_job.id}"
        )

    youtube_upload_ready: Dict[str, Any] = {
        "title": title,
        "description": description,
        "tags": tags,
    }

    return {
        "elevenlabs_ready": elevenlabs_ready,
        "kling_ready": kling_ready,
        "leonardo_ready": leonardo_ready,
        "capcut_ready": capcut_ready,
        "youtube_upload_ready": youtube_upload_ready,
        "story_pack": build_story_pack_dict(generated_script=generated_script),
        "voice_artefakte": list(voice_artefakte or []),
    }


def build_json_export_package(
    *,
    manifest: RenderManifest,
    provider_templates: Dict[str, Any],
) -> bytes:
    payload: Dict[str, Any] = {
        "manifest": manifest.model_dump(mode="json"),
        "provider_templates": provider_templates,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    return text.encode("utf-8")


def build_markdown_export(
    *,
    manifest: RenderManifest,
    title: str,
) -> bytes:
    lines: List[str] = []
    head = (title or "").strip() or "Production Export"
    lines.append(f"# {head}")
    lines.append("")
    for t in manifest.timeline or []:
        lines.append(f"## Szene {t.scene_number}")
        lines.append("")
        lines.append(f"Voice: {t.voice_text or ''}")
        lines.append("")
        lines.append(f"Image Prompt: {t.image_prompt or ''}")
        lines.append("")
        lines.append(f"Video Prompt: {t.video_prompt or ''}")
        lines.append("")
    body = "\n".join(lines).strip() + "\n"
    return body.encode("utf-8")


def build_csv_export(*, manifest: RenderManifest) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        ["scene_number", "title", "voice", "image_prompt", "video_prompt", "duration"]
    )
    # Titel aus Szene optional: Timeline hat kein title — leer oder S{num}
    for t in manifest.timeline or []:
        w.writerow(
            [
                t.scene_number,
                f"Szene {t.scene_number}",
                t.voice_text or "",
                t.image_prompt or "",
                t.video_prompt or "",
                t.duration_seconds,
            ]
        )
    return buf.getvalue().encode("utf-8-sig")


def build_txt_export(*, manifest: RenderManifest, title: str) -> bytes:
    """Einfache CapCut-/Notiz-Ausgabe: nummerierte Blöcke."""
    lines: List[str] = []
    head = (title or "").strip() or "Production"
    lines.append(head)
    lines.append("=" * min(60, max(20, len(head) + 5)))
    lines.append("")
    for t in manifest.timeline or []:
        lines.append(f"[{t.scene_number}] Dauer ca. {t.duration_seconds}s")
        lines.append(f"VO: {t.voice_text or ''}")
        lines.append(f"BILD: {t.image_prompt or ''}")
        lines.append(f"VIDEO: {t.video_prompt or ''}")
        lines.append("")
    body = "\n".join(lines).strip() + "\n"
    return body.encode("utf-8")


def export_download_body(
    fmt: str,
    *,
    manifest: RenderManifest,
    provider_templates: Dict[str, Any],
    title: str,
) -> Tuple[bytes, str, str]:
    """Liefert (body, media_type, dateiname_suffix). fmt: json|markdown|csv|txt."""
    f = (fmt or "").strip().lower()
    if f == "json":
        return (
            build_json_export_package(
                manifest=manifest, provider_templates=provider_templates
            ),
            "application/json; charset=utf-8",
            "json",
        )
    if f == "markdown":
        return (
            build_markdown_export(manifest=manifest, title=title),
            "text/markdown; charset=utf-8",
            "md",
        )
    if f == "csv":
        return (
            build_csv_export(manifest=manifest),
            "text/csv; charset=utf-8",
            "csv",
        )
    if f == "txt":
        return (
            build_txt_export(manifest=manifest, title=title),
            "text/plain; charset=utf-8",
            "txt",
        )
    raise ValueError(f"Unsupported export format: {fmt!r}")
