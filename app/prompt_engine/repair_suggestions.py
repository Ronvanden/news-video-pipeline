"""BA 9.15 — Konkrete Reparaturvorschläge aus Quality, Narrative, Gate und Performance (ohne LLM)."""

from __future__ import annotations

from typing import List, Set, Tuple

from app.prompt_engine.performance_learning import evaluate_performance_snapshot
from app.prompt_engine.quality_check import MIN_CHAPTERS_PRODUCTION, MIN_HOOK_CHARS
from app.prompt_engine.schema import (
    ProductionPromptPlan,
    PromptRepairSuggestion,
    PromptRepairSuggestionsResult,
    RepairSuggestionCategory,
    RepairSuggestionPriority,
)

HOOK_CURIOSITY_LOW = 45
THUMB_SUB_LOW = 45
ESCALATION_LOW = 45
EMOTION_LOW = 45
MANY_QUALITY_WARNINGS = 5


def _push(
    out: List[PromptRepairSuggestion],
    seen: Set[Tuple[str, str]],
    category: RepairSuggestionCategory,
    priority: RepairSuggestionPriority,
    issue: str,
    suggestion: str,
) -> None:
    key = (category, issue[:240])
    if key in seen:
        return
    seen.add(key)
    out.append(
        PromptRepairSuggestion(
            category=category,
            priority=priority,
            issue=issue,
            suggestion=suggestion,
        )
    )


