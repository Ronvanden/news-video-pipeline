"""Tests für POST /watchlist/channels/{id}/check (Mock Firestore + Mock Feed)."""

from __future__ import annotations

import unittest
from typing import Any, Dict
from unittest.mock import MagicMock

from app.watchlist.firestore_repo import FirestoreUnavailableError, FirestoreWatchlistRepository
from app.watchlist.models import ProcessedVideo, WatchlistChannel
from app.watchlist import service as watchlist_service


def _channel(
    *,
    cid: str = "UC_test_channel",
    status: str = "active",
    max_results: int = 10,
    min_score: int = 40,
    ignore_shorts: bool = True,
) -> WatchlistChannel:
    return WatchlistChannel(
        id=cid,
        channel_url=f"https://www.youtube.com/channel/{cid}",
        channel_id=cid,
        channel_name="Test Channel",
        status=status,
        check_interval="manual",
        max_results=max_results,
        auto_generate_script=False,
        auto_review_script=True,
        target_language="de",
        duration_minutes=10,
        min_score=min_score,
        ignore_shorts=ignore_shorts,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )


def _vid(
    *,
    vid: str = "videoid1",
    title: str = "Normal video title enough words here",
    url: str = "https://www.youtube.com/watch?v=videoid1",
    score: int = 50,
    published_at: str = "2026-04-01T12:00:00Z",
) -> Dict[str, Any]:
    return {
        "title": title,
        "url": url,
        "video_id": vid,
        "published_at": published_at,
        "summary": "x",
        "score": score,
        "reason": "test reason",
        "duration_seconds": 600,
        "media_keywords": "",
    }


class TestWatchlistCheckChannel(unittest.TestCase):
    def test_a_channel_not_found(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        repo.get_watch_channel.return_value = None
        feed = MagicMock()

        resp = watchlist_service.check_channel("UC_missing", repo=repo, get_videos=feed)

        feed.assert_not_called()
        self.assertEqual(resp.warnings[0], "Watchlist channel not found.")

    def test_b_new_seen_and_processed_created(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        ch = _channel(cid="UC_a")
        repo.get_watch_channel.return_value = ch
        vidrow = _vid(vid="v_new", score=50)
        feed = MagicMock(
            return_value={"channel": ch.channel_name, "videos": [vidrow], "warnings": ["w-feed"]}
        )
        repo.get_processed_video.return_value = None
        pv_store: Dict[str, ProcessedVideo] = {}

        def create_pv(pv: ProcessedVideo) -> ProcessedVideo:
            pv_store[pv.video_id] = pv
            return pv

        repo.create_processed_video.side_effect = create_pv

        resp = watchlist_service.check_channel(ch.channel_id, repo=repo, get_videos=feed)

        self.assertEqual(len(resp.new_videos), 1)
        self.assertEqual(resp.new_videos[0].video_id, "v_new")
        self.assertEqual(resp.created_processed_videos, 1)
        repo.upsert_watch_channel.assert_called()
        repo.create_processed_video.assert_called_once()
        self.assertEqual(pv_store["v_new"].status, "seen")
        self.assertIn("w-feed", resp.warnings)

    def test_c_repeat_check_known_no_duplicate_writes(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        ch = _channel(cid="UC_c")
        repo.get_watch_channel.return_value = ch
        vidrow = _vid(vid="v_same", score=90)
        feed = MagicMock(
            return_value={"channel": ch.channel_name, "videos": [vidrow], "warnings": []}
        )
        existing = ProcessedVideo(
            id="v_same",
            channel_id=ch.channel_id,
            video_id="v_same",
            video_url=vidrow["url"],
            title=vidrow["title"],
            published_at=vidrow["published_at"],
            first_seen_at="2026-01-01T00:00:00Z",
            status="seen",
            score=90,
            reason="old",
            is_short=False,
            skip_reason="",
            script_job_id=None,
            review_result_id=None,
            last_error="",
        )
        repo.get_processed_video.return_value = existing

        resp = watchlist_service.check_channel(ch.channel_id, repo=repo, get_videos=feed)

        self.assertEqual(len(resp.known_videos), 1)
        self.assertEqual(len(resp.new_videos), 0)
        repo.create_processed_video.assert_not_called()
        self.assertEqual(resp.created_processed_videos, 0)

    def test_d_ignore_shorts_short_skipped(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        ch = _channel(cid="UC_d", ignore_shorts=True)
        repo.get_watch_channel.return_value = ch
        vidrow = _vid(
            vid="vshort",
            url="https://www.youtube.com/shorts/vshort",
            title="Shorts",
            score=90,
        )
        feed = MagicMock(
            return_value={"channel": ch.channel_name, "videos": [vidrow], "warnings": []}
        )
        repo.get_processed_video.return_value = None

        resp = watchlist_service.check_channel(ch.channel_id, repo=repo, get_videos=feed)

        self.assertEqual(len(resp.skipped_videos), 1)
        self.assertEqual(resp.skipped_videos[0].skip_reason, "shorts_ignored")
        args, _ = repo.create_processed_video.call_args
        self.assertEqual(args[0].status, "skipped")
        self.assertEqual(args[0].skip_reason, "shorts_ignored")

    def test_e_score_below_minimum(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        ch = _channel(cid="UC_e", min_score=70, ignore_shorts=False)
        repo.get_watch_channel.return_value = ch
        vidrow = _vid(vid="vlow", score=20)
        vidrow["url"] = "https://www.youtube.com/watch?v=vlow"
        feed = MagicMock(
            return_value={"channel": ch.channel_name, "videos": [vidrow], "warnings": []}
        )
        repo.get_processed_video.return_value = None

        resp = watchlist_service.check_channel(ch.channel_id, repo=repo, get_videos=feed)

        self.assertEqual(len(resp.skipped_videos), 1)
        self.assertEqual(resp.skipped_videos[0].skip_reason, "score_below_minimum")
        args, _ = repo.create_processed_video.call_args
        self.assertEqual(args[0].skip_reason, "score_below_minimum")

    def test_f_paused_no_feed_call(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        ch = _channel(cid="UC_f", status="paused")
        repo.get_watch_channel.return_value = ch
        feed = MagicMock()

        resp = watchlist_service.check_channel(ch.channel_id, repo=repo, get_videos=feed)

        feed.assert_not_called()
        self.assertEqual(resp.warnings[0], "Watchlist channel is not active.")
        repo.upsert_watch_channel.assert_not_called()

    def test_firestore_propagates(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        repo.get_watch_channel.side_effect = FirestoreUnavailableError("x")

        with self.assertRaises(FirestoreUnavailableError):
            watchlist_service.check_channel("UC_x", repo=repo)


if __name__ == "__main__":
    unittest.main()
