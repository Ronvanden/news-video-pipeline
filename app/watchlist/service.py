"""Watchlist-Service: Kanal auflösen, Metadaten, Firestore."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

from app.youtube.rss import fetch_channel_feed_entries
from app.youtube.resolver import resolve_channel_id
from app.watchlist.firestore_repo import (
    FirestoreUnavailableError,
    FirestoreWatchlistRepository,
)
from app.watchlist.models import (
    CreateWatchlistChannelResponse,
    ListWatchlistChannelsResponse,
    WatchlistChannel,
    WatchlistChannelCreateRequest,
)

logger = logging.getLogger(__name__)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _strip_feed_title(feed_title: str) -> str:
    s = (feed_title or "").strip()
    if s.endswith(" - YouTube"):
        s = s[: -len(" - YouTube")].strip()
    return s


def _canonical_channel_url(channel_id: str) -> str:
    return f"https://www.youtube.com/channel/{channel_id}"


def _doc_to_channel(data: dict) -> WatchlistChannel:
    return WatchlistChannel.model_validate(data)


def create_channel(
    request: WatchlistChannelCreateRequest,
    repo: FirestoreWatchlistRepository | None = None,
) -> CreateWatchlistChannelResponse:
    repo = repo or FirestoreWatchlistRepository()

    merged_warnings: List[str] = []

    channel_id, w_res = resolve_channel_id(request.channel_url)
    merged_warnings.extend(w_res)

    if not channel_id:
        merged_warnings.append(
            "Konnte keine Channel-ID auflösen; Kanal wird nicht gespeichert. "
            "Bitte vorzugsweise eine /channel/UC…-URL verwenden."
        )
        logger.info(
            "watchlist create aborted: unresolved channel_url (warnings=%s)",
            len(w_res),
        )
        return CreateWatchlistChannelResponse(channel=None, warnings=merged_warnings)

    feed_title, _entries, w_feed = fetch_channel_feed_entries(channel_id, 1)
    merged_warnings.extend(w_feed)

    display_name = _strip_feed_title(feed_title) or channel_id
    canon_url = _canonical_channel_url(channel_id)

    now = utc_now_iso()
    try:
        existing = repo.get_watch_channel_doc(channel_id)
    except FirestoreUnavailableError as e:
        raise FirestoreUnavailableError(str(e)) from e

    last_checked_at: str | None = None
    last_success_at: str | None = None
    last_error = ""

    if existing:
        raw_ca = existing.get("created_at")
        created_at = raw_ca if isinstance(raw_ca, str) and raw_ca.strip() else now
        st = existing.get("status")
        if st == "error":
            status_now = "active"
        elif st in ("active", "paused"):
            status_now = st
        else:
            status_now = "active"
        if isinstance(existing.get("last_checked_at"), str):
            last_checked_at = existing["last_checked_at"]
        if isinstance(existing.get("last_success_at"), str):
            last_success_at = existing["last_success_at"]
        last_error = str(existing.get("last_error") or "")
    else:
        created_at = now
        status_now = "active"

    channel = WatchlistChannel(
        id=channel_id,
        channel_url=canon_url,
        channel_id=channel_id,
        channel_name=display_name,
        status=status_now,
        check_interval=request.check_interval,
        max_results=request.max_results,
        auto_generate_script=request.auto_generate_script,
        auto_review_script=request.auto_review_script,
        target_language=request.target_language,
        duration_minutes=request.duration_minutes,
        min_score=request.min_score,
        ignore_shorts=request.ignore_shorts,
        created_at=created_at,
        updated_at=now,
        last_checked_at=last_checked_at,
        last_success_at=last_success_at,
        last_error=last_error,
        notes=request.notes,
    )

    try:
        repo.upsert_watch_channel(channel_id, channel.model_dump())
    except FirestoreUnavailableError:
        raise

    logger.info(
        "watchlist channel upserted: channel_id=%s status=%s",
        channel_id,
        channel.status,
    )
    return CreateWatchlistChannelResponse(channel=channel, warnings=merged_warnings)


def list_channels(
    repo: FirestoreWatchlistRepository | None = None,
) -> ListWatchlistChannelsResponse:
    repo = repo or FirestoreWatchlistRepository()
    try:
        docs = repo.list_watch_channel_docs()
    except FirestoreUnavailableError as e:
        raise FirestoreUnavailableError(str(e)) from e

    channels: List[WatchlistChannel] = []
    for d in docs:
        try:
            channels.append(_doc_to_channel(d))
        except Exception as e:
            logger.warning(
                "skipping malformed watch_channels doc doc_id=%s type=%s",
                d.get("id", "?"),
                type(e).__name__,
            )
            continue

    channels.sort(key=lambda c: c.created_at, reverse=True)
    return ListWatchlistChannelsResponse(channels=channels, warnings=[])
