"""BA 9.27 — Template-Empfehlung aus Topic + optionaler Performance-Historie."""

from __future__ import annotations

from typing import Dict, List, Optional

from app.prompt_engine.performance_learning import summarize_template_performance
from app.prompt_engine.schema import PerformanceRecord, TemplateRecommendationBasis, TemplateRecommendationResult
from app.prompt_engine.topic_classifier import classify_topic


def recommend_best_template(
    topic: str,
    available_templates: List[str],
    performance_data: Optional[List[PerformanceRecord]] = None,
    *,
    template_docs: Optional[Dict[str, Dict]] = None,
    current_narrative_archetype_id: str = "",
) -> TemplateRecommendationResult:
    warnings: List[str] = []
    cleaned = [t for t in available_templates if t and str(t).strip()]
    if not cleaned:
        warnings.append("available_templates leer — Fallback true_crime.")
        return TemplateRecommendationResult(
            recommended_template="true_crime",
            confidence=20,
            recommendation_basis="topic_match",
            alternatives=[],
            warnings=warnings,
        )

    docs = template_docs or {k: {} for k in cleaned}
    sub_docs = {k: docs[k] for k in cleaned if k in docs}
    classification = classify_topic(topic, sub_docs)
    topic_pick = (
        classification.template_type
        if classification.template_type in cleaned
        else cleaned[0]
    )

    basis: TemplateRecommendationBasis = "topic_match"
    confidence = 55
    recommended = topic_pick

    scores = dict(classification.scores) if classification.scores else {}
    top_hits = max(scores.values()) if scores else 0
    if top_hits >= 2:
        confidence += 15
    elif top_hits == 0:
        confidence -= 10
        warnings.append("Keine Keyword-Überlappung mit Templates — Default-Gewichtung.")

    if performance_data:
        summaries = summarize_template_performance(performance_data)
        if summaries:
            ranked = sorted(
                summaries,
                key=lambda s: (
                    -(s.avg_learning_score or 0.0) * 0.4
                    - (s.avg_quality_score or 0.0) * 0.3
                    - (s.avg_narrative_score or 0.0) * 0.3,
                    s.template_type,
                ),
            )
            historical_winner = ranked[0].template_type
            if historical_winner in cleaned and historical_winner != topic_pick:
                recommended = historical_winner
                basis = "historical_performance"
                confidence = min(95, confidence + 22)
                alternatives = [topic_pick] + [t for t in cleaned if t not in (recommended, topic_pick)][:2]
            elif historical_winner in cleaned:
                recommended = historical_winner
                basis = "historical_performance"
                confidence = min(92, confidence + 12)
                alternatives = [t for t in cleaned if t != recommended][:3]

    if basis == "topic_match":
        alternatives = [t for t in cleaned if t != recommended][:3]

    if template_docs and current_narrative_archetype_id and basis != "historical_performance":
        arc_hits: List[str] = []
        for key, doc in template_docs.items():
            if key not in cleaned:
                continue
            arcs = doc.get("narrative_archetypes") or doc.get("archetypes") or []
            for a in arcs:
                if not isinstance(a, dict):
                    continue
                aid = str(a.get("id", ""))
                if aid and aid == current_narrative_archetype_id:
                    arc_hits.append(key)
                    break
        if arc_hits:
            alt_pick = arc_hits[0]
            if alt_pick != recommended:
                alternatives = [recommended] + [x for x in arc_hits if x != alt_pick][:2]
                recommended = alt_pick
                basis = "narrative_fit"
                confidence = min(88, confidence + 10)

    confidence = max(15, min(100, confidence))
    return TemplateRecommendationResult(
        recommended_template=recommended,
        confidence=confidence,
        recommendation_basis=basis,
        alternatives=alternatives,
        warnings=warnings,
    )
