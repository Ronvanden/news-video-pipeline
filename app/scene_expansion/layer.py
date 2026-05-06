"""BA 18.0 — Kapitel × Szenen-Prompt → mehrere Visual-Beats (deterministisch)."""

from __future__ import annotations

from typing import List

from app.prompt_engine.schema import ProductionPromptPlan
from app.scene_expansion.schema import AssetBeatType, ExpandedSceneAssetBeat, SceneExpansionResult

_MOTIONS = (
    "slow push-in, tripod, neutral DE framing",
    "subtle pan left-to-right, hold on subject anchor",
    "static lock-off, slight handheld micro-movement",
)
_SAFETY_BASE = (
    "Avoid explicit violence or identifiable victims without editorial clearance.",
    "Do not invent locations, dates, or quotes; align with source and script.",
)


def _beats_for_chapter(scene_text: str) -> int:
    t = (scene_text or "").strip()
    return 3 if len(t) > 100 else 2


def _asset_types(n: int) -> List[AssetBeatType]:
    if n >= 3:
        return ["establishing", "detail", "broll"]
    return ["establishing", "detail"]


def _duration_seconds(n_beats: int, chapter_count: int) -> int:
    """Grobe Segmentlänge: längeres Gesamtformat → etwas längere Beats."""
    if chapter_count <= 0:
        return 10
    if chapter_count <= 4:
        return max(6, min(18, 90 // max(n_beats * chapter_count, 1)))
    return max(5, min(14, 72 // max(n_beats * chapter_count, 1)))


def build_scene_expansion_layer(plan: ProductionPromptPlan) -> SceneExpansionResult:
    chapters = list(plan.chapter_outline or [])
    scenes = list(plan.scene_prompts or [])
    assets: List[ExpandedSceneAssetBeat] = []
    chapter_count = len(chapters)

    for ci, ch in enumerate(chapters):
        scene_text = scenes[ci] if ci < len(scenes) else ""
        if not scene_text.strip():
            scene_text = f"{ch.title or 'Kapitel'}: {ch.summary or ''}".strip()
        n_beats = _beats_for_chapter(scene_text)
        types = _asset_types(n_beats)
        dur = _duration_seconds(n_beats, max(chapter_count, 1))
        base = (scene_text or "")[:900]

        for bi in range(n_beats):
            atype: AssetBeatType = types[bi] if bi < len(types) else "image"
            motion = _MOTIONS[bi % len(_MOTIONS)]
            if bi == 0:
                vp = f"Establishing: {base[:320].strip()} — wide readable composition, documentary lighting."
            elif bi == 1 and n_beats > 2:
                vp = f"Detail beat: focus element from chapter — {base[80:400].strip() or ch.title}"
            else:
                vp = f"B-roll / cutaway supporting narrative — {base[40:360].strip() or ch.summary[:200]}"

            if bi > 0:
                cont = (
                    f"Match palette and subject line from chapter {ci} beat {bi - 1}; "
                    "avoid harsh jump cuts on faces."
                )
            elif (plan.hook or "").strip():
                cont = f"Open chapter {ci + 1}; align with hook tone: {(plan.hook or '')[:80]} …"
            else:
                cont = f"Open chapter {ci + 1}; maintain template mood ({plan.template_type})."

            assets.append(
                ExpandedSceneAssetBeat(
                    chapter_index=ci,
                    beat_index=bi,
                    visual_prompt=vp[:1200],
                    camera_motion_hint=motion,
                    duration_seconds=dur,
                    asset_type=atype,
                    continuity_note=cont[:500],
                    safety_notes=list(_SAFETY_BASE),
                )
            )

    note = (
        f"Generated {len(assets)} visual beats from {chapter_count} chapter(s) "
        f"(default {_beats_for_chapter(scenes[0] if scenes else '')} beats where scene text is long). "
        "Use for Leonardo/Kling batch planning locally — no API calls from this layer."
    )
    signals = [
        f"chapters={chapter_count}",
        f"scene_prompts={len(scenes)}",
        f"template={plan.template_type or ''}",
    ]
    return SceneExpansionResult(
        beats_per_chapter_default=3,
        expanded_scene_assets=assets,
        founder_note=note,
        checked_signals=signals,
    )
