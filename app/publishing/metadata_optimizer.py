"""BA 13.1 — Title / Description / Tag Optimizer."""

from __future__ import annotations

from typing import List

from app.publishing.metadata_master_package import build_metadata_master_package
from app.publishing.schema import MetadataOptimizerResult


def _dedupe(items: List[str], *, limit: int) -> List[str]:
    out: List[str] = []
    for item in items:
        cleaned = " ".join((item or "").split())
        if cleaned and cleaned not in out:
            out.append(cleaned)
    return out[:limit]


def build_metadata_optimizer(plan: object) -> MetadataOptimizerResult:
    warnings: List[str] = []
    meta = getattr(plan, "metadata_master_package_result", None) or build_metadata_master_package(plan)
    base = meta.canonical_title or "Neue Story"
    hook = getattr(plan, "hook", "") or base
    archetype = getattr(plan, "narrative_archetype_id", "") or "story"

    titles = _dedupe(
        [
            base,
            f"Was wirklich hinter {base[:48]} steckt",
            f"{base[:58]}: Die wichtigsten Fragen",
            f"Die Story, die jetzt wichtig wird: {base[:48]}",
        ],
        limit=4,
    )
    descriptions = _dedupe(
        [
            meta.canonical_description,
            f"{base}\n\nKurzüberblick: {hook}\n\nKapitel und Kontext im Video.",
            f"Eine strukturierte Einordnung mit Kontext, Timeline und Fazit.\n\n{meta.canonical_description}",
        ],
        limit=3,
    )
    tags = _dedupe(meta.canonical_tags + [archetype, "youtube", "dokumentation", "analyse"], limit=20)

    if len(titles) < 3:
        warnings.append("few_title_variants")
    if len(tags) < 8:
        warnings.append("tag_cluster_sparse")

    seo_score = min(100, 40 + len(tags) * 3 + len(titles) * 5 + (10 if descriptions else 0))
    click_score = min(100, 35 + len(titles) * 8 + (10 if "?" in " ".join(titles) else 0))
    if meta.metadata_status == "blocked":
        seo_score = min(seo_score, 35)
        click_score = min(click_score, 35)
        warnings.append("metadata_blocked_optimizer_limited")

    return MetadataOptimizerResult(
        optimized_titles=titles,
        optimized_descriptions=descriptions,
        optimized_tags=tags,
        seo_score=seo_score,
        click_potential_score=click_score,
        warnings=list(dict.fromkeys(warnings + list(meta.compliance_warnings))),
    )
