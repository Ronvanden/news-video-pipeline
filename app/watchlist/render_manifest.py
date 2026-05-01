"""BA 6.9: Render-Manifest aus Production-Job-Bausteinen (kein Rendering)."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from app.watchlist.models import (
    ProductionJob,
    Scene,
    SceneAssetItem,
    SceneAssets,
    ScenePlan,
    TimelineItem,
    VoiceBlock,
    VoicePlan,
)
from app.watchlist.voice_plan import estimate_speech_seconds_from_text

EXPORT_VERSION = "7.1.0"


def _scene_duration_from_plan(plan: Optional[ScenePlan], scene_number: int) -> int:
    if plan is None:
        return 30
    for sc in plan.scenes or []:
        if isinstance(sc, Scene) and sc.scene_number == scene_number:
            return max(1, int(sc.duration_seconds))
    return 30


def _asset_by_number(assets: Optional[SceneAssets], n: int) -> Optional[SceneAssetItem]:
    if assets is None:
        return None
    for s in assets.scenes or []:
        if s.scene_number == n:
            return s
    return None


def _voice_block_by_number(vp: Optional[VoicePlan], n: int) -> Optional[VoiceBlock]:
    if vp is None:
        return None
    for b in vp.blocks or []:
        if b.scene_number == n:
            return b
    return None


def build_timeline(
    scene_plan: Optional[ScenePlan],
    scene_assets: Optional[SceneAssets],
    voice_plan: Optional[VoicePlan],
) -> Tuple[List[TimelineItem], int]:
    if scene_assets is None or not scene_assets.scenes:
        return [], 0

    numbers = sorted({s.scene_number for s in scene_assets.scenes})
    items: List[TimelineItem] = []
    total_pause = 0.0
    for n in numbers:
        sa = _asset_by_number(scene_assets, n)
        if sa is None:
            continue
        vb = _voice_block_by_number(voice_plan, n)
        voice_text = (vb.voice_text if vb else (sa.voiceover_chunk or "")).strip()
        if not voice_text:
            voice_text = (sa.title or f"Szene {n}").strip()

        plan_dur = _scene_duration_from_plan(scene_plan, n)
        est_voice = (
            vb.estimated_duration_seconds
            if vb
            else estimate_speech_seconds_from_text(sa.voiceover_chunk or "")
        )
        dur = max(plan_dur, est_voice, 1)

        mood = (sa.mood or "").lower()
        if vb and vb.pause_after_seconds:
            total_pause += float(vb.pause_after_seconds)
        if "dram" in mood or mood == "dramatic":
            trans = "dissolve_slow"
        elif mood == "neutral":
            trans = "cut"
        else:
            trans = "crossfade"

        items.append(
            TimelineItem(
                scene_number=n,
                voice_text=voice_text,
                image_prompt=sa.image_prompt or "",
                video_prompt=sa.video_prompt or "",
                camera_direction=sa.camera_direction or "",
                duration_seconds=dur,
                asset_type=sa.asset_type,
                transition_hint=trans,
            )
        )

    # stable sort redundant (already sorted by n)
    items.sort(key=lambda x: x.scene_number)
    base = sum(t.duration_seconds for t in items)
    estimated_total = int(round(base + total_pause))
    return items, estimated_total


def decide_manifest_status(
    *,
    production_job: Optional[ProductionJob],
    scene_plan: Optional[ScenePlan],
    scene_assets: Optional[SceneAssets],
    voice_plan: Optional[VoicePlan],
) -> str:
    if production_job is None or scene_assets is None:
        return "failed"
    if (scene_assets.status or "") != "ready":
        return "failed"
    if scene_plan is None or voice_plan is None:
        return "incomplete"
    if (voice_plan.status or "") != "ready":
        return "incomplete"
    return "ready"
