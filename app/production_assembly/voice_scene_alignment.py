"""BA 12.3 — Voice / Scene Alignment."""

from __future__ import annotations

from typing import List

from app.production_assembly.schema import VoiceSceneAlignmentResult
from app.production_assembly.timeline_finalizer import build_final_timeline


def build_voice_scene_alignment(plan: object) -> VoiceSceneAlignmentResult:
    final_timeline = getattr(plan, "final_timeline_result", None) or build_final_timeline(plan)
    warnings: List[str] = []
    aligned: List[int] = []
    missing: List[int] = []
    recommendations: List[str] = []

    for scene in final_timeline.scenes:
        if scene.narration_asset:
            aligned.append(scene.scene_index)
            duration = max(0, scene.end_time - scene.start_time)
            if duration < 8:
                warnings.append(f"scene_{scene.scene_index}_voice_window_short")
            if duration > 70:
                warnings.append(f"scene_{scene.scene_index}_voice_window_long")
        else:
            missing.append(scene.scene_index)

    if missing:
        recommendations.append("Generate or attach narration assets for missing scenes before render.")
    if warnings:
        recommendations.append("Review voice pacing against final scene durations.")
    if not final_timeline.scenes:
        recommendations.append("Build final timeline before voice alignment.")

    if not final_timeline.scenes:
        status = "blocked"
    elif missing:
        status = "partial"
    else:
        status = "complete"

    return VoiceSceneAlignmentResult(
        alignment_status=status,
        aligned_scenes=aligned,
        missing_voice_scenes=missing,
        voice_overflow_warnings=list(dict.fromkeys(warnings)),
        recommendations=list(dict.fromkeys(recommendations)),
    )
