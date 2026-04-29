"""Tests für POST /watchlist/channels/{id}/check (Mock Firestore + Mock Feed)."""

from __future__ import annotations

import unittest
from typing import Any, Dict
from unittest.mock import MagicMock

from app.watchlist.firestore_repo import FirestoreUnavailableError, FirestoreWatchlistRepository
from app.watchlist.models import ProcessedVideo, ScriptJob, WatchlistChannel
from app.watchlist import service as watchlist_service


def _channel(
    *,
    cid: str = "UC_test_channel",
    status: str = "active",
    max_results: int = 10,
    min_score: int = 40,
    ignore_shorts: bool = True,
    auto_generate_script: bool = False,
) -> WatchlistChannel:
    return WatchlistChannel(
        id=cid,
        channel_url=f"https://www.youtube.com/channel/{cid}",
        channel_id=cid,
        channel_name="Test Channel",
        status=status,
        check_interval="manual",
        max_results=max_results,
        auto_generate_script=auto_generate_script,
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


def _make_check_repo() -> MagicMock:
    repo = MagicMock(spec=FirestoreWatchlistRepository)
    repo.get_script_job.return_value = None
    return repo


class TestWatchlistCheckChannel(unittest.TestCase):
    def test_a_channel_not_found(self):
        repo = _make_check_repo()
        repo.get_watch_channel.return_value = None
        feed = MagicMock()

        resp = watchlist_service.check_channel("UC_missing", repo=repo, get_videos=feed)

        feed.assert_not_called()
        self.assertEqual(resp.warnings[0], "Watchlist channel not found.")

    def test_b_auto_off_seen_processed_created_jobs_empty(self):
        repo = _make_check_repo()
        ch = _channel(cid="UC_a", auto_generate_script=False)
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
        self.assertEqual(resp.created_jobs, [])
        repo.upsert_watch_channel.assert_called()
        repo.create_processed_video.assert_called_once()
        self.assertEqual(pv_store["v_new"].status, "seen")
        self.assertIn("w-feed", resp.warnings)
        repo.get_script_job.assert_not_called()

    def test_c_auto_on_creates_pending_script_job(self):
        repo = _make_check_repo()
        ch = _channel(cid="UC_auto", auto_generate_script=True)
        repo.get_watch_channel.return_value = ch
        vidrow = _vid(vid="v_job", score=65)
        feed = MagicMock(return_value={"channel": ch.channel_name, "videos": [vidrow], "warnings": []})
        repo.get_processed_video.return_value = None

        captured_jobs = []

        def capture_job(job):
            captured_jobs.append(job)
            return job

        repo.create_script_job.side_effect = capture_job

        resp = watchlist_service.check_channel(ch.channel_id, repo=repo, get_videos=feed)

        self.assertEqual(len(resp.created_jobs), 1)
        cj = resp.created_jobs[0]
        self.assertEqual(cj.video_id, "v_job")
        self.assertEqual(cj.status, "pending")
        self.assertEqual(cj.target_language, "de")
        self.assertEqual(cj.duration_minutes, 10)
        self.assertEqual(cj.video_url, vidrow["url"])
        repo.create_script_job.assert_called_once()
        self.assertEqual(captured_jobs[0].status, "pending")
        self.assertEqual(captured_jobs[0].source_type, "youtube_transcript")
        repo.update_processed_video_job_link.assert_called_once_with("v_job", "v_job")

    def test_d_repeat_check_known_no_job_call(self):
        repo = _make_check_repo()
        ch = _channel(cid="UC_c", auto_generate_script=True)
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
        self.assertEqual(resp.created_jobs, [])
        repo.get_script_job.assert_not_called()

    def test_e_ignore_shorts_no_job(self):
        repo = _make_check_repo()
        ch = _channel(cid="UC_d", ignore_shorts=True, auto_generate_script=True)
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
        self.assertEqual(resp.created_jobs, [])
        repo.get_script_job.assert_not_called()

    def test_f_score_below_minimum_no_job(self):
        repo = _make_check_repo()
        ch = _channel(cid="UC_e", min_score=70, ignore_shorts=False, auto_generate_script=True)
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
        self.assertEqual(resp.created_jobs, [])
        repo.get_script_job.assert_not_called()

    def test_g_existing_script_job_no_duplicate(self):
        repo = _make_check_repo()
        ch = _channel(cid="UC_dup", auto_generate_script=True)
        repo.get_watch_channel.return_value = ch
        vidrow = _vid(vid="v_dup", score=80)
        feed = MagicMock(
            return_value={"channel": ch.channel_name, "videos": [vidrow], "warnings": []}
        )
        repo.get_processed_video.return_value = None
        existing_job = ScriptJob(
            id="v_dup",
            video_id="v_dup",
            channel_id=ch.channel_id,
            video_url=vidrow["url"],
            status="pending",
            created_at="2026-01-01T00:00:00Z",
        )
        repo.get_script_job.return_value = existing_job

        resp = watchlist_service.check_channel(ch.channel_id, repo=repo, get_videos=feed)

        self.assertEqual(resp.created_jobs, [])
        repo.create_script_job.assert_not_called()
        repo.update_processed_video_job_link.assert_called_once_with("v_dup", "v_dup")
        self.assertTrue(any("already exists" in w for w in resp.warnings))

    def test_h_paused_no_feed_call(self):
        repo = _make_check_repo()
        ch = _channel(cid="UC_f", status="paused")
        repo.get_watch_channel.return_value = ch
        feed = MagicMock()

        resp = watchlist_service.check_channel(ch.channel_id, repo=repo, get_videos=feed)

        feed.assert_not_called()
        self.assertEqual(resp.warnings[0], "Watchlist channel is not active.")
        repo.upsert_watch_channel.assert_not_called()

    def test_i_list_script_jobs_delegates(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        job = ScriptJob(
            id="v1",
            video_id="v1",
            channel_id="UC_x",
            video_url="https://www.youtube.com/watch?v=v1",
            status="pending",
            created_at="2026-04-01T00:00:00Z",
        )
        repo.list_script_jobs.return_value = [job]

        out = watchlist_service.list_script_jobs(repo=repo, limit=10)

        self.assertEqual(len(out.jobs), 1)
        self.assertEqual(out.jobs[0].video_id, "v1")
        repo.list_script_jobs.assert_called_once_with(limit=10)

    def test_firestore_propagates(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        repo.get_watch_channel.side_effect = FirestoreUnavailableError("x")

        with self.assertRaises(FirestoreUnavailableError):
            watchlist_service.check_channel("UC_x", repo=repo)


if __name__ == "__main__":
    unittest.main()
