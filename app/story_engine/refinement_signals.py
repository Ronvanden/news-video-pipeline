"""BA 9.7 — Adaptive Refinement Inputs (Lesevorschläge, kein automatisches Rewrite)."""

from __future__ import annotations

from typing import List

from app.watchlist.models import StoryEngineDriftTemplateRow

_PERF_TAG = "[template_conformance:"


def refinement_suggestions_for_template_rows(
    drift_rows: List[StoryEngineDriftTemplateRow],
) -> List[str]:
    refined: List[str] = []
    for d in drift_rows:
        tid = d.template_id
        n = max(d.script_count, 1)
        nn = getattr(d, "distinct_nonempty_template_definition_versions", 0)
        warn_frac = float(d.scripts_with_any_template_conformance_warning) / float(n)
        fail_frac = float(d.scripts_template_gate_failed) / float(n)
        if nn > 2 and n >= 5:
            refined.append(
                f"[template_refinement:template_definition_alignment] Für '{tid}' gibt es "
                f"{nn} verschiedene `template_definition_version`-Werte in der Stichprobe — "
                "Blueprint-Änderungen bündeln und Version hochziehen.",
            )
        if warn_frac >= 0.22 and n >= 4:
            refined.append(
                f"[template_refinement:blueprint_review] Für '{tid}' sind viele Skripte mit "
                f"`{_PERF_TAG}…`-Hinweisen versehen (~{warn_frac:.0%} der Stichprobe) — Blueprint prüfen.",
            )
        if fail_frac >= 0.12 and n >= 4:
            refined.append(
                f"[template_refinement:template_gate_review] Für '{tid}' ist der Anteil gate `failed` "
                f"höher (~{fail_frac:.0%}) — Strict-Schwellen oder Eingangsqualität prüfen.",
            )
    return sorted(set(refined))


def low_sample_warning_line(min_n: int) -> str:
    return (
        f"[template_refinement:low_sample_size] Weniger als {min_n} Skripte in der "
        "Stichprobe — Scores sind nur indicative."
    )


def empty_sample_warning_line() -> str:
    return "Stichprobe leer — keine Story-Engine-Optimization-Statistik."
