"""BA 9.16 — Deterministische Repair-Vorschau ohne Überschreibung des Originalplans."""

from __future__ import annotations

from typing import Any, Dict, List

from app.prompt_engine.narrative_scoring import evaluate_narrative_score
from app.prompt_engine.quality_check import MIN_CHAPTERS_PRODUCTION, MIN_HOOK_CHARS, evaluate_prompt_plan_quality
from app.prompt_engine.repair_suggestions import build_prompt_repair_suggestions
from app.prompt_engine.review_gate import evaluate_prompt_plan_review_gate
from app.prompt_engine.schema import ProductionPromptPlan, PromptRepairPreviewResult

DEFAULT_HOOK = (
    "Warum diese Geschichte bis heute Fragen offenlässt — und was wirklich dahintersteckt."
)
DEFAULT_THUMBNAIL_ANGLE = (
    "A visually tense contrast between the main subject and an unanswered question."
)
NARRATIVE_WEAK_HINT = (
    "Narrative weakness requires deeper rewrite beyond deterministic preview."
)

STANDARD_BEAT_TITLES: List[str] = [
    "Setup",
    "Kontext",
    "Konflikt",
    "Wendepunkt",
    "Auflösung oder offene Frage",
]


def _voice_for_template(template_type: str) -> str:
    tt = (template_type or "").strip()
    if tt == "true_crime":
        return "calm investigative documentary voice"
    if tt == "mystery_history":
        return "cinematic historical mystery narration"
    return "clear documentary narration"


def _reevaluate_preview_plan(preview: ProductionPromptPlan) -> ProductionPromptPlan:
    cleared = preview.model_copy(
        update={
            "quality_result": None,
            "narrative_score_result": None,
            "review_gate_result": None,
            "repair_suggestions_result": None,
            "repair_preview_result": None,
        }
    )
    q = evaluate_prompt_plan_quality(cleared)
    n = evaluate_narrative_score(cleared.model_copy(update={"quality_result": q}))
    tmp = cleared.model_copy(update={"quality_result": q, "narrative_score_result": n})
    gate = evaluate_prompt_plan_review_gate(tmp)
    sug = build_prompt_repair_suggestions(tmp.model_copy(update={"review_gate_result": gate}))
    return tmp.model_copy(
        update={
            "review_gate_result": gate,
            "repair_suggestions_result": sug,
            "repair_preview_result": None,
        }
    )


def build_repair_preview(plan: ProductionPromptPlan) -> PromptRepairPreviewResult:
    rg = plan.review_gate_result
    if rg is not None and rg.decision == "go":
        return PromptRepairPreviewResult(
            status="not_needed",
            preview_plan=None,
            applied_repairs=[],
            remaining_issues=[],
            warnings=[],
        )

    applied_repairs: List[str] = []
    remaining_issues: List[str] = []
    warnings: List[str] = []

    if plan.narrative_score_result is not None and plan.narrative_score_result.status == "weak":
        remaining_issues.append(NARRATIVE_WEAK_HINT)
        warnings.append(NARRATIVE_WEAK_HINT)

    try:
        data: Dict[str, Any] = plan.model_dump(mode="python")
    except Exception:
        return PromptRepairPreviewResult(
            status="not_possible",
            preview_plan=None,
            applied_repairs=applied_repairs,
            remaining_issues=remaining_issues,
            warnings=warnings + ["repair_preview: plan_dump_failed"],
        )

    for key in (
        "quality_result",
        "narrative_score_result",
        "review_gate_result",
        "repair_suggestions_result",
        "repair_preview_result",
    ):
        data[key] = None

    hk = (data.get("hook") or "").strip()
    if not hk or len(hk) < MIN_HOOK_CHARS:
        data["hook"] = DEFAULT_HOOK
        applied_repairs.append("hook_repaired")

    chapters: List[Dict[str, Any]] = list(data.get("chapter_outline") or [])
    if len(chapters) < MIN_CHAPTERS_PRODUCTION:
        for idx in range(len(chapters), MIN_CHAPTERS_PRODUCTION):
            title = STANDARD_BEAT_TITLES[idx]
            chapters.append(
                {
                    "title": title,
                    "summary": f"Strukturbeat „{title}“ im narrativen Standardbogen.",
                }
            )
        data["chapter_outline"] = chapters
        applied_repairs.append("chapters_extended")

    n_ch = len(data["chapter_outline"])
    scenes: List[str] = list(data.get("scene_prompts") or [])
    if n_ch == 0 or len(scenes) != n_ch:
        new_scenes: List[str] = []
        for ch in data["chapter_outline"]:
            title = ch["title"] if isinstance(ch, dict) else getattr(ch, "title", "Chapter")
            new_scenes.append(
                f'Scene prompt for chapter "{title}": one clear visual beat per chapter, '
                f"steady framing, mood aligned with {data.get('template_type', 'story')}."
            )
        data["scene_prompts"] = new_scenes
        applied_repairs.append("scene_prompts_aligned")

    if not (data.get("voice_style") or "").strip():
        data["voice_style"] = _voice_for_template(str(data.get("template_type") or ""))
        applied_repairs.append("voice_style_added")

    if not (data.get("thumbnail_angle") or "").strip():
        data["thumbnail_angle"] = DEFAULT_THUMBNAIL_ANGLE
        applied_repairs.append("thumbnail_angle_added")

    try:
        preview_struct = ProductionPromptPlan.model_validate(data)
    except Exception:
        return PromptRepairPreviewResult(
            status="not_possible",
            preview_plan=None,
            applied_repairs=applied_repairs,
            remaining_issues=remaining_issues,
            warnings=warnings + ["repair_preview: validate_failed"],
        )

    preview_final = _reevaluate_preview_plan(preview_struct)
    return PromptRepairPreviewResult(
        status="preview_available",
        preview_plan=preview_final,
        applied_repairs=applied_repairs,
        remaining_issues=remaining_issues,
        warnings=warnings,
    )
