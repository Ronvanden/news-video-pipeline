"""Tests für ``run_script_job`` und POST ``/watchlist/jobs/{job_id}/run`` (Mocks, keine Cloud-Calls)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import Chapter, GenerateScriptResponse
from app.utils import (
    check_youtube_transcript_available_by_video_id,
    generate_script_from_youtube_video,
)
from app.watchlist.firestore_repo import FirestoreUnavailableError, FirestoreWatchlistRepository
from app.watchlist.models import GeneratedScript, ProcessedVideo, ScriptJob
from app.watchlist import service as watchlist_service


def _pending_job(**kwargs) -> ScriptJob:
    base = dict(
        id="vid_run",
        video_id="vid_run",
        channel_id="UC_t",
        video_url="https://www.youtube.com/watch?v=vid_run",
        status="pending",
        created_at="2026-04-01T12:00:00Z",
        started_at=None,
        completed_at=None,
        error="",
        generated_script_id=None,
        review_result_id=None,
        target_language="de",
        duration_minutes=10,
    )
    base.update(kwargs)
    return ScriptJob(**base)


class TestRunScriptJobService(unittest.TestCase):
    def test_a_job_not_found(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        repo.get_script_job.return_value = None

        with self.assertRaises(watchlist_service.ScriptJobNotFoundError):
            watchlist_service.run_script_job("unknown", repo=repo)

    def test_b_success_persists_script_and_updates_processed(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        job = _pending_job()
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
        repo.get_processed_video.return_value = ProcessedVideo(
            id="vid_run",
            channel_id="UC_t",
            video_id="vid_run",
            video_url=job.video_url,
            title="T",
            published_at="2026-04-01T10:00:00Z",
            first_seen_at="2026-04-01T11:00:00Z",
            status="seen",
            script_job_id="vid_run",
        )

        def gen(*_a, **_kw):
            return GenerateScriptResponse(
                title="Titel",
                hook="H",
                chapters=[Chapter(title="K1", content="C")],
                full_script="word " * 50,
                sources=["https://www.youtube.com/watch?v=vid_run"],
                warnings=["w1"],
            )

        out = watchlist_service.run_script_job("vid_run", repo=repo, generate_fn=gen)

        repo.mark_script_job_running.assert_called_once_with("vid_run")
        repo.create_generated_script.assert_called_once()
        gs_arg = repo.create_generated_script.call_args[0][0]
        self.assertIsInstance(gs_arg, GeneratedScript)
        self.assertEqual(gs_arg.id, "vid_run")
        self.assertGreater(gs_arg.word_count, 0)
        repo.mark_script_job_completed.assert_called_once_with("vid_run", "vid_run")
        repo.update_processed_video_status.assert_called_once()
        u_call = repo.update_processed_video_status.call_args
        self.assertEqual(u_call[0][1], "script_generated")
        self.assertEqual(out.job.generated_script_id, "vid_run")
        self.assertEqual(out.script.word_count, gs_arg.word_count)
        self.assertIsNotNone(out.script)

    def test_c_empty_script_marks_failed(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        job = _pending_job()
        repo.get_script_job.return_value = job

        def gen(*_a, **_kw):
            return GenerateScriptResponse(
                title="",
                hook="",
                chapters=[],
                full_script="",
                sources=[],
                warnings=["Transcript not available for this video."],
            )

        out = watchlist_service.run_script_job("vid_run", repo=repo, generate_fn=gen)

        repo.mark_script_job_failed.assert_called_once()
        fail_args = repo.mark_script_job_failed.call_args
        self.assertEqual(fail_args[0][1], "transcript_not_available")
        self.assertEqual(
            fail_args.kwargs.get("error_code"), "transcript_not_available"
        )
        repo.create_generated_script.assert_not_called()
        self.assertIsNone(out.script)
        self.assertTrue(any("Transcript" in w for w in out.warnings))

    def test_c2_empty_script_generation_empty_code(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        job = _pending_job()
        repo.get_script_job.return_value = job

        def gen(*_a, **_kw):
            return GenerateScriptResponse(
                title="",
                hook="",
                chapters=[],
                full_script="",
                sources=[],
                warnings=["Target word count: 1400, Actual word count: 0"],
            )

        watchlist_service.run_script_job("vid_run", repo=repo, generate_fn=gen)

        repo.mark_script_job_failed.assert_called_once()
        self.assertEqual(
            repo.mark_script_job_failed.call_args[0][1], "script_generation_empty"
        )

    def test_d_completed_idempotent(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        stored = GeneratedScript(
            id="vid_run",
            script_job_id="vid_run",
            source_url="https://youtu.be/vid_run",
            title="X",
            hook="",
            chapters=[],
            full_script="short",
            sources=[],
            warnings=[],
            word_count=1,
            created_at="2026-01-01T00:00:00Z",
        )
        job = _pending_job(status="completed", generated_script_id="vid_run")
        repo.get_script_job.return_value = job
        repo.get_generated_script.return_value = stored

        out = watchlist_service.run_script_job("vid_run", repo=repo)

        repo.mark_script_job_running.assert_not_called()
        self.assertIn("already completed", out.warnings[0].lower())
        self.assertEqual(out.script, stored)

    def test_e_running_conflict(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        repo.get_script_job.return_value = _pending_job(status="running")

        with self.assertRaises(watchlist_service.ScriptJobConflictError):
            watchlist_service.run_script_job("vid_run", repo=repo)

    def test_f_create_script_firestore_fails(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        job = _pending_job()
        repo.get_script_job.return_value = job

        def gen(*_a, **_kw):
            return GenerateScriptResponse(
                title="T",
                hook="h",
                chapters=[],
                full_script="alpha beta gamma delta " * 20,
                sources=[],
                warnings=[],
            )

        repo.create_generated_script.side_effect = FirestoreUnavailableError("x")

        with self.assertRaises(FirestoreUnavailableError):
            watchlist_service.run_script_job("vid_run", repo=repo, generate_fn=gen)

        repo.mark_script_job_failed.assert_called()
        self.assertEqual(
            repo.mark_script_job_failed.call_args[0][1],
            watchlist_service.JOB_ERR_FIRESTORE_WRITE,
        )


class TestRunScriptJobRoute(unittest.TestCase):
    def test_route_404(self):
        with patch(
            "app.routes.watchlist.watchlist_service.run_script_job",
            side_effect=watchlist_service.ScriptJobNotFoundError(),
        ):
            c = TestClient(app)
            r = c.post("/watchlist/jobs/nope/run")
            self.assertEqual(r.status_code, 404)

    def test_route_409(self):
        with patch(
            "app.routes.watchlist.watchlist_service.run_script_job",
            side_effect=watchlist_service.ScriptJobConflictError("Script job is already running."),
        ):
            c = TestClient(app)
            r = c.post("/watchlist/jobs/x/run")
            self.assertEqual(r.status_code, 409)


class TestTranscriptPreflightUtils(unittest.TestCase):
    @patch("app.utils.fetch_youtube_transcript_by_video_id", return_value="hello transcript text")
    def test_preflight_ok(self, _m):
        ok, w = check_youtube_transcript_available_by_video_id("dQw4w9WgXcQ")
        self.assertTrue(ok)
        self.assertEqual(w, [])

    @patch("app.utils.fetch_youtube_transcript_by_video_id", return_value="   ")
    def test_preflight_empty_returns_warning(self, _m):
        ok, w = check_youtube_transcript_available_by_video_id("dQw4w9WgXcQ")
        self.assertFalse(ok)
        self.assertTrue(any("Transcript not available" in x for x in w))

    @patch(
        "app.utils.fetch_youtube_transcript_by_video_id",
        side_effect=RuntimeError("network"),
    )
    def test_preflight_exception_technical_warning(self, _m):
        ok, w = check_youtube_transcript_available_by_video_id("dQw4w9WgXcQ")
        self.assertFalse(ok)
        self.assertTrue(any("could not be verified" in x.lower() for x in w))


class TestYoutubeGenerateScriptUsesSharedFn(unittest.TestCase):
    @patch("app.utils.fetch_youtube_transcript_by_video_id", return_value="")
    def test_g_contract_keys_stable(self, _mock_tr):
        r = generate_script_from_youtube_video(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            target_language="de",
            duration_minutes=10,
        )
        self.assertIsInstance(r, GenerateScriptResponse)
        keys = set(r.model_dump().keys())
        self.assertEqual(
            keys,
            {"title", "hook", "chapters", "full_script", "sources", "warnings"},
        )


if __name__ == "__main__":
    unittest.main()
