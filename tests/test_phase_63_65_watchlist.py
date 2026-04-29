"""BA 6.3–6.5: Dashboard-Zähler, Review-Persistenz, Production-Endpoints (Mocks)."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import ReviewScriptResponse
from app.watchlist.firestore_repo import (
    GENERATED_SCRIPTS_COLLECTION,
    FirestoreWatchlistRepository,
    PROCESSED_VIDEOS_COLLECTION,
)
from app.watchlist.models import (
    GeneratedScript,
    ProductionJob,
    ProductionJobActionResponse,
    ScriptJob,
)
from app.watchlist import service as watchlist_service


def _review_resp() -> ReviewScriptResponse:
    from app.models import ReviewIssue, ReviewRecommendation

    return ReviewScriptResponse(
        risk_level="low",
        originality_score=88,
        similarity_flags=[],
        issues=[ReviewIssue(severity="info", code="x", message="m")],
        recommendations=[
            ReviewRecommendation(
                priority="low",
                action="keep",
                rationale="ok",
            )
        ],
        warnings=[],
    )


class Phase63Dashboard(unittest.TestCase):
    def test_dashboard_no_negative_count_warnings_when_repo_ok(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        repo.list_watch_channel_docs.return_value = []
        repo.count_collection.side_effect = lambda c: {
            PROCESSED_VIDEOS_COLLECTION: 2,
            GENERATED_SCRIPTS_COLLECTION: 1,
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
        self.assertEqual(out.counts.generated_scripts_total, 1)
        self.assertEqual(out.counts.processed_videos_total, 2)
        self.assertFalse(
            any("nicht ermittelbar" in w for w in out.health.warnings)
        )

    def test_successful_run_increments_dashboard_script_total_mock(self):
        """Completed Job und generated_script spiegeln sich in Dashboard-Mocks wider."""
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        from app.models import Chapter, GenerateScriptResponse

        job = ScriptJob(
            id="vid_ok",
            video_id="vid_ok",
            channel_id="UC",
            video_url="https://youtu.be/vid_ok",
            status="pending",
            created_at="2026-04-01T12:00:00Z",
            target_language="de",
            duration_minutes=10,
        )
        calls = {"n": 0}

        def get_side(jid):
            calls["n"] += 1
            if calls["n"] >= 3:
                return job.model_copy(
                    update={
                        "status": "completed",
                        "generated_script_id": jid,
                        "completed_at": "2026-04-01T13:00:00Z",
                    }
                )
            return job

        repo.get_script_job.side_effect = get_side
        repo.get_processed_video.return_value = None

        def gen(*_a, **_kw):
            return GenerateScriptResponse(
                title="T",
                hook="H",
                chapters=[Chapter(title="K", content="c")],
                full_script="text " * 40,
                sources=[],
                warnings=[],
            )

        watchlist_service.run_script_job("vid_ok", repo=repo, generate_fn=gen)
        repo.count_collection.side_effect = lambda c: {
            PROCESSED_VIDEOS_COLLECTION: 0,
            GENERATED_SCRIPTS_COLLECTION: 3,
        }.get(c, 0)
        repo.count_processed_videos_by_status.return_value = 0
        repo.count_processed_videos_by_skip_reason.return_value = 0
        repo.count_script_jobs_by_status.side_effect = lambda s: (
            1 if s == "completed" else 0
        )
        repo.get_latest_completed_job_completed_at.return_value = (
            "2026-04-01T13:00:00Z"
        )
        repo.get_last_automation_cycle_at.return_value = None
        repo.list_running_script_jobs.return_value = []

        with patch.object(watchlist_service, "list_channels") as lc:
            lc.return_value = SimpleNamespace(channels=[])
            dash = watchlist_service.get_watchlist_dashboard(repo=repo)
        self.assertEqual(dash.counts.generated_scripts_total, 3)
        self.assertEqual(dash.counts.script_jobs_completed, 1)

    def test_transcript_not_available_stability(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        from app.models import GenerateScriptResponse

        job = ScriptJob(
            id="vid_f",
            video_id="vid_f",
            channel_id="UC",
            video_url="https://youtu.be/vid_f",
            status="pending",
            created_at="2026-04-01T12:00:00Z",
            target_language="de",
            duration_minutes=10,
        )
        failed_job = job.model_copy(
            update={
                "status": "failed",
                "error_code": "transcript_not_available",
                "completed_at": "2026-04-01T12:05:00Z",
            }
        )
        gj_calls = []

        def get_side(jid):
            gj_calls.append(jid)
            if len(gj_calls) == 1:
                return job
            if len(gj_calls) == 2:
                return job.model_copy(
                    update={
                        "status": "running",
                        "started_at": "2026-04-01T12:01:00Z",
                    }
                )
            return failed_job

        repo.get_script_job.side_effect = get_side

        def gen(*_a, **_kw):
            return GenerateScriptResponse(
                title="",
                hook="",
                chapters=[],
                full_script="",
                sources=[],
                warnings=["Transcript not available for this video."],
            )

        out = watchlist_service.run_script_job("vid_f", repo=repo, generate_fn=gen)
        self.assertEqual(out.job.status, "failed")
        self.assertIsNone(out.script)

    def test_pending_runner_not_broken(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        repo.list_pending_script_jobs.return_value = []
        out = watchlist_service.run_pending_script_jobs(3, repo=repo)
        self.assertEqual(out.checked_jobs, 0)


class Phase64ReviewPersistence(unittest.TestCase):
    def test_review_persists_and_links_job(self):
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
        repo.get_processed_video.return_value = None

        with patch.object(
            watchlist_service, "review_script", return_value=_review_resp()
        ):
            out = watchlist_service.review_generated_script_for_job("jid", repo=repo)

        self.assertIsNotNone(out.review)
        repo.create_review_result.assert_called_once()
        repo.set_script_job_review_result_id.assert_called_once()
        rid = repo.set_script_job_review_result_id.call_args[0][1]
        self.assertTrue(rid.startswith("rr_"))

    def test_review_persist_firestore_failure_returns_review_with_warning(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        gj = GeneratedScript(
            id="j3",
            script_job_id="j3",
            source_url="u",
            title="x",
            hook="h",
            chapters=[],
            full_script=("w " * 40),
            sources=[],
            warnings=[],
            word_count=40,
            created_at="2026-01-01T00:00:00Z",
        )
        job = ScriptJob(
            id="j3",
            video_id="j3",
            channel_id="UC",
            video_url="u",
            status="completed",
            created_at="2026-01-01T00:00:00Z",
            target_language="de",
            duration_minutes=10,
            generated_script_id=gj.id,
        )
        repo.get_script_job.return_value = job
        repo.get_generated_script.return_value = gj
        repo.create_review_result.side_effect = RuntimeError("db")
        with patch.object(
            watchlist_service, "review_script", return_value=_review_resp()
        ):
            out = watchlist_service.review_generated_script_for_job("j3", repo=repo)
        self.assertIsNotNone(out.review)
        self.assertTrue(any("gespeichert" in w.lower() for w in out.warnings))
        repo.mark_script_job_failed.assert_not_called()

    def test_no_review_without_generated_script_id(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        job = ScriptJob(
            id="nx",
            video_id="nx",
            channel_id="UC",
            video_url="u",
            status="completed",
            created_at="2026-01-01T00:00:00Z",
            target_language="de",
            duration_minutes=10,
            generated_script_id=None,
        )
        repo.get_script_job.return_value = job
        out = watchlist_service.review_generated_script_for_job("nx", repo=repo)
        self.assertIsNone(out.review)
        self.assertTrue(any("generated_script_id" in w for w in out.warnings))
        repo.create_review_result.assert_not_called()

    def test_no_review_for_pending_job(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        job = ScriptJob(
            id="pe",
            video_id="pe",
            channel_id="UC",
            video_url="u",
            status="pending",
            created_at="2026-01-01T00:00:00Z",
            target_language="de",
            duration_minutes=10,
            generated_script_id="x",
        )
        repo.get_script_job.return_value = job
        out = watchlist_service.review_generated_script_for_job("pe", repo=repo)
        self.assertIsNone(out.review)
        repo.create_review_result.assert_not_called()


class Phase65Production(unittest.TestCase):
    def test_list_and_detail(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        pj = ProductionJob(
            id="gs1",
            generated_script_id="gs1",
            script_job_id="gs1",
            status="queued",
            created_at="2026-01-02T00:00:00Z",
            updated_at="2026-01-02T00:00:00Z",
        )
        repo.list_production_jobs.return_value = [pj]
        repo.get_production_job.return_value = pj
        out = watchlist_service.list_production_jobs(limit=10, repo=repo)
        self.assertEqual(len(out.jobs), 1)
        d = watchlist_service.get_production_job_detail("gs1", repo=repo)
        self.assertEqual(d.job.id, "gs1")

    def test_skip_queued(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        pj = ProductionJob(
            id="g2",
            generated_script_id="g2",
            script_job_id="g2",
            status="queued",
            created_at="2026-01-02T00:00:00Z",
            updated_at="2026-01-02T00:00:00Z",
        )
        sk = ProductionJob(
            id="g2",
            generated_script_id="g2",
            script_job_id="g2",
            status="skipped",
            created_at="2026-01-02T00:00:00Z",
            updated_at="2026-01-03T00:00:00Z",
        )
        repo.get_production_job.side_effect = [pj, sk]
        out = watchlist_service.skip_production_job("g2", repo=repo)
        self.assertEqual(out.job.status, "skipped")
        repo.patch_production_job.assert_called_once()

    def test_retry_skipped(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        pj = ProductionJob(
            id="g3",
            generated_script_id="g3",
            script_job_id="g3",
            status="skipped",
            created_at="2026-01-02T00:00:00Z",
            updated_at="2026-01-02T00:00:00Z",
        )
        rq = ProductionJob(
            id="g3",
            generated_script_id="g3",
            script_job_id="g3",
            status="queued",
            created_at="2026-01-02T00:00:00Z",
            updated_at="2026-01-03T01:00:00Z",
        )
        repo.get_production_job.side_effect = [pj, rq]
        out = watchlist_service.retry_production_job("g3", repo=repo)
        self.assertEqual(out.job.status, "queued")

    def test_skip_blocked_completed(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        pj = ProductionJob(
            id="g4",
            generated_script_id="g4",
            script_job_id="g4",
            status="completed",
            created_at="2026-01-02T00:00:00Z",
            updated_at="2026-01-02T00:00:00Z",
        )
        repo.get_production_job.return_value = pj
        out = watchlist_service.skip_production_job("g4", repo=repo)
        self.assertEqual(out.job.status, "completed")
        repo.patch_production_job.assert_not_called()


class Phase65ProductionRoutes(unittest.TestCase):
    def test_detail_404(self):
        client = TestClient(app)
        with patch(
            "app.routes.production.watchlist_service.get_production_job_detail"
        ) as m:
            m.return_value = ProductionJobActionResponse(
                job=None,
                warnings=["Production job not found."],
            )
            r = client.get("/production/jobs/missing-id")
            self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
