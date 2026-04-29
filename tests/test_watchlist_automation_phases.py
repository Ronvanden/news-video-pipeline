"""Watchlist Ops 5.5–5.7: Recheck, Pending-Runner, Automation-Zyklus, Review-Anbindung (Mocks)."""

from __future__ import annotations

import unittest
from typing import Any, Dict
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import ReviewRecommendation, ReviewScriptResponse, SimilarityFlag
from app.watchlist.firestore_repo import FirestoreWatchlistRepository
from app.watchlist.models import (
    CheckWatchlistChannelResponse,
    GeneratedScript,
    ListWatchlistChannelsResponse,
    PendingJobRunResultItem,
    ProcessedVideo,
    RunAutomationCycleResponse,
    RunPendingScriptJobsResponse,
    ScriptJob,
    WatchlistChannel,
)
from app.watchlist import service as watchlist_service


def _active_channel(cid: str = "UC_cycle") -> WatchlistChannel:
    return WatchlistChannel(
        id=cid,
        channel_url=f"https://www.youtube.com/channel/{cid}",
        channel_id=cid,
        channel_name="Chan",
        status="active",
        check_interval="manual",
        max_results=10,
        auto_generate_script=False,
        auto_review_script=True,
        target_language="de",
        duration_minutes=10,
        min_score=40,
        ignore_shorts=True,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )


def _feed_row(vid: str) -> Dict[str, Any]:
    return {
        "title": "Enough words in title example here",
        "url": f"https://www.youtube.com/watch?v={vid}",
        "video_id": vid,
        "published_at": "2026-04-01T12:00:00Z",
        "score": 50,
        "reason": "r",
        "duration_seconds": 600,
        "media_keywords": "",
    }


def _empty_review_resp() -> ReviewScriptResponse:
    return ReviewScriptResponse(
        risk_level="low",
        originality_score=80,
        similarity_flags=[
            SimilarityFlag(
                flag_type="stub",
                severity="info",
                detail="stub",
                evidence_hint=None,
            )
        ],
        issues=[],
        recommendations=[
            ReviewRecommendation(priority="low", action="a", rationale="r")
        ],
        warnings=[],
    )


