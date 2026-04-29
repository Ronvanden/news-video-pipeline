"""Orchestrierung: Resolver + RSS + Scoring."""

from __future__ import annotations

from typing import Any, Dict, List

from app.youtube.resolver import resolve_channel_id
from app.youtube.rss import fetch_channel_feed_entries
from app.youtube.scoring import build_summary_from_title, score_video


def get_latest_channel_videos(
    channel_url: str,
    max_results: int,
    *,
    include_feed_metadata: bool = False,
) -> Dict[str, Any]:
    """Liefert neueste Videos aus dem Kanal-RSS.

    ``include_feed_metadata`` ist nur für interne Aufrufe (z. B. Watchlist-Check):
    ergänzt pro Video ``duration_seconds`` und ``media_keywords`` — der
    öffentliche Endpoint ``POST /youtube/latest-videos`` nutzt den Default ``False``.
    """
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
        row: Dict[str, Any] = {
            "title": e.title,
            "url": e.url,
            "video_id": e.video_id,
            "published_at": e.published_at,
            "summary": summary,
            "score": sc,
            "reason": reason,
        }
        if include_feed_metadata:
            row["duration_seconds"] = e.duration_seconds
            row["media_keywords"] = e.media_keywords
        videos.append(row)

    return {
        "channel": display_name or channel_id,
        "videos": videos,
        "warnings": warnings,
    }
