"""Topic → template_key (deterministisch, keyword-scoring)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class TopicClassification:
    template_type: str
    scores: Tuple[Tuple[str, int], ...]
    rationale: str


def classify_topic(topic: str, templates: Dict[str, Dict]) -> TopicClassification:
    blob = (topic or "").lower()
    scores: List[Tuple[str, int]] = []
    for key, doc in sorted(templates.items()):
        kws = doc.get("classifier_keywords") or []
        s = sum(1 for w in kws if str(w).lower() in blob)
        scores.append((key, s))
    scores.sort(key=lambda x: (-x[1], x[0]))

    if not scores:
        return TopicClassification(
            template_type="true_crime",
            scores=tuple(),
            rationale="Keine Templates geladen (Fallback true_crime).",
        )

    winner = scores[0][0]
    if scores[0][1] == 0 and "true_crime" in templates:
        winner = "true_crime"

    rationale = (
        f"Keyword-Treffer je Template: {dict(scores)}; "
        f"Auswahl '{winner}' (bei 0 Treffern: Default true_crime wenn vorhanden)."
    )
    return TopicClassification(
        template_type=winner,
        scores=tuple(scores),
        rationale=rationale,
    )