def build_prompt_repair_suggestions(plan: ProductionPromptPlan) -> PromptRepairSuggestionsResult:
    checked: List[str] = []
    rg = plan.review_gate_result

    if rg and rg.decision == "go":
        checked.extend(["review_gate"])
        return PromptRepairSuggestionsResult(
            status="not_needed",
            suggestions=[],
            summary="Plan is production-ready; no repair suggestions required.",
            checked_sources=checked,
        )

    if rg is None:
        checked.append("review_gate:missing")

    suggestions: List[PromptRepairSuggestion] = []
    seen: Set[Tuple[str, str]] = set()

    checked.append("review_gate")
    q = plan.quality_result
    n = plan.narrative_score_result

    if q:
        checked.append("quality_result")
        for bi in q.blocking_issues or []:
            _push(
                suggestions,
                seen,
                "quality",
                "high",
                f"Blocker: {bi}",
                "Zuerst diesen Blocker beheben; danach strukturelle Quality-Warnungen reduzieren.",
            )
        qw = len(q.warnings or [])
        if qw > MANY_QUALITY_WARNINGS:
            _push(
                suggestions,
                seen,
                "quality",
                "medium",
                f"Viele Quality-Warnungen ({qw}).",
                "Blocker entfernen, dann Warnungen der Reihe nach abarbeiten (Kapitel, Hook-Länge, Pflichtfelder).",
            )

    if n:
        checked.append("narrative_score_result")
        for w in n.weaknesses or []:
            _push(
                suggestions,
                seen,
                "narrative",
                "medium",
                str(w),
                "Stärkeren Konflikt, klaren Wendepunkt und höhere Stakes einbauen; Emotion und Eskalation schärfen.",
            )
        sub = n.subscores
        if sub.hook_curiosity_score < HOOK_CURIOSITY_LOW:
            _push(
                suggestions,
                seen,
                "hook",
                "medium",
                f"niedriger hook_curiosity_score ({sub.hook_curiosity_score}).",
                "Hook mit Curiosity Gap, konkretem Konflikt oder klarem Rätsel neu formulieren.",
            )
        if sub.escalation_score < ESCALATION_LOW:
            _push(
                suggestions,
                seen,
                "narrative",
                "medium",
                f"niedrige Eskalation ({sub.escalation_score}).",
                "Kapitelverlauf mit Setup → Wendepunkt → Auflösung schärfen; Zwischenacts markieren.",
            )
        if sub.emotional_pull_score < EMOTION_LOW:
            _push(
                suggestions,
                seen,
                "narrative",
                "medium",
                f"niedriger emotional_pull_score ({sub.emotional_pull_score}).",
                "Menschliche Stakes (Angst, Hoffnung, Risiko) für den Zuschauer erkennbar machen.",
            )
        if sub.thumbnail_potential_score < THUMB_SUB_LOW:
            _push(
                suggestions,
                seen,
                "thumbnail",
                "low",
                f"niedriger thumbnail_potential_score ({sub.thumbnail_potential_score}).",
                "Visuell klare Spannung: tragendes Objekt, Ort, Kontrast, eine offene Frage im Bildkonzept.",
            )
        if n.status == "weak":
            _push(
                suggestions,
                seen,
                "narrative",
                "high",
                "Narrativ-Status weak.",
                "Konflikt, Wendepunkt und emotionale Stakes über alle Kapitel hinweg stärken.",
            )

    hk = (plan.hook or "").strip()
    if not hk:
        _push(
            suggestions,
            seen,
            "hook",
            "high",
            "Hook leer.",
            "Hook mit Curiosity Gap, Konflikt oder konkretem Rätsel formulieren (keine Platzhalter).",
        )
    elif len(hk) < MIN_HOOK_CHARS:
        _push(
            suggestions,
            seen,
            "hook",
            "high",
            f"Hook zu kurz (< {MIN_HOOK_CHARS} Zeichen).",
            "Hook ausbauen: konkrete Szene, Zeitdruck oder offene Frage, die Retention stützt.",
        )

    n_ch = len(plan.chapter_outline or [])
    if n_ch == 0:
        _push(
            suggestions,
            seen,
            "chapters",
            "high",
            "Keine Kapitel.",
            "Kapitelstruktur mit mindestens 5 narrativen Beats anlegen: Setup, Kontext, Konflikt, Wendepunkt, Auflösung/offene Frage.",
        )
    elif n_ch < MIN_CHAPTERS_PRODUCTION:
        _push(
            suggestions,
            seen,
            "chapters",
            "high",
            f"Zu wenige Kapitel ({n_ch}; Ziel ≥ {MIN_CHAPTERS_PRODUCTION}).",
            "Struktur auf mindestens 5 Beats erweitern: (1) Setup (2) Kontext (3) Konflikt (4) Wendepunkt (5) Auflösung/offene Frage.",
        )

    n_sc = len(plan.scene_prompts or [])
    if n_sc == 0:
        _push(
            suggestions,
            seen,
            "scenes",
            "high",
            "Keine Szenen-Prompts.",
            "Pro Kapitel genau einen Scene Prompt erzeugen und visuell zum Beat passend halten.",
        )
    elif n_ch > 0 and n_sc != n_ch:
        _push(
            suggestions,
            seen,
            "scenes",
            "high",
            f"Szenenanzahl ({n_sc}) passt nicht zu Kapiteln ({n_ch}).",
            "Für jedes Kapitel genau einen Scene Prompt ableiten und synchronisieren.",
        )

    if not (plan.voice_style or "").strip():
        _push(
            suggestions,
            seen,
            "voice",
            "medium",
            "voice_style leer.",
            "Voice-Persona passend zum Template ergänzen (z. B. ruhig, investigativ, dokumentarisch).",
        )

    if not (plan.thumbnail_angle or "").strip():
        _push(
            suggestions,
            seen,
            "thumbnail",
            "medium",
            "thumbnail_angle leer.",
            "Thumbnail: klare visuelle Spannung — Objekt, Ort, Kontrast, eine implizite Frage.",
        )

    if rg:
        checked.append("review_gate.required_actions")
        for ra in rg.required_actions or []:
            ra_stripped = (ra or "").strip()
            if not ra_stripped:
                continue
            _push(suggestions, seen, "quality", "medium", ra_stripped, ra_stripped)

    if plan.performance_record is not None:
        checked.append("performance_record")
        snap = evaluate_performance_snapshot(plan.performance_record)
        if snap.status == "pending_data":
            _push(
                suggestions,
                seen,
                "performance",
                "low",
                "Performance-KPIs noch nicht geliefert (pending_data).",
                "Später CTR, Watchtime und RPM ergänzen, um Template-Performance zu messen.",
            )

    summary = (
        f"{len(suggestions)} konkrete Reparaturhinweise aus Quality, Narrative, Gate und Performance-Signalen."
        if suggestions
        else "Keine zusätzlichen strukturierten Vorschläge generiert."
    )

    return PromptRepairSuggestionsResult(
        status="suggestions_available",
        suggestions=suggestions,
        summary=summary,
        checked_sources=list(dict.fromkeys(checked)),
    )
