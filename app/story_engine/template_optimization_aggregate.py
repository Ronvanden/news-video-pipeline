"""BA 9.7 — Ergebniszusammenstellung Adaptive Template Optimization."""

from __future__ import annotations

from typing import List, Sequence

from app.story_engine.refinement_signals import (
    empty_sample_warning_line,
    low_sample_warning_line,
    refinement_suggestions_for_template_rows,
)
from app.story_engine.template_drift import (
    build_drift_row_for_template,
    group_scripts_by_normalized_template,
)
from app.story_engine.template_health_score import scores_from_drift_row
from app.watchlist.models import (
    GeneratedScript,
    StoryEngineDriftTemplateRow,
    StoryEngineTemplateOptimizationSummary,
)

_MIN_STATS_SAMPLE = 12


def build_story_engine_template_optimization_summary(
    rows: Sequence[GeneratedScript],
) -> StoryEngineTemplateOptimizationSummary:
    """
    Liefert Drift-, Score- und Refinement-Signale ohne Persistenz oder Generate-Vertragsänderung.
    """
    if not rows:
        return StoryEngineTemplateOptimizationSummary(
            sample_scripts=0,
            min_statistics_sample_met=False,
            warnings=[empty_sample_warning_line()],
        )

    grouped, nw = group_scripts_by_normalized_template(rows)

    drift_rows: List[StoryEngineDriftTemplateRow] = []
    for tid in sorted(grouped.keys()):
        grp = grouped[tid]
        drift_rows.append(build_drift_row_for_template(tid, grp))

    scores = [scores_from_drift_row(d) for d in drift_rows]

    refinement = refinement_suggestions_for_template_rows(drift_rows)

    total_n = sum(d.script_count for d in drift_rows)
    min_met = total_n >= _MIN_STATS_SAMPLE
    warnings_all: List[str] = []
    warnings_all.extend(list(dict.fromkeys(nw)))
    if not min_met:
        warnings_all.append(low_sample_warning_line(_MIN_STATS_SAMPLE))

    return StoryEngineTemplateOptimizationSummary(
        sample_scripts=total_n,
        min_statistics_sample_met=min_met,
        drift_rows=drift_rows,
        scores=scores,
        refinement_suggestions=refinement,
        warnings=list(dict.fromkeys(warnings_all)),
    )
