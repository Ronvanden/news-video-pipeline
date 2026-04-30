"""BA 9.7 — Template Health / Performance-Schätzungen (interne Heuristik, keine externen KPIs)."""

from __future__ import annotations

from app.watchlist.models import StoryEngineDriftTemplateRow, StoryEngineTemplateScoresRow


def scores_from_drift_row(drift: StoryEngineDriftTemplateRow) -> StoryEngineTemplateScoresRow:
    """
    Leitet Health- und Roh-Performance-Schätzungen aus Drift-Kennzahlen ab.
    """
    n = max(drift.script_count, 1)
    warn_frac = float(drift.scripts_with_any_template_conformance_warning) / float(n)
    fail_frac = float(drift.scripts_template_gate_failed) / float(n)
    avg_hook = drift.avg_hook_score

    internal_performance = 45.0 + 6.5 * avg_hook - 52.0 * warn_frac - 52.0 * fail_frac
    internal_performance = round(max(0.0, min(100.0, internal_performance)), 3)

    distinct_non_empty = drift.distinct_nonempty_template_definition_versions
    dispersion_ratio = drift.definition_version_dispersion_ratio
    if distinct_non_empty > 2:
        drift_penalty_multiplier = 1.0
    else:
        drift_penalty_multiplier = 0.6
    drift_factor = dispersion_ratio * drift_penalty_multiplier
    health = internal_performance - 18.0 * min(1.0, drift_factor)
    health = round(max(0.0, min(100.0, health)), 3)

    return StoryEngineTemplateScoresRow(
        template_id=drift.template_id,
        health_score_0_to_100=health,
        internal_performance_score_0_to_100=internal_performance,
    )
