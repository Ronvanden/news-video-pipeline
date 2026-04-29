"""BA 6.6.1 Dev-Fixtures Endpoint (ENABLE_TEST_FIXTURES)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.watchlist.dev_fixture_seed import DevFixtureConflictError, seed_completed_script_job_fixture
from app.watchlist.models import ProductionJob, ScriptJob
from app.watchlist.firestore_repo import FirestoreWatchlistRepository


class DevFixtureRouteTests(unittest.TestCase):
    def test_disabled_returns_403_by_default(self):
        client = TestClient(app)
        with patch("app.routes.dev_fixtures.settings") as s:
            s.enable_test_fixtures = False
            r = client.post("/dev/fixtures/completed-script-job", json={})
        self.assertEqual(r.status_code, 403)

    def test_enabled_seeds_and_returns_200(self):
        client = TestClient(app)
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        repo.get_script_job.return_value = None
        repo.get_generated_script.return_value = None
        repo.get_production_job.return_value = None
        job = ScriptJob(
            id="dev_fixture_x1",
            video_id="dev_fixture_x1",
            channel_id="UC",
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            status="completed",
            created_at="2026-01-01T00:00:00Z",
            target_language="de",
            duration_minutes=10,
            completed_at="2026-01-01T01:00:00Z",
            generated_script_id="dev_fixture_x1",
        )
        pj = ProductionJob(
            id="dev_fixture_x1",
            generated_script_id="dev_fixture_x1",
            script_job_id="dev_fixture_x1",
            status="queued",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        with patch("app.routes.dev_fixtures.seed_completed_script_job_fixture") as seed:
            seed.return_value = (job, MagicMock(), pj, [])
            with patch(
                "app.routes.dev_fixtures.FirestoreWatchlistRepository", return_value=repo
            ):
                with patch("app.routes.dev_fixtures.settings") as s:
                    s.enable_test_fixtures = True
                    r = client.post(
                        "/dev/fixtures/completed-script-job",
                        json={"fixture_id": "unit1", "create_production_job": True},
                    )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["job_id"], "dev_fixture_x1")
        self.assertTrue(data["production_job_created"])

    def test_conflict_409(self):
        client = TestClient(app)
        with patch(
            "app.routes.dev_fixtures.seed_completed_script_job_fixture"
        ) as seed:
            seed.side_effect = DevFixtureConflictError("dev_fixture_dup")
            with patch(
                "app.routes.dev_fixtures.FirestoreWatchlistRepository"
            ):
                with patch("app.routes.dev_fixtures.settings") as s:
                    s.enable_test_fixtures = True
                    r = client.post("/dev/fixtures/completed-script-job")
        self.assertEqual(r.status_code, 409)


class DevFixtureSeedTests(unittest.TestCase):
    def test_seed_raises_on_existing_job(self):
        repo = MagicMock(spec=FirestoreWatchlistRepository)
        repo.get_script_job.return_value = MagicMock()

        def _raise():
            seed_completed_script_job_fixture(
                fixture_job_id_raw="abc",
                create_production_job=False,
                repo=repo,
            )

        self.assertRaises(DevFixtureConflictError, _raise)


if __name__ == "__main__":
    unittest.main()
