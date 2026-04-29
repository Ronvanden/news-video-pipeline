"""BA 5.8–6.2: Control Tower (Dashboard, Errors, Queue-Governance, Production-Stubs)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.watchlist.firestore_repo import (
    GENERATED_SCRIPTS_COLLECTION,
    PROCESSED_VIDEOS_COLLECTION,
    FirestoreWatchlistRepository,
)
from app.watchlist.models import (
    GeneratedScript,
    ProductionJob,
    ScriptJob,
    WatchlistChannel,
)
from app.watchlist import service as watchlist_service


def _ch(cid: str = "UC1", status: str = "active") -> WatchlistChannel:
    return WatchlistChannel(
        id=cid,
        channel_url=f"https://www.youtube.com/channel/{cid}",
        channel_id=cid,
        channel_name="N",
        status=status,  # type: ignore[arg-type]
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


class Phase58PendingQuery(unittest.TestCase):
    def test_pending_query_chain_limit(self):
        mock_client = MagicMock()
        q_final = MagicMock()
        q_ob = MagicMock()
        q_wh = MagicMock()
        col = MagicMock()
        mock_client.collection.return_value = col
        col.where.return_value = q_wh
        q_wh.order_by.return_value = q_ob
        q_ob.limit.return_value = q_final
        q_final.stream.return_value = iter([])

        repo = FirestoreWatchlistRepository(client=mock_client)
        repo.list_pending_script_jobs(7)

        col.where.assert_called_once_with("status", "==", "pending")
        q_wh.order_by.assert_called_once_with("created_at")
        q_ob.limit.assert_called_once_with(7)

    def test_script_job_attempt_defaults_compatible(self):
        d = {
            "id": "v1",
            "video_id": "v1",
            "channel_id": "UC",
            "video_url": "https://youtu.be/v1",
            "status": "pending",
            "created_at": "2026-01-01T00:00:00Z",
        }
        job = ScriptJob.model_validate(d)
        self.assertEqual(job.attempt_count, 0)
        self.assertIsNone(job.last_attempt_at)


class Phase59Dashboard(unittest.TestCase):
    def test_dashboard_empty(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        repo.list_watch_channel_docs.return_value = []
        repo.count_collection.side_effect = lambda c: {
            PROCESSED_VIDEOS_COLLECTION: 0,
            GENERATED_SCRIPTS_COLLECTION: 0,
        }.get(c, 0)
        repo.count_processed_videos_by_status.return_value = 0
        repo.count_processed_videos_by_skip_reason.return_value = 0
        repo.count_script_jobs_by_status.return_value = 0
        repo.get_latest_completed_job_completed_at.return_value = None
        repo.get_last_automation_cycle_at.return_value = None
        repo.list_running_script_jobs.return_value = []

        with patch.object(watchlist_service, "list_channels") as lc:
            lc.return_value = SimpleNamespace(channels=[])
            out = watchlist_service.get_watchlist_dashboard(repo=repo)
        self.assertEqual(out.counts.channels_active, 0)
        self.assertEqual(out.counts.generated_scripts_total, 0)

    def test_dashboard_with_data(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        repo.list_watch_channel_docs.return_value = []

        def _count_col(name: str) -> int:
            if name == PROCESSED_VIDEOS_COLLECTION:
                return 10
            if name == GENERATED_SCRIPTS_COLLECTION:
                return 4
            return 0

        repo.count_collection.side_effect = _count_col
        repo.count_processed_videos_by_status.return_value = 1
        repo.count_processed_videos_by_skip_reason.return_value = 1

        def _sj_status(_st: str) -> int:
            return {"pending": 3, "running": 0, "completed": 5, "failed": 1}.get(
                _st, 0
            )

        repo.count_script_jobs_by_status.side_effect = lambda s: _sj_status(s)
        repo.get_latest_completed_job_completed_at.return_value = (
            "2026-04-01T00:00:00Z"
        )
        repo.get_last_automation_cycle_at.return_value = "2026-04-02T00:00:00Z"
        repo.list_running_script_jobs.return_value = []

        chs = [_ch("UCa", "active"), _ch("UCp", "paused"), _ch("UCe", "error")]
        with patch.object(watchlist_service, "list_channels") as lc:
            lc.return_value = SimpleNamespace(channels=chs)
            out = watchlist_service.get_watchlist_dashboard(repo=repo)
        self.assertEqual(out.counts.channels_active, 1)
        self.assertEqual(out.counts.channels_paused, 1)
        self.assertEqual(out.counts.channels_error, 1)
        self.assertEqual(out.counts.script_jobs_pending, 3)
        self.assertEqual(
            out.health.last_successful_job_at, "2026-04-01T00:00:00Z"
        )


class Phase60Errors(unittest.TestCase):
    def test_error_summary_codes_and_skips(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        repo.stream_script_jobs_for_error_summary.return_value = (
            [
                ScriptJob(
                    id="j1",
                    video_id="j1",
                    channel_id="UC",
                    video_url="u",
                    status="failed",
                    created_at="2026-01-01T00:00:00Z",
                    error_code="transcript_not_available",
                ),
                ScriptJob(
                    id="j2",
                    video_id="j2",
                    channel_id="UC",
                    video_url="u",
                    status="failed",
                    created_at="2026-01-01T01:00:00Z",
                    error_code="transcript_not_available",
                ),
            ],
            False,
        )
        from app.watchlist.models import ProcessedVideo as PV

        repo.stream_processed_videos_skipped_for_summary.return_value = (
            [
                PV(
                    id="v9",
                    channel_id="UC",
                    video_id="v9",
                    video_url="u",
                    title="t",
                    published_at="p",
                    first_seen_at="f",
                    status="skipped",
                    skip_reason="transcript_not_available",
                ),
            ],
            False,
        )
        out = watchlist_service.get_watchlist_errors_summary(repo=repo)
        codes = {x.error_code: x.count for x in out.by_error_code}
        self.assertEqual(codes.get("transcript_not_available"), 2)
        skips = {x.skip_reason: x.count for x in out.by_skip_reason}
        self.assertEqual(
            skips.get("transcript_not_available")
            or skips.get("(empty_skip_reason)"),
            1,
        )


class Phase61Governance(unittest.TestCase):
    def test_retry_failed(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        failed = ScriptJob(
            id="jx",
            video_id="jx",
            channel_id="UC",
            video_url="u",
            status="failed",
            created_at="2026-01-01T00:00:00Z",
            error="x",
            error_code="e",
        )
        pending = failed.model_copy(
            update={"status": "pending", "error": "", "error_code": ""}
        )
        repo.get_script_job.side_effect = [failed, pending]
        out = watchlist_service.retry_script_job("jx", repo=repo)
        repo.reset_script_job_to_pending.assert_called_once_with("jx")
        self.assertEqual(out.job.status, "pending")

    def test_skip_pending(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        job = ScriptJob(
            id="jy",
            video_id="jy",
            channel_id="UC",
            video_url="u",
            status="pending",
            created_at="2026-01-01T00:00:00Z",
        )
        skipped = job.model_copy(update={"status": "skipped"})
        repo.get_script_job.side_effect = [job, skipped]
        out = watchlist_service.skip_script_job_manually("jy", repo=repo)
        self.assertEqual(out.job.status, "skipped")

    def test_pause_resume(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        pa = _ch("UCz", "active")
        repo.get_watch_channel.return_value = pa
        pout = watchlist_service.pause_watchlist_channel("UCz", repo=repo)
        self.assertEqual(pout.channel.status, "paused")
        repo.patch_watch_channel_fields.assert_called_once()
        repo.get_watch_channel.return_value = pout.channel
        rout = watchlist_service.resume_watchlist_channel("UCz", repo=repo)
        self.assertEqual(rout.channel.status, "active")


class Phase62Production(unittest.TestCase):
    def test_create_production_completed(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        job = ScriptJob(
            id="done",
            video_id="done",
            channel_id="UC",
            video_url="u",
            status="completed",
            created_at="2026-01-01T00:00:00Z",
            generated_script_id="done",
        )
        repo.get_script_job.return_value = job
        repo.get_production_job.return_value = None
        out = watchlist_service.create_production_job_from_script_job(
            "done", None, repo=repo
        )
        self.assertTrue(out.created)
        self.assertIsNotNone(out.job)
        repo.create_production_job.assert_called_once()

    def test_no_duplicate_production(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        job = ScriptJob(
            id="done",
            video_id="done",
            channel_id="UC",
            video_url="u",
            status="completed",
            created_at="2026-01-01T00:00:00Z",
            generated_script_id="done",
        )
        existing = ProductionJob(
            id="done",
            generated_script_id="done",
            script_job_id="done",
            created_at="t",
            updated_at="t",
        )
        repo.get_script_job.return_value = job
        repo.get_production_job.return_value = existing
        out = watchlist_service.create_production_job_from_script_job(
            "done", None, repo=repo
        )
        self.assertFalse(out.created)
        repo.create_production_job.assert_not_called()

    def test_block_not_completed(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        job = ScriptJob(
            id="p1",
            video_id="p1",
            channel_id="UC",
            video_url="u",
            status="pending",
            created_at="2026-01-01T00:00:00Z",
        )
        repo.get_script_job.return_value = job
        out = watchlist_service.create_production_job_from_script_job(
            "p1", None, repo=repo
        )
        self.assertIsNone(out.job)
        self.assertFalse(out.created)
