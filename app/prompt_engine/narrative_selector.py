"""Wählt Narrativ-Archetyp innerhalb eines geladenen Templates."""

from __future__ import annotations

from typing import Any, Dict, List


def select_archetype(topic: str, template_doc: Dict[str, Any]) -> Dict[str, Any]:
    blob = (topic or "").lower()
    archetypes: List[Dict[str, Any]] = template_doc.get("narrative_archetypes") or []
    default_id = str(template_doc.get("default_archetype_id") or "")

    scored: List[tuple[int, str, Dict[str, Any]]] = []
    for arc in archetypes:
        kws = arc.get("match_keywords") or []
        score = sum(1 for w in kws if str(w).lower() in blob)
        arc_id = str(arc.get("id") or "")
        scored.append((score, arc_id, arc))
    scored.sort(key=lambda x: (-x[0], x[1]))

    if scored and scored[0][0] > 0:
        return scored[0][2]

    for arc in archetypes:
        if str(arc.get("id")) == default_id:
            return arc
    if archetypes:
        return archetypes[0]
    return {"id": default_id or "default", "chapter_slots": []}
