"""BA 9.14 — Review Gate: operative Ampel (go / revise / stop) ohne LLM und ohne Firestore."""

from __future__ import annotations

from typing import List, Literal

from app.prompt_engine.performance_learning import evaluate_performance_snapshot
from app.prompt_engine.schema import ProductionPromptPlan, PromptPlanReviewGateResult

WARNING_BUDGET_QUALITY = 6
WARNING_BUDGET_SUBSTANTIVE_PLAN = 4


def _substantive_plan_warnings(plan: ProductionPromptPlan) -> List[str]:
    out: List[str] = []
    for w in plan.warnings or []:
        s = (w or "").strip()
        if not s or s.startswith("[prompt_plan]"):
            continue
        out.append(s)
    return out


def _confidence_raw(plan: ProductionPromptPlan, perf_note: bool) -> int:
    q = plan.quality_result
    n = plan.narrative_score_result
    score = 100
    if q:
        score -= min(35, 5 * len(q.warnings or []))
    if n:
        if n.status == "weak":
            score -= 18
        elif n.status == "moderate":
            score -= 6
        if n.score < 60:
            score -= 8
    score -= min(12, 3 * len(_substantive_plan_warnings(plan)))
    if not (plan.voice_style or "").strip():
        score -= 4
    if not (plan.thumbnail_angle or "").strip():
        score -= 4
    if perf_note:
        score -= 3
    return max(0, min(100, score))


def _clamp_confidence(decision: Literal["go", "revise", "stop"], raw: int) -> int:
    if decision == "stop":
        return min(raw, 40)
    if decision == "revise":
        return max(40, min(79, raw))
    return max(80, min(100, raw))


def evaluate_prompt_plan_review_gate(plan: ProductionPromptPlan) -> PromptPlanReviewGateResult:
    checked = [
        "quality_status",
        "blocking_issues",
        "hook_nonempty",
        "chapter_count",
        "scene_prompts_count",
        "narrative_status",
        "narrative_score",
        "warnings_load",
        "performance_snapshot_optional",
    ]
    reasons: List[str] = []
    actions: List[str] = []

    perf_note = False
    if plan.performance_record is not None:
        snap = evaluate_performance_snapshot(plan.performance_record)
        checked.append(f"performance_snapshot:{snap.status}")
        if snap.status == "pending_data":
            perf_note = True
            reasons.append("Hinweis: Performance-KPIs noch pending_data (kein Stop).")

    q = plan.quality_result
    if q is None:
        reasons.append("quality_result fehlt — Gate konservativ gestoppt.")
        actions.append("Qualitätslayer erneut ausführen oder Pipeline prüfen.")
        conf = _clamp_confidence("stop", _confidence_raw(plan, perf_note))
        return _pack("stop", conf, reasons, actions, checked)

    n = plan.narrative_score_result
    hk = (plan.hook or "").strip()
    n_ch = len(plan.chapter_outline or [])
    n_sc = len(plan.scene_prompts or [])

    if q.status == "fail":
        reasons.append("Quality-Status fail.")
        actions.append("Qualitätsgate erfüllen oder Template/Struktur anpassen.")

    if q.blocking_issues:
        reasons.append(f"blocking_issues ({len(q.blocking_issues)}).")
        for b in q.blocking_issues[:5]:
            actions.append(f"Blocker beheben: {b}")

    if not hk:
        reasons.append("Hook leer.")
        actions.append("Hook formulieren oder Quelle anreichern.")

    if n_ch == 0:
        reasons.append("Keine Kapitel im Plan.")
        actions.append("Kapitelstruktur erzeugen.")

    if n_sc == 0:
        reasons.append("Keine Szenen-Prompts.")
        actions.append("Szenen-Prompts ableiten.")

    stop_hard = (
        q.status == "fail"
        or bool(q.blocking_issues)
        or not hk
        or n_ch == 0
        or n_sc == 0
    )
    stop_combo = n is not None and n.status == "weak" and q.status != "pass"

    if stop_combo:
        reasons.append("Narrativ weak bei Quality ≠ pass — zu hohes Gesamtrisiko.")
        actions.append("Struktur und Story gemeinsam nachziehen.")

    if stop_hard or stop_combo:
        conf = _clamp_confidence("stop", _confidence_raw(plan, perf_note))
        return _pack("stop", conf, reasons, actions, checked)

    revise = False
    if q.status == "warning":
        revise = True
        reasons.append("Quality-Status warning.")
        actions.append("Quality-Warnungen abarbeiten.")

    if n is None:
        revise = True
        reasons.append("narrative_score_result fehlt.")
        actions.append("Narrative-Bewertung sicherstellen.")
    else:
        if n.status == "weak":
            revise = True
            reasons.append("Narrativ-Status weak (Quality ist pass).")
            actions.append("Story-Zugkraft stärken (siehe narrative_score_result).")
        if n.score < 50:
            revise = True
            reasons.append(f"Narrativ-Gesamtscore niedrig ({n.score}).")
            actions.append("Narrative Teilscores und Hook/Kapitel prüfen.")

    qw = len(q.warnings or [])
    if qw > WARNING_BUDGET_QUALITY:
        revise = True
        reasons.append(f"Viele Quality-Warnungen ({qw}).")
        actions.append("Warnliste gezielt reduzieren.")

    subs = _substantive_plan_warnings(plan)
    if len(subs) > WARNING_BUDGET_SUBSTANTIVE_PLAN:
        revise = True
        reasons.append(f"Viele substanzielle Plan-Warnungen ({len(subs)}).")
        actions.append("Quellen- und Hook-Engine-Hinweise prüfen.")

    if revise:
        conf = _clamp_confidence("revise", _confidence_raw(plan, perf_note))
        return _pack("revise", conf, reasons, actions, checked)

    reasons.append("Quality pass, Narrativ strong/moderate, keine Blocker.")
    conf = _clamp_confidence("go", _confidence_raw(plan, perf_note))
    return _pack("go", conf, reasons, actions, checked)


def _pack(
    decision: Literal["go", "revise", "stop"],
    confidence: int,
    reasons: List[str],
    actions: List[str],
    checked: List[str],
) -> PromptPlanReviewGateResult:
    reasons = list(dict.fromkeys(reasons))
    actions = list(dict.fromkeys(actions))
    return PromptPlanReviewGateResult(
        decision=decision,
        confidence=confidence,
        reasons=reasons,
        required_actions=actions,
        checked_signals=checked,
    )
