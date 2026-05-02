"""BA 9.11 — Qualitätsprüfung für ProductionPromptPlan (heuristisch, ohne LLM)."""

from __future__ import annotations

from typing import List

from app.prompt_engine.schema import ProductionPromptPlan, PromptPlanQualityResult

MIN_CHAPTERS_PRODUCTION = 5
MIN_HOOK_CHARS = 12


def _substantive_plan_warnings(plan: ProductionPromptPlan) -> List[str]:
    """Plan-Warnungen außer reinem Klassifikator-Hinweis ``[prompt_plan]``."""
    out: List[str] = []
    for w in plan.warnings or []:
        s = (w or "").strip()
        if not s or s.startswith("[prompt_plan]"):
            continue
        out.append(s)
    return out


def evaluate_prompt_plan_quality(plan: ProductionPromptPlan) -> PromptPlanQualityResult:
    """
    Bewertet Produktionsreife: blockierende Mängel → ``fail``,
    nachrangige / Mengen-Themen → ``warning``, sonst ``pass``.
    """
    checked_fields: List[str] = []
    blocking: List[str] = []
    structural: List[str] = []

    checked_fields.append("template_type")
    if not (plan.template_type or "").strip():
        blocking.append("template_type_missing")

    checked_fields.append("hook")
    hk = (plan.hook or "").strip()
    if not hk:
        blocking.append("hook_empty")
    elif len(hk) < MIN_HOOK_CHARS:
        structural.append(f"hook_kurz_unter_{MIN_HOOK_CHARS}_zeichen")

    checked_fields.append("tone")
    if not (plan.tone or "").strip():
        structural.append("tone_leer")

    checked_fields.append("chapter_outline")
    n_ch = len(plan.chapter_outline or [])
    if n_ch == 0:
        blocking.append("chapter_outline_leer")
    elif n_ch < MIN_CHAPTERS_PRODUCTION:
        structural.append(f"kapitel_unter_mindestanzahl_{MIN_CHAPTERS_PRODUCTION}")

    checked_fields.append("scene_prompts")
    n_sc = len(plan.scene_prompts or [])
    if n_sc == 0:
        blocking.append("scene_prompts_leer")
    elif n_ch > 0 and n_sc != n_ch:
        blocking.append("scene_und_kapitel_anzahl_stimmen_nicht")

    checked_fields.append("voice_style")
    if not (plan.voice_style or "").strip():
        structural.append("voice_style_leer")

    checked_fields.append("thumbnail_angle")
    if not (plan.thumbnail_angle or "").strip():
        structural.append("thumbnail_angle_leer")

    checked_fields.append("narrative_archetype_id")
    if not (plan.narrative_archetype_id or "").strip():
        structural.append("narrative_archetype_id_leer")

    checked_fields.append("plan_warnings")
    substantive_pw = _substantive_plan_warnings(plan)

    inherited = [f"inherited_plan_warning:{w}" for w in (plan.warnings or [])]

    all_warnings = structural + [f"substantive:{w}" for w in substantive_pw] + inherited

    # Score 0–100 (heuristisch)
    score = 100
    score -= 28 * len(blocking)
    score -= 10 * len([s for s in structural if "kapitel_unter" in s])
    score -= 8 * len([s for s in structural if "hook_kurz" in s])
    score -= 5 * len(
        [s for s in structural if s in ("tone_leer", "voice_style_leer", "thumbnail_angle_leer", "narrative_archetype_id_leer")]
    )
    score -= 4 * len(substantive_pw)
    score = max(0, min(100, score))

    if blocking:
        score = min(score, 35)

    if blocking:
        status = "fail"
    elif structural or substantive_pw:
        status = "warning"
    else:
        status = "pass"

    return PromptPlanQualityResult(
        score=score,
        status=status,
        warnings=all_warnings,
        blocking_issues=blocking,
        checked_fields=checked_fields,
    )
