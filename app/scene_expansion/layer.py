"""BA 18.0 — Kapitel × Szenen-Prompt → mehrere Visual-Beats (deterministisch)."""

from __future__ import annotations

from typing import List

from app.prompt_engine.schema import ProductionPromptPlan
from app.scene_expansion.schema import AssetBeatType, ExpandedSceneAssetBeat, SceneExpansionResult
from app.visual_plan.engine_v1 import VisualPromptEngineContext, VisualPromptEngineResult, build_visual_prompt_v1

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


def _engine_fields(result: VisualPromptEngineResult) -> dict:
    return {
        "visual_prompt_raw": result.visual_prompt_raw,
        "visual_prompt_effective": result.visual_prompt_effective,
        "negative_prompt": result.negative_prompt,
        "visual_policy_warnings": list(result.visual_policy_warnings or []),
        "visual_style_profile": result.visual_style_profile,
        "prompt_quality_score": result.prompt_quality_score,
        "prompt_risk_flags": list(result.prompt_risk_flags or []),
        "normalized_controls": dict(result.normalized_controls or {}),
    }


def _build_engine_prompt(
    *,
    chapter_title: str,
    beat_role: str,
    narration: str,
    video_template: str,
) -> VisualPromptEngineResult:
    return build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title=chapter_title or beat_role or "Scene",
            narration=narration,
            video_template=video_template,
            beat_role=beat_role,
        )
    )


def _engine_narration_for_beat(chapter_title: str, chapter_summary: str, scene_text: str, beat_prompt: str) -> str:
    title = (chapter_title or "").strip()
    title_key = title.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    if title_key in {"hook", "the hook", "opening hook", "intro hook", "viral hook", "aufhaenger"}:
        if (chapter_summary or "").strip():
            return chapter_summary
        if ":" in (scene_text or ""):
            return scene_text.split(":", 1)[1].strip()
        return ""
    return beat_prompt


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

            engine_result = _build_engine_prompt(
                chapter_title=ch.title or f"Kapitel {ci + 1}",
                beat_role=atype,
                narration=_engine_narration_for_beat(ch.title, ch.summary, scene_text, vp),
                video_template=getattr(plan, "video_template", "") or plan.template_type or "",
            )

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
                    visual_prompt=engine_result.visual_prompt_effective,
                    camera_motion_hint=motion,
                    duration_seconds=dur,
                    asset_type=atype,
                    continuity_note=cont[:500],
                    safety_notes=list(_SAFETY_BASE),
                    **_engine_fields(engine_result),
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
