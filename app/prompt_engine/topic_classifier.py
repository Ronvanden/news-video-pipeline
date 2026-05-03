"""Topic → template_key (deterministisch, keyword-scoring)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

# Bei 0 Keyword-Treffern: eher Nachricht/Doku als True-Crime (Founder-Demo, generische URLs).
_ZERO_KEYWORD_FALLBACK_ORDER: Tuple[str, ...] = (
    "documentary",
    "public_interest",
    "mystery_history",
    "true_crime",
)


def _template_for_zero_keyword_hits(templates: Dict[str, Dict]) -> str:
    for key in _ZERO_KEYWORD_FALLBACK_ORDER:
        if key in templates:
            return key
    return sorted(templates.keys())[0]


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
        fb = _template_for_zero_keyword_hits(templates) if templates else "true_crime"
        return TopicClassification(
            template_type=fb,
            scores=tuple(),
            rationale=f"Keine Templates geladen oder leerer Katalog — Fallback {fb!r}.",
        )

    winner = scores[0][0]
    if scores[0][1] == 0:
        winner = _template_for_zero_keyword_hits(templates)

    rationale = (
        f"Keyword-Treffer je Template: {dict(scores)}; "
        f"Auswahl '{winner}' (bei 0 Treffern: Priorität documentary → public_interest → mystery_history → true_crime)."
    )
    return TopicClassification(
        template_type=winner,
        scores=tuple(scores),
        rationale=rationale,
    )
