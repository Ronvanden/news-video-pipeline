"""BA 9.23 — Produktionstimeline aus Hook + Kapitel/Szenen (ohne Render-Start)."""

from __future__ import annotations

from typing import List

from app.prompt_engine.schema import (
    ProductionPromptPlan,
    ProductionTimelineResult,
    TimelineOverallStatus,
    TimelineScene,
    TimelineRole,
    VideoLengthCategory,
)

HOOK_DURATION_S = 12  # 8–15s Band, deterministischer Mittelwert
SETUP_DURATION_S = 28
BUILD_DURATION_S = 32
ESCALATION_DURATION_S = 38
CLIMAX_DURATION_S = 45  # 30–60s Band
OUTRO_DURATION_S = 15  # 10–20s Band

VISUAL_PROVIDER_TARGETS = ["Leonardo", "Kling"]


def _duration_for_role(role: TimelineRole) -> int:
    if role == "hook":
        return HOOK_DURATION_S
    if role == "setup":
        return SETUP_DURATION_S
    if role == "build":
        return BUILD_DURATION_S
    if role == "escalation":
        return ESCALATION_DURATION_S
    if role == "climax":
        return CLIMAX_DURATION_S
    return OUTRO_DURATION_S


def _body_role(body_idx: int, n_body: int) -> TimelineRole:
    if n_body <= 0:
        return "outro"
    if n_body == 1:
        return "outro"
    if n_body == 2:
        return "setup" if body_idx == 0 else "outro"
    if body_idx == 0:
        return "setup"
    if body_idx == n_body - 1:
        return "outro"
    if body_idx == n_body - 2:
        return "climax"
    return "build" if body_idx % 2 == 1 else "escalation"


def _length_category(total_s: int) -> VideoLengthCategory:
    if total_s < 90:
        return "short"
    if total_s <= 480:
        return "medium"
    return "long"


def build_production_timeline(plan: ProductionPromptPlan) -> ProductionTimelineResult:
    warnings: List[str] = []
    ex = plan.production_export_contract_result
    if ex is None or ex.export_status == "blocked":
        msg = "Export contract missing or blocked; timeline not built."
        warnings.append(msg)
        return ProductionTimelineResult(
            timeline_status="blocked",
            total_estimated_duration_seconds=0,
            target_video_length_category="short",
            scenes=[],
            warnings=warnings,
        )

    chapters = list(plan.chapter_outline or [])
    scenes = list(plan.scene_prompts or [])
    n_ch, n_sc = len(chapters), len(scenes)
    paired = min(n_ch, n_sc)
    if n_ch != n_sc:
        warnings.append("Chapter/scene count mismatch; timeline is partial.")
    if paired == 0 and not (plan.hook or "").strip():
        warnings.append("No hook and no chapter/scene pairs.")
        return ProductionTimelineResult(
            timeline_status="blocked",
            total_estimated_duration_seconds=0,
            target_video_length_category="short",
            scenes=[],
            warnings=warnings,
        )

    if paired == 0 and (plan.hook or "").strip():
        warnings.append("No chapter/scene pairs; hook-only timeline.")

    out_scenes: List[TimelineScene] = []
    idx = 0
    hk = (plan.hook or "").strip()
    if hk:
        out_scenes.append(
            TimelineScene(
                scene_index=idx,
                chapter_title="Hook",
                scene_prompt=plan.hook,
                estimated_duration_seconds=_duration_for_role("hook"),
                timeline_role="hook",
                provider_targets=list(VISUAL_PROVIDER_TARGETS),
            )
        )
        idx += 1
    elif paired > 0:
        warnings.append("Hook empty; timeline starts at first chapter beat.")

    n_body = paired
    for b in range(n_body):
        role = _body_role(b, n_body)
        ch = chapters[b]
        sp = scenes[b] if b < n_sc else ""
        if not sp.strip():
            warnings.append(f"Scene prompt empty for chapter '{ch.title}'.")
        out_scenes.append(
            TimelineScene(
                scene_index=idx,
                chapter_title=ch.title,
                scene_prompt=sp,
                estimated_duration_seconds=_duration_for_role(role),
                timeline_role=role,
                provider_targets=list(VISUAL_PROVIDER_TARGETS),
            )
        )
        idx += 1

    total = sum(s.estimated_duration_seconds for s in out_scenes)
    cat = _length_category(total)

    if not out_scenes:
        return ProductionTimelineResult(
            timeline_status="blocked",
            total_estimated_duration_seconds=0,
            target_video_length_category="short",
            scenes=[],
            warnings=warnings + ["No timeline scenes generated."],
        )

    status: TimelineOverallStatus = "ready"
    if warnings or n_ch != n_sc or paired == 0:
        status = "partial"

    return ProductionTimelineResult(
        timeline_status=status,
        total_estimated_duration_seconds=total,
        target_video_length_category=cat,
        scenes=out_scenes,
        warnings=list(dict.fromkeys(warnings)),
    )
