"""BA 10.1 — deterministischer Prompt-Quality-Layer (kein LLM, keine externen Calls)."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.models import (
    PromptQualityReport,
    PromptQualitySceneEntry,
    SceneBlueprintPlanResponse,
    SceneExpandedPrompt,
)

# Kurze, stabile Check-Codes für Clients/OpenAPI-Doku
CHK_NO_SCENES = "no_scenes"
CHK_BLUEPRINT_DRAFT = "blueprint_draft"
CHK_POSITIVE_SHORT = "positive_prompt_short"
CHK_SPARSE_CHAPTER = "sparse_chapter_risk"
CHK_REDACTION = "redaction_warnings_present"
CHK_CONTINUITY_MISSING = "continuity_lock_token_missing"
CHK_NEGATIVE_SPARSE = "negative_prompt_few_segments"


def _by_scene_number_expanded(scenes: List[SceneExpandedPrompt]) -> Dict[int, SceneExpandedPrompt]:
    return {int(s.scene_number): s for s in scenes}


def build_prompt_quality(
    blueprint: SceneBlueprintPlanResponse,
    scenes: List[SceneExpandedPrompt],
    *,
    continuity_lock: bool,
    policy_profile: str = "prompt_quality_v10_1_20260501",
) -> PromptQualityReport:
    global_checks: List[str] = []
    scene_entries: List[PromptQualitySceneEntry] = []

    if blueprint.status == "draft":
        global_checks.append(CHK_BLUEPRINT_DRAFT)

    if not blueprint.scenes:
        global_checks.append(CHK_NO_SCENES)
        summary = "Keine Szenen im Blueprint — keine Prompt-Qualität je Szene."
        return PromptQualityReport(
            policy_profile=policy_profile,
            summary=summary,
            global_checks=global_checks,
            scenes=[],
        )

    exp_map = _by_scene_number_expanded(scenes)

    for sc in blueprint.scenes:
        sn = int(sc.scene_number)
        checks: List[str] = []
        evidence: List[str] = []
        ep: Optional[SceneExpandedPrompt] = exp_map.get(sn)

        if sc.risk_flags:
            for rf in sc.risk_flags:
                if (rf or "").strip() == "sparse_chapter":
                    checks.append(CHK_SPARSE_CHAPTER)
                    evidence.append(f"risk_flag:{rf}")

        if sc.redaction_warnings:
            checks.append(CHK_REDACTION)
            evidence.append(f"redaction_count:{len(sc.redaction_warnings)}")

        if ep:
            pos = (ep.positive_expanded or "").strip()
            if len(pos) < 120:
                checks.append(CHK_POSITIVE_SHORT)
                evidence.append(f"positive_len:{len(pos)}")

            neg = (ep.negative_prompt or "").strip()
            seg_count = len([x for x in neg.split(";") if x.strip()]) if neg else 0
            if seg_count < 3:
                checks.append(CHK_NEGATIVE_SPARSE)
                evidence.append(f"negative_segments:{seg_count}")

            if continuity_lock and sn > 1 and "Continuity_lock:" not in (ep.positive_expanded or ""):
                checks.append(CHK_CONTINUITY_MISSING)
                evidence.append("expected Continuity_lock in positive_expanded")

        scene_entries.append(
            PromptQualitySceneEntry(scene_number=sn, checks=sorted(set(checks)), evidence_hints=evidence[:5])
        )

    n_warn = sum(1 for e in scene_entries if e.checks)
    summary = (
        f"{len(scene_entries)} Szenen; {n_warn} mit mindestens einem Qualitätshinweis."
        if scene_entries
        else "Keine Szenen-Einträge."
    )

    return PromptQualityReport(
        policy_profile=policy_profile,
        summary=summary,
        global_checks=sorted(set(global_checks)),
        scenes=scene_entries,
    )