class Phase55Recheck(unittest.TestCase):
    def test_recheck_single_video_deletes_processed_and_runs(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        repo.get_script_job.return_value = None
        ch = _active_channel(cid="UC_re").model_copy(
            update={"auto_generate_script": False, "ignore_shorts": False}
        )
        repo.get_watch_channel.return_value = ch
        pv = ProcessedVideo(
            id="v_1",
            channel_id="UC_re",
            video_id="v_1",
            video_url="https://www.youtube.com/watch?v=v_1",
            title="T",
            published_at="2026-04-01T10:00:00Z",
            first_seen_at="2026-04-01T11:00:00Z",
            status="seen",
            score=50,
            reason="r",
            is_short=False,
        )
        repo.get_processed_video.side_effect = [pv, None]
        repo.delete_processed_video.return_value = True

        def feed_side(_url: str, mx: int) -> Dict[str, Any]:
            return {"channel": "", "videos": [_feed_row("v_1")], "warnings": []}

        chk = MagicMock(return_value=(True, []))

        out = watchlist_service.recheck_video(
            "UC_re",
            "v_1",
            repo=repo,
            get_videos=feed_side,
            transcript_checker=chk,
        )

        self.assertTrue(any("processed_videos" in w.lower() for w in out.warnings))
        self.assertTrue(
            any(
                ("ein video" in w.lower() or "ein Video" in w)
                for w in out.warnings
            )
        )
        self.assertGreaterEqual(len(out.new_videos), 1)
        repo.delete_processed_video.assert_called_once_with("v_1")
        repo.upsert_watch_channel.assert_called()


class Phase55RunPending(unittest.TestCase):
    def test_no_pending_jobs(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        repo.list_pending_script_jobs.return_value = []

        out = watchlist_service.run_pending_script_jobs(3, repo=repo)

        self.assertEqual(out.checked_jobs, 0)
        self.assertIn("No pending script jobs.", out.warnings)

    def test_success(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)

        pj = ScriptJob(
            id="a",
            video_id="a",
            channel_id="UC",
            video_url="https://youtu.be/a",
            status="pending",
            created_at="2026-01-01T00:00:00Z",
            target_language="de",
            duration_minutes=10,
        )

        repo.list_pending_script_jobs.return_value = [pj]

        with patch.object(
            watchlist_service,
            "run_script_job",
            return_value=SimpleNamespace(
                job=SimpleNamespace(status="completed"), warnings=[], script=None
            ),
        ) as mrf:
            out = watchlist_service.run_pending_script_jobs(10, repo=repo)

            mrf.assert_called_once()
            self.assertEqual(out.checked_jobs, 1)
            self.assertEqual(out.completed_jobs, 1)
            self.assertEqual(out.results[0].outcome, "completed")

    def test_partial_error_continues(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)

        jobs = [
            ScriptJob(
                id="job_ok",
                video_id="job_ok",
                channel_id="UC",
                video_url="https://youtu.be/job_ok",
                status="pending",
                created_at="2026-01-01T00:01:00Z",
                target_language="de",
                duration_minutes=10,
            ),
            ScriptJob(
                id="job_skip",
                video_id="job_skip",
                channel_id="UC",
                video_url="https://youtu.be/job_skip",
                status="pending",
                created_at="2026-01-01T00:02:00Z",
                target_language="de",
                duration_minutes=10,
            ),
        ]
        repo.list_pending_script_jobs.return_value = jobs

        def rf(jid: str, **_kw):
            if jid == "job_skip":
                raise watchlist_service.ScriptJobConflictError("busy")
            return SimpleNamespace(job=SimpleNamespace(status="completed"), warnings=[])

        with patch.object(watchlist_service, "run_script_job", side_effect=rf):
            out = watchlist_service.run_pending_script_jobs(10, repo=repo)

        self.assertEqual(out.checked_jobs, 2)
        self.assertEqual(out.completed_jobs, 1)
        self.assertEqual(out.skipped_jobs, 1)

    def test_respects_limit(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        jobs = []
        for i in range(20):
            jobs.append(
                ScriptJob(
                    id=f"id{i}",
                    video_id=f"id{i}",
                    channel_id="UC",
                    video_url=f"https://youtu.be/id{i}",
                    status="pending",
                    created_at="2026-01-01T00:02:50Z",
                    target_language="de",
                    duration_minutes=10,
                ),
            )

        repo.list_pending_script_jobs.side_effect = lambda lim: jobs[:lim]

        with patch.object(watchlist_service, "run_script_job") as mrf:
            mrf.return_value = SimpleNamespace(
                job=SimpleNamespace(status="completed"), warnings=[]
            )
            out = watchlist_service.run_pending_script_jobs(7, repo=repo)

        repo.list_pending_script_jobs.assert_called_with(7)
        self.assertEqual(out.checked_jobs, 7)

    def test_route_run_pending_limit_bounds(self):
        c = TestClient(app)
        r = c.post("/watchlist/jobs/run-pending?limit=11")
        self.assertEqual(r.status_code, 422)


class Phase56Automation(unittest.TestCase):
    def test_cycle_no_active_channels(self):
        paused = _active_channel(cid="UC_p").model_copy(update={"status": "paused"})

        fake_batch = RunPendingScriptJobsResponse(
            checked_jobs=0,
            completed_jobs=0,
            failed_jobs=0,
            skipped_jobs=0,
            results=[],
            warnings=["No pending script jobs."],
        )

        repo = MagicMock(spec=FirestoreWatchlistRepository)

        with patch.object(watchlist_service, "check_channel") as pch:
            with patch.object(
                watchlist_service,
                "list_channels",
                return_value=ListWatchlistChannelsResponse(
                    channels=[paused], warnings=[]
                ),
            ):
                with patch.object(
                    watchlist_service,
                    "run_pending_script_jobs",
                    return_value=fake_batch,
                ) as prun:
                    watchlist_service.run_automation_cycle(repo=repo)

            pch.assert_not_called()

            prun.assert_called_once_with(3, repo=repo, generate_fn=None)

    def test_cycle_with_active_channel_batches_jobs(self):
        c1 = _active_channel(cid="UC_first")
        ch_list = ListWatchlistChannelsResponse(channels=[c1], warnings=[])

        check_resp = CheckWatchlistChannelResponse(channel_id=c1.channel_id, warnings=[])

        jb = RunPendingScriptJobsResponse(
            checked_jobs=1,
            completed_jobs=1,
            failed_jobs=0,
            skipped_jobs=0,
            results=[
                PendingJobRunResultItem(job_id="jid", outcome="completed", warnings=[])
            ],
            warnings=[],
        )

        repo = MagicMock(spec=FirestoreWatchlistRepository)

        with patch.object(watchlist_service, "list_channels", return_value=ch_list):
            with patch.object(
                watchlist_service, "check_channel", return_value=check_resp
            ) as pch:
                with patch.object(
                    watchlist_service, "run_pending_script_jobs", return_value=jb
                ) as prun:
                    out = watchlist_service.run_automation_cycle(
                        repo=repo,
                        channel_limit=3,
                        job_limit=5,
                    )

        pch.assert_called_once_with(
            c1.channel_id,
            repo=repo,
            get_videos=None,
            transcript_checker=None,
        )
        prun.assert_called_once_with(5, repo=repo, generate_fn=None)
        self.assertEqual(out.checked_channels, 1)
        self.assertEqual(out.run_jobs, 1)

    def test_cycle_respects_limits(self):
        active = [_active_channel(cid=f"UC{i}") for i in range(5)]

        def check_side(cid: str, **_kw) -> CheckWatchlistChannelResponse:
            return CheckWatchlistChannelResponse(channel_id=cid, warnings=[])

        with patch.object(
            watchlist_service,
            "list_channels",
            return_value=ListWatchlistChannelsResponse(channels=active, warnings=[]),
        ):
            with patch.object(watchlist_service, "check_channel", side_effect=check_side) as pch:
                with patch.object(
                    watchlist_service,
                    "run_pending_script_jobs",
                    return_value=RunPendingScriptJobsResponse(),
                ):
                    watchlist_service.run_automation_cycle(channel_limit=2)

        self.assertEqual(pch.call_count, 2)

    def test_cycle_channel_failure_does_not_abort(self):
        a1 = _active_channel(cid="UC_a")
        a2 = _active_channel(cid="UC_b")

        def chk_side(cid: str, **_kw):
            if cid == "UC_a":
                raise RuntimeError("simulated failure")
            return CheckWatchlistChannelResponse(channel_id=cid)

        repo = MagicMock(spec=FirestoreWatchlistRepository)

        with patch.object(
            watchlist_service,
            "list_channels",
            return_value=ListWatchlistChannelsResponse(channels=[a1, a2], warnings=[]),
        ):
            with patch.object(watchlist_service, "check_channel", side_effect=chk_side):
                with patch.object(
                    watchlist_service,
                    "run_pending_script_jobs",
                    return_value=RunPendingScriptJobsResponse(),
                ):
                    out = watchlist_service.run_automation_cycle(
                        repo=repo,
                        channel_limit=10,
                    )

        self.assertEqual(len(out.channel_results), 2)
        self.assertFalse(out.channel_results[0].ok)

    def test_route_run_cycle_accepts_defaults(self):
        c = TestClient(app)
        with patch(
            "app.routes.watchlist.watchlist_service.run_automation_cycle",
            return_value=RunAutomationCycleResponse(),
        ) as m:
            r = c.post("/watchlist/automation/run-cycle", json={})
            self.assertEqual(r.status_code, 200)
            kw = m.call_args.kwargs
            self.assertEqual(kw["channel_limit"], 3)
            self.assertEqual(kw["job_limit"], 3)


class Phase57Review(unittest.TestCase):
    def test_review_for_saved_script_returns_response(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)

        gj = GeneratedScript(
            id="jid",
            script_job_id="jid",
            source_url="https://youtu.be/jid",
            title="x",
            hook="h",
            chapters=[],
            full_script=("word " * 40),
            sources=[],
            warnings=["prior"],
            word_count=40,
            created_at="2026-01-01T00:00:00Z",
        )

        job = ScriptJob(
            id="jid",
            video_id="jid",
            channel_id="UC",
            video_url=gj.source_url,
            status="completed",
            created_at="2026-01-01T00:00:00Z",
            target_language="de",
            duration_minutes=10,
            generated_script_id=gj.id,
        )

        repo.get_script_job.return_value = job
        repo.get_generated_script.return_value = gj

        with patch.object(
            watchlist_service, "review_script", return_value=_empty_review_resp()
        ):
            out = watchlist_service.review_generated_script_for_job("jid", repo=repo)

        self.assertIsNotNone(out.review)
        self.assertEqual(out.review.originality_score, 80)

    def test_review_exception_does_not_mark_job_failed(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)

        gj = GeneratedScript(
            id="jid2",
            script_job_id="jid2",
            source_url="https://youtu.be/jid2",
            title="x",
            hook="h",
            chapters=[],
            full_script=("word " * 40),
            sources=[],
            warnings=[],
            word_count=40,
            created_at="2026-01-01T00:00:00Z",
        )

        job = ScriptJob(
            id="jid2",
            video_id="jid2",
            channel_id="UC",
            video_url=gj.source_url,
            status="completed",
            created_at="2026-01-01T00:00:00Z",
            target_language="de",
            duration_minutes=10,
            generated_script_id=gj.id,
        )

        repo.get_script_job.return_value = job
        repo.get_generated_script.return_value = gj

        with patch.object(watchlist_service, "review_script", side_effect=RuntimeError):
            out = watchlist_service.review_generated_script_for_job("jid2", repo=repo)

        self.assertIsNone(out.review)
        self.assertTrue(
            any("unverändert" in w.lower() or "unerwartet" in w.lower() for w in out.warnings)
            or len(out.warnings) > 0
        )
        repo.mark_script_job_failed.assert_not_called()


if __name__ == "__main__":
    unittest.main()
