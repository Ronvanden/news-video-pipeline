"""Szenen-Prompt-Zeilen aus Kapiteln + Template-Pattern."""

from __future__ import annotations

from typing import Dict, List

from app.prompt_engine.schema import ChapterOutlineItem


def build_scene_prompts(
    chapters: List[ChapterOutlineItem],
    template_doc: Dict,
    topic: str,
) -> List[str]:
    pattern = str(template_doc.get("scene_pattern") or "").strip()
    t = (topic or "").strip() or "Thema"
    prompts: List[str] = []
    for idx, ch in enumerate(chapters, start=1):
        line = pattern.format(
            idx=idx,
            chapter_title=ch.title,
            topic=t,
        )
        prompts.append(line.strip())
    return prompts
