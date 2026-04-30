"""BA 9.7 — Template Drift Detection (deterministisch aus persistierten Feldern)."""

from __future__ import annotations

from collections import Counter
from typing import List, Sequence

from app.story_engine.templates import normalize_story_template_id
from app.watchlist.models import GeneratedScript, StoryEngineDriftTemplateRow

_PERF_TAG = "[template_conformance:"


def has_template_conformance_warning(warnings: Sequence[str]) -> bool:
    for w in warnings or ():
        if _PERF_TAG in str(w).lower():
            return True
    return False


def group_scripts_by_normalized_template(
    rows: Sequence[GeneratedScript],
) -> tuple[dict[str, List[GeneratedScript]], List[str]]:
    """Gruppiere nach kanonischer Template-ID; sammle Normalisierungs-Warnungen."""
    groups: dict[str, List[GeneratedScript]] = {}
    nw: List[str] = []
    for r in rows:
        tid, ws = normalize_story_template_id(getattr(r, "video_template", None))
        groups.setdefault(tid, []).append(r)
        for w in ws:
            nw.append(str(w))
    return groups, nw


def build_drift_row_for_template(template_id: str, grp: Sequence[GeneratedScript]) -> StoryEngineDriftTemplateRow:
    """Eine Aggregationszeile für Drift-Analyse je Template-Stichprobe."""
    n = len(grp)
    raw_versions = [((getattr(x, "template_definition_version", None) or "").strip()) for x in grp]
    non_empty = [v for v in raw_versions if v]
    distinct_non_empty_count = len(set(non_empty)) if non_empty else 0
    distinct_eff = distinct_non_empty_count if distinct_non_empty_count else (1 if n else 0)
    ctr = Counter(raw_versions if any(raw_versions) else ["(empty)"])
    dominant = ctr.most_common(1)[0][0]

    dispersion = (
        float(distinct_non_empty_count) / float(max(n, 1)) if distinct_non_empty_count else 0.0
    )
    dispersion = min(1.0, dispersion)

    conf_warn = sum(1 for x in grp if has_template_conformance_warning(x.warnings))
    gate_fail = sum(
        1
        for x in grp
        if (str(getattr(x, "template_conformance_gate", None) or "")).strip().lower() == "failed"
    )
    avg_hook = (
        sum(float(getattr(x, "hook_score", 0.0) or 0.0) for x in grp) / float(max(n, 1))
        if n
        else 0.0
    )
    return StoryEngineDriftTemplateRow(
        template_id=template_id,
        script_count=n,
        distinct_template_definition_versions=distinct_eff,
        distinct_nonempty_template_definition_versions=distinct_non_empty_count,
        dominant_template_definition_version=dominant,
        definition_version_dispersion_ratio=dispersion,
        scripts_with_any_template_conformance_warning=conf_warn,
        scripts_template_gate_failed=gate_fail,
        avg_hook_score=round(min(10.0, max(0.0, avg_hook)), 6),
    )
