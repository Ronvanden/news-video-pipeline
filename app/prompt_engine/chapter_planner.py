"""Kapitel-Outline aus gewähltem Archetyp — Platzhalter deterministisch ersetzt."""

from __future__ import annotations

from typing import Any, Dict, List

from app.prompt_engine.schema import ChapterOutlineItem


def _fill(template: str, topic: str) -> str:
    return template.replace("{topic}", topic.strip() or "Thema")


def build_chapter_outline(archetype_doc: Dict[str, Any], topic: str) -> List[ChapterOutlineItem]:
    slots = archetype_doc.get("chapter_slots") or []
    out: List[ChapterOutlineItem] = []
    for slot in slots:
        title = _fill(str(slot.get("title") or ""), topic)
        summary = _fill(str(slot.get("summary") or ""), topic)
        out.append(ChapterOutlineItem(title=title, summary=summary))
    return out
