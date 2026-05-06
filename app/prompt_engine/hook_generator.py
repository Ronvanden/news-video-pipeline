"""Dünne Schicht auf BA 9.2 Hook Engine — gleiche Regeln, kein zweites Regelwerk."""

from __future__ import annotations

from app.story_engine.hook_engine import generate_hook_v1


def planned_hook(
    *,
    video_template: str,
    topic: str,
    title: str,
    source_summary: str,
    manual_url_rewrite_mode: str = "",
):
    """Delegiert an generate_hook_v1 (HookEngineResult)."""
    return generate_hook_v1(
        video_template=video_template,
        topic=topic,
        title=title,
        source_summary=source_summary,
        manual_url_rewrite_mode=manual_url_rewrite_mode,
    )
