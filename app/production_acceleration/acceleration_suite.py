"""BA 15.0–15.9 — First Production Acceleration Suite."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from app.production_acceleration.schema import (
    AssetDownloaderResult,
    BatchTopicRunnerResult,
    CostSnapshotResult,
    DemoVideoAutomationResult,
    FounderLocalDashboardResult,
    SceneStitcherResult,
    SubtitleDraftResult,
    ThumbnailExtractResult,
    ViralPrototypePresetsResult,
    VoiceRegistryResult,
)
from app.production_connectors.voice_live_connector import DEFAULT_ELEVENLABS_TEST_VOICE_ID


def _first_image_source(plan: object) -> Optional[str]:
    manifest = getattr(plan, "master_asset_manifest_result", None)
    for asset in getattr(manifest, "assets", []) or []:
        if getattr(asset, "asset_type", "") == "image":
            return getattr(asset, "asset_url", None) or getattr(asset, "local_path", None)
    live = getattr(plan, "leonardo_live_result", None)
    norm = getattr(live, "normalized_asset", None)
    return getattr(norm, "asset_url", None) or getattr(norm, "local_path", None)


def build_demo_video_automation(plan: object) -> DemoVideoAutomationResult:
    image = _first_image_source(plan)
    blocking: List[str] = []
    warnings: List[str] = []
    if not image:
        blocking.append("image_source_missing")
    command = ["python", "scripts/build_first_demo_video.py", image or "<image_url_or_path>"]
    status = "ready" if image else "blocked"
    if not image:
        warnings.append("demo_video_requires_real_or_downloadable_image")
    return DemoVideoAutomationResult(
        automation_status=status,
        image_source=image,
        command_hint=command,
        warnings=warnings,
        blocking_reasons=blocking,
    )


def build_asset_downloader(plan: object) -> AssetDownloaderResult:
    targets: List[Dict[str, Any]] = []
    local_paths: List[str] = []
    manifest = getattr(plan, "master_asset_manifest_result", None)
    for asset in getattr(manifest, "assets", []) or []:
        asset_type = getattr(asset, "asset_type", "")
        url = getattr(asset, "asset_url", None)
        local = getattr(asset, "local_path", None)
        if url:
            targets.append({"asset_type": asset_type, "provider_name": getattr(asset, "provider_name", ""), "asset_url": url})
        if local:
            local_paths.append(str(local))
    if not targets and not local_paths:
        return AssetDownloaderResult(
            downloader_status="blocked",
            warnings=["no_assets_available_for_download_plan"],
        )
    return AssetDownloaderResult(
        downloader_status="ready" if targets or local_paths else "partial",
        download_targets=targets,
        local_asset_paths=local_paths,
        warnings=[],
    )


def build_voice_registry(_: object) -> VoiceRegistryResult:
    present = bool((os.getenv("VOICE_ID") or "").strip())
    return VoiceRegistryResult(
        registry_status="ready",
        default_voice_id=DEFAULT_ELEVENLABS_TEST_VOICE_ID,
        configured_voice_id_present=present,
        voice_sources=["VOICE_ID_env", "ElevenLabs_default_test_voice", "scripts/list_elevenlabs_voices.py"],
        warnings=[] if present else ["voice_id_env_missing_using_default_test_voice"],
    )


def build_scene_stitcher(plan: object) -> SceneStitcherResult:
    timeline = getattr(plan, "final_timeline_result", None)
    scenes = list(getattr(timeline, "scenes", []) or [])
    stitch_plan = [
        {
            "scene_index": getattr(scene, "scene_index", idx),
            "start_time": getattr(scene, "start_time", 0),
            "end_time": getattr(scene, "end_time", 0),
            "linked_assets": list(getattr(scene, "linked_assets", []) or []),
            "narration_asset": getattr(scene, "narration_asset", None),
        }
        for idx, scene in enumerate(scenes)
    ]
    if not stitch_plan:
        return SceneStitcherResult(stitcher_status="blocked", warnings=["no_final_timeline_scenes_available"])
    return SceneStitcherResult(
        stitcher_status="ready" if all(item["linked_assets"] for item in stitch_plan) else "partial",
        scene_count=len(stitch_plan),
        stitch_plan=stitch_plan,
        warnings=[] if all(item["linked_assets"] for item in stitch_plan) else ["some_scenes_missing_linked_assets"],
    )


def build_subtitle_draft(plan: object) -> SubtitleDraftResult:
    chapters = list(getattr(plan, "chapter_outline", []) or [])
    blocks: List[Dict[str, Any]] = []
    cursor = 0
    for idx, chapter in enumerate(chapters, start=1):
        text = getattr(chapter, "summary", "") or getattr(chapter, "title", "")
        blocks.append({"index": idx, "start_seconds": cursor, "end_seconds": cursor + 12, "text": str(text)[:180]})
        cursor += 12
    if not blocks:
        return SubtitleDraftResult(subtitle_status="blocked", warnings=["no_chapters_available_for_subtitle_draft"])
    return SubtitleDraftResult(subtitle_status="ready", subtitle_blocks=blocks)


def build_thumbnail_extract(_: object) -> ThumbnailExtractResult:
    return ThumbnailExtractResult(
        extract_status="ready",
        command_hint=[
            "ffmpeg",
            "-y",
            "-ss",
            "00:00:01",
            "-i",
            "output/first_demo_video.mp4",
            "-frames:v",
            "1",
            "output/first_demo_thumbnail.jpg",
        ],
    )


def build_batch_topic_runner(plan: object) -> BatchTopicRunnerResult:
    topic = getattr(plan, "template_type", "") or "current_prompt_plan"
    item = {
        "batch_item_id": "demo_topic_001",
        "template_type": topic,
        "status": "ready_for_local_demo",
    }
    return BatchTopicRunnerResult(batch_status="ready", topic_count=1, batch_items=[item])


def build_cost_snapshot(plan: object) -> CostSnapshotResult:
    projection = getattr(plan, "cost_projection_result", None)
    total = float(getattr(projection, "total_estimated_cost_eur", 0.0) or 0.0)
    provider_costs = list(getattr(projection, "provider_costs", []) or [])
    items = [
        {
            "provider_name": getattr(item, "provider_name", ""),
            "provider_type": getattr(item, "provider_type", ""),
            "estimated_cost_eur": getattr(item, "estimated_cost_eur", 0.0),
        }
        for item in provider_costs
    ]
    if not items:
        items = [
            {"component": "leonardo_image_smoke", "estimated_cost": 0.0},
            {"component": "elevenlabs_voice_smoke", "estimated_cost": 0.0},
            {"component": "local_ffmpeg_render", "estimated_cost": 0.0},
        ]
    return CostSnapshotResult(
        snapshot_status="ready",
        estimated_cost=total,
        cost_items=items,
        warnings=[] if total else ["cost_snapshot_uses_zero_or_missing_projection"],
    )


def build_viral_prototype_presets(plan: object) -> ViralPrototypePresetsResult:
    template = getattr(plan, "template_type", "") or "generic"
    hook_type = getattr(plan, "hook_type", "") or "curiosity"
    presets = [
        {"preset_id": "documentary_proof", "template_type": template, "hook_type": hook_type, "pace": "steady"},
        {"preset_id": "mystery_short", "template_type": template, "hook_type": "open_loop", "pace": "fast"},
        {"preset_id": "authority_explainer", "template_type": template, "hook_type": "context_first", "pace": "measured"},
    ]
    return ViralPrototypePresetsResult(recommended_preset="documentary_proof", presets=presets)


def build_founder_local_dashboard(plan: object) -> FounderLocalDashboardResult:
    checks = {
        "demo_video_automation": getattr(plan, "demo_video_automation_result", None),
        "asset_downloader": getattr(plan, "asset_downloader_result", None),
        "voice_registry": getattr(plan, "voice_registry_result", None),
        "scene_stitcher": getattr(plan, "scene_stitcher_result", None),
        "subtitle_draft": getattr(plan, "subtitle_draft_result", None),
        "thumbnail_extract": getattr(plan, "thumbnail_extract_result", None),
    }
    ready: List[str] = []
    blocked: List[str] = []
    for name, result in checks.items():
        status = (
            getattr(result, "automation_status", None)
            or getattr(result, "downloader_status", None)
            or getattr(result, "registry_status", None)
            or getattr(result, "stitcher_status", None)
            or getattr(result, "subtitle_status", None)
            or getattr(result, "extract_status", None)
        )
        if status == "blocked":
            blocked.append(name)
        else:
            ready.append(name)
    score = int(round((len(ready) / max(1, len(checks))) * 100))
    next_actions = ["run_voice_smoke_test_and_save", "build_first_demo_video"]
    if blocked:
        next_actions.insert(0, "provide_real_image_and_audio_assets")
    return FounderLocalDashboardResult(
        dashboard_status="ready" if not blocked else "partial",
        readiness_score=score,
        ready_components=ready,
        blocked_components=blocked,
        next_actions=next_actions,
    )


def apply_production_acceleration_suite(plan: object) -> object:
    """Demo automation → downloader → voice registry → stitch/subtitle/thumb → ops snapshot."""
    p = plan.model_copy(update={"demo_video_automation_result": build_demo_video_automation(plan)})
    p = p.model_copy(update={"asset_downloader_result": build_asset_downloader(p)})
    p = p.model_copy(update={"voice_registry_result": build_voice_registry(p)})
    p = p.model_copy(update={"scene_stitcher_result": build_scene_stitcher(p)})
    p = p.model_copy(update={"subtitle_draft_result": build_subtitle_draft(p)})
    p = p.model_copy(update={"thumbnail_extract_result": build_thumbnail_extract(p)})
    p = p.model_copy(update={"founder_local_dashboard_result": build_founder_local_dashboard(p)})
    p = p.model_copy(update={"batch_topic_runner_result": build_batch_topic_runner(p)})
    p = p.model_copy(update={"cost_snapshot_result": build_cost_snapshot(p)})
    p = p.model_copy(update={"viral_prototype_presets_result": build_viral_prototype_presets(p)})
    return p

