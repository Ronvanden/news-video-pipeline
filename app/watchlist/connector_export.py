"""BA 7.0: Connector-Export ohne externe Aufrufe — reine Datenaufbereitung."""

from __future__ import annotations

from typing import Any, Dict, List

from app.watchlist.models import (
    ConnectorExportMetadata,
    ConnectorExportPayload,
    GeneratedScript,
    ProductionJob,
    RenderManifest,
    SceneAssets,
    VoicePlan,
)


def thumbnail_prompt_resolve(
    pj: ProductionJob | None,
    assets: SceneAssets | None,
) -> str:
    if pj is not None and (pj.thumbnail_prompt or "").strip():
        return (pj.thumbnail_prompt or "").strip()
    if assets is None:
        return ""
    for s in sorted(assets.scenes or [], key=lambda x: x.scene_number):
        if (s.thumbnail_prompt or "").strip():
            return (s.thumbnail_prompt or "").strip()
    return ""


def build_capcut_timeline_hint(manifest: RenderManifest | None) -> Dict[str, Any]:
    if manifest is None or not manifest.timeline:
        return {
            "order": [],
            "note": "Kein Render-Manifest oder leere Timeline; zuerst render-manifest/generate ausführen.",
        }
    order = []
    prev = ""
    for t in manifest.timeline:
        step = {
            "scene_number": t.scene_number,
            "duration_seconds_estimate": float(t.duration_seconds),
            "label": prev or "(Start)",
            "transition_hint": t.transition_hint,
        }
        order.append(step)
        prev = f"S{t.scene_number}"
    return {"order": order, "suggested_aspect": "1080x1920_shorts_variant_914_914"}


def build_connector_export_payload(
    *,
    production_job: ProductionJob | None,
    manifest: RenderManifest | None,
    voice_plan: VoicePlan | None,
    scene_assets: SceneAssets | None,
    generated_script: GeneratedScript | None,
    render_manifest_warnings: List[str],
) -> ConnectorExportPayload:
    warns = list(render_manifest_warnings or [])
    if manifest is None:
        warns.insert(0, "Render-Manifest fehlt oder wurde nicht geladen.")

    gm: Dict[str, Any] = {}
    if manifest is not None:
        gm = manifest.model_dump(mode="json")

    elevenlabs_blocks: List[Dict[str, Any]] = []
    if voice_plan is not None:
        for b in voice_plan.blocks or []:
            elevenlabs_blocks.append(
                {
                    "scene_number": b.scene_number,
                    "text": b.voice_text,
                    "voice_style": b.speaker_style,
                    "provider_hint": voice_plan.voice_profile,
                    "pause_after_seconds": b.pause_after_seconds,
                    "estimated_duration_seconds": b.estimated_duration_seconds,
                    "tts_provider_hint": b.tts_provider_hint,
                    "pronunciation_notes": b.pronunciation_notes or "",
                }
            )

    kling_prompts: List[Dict[str, Any]] = []
    leonardo_prompts: List[Dict[str, Any]] = []
    if manifest is not None:
        for t in manifest.timeline or []:
            kling_prompts.append(
                {"scene_number": t.scene_number, "prompt": t.video_prompt or ""}
            )
            leonardo_prompts.append(
                {"scene_number": t.scene_number, "prompt": t.image_prompt or ""}
            )
    elif scene_assets is not None:
        for s in sorted(scene_assets.scenes or [], key=lambda x: x.scene_number):
            kling_prompts.append(
                {"scene_number": s.scene_number, "prompt": s.video_prompt or ""}
            )
            leonardo_prompts.append(
                {"scene_number": s.scene_number, "prompt": s.image_prompt or ""}
            )

    title = (generated_script.title if generated_script else "") or (
        production_job.thumbnail_prompt[:80] if production_job and production_job.thumbnail_prompt else ""
    )
    if not title and production_job is not None:
        title = f"Production {production_job.id}"

    description_draft = ""
    if generated_script is not None:
        description_draft = (generated_script.hook or "")[:500]
    tags: List[str] = []
    if generated_script is not None and generated_script.chapters:
        tags = [c.title for c in generated_script.chapters[:8] if c.title]

    thumb = thumbnail_prompt_resolve(production_job, scene_assets)

    return ConnectorExportPayload(
        generic_manifest=gm,
        elevenlabs_blocks=elevenlabs_blocks,
        kling_prompts=kling_prompts,
        leonardo_prompts=leonardo_prompts,
        thumbnail_prompt=thumb,
        capcut_timeline_hint=build_capcut_timeline_hint(manifest),
        metadata=ConnectorExportMetadata(
            title=title,
            description_draft=description_draft,
            tags=tags,
            warnings=warns,
        ),
    )
