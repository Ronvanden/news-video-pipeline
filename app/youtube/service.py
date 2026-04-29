"""Orchestrierung: Resolver + RSS + Scoring."""

from __future__ import annotations

from typing import Any, Dict, List

from app.youtube.resolver import resolve_channel_id
from app.youtube.rss import fetch_channel_feed_entries
from app.youtube.scoring import build_summary_from_title, score_video

def get_latest_channel_videos(channel_url: str, max_results: int) -> Dict[str, Any]:
    warnings: List[str] = []
    n = max(1, int(max_results))

    channel_id, w_res = resolve_channel_id(channel_url)
    warnings.extend(w_res)
    if not channel_id:
        return {"channel": "", "videos": [], "warnings": warnings}

    feed_title, entries, w_feed = fetch_channel_feed_entries(channel_id, n)
    warnings.extend(w_feed)

    display_name = feed_title
    if display_name.endswith(" - YouTube"):
        display_name = display_name[: -len(" - YouTube")].strip()

    videos: List[Dict[str, Any]] = []
    for e in entries:
        sc, reason = score_video(
            e.title,
            e.published_at,
            e.duration_seconds,
            video_url=e.url,
            media_keywords=e.media_keywords,
        )
        summary = build_summary_from_title(e.title)
        videos.append(
            {
                "title": e.title,
                "url": e.url,
                "video_id": e.video_id,
                "published_at": e.published_at,
                "summary": summary,
                "score": sc,
                "reason": reason,
            }
        )

    return {
        "channel": display_name or channel_id,
        "videos": videos,
        "warnings": warnings,
    }
