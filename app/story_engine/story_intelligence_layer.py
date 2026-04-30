"""BA 9.8 — Story Intelligence Layer: erklärbare Hinweise (kein Auto-Umschalten ohne Policy)."""

from __future__ import annotations

from collections import Counter
from typing import Iterable, Sequence

from app.watchlist.models import (
    GeneratedScript,
    StoryEngineDriftTemplateRow,
    StoryEngineIntelligenceSummary,
    StoryEngineTemplateOptimizationSummary,
    StoryEngineTemplateScoresRow,
)


def build_story_engine_intelligence_summary(
    rows: Sequence[GeneratedScript],
    optimization: StoryEngineTemplateOptimizationSummary,
) -> StoryEngineIntelligenceSummary:
    """
    Nutzt bestehende Stichprobe + BA-9.7-Signalblock.
    Alle Ausgaben sind Textlisten für Ops/Governance-Auswertung.
    """
    narrative: list[str] = []
    cross: list[str] = []
    readiness: list[str] = []

    if not optimization.min_statistics_sample_met or optimization.sample_scripts < 1:
        readiness.append(
            "[story_intelligence:readiness_sampling] Zu wenige Skripte — Empfehlungen nur "
            "qualitativ; mehr Watchlist-Produktion abwarten oder Stichprobengrenze erhöhen.",
        )

    tmpl_counts = Counter()
    experiments = Counter()
    variants = Counter()
    for r in rows or []:
        vt = str(getattr(r, "video_template", "") or "").strip() or "(unset)"
        tmpl_counts[vt] += 1
        if (getattr(r, "experiment_id", None) or "").strip():
            experiments[(getattr(r, "experiment_id", None) or "").strip()] += 1
        if (getattr(r, "hook_variant_id", None) or "").strip():
            variants[(getattr(r, "hook_variant_id", None) or "").strip()] += 1

    total_scripts = optimization.sample_scripts or sum(tmpl_counts.values()) or len(rows)

    readiness.append(
        "[story_intelligence:readiness_no_closed_loop] Kein automatisches Lernen: "
        "Empfehlungen sind Read-only Vorschläge ohne Schreibzugriff auf Produktions-Skripte.",
    )

    if experiments:
        readiness.append(
            "[story_intelligence:readiness_experimentation] Experiment-IDs in der Stichprobe "
            f"erfassbar ({len(experiments)} Kennungen) — geeigneter Vorläufer für Auswertung.",
        )
    else:
        readiness.append(
            "[story_intelligence:readiness_experimentation_sparse] Keine Experiment-IDs in dieser "
            "Stichprobe — A/B-/Registry-Felder aktivieren oder längeres Fenster wählen.",
        )

    high_dispersion_templates = sorted(
        d.template_id for d in optimization.drift_rows if d.definition_version_dispersion_ratio > 0.35
    )
    if high_dispersion_templates:
        readiness.append(
            "[story_intelligence:readiness_drift_signals] Höhere Versions-Dispersion bei: "
            f"{', '.join(high_dispersion_templates)}.",
        )

    if total_scripts > 0:
        tops = tmpl_counts.most_common(12)
        for vt, ct in tops:
            cross.append(f"template_distribution: {vt!r}: {100.0 * float(ct)/float(total_scripts):.1f}% ({ct})")

    scores_by_template: Iterable[StoryEngineTemplateScoresRow] = optimization.scores
    drift_by_template: Iterable[StoryEngineDriftTemplateRow] = optimization.drift_rows
    drift_index = {d.template_id: d for d in drift_by_template}

    ranked = sorted(
        scores_by_template,
        key=lambda x: x.health_score_0_to_100,
        reverse=True,
    )
    if ranked and optimization.min_statistics_sample_met:
        best = ranked[0]
        worst = ranked[-1]
        dd = drift_index.get(best.template_id)
        narrative.append(
            f"[story_intelligence:template_observation_health] Höchste aggregierte Gesundheit in dieser "
            f"Stichprobe: `{best.template_id}` (health≈{best.health_score_0_to_100:.1f}); "
            f"niedrigste: `{worst.template_id}` (≈{worst.health_score_0_to_100:.1f}). "
            "Keine automatische Produkt-Umstellung ohne redaktionelle Freigabe."
        )
        if dd:
            narrative.append(
                f"[story_intelligence:operational_followup_template] Bei Umstellungsüberlegungen erst "
                f"`template_definition_version` und Blueprint von `{best.template_id}` prüfen "
                f"(dominant {dd.dominant_template_definition_version!r}).",
            )

    narrative.append(
        "[story_intelligence:template_recommendation_logic] Für neue Kanäle ohne festes Editorial: "
        "als Startpunkt die Templates mit höherem `health_score_0_to_100` in "
        "`template_optimization.scores` prüfen; Ausnahmen bei Genre/Marke dokumentieren.",
    )

    return StoryEngineIntelligenceSummary(
        narrative_recommendations=narrative,
        cross_template_summary=cross,
        self_learning_readiness_notes=readiness,
    )
