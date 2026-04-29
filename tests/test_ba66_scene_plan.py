"""BA 6.6: Script-to-Scene Planner (Service + Routen-Stubs mit Mocks)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import Chapter
from app.watchlist.models import (
    GeneratedScript,
    ProductionJob,
    ScenePlan,
    ScenePlanGenerateResponse,
    ScenePlanGetResponse,
)
from app.watchlist import service as watchlist_service


def _gs_with_chapters(gid: str = "pj1") -> GeneratedScript:
    return GeneratedScript(
        id=gid,
        script_job_id=gid,
        source_url="u",
        title="Titel",
        hook="Hook",
        chapters=[
            Chapter(title="Kap A", content="Einleitung hier. Und mehr Satzwerk."),
            Chapter(title="Leer", content="   "),
            Chapter(title="Kap B", content=" Zweiter Block mit Inhalt für die Szene. " * 3),
        ],
        full_script="fallback body " * 20,
        sources=[],
        warnings=[],
        word_count=200,
        created_at="2026-04-02T12:00:00Z",
    )


def _pj(pid: str = "pj1") -> ProductionJob:
    return ProductionJob(
        id=pid,
        generated_script_id=pid,
        script_job_id=pid,
        status="queued",
        created_at="2026-04-02T12:00:00Z",
        updated_at="2026-04-02T12:00:00Z",
    )


class Ba66ScenePlanService(unittest.TestCase):
    def test_generate_scene_plan_success(self):
        repo = MagicMock()
        pj = _pj()
        gs = _gs_with_chapters()
        repo.get_scene_plan.return_value = None
        repo.get_production_job.return_value = pj
        repo.get_generated_script.return_value = gs

        out = watchlist_service.generate_scene_plan("pj1", repo=repo)

        self.assertIsNotNone(out.scene_plan)
        assert out.scene_plan is not None
        self.assertEqual(out.scene_plan.production_job_id, "pj1")
        self.assertTrue(len(out.scene_plan.scenes) >= 1)
        self.assertGreater(len(out.scene_plan.source_fingerprint), 8)
        repo.upsert_scene_plan.assert_called_once()
        sp_arg = repo.upsert_scene_plan.call_args[0][0]
        self.assertEqual(sp_arg.status, "ready")

    def test_generate_idempotent_existing(self):
        repo = MagicMock()
        existing = ScenePlan(
            id="pj1",
            production_job_id="pj1",
            generated_script_id="pj1",
            script_job_id="pj1",
            status="ready",
            plan_version=1,
            source_fingerprint="abc",
            scenes=[],
            warnings=[],
            created_at="x",
            updated_at="x",
        )
        repo.get_scene_plan.return_value = existing

        out = watchlist_service.generate_scene_plan("pj1", repo=repo)

        self.assertIs(out.scene_plan, existing)
        self.assertEqual(len(out.warnings), 1)
        self.assertIn("idempotent", out.warnings[0].lower())
        repo.get_production_job.assert_not_called()
        repo.upsert_scene_plan.assert_not_called()

    def test_generate_404_missing_production_job(self):
        repo = MagicMock()
        repo.get_scene_plan.return_value = None
        repo.get_production_job.return_value = None

        out = watchlist_service.generate_scene_plan("missing", repo=repo)

        self.assertIsNone(out.scene_plan)
        self.assertIn("Production job not found", out.warnings[0])

    def test_generate_404_missing_generated_script(self):
        repo = MagicMock()
        repo.get_scene_plan.return_value = None
        repo.get_production_job.return_value = _pj()
        repo.get_generated_script.return_value = None

        out = watchlist_service.generate_scene_plan("pj1", repo=repo)

        self.assertIsNone(out.scene_plan)
        self.assertIn("Generated script not found", out.warnings[0])

    def test_fallback_without_chapters(self):
        repo = MagicMock()
        pj = _pj()
        gs = GeneratedScript(
            id="pj1",
            script_job_id="pj1",
            source_url="u",
            title="x",
            hook="h",
            chapters=[],
            full_script=(
                "Absatz eins hier genug Text.\n\n"
                "Absatz zwei weiterer Inhalt hier.\n\n"
                "Drei und Ende."
            ),
            sources=[],
            warnings=[],
            word_count=50,
            created_at="2026-04-02T12:00:00Z",
        )
        repo.get_scene_plan.return_value = None
        repo.get_production_job.return_value = pj
        repo.get_generated_script.return_value = gs

        out = watchlist_service.generate_scene_plan("pj1", repo=repo)

        assert out.scene_plan is not None
        self.assertGreaterEqual(len(out.scene_plan.scenes), 2)
        warn_joined = " ".join(out.scene_plan.warnings).lower()
        self.assertIn("fallback", warn_joined)

    def test_empty_chapter_warnings(self):
        repo = MagicMock()
        pj = _pj()
        gs = _gs_with_chapters()
        repo.get_scene_plan.return_value = None
        repo.get_production_job.return_value = pj
        repo.get_generated_script.return_value = gs

        out = watchlist_service.generate_scene_plan("pj1", repo=repo)

        assert out.scene_plan is not None
        self.assertTrue(any("leer" in w.lower() for w in out.scene_plan.warnings))

    def test_get_scene_plan_ok(self):
        repo = MagicMock()
        stored = ScenePlan(
            id="pj1",
            production_job_id="pj1",
            generated_script_id="pj1",
            script_job_id="pj1",
            status="ready",
            plan_version=1,
            source_fingerprint="x",
            scenes=[],
            warnings=[],
            created_at="a",
            updated_at="a",
        )
        repo.get_scene_plan.return_value = stored

        out = watchlist_service.get_scene_plan_for_production_job("pj1", repo=repo)

        self.assertIs(out.scene_plan, stored)
        self.assertEqual(out.warnings, [])

    def test_get_scene_plan_404(self):
        repo = MagicMock()
        repo.get_scene_plan.return_value = None

        out = watchlist_service.get_scene_plan_for_production_job("nix", repo=repo)

        self.assertIsNone(out.scene_plan)


class Ba66ProductionRoutes(unittest.TestCase):
    def test_post_generate_returns_404_detail(self):
        client = TestClient(app)
        with patch(
            "app.routes.production.watchlist_service.generate_scene_plan",
            return_value=ScenePlanGenerateResponse(
                scene_plan=None,
                warnings=["Production job not found."],
            ),
        ):
            r = client.post("/production/jobs/xyz/scene-plan/generate")
        self.assertEqual(r.status_code, 404)

    def test_get_scene_plan_returns_404(self):
        client = TestClient(app)
        with patch(
            "app.routes.production.watchlist_service.get_scene_plan_for_production_job",
            return_value=ScenePlanGetResponse(scene_plan=None, warnings=["Scene plan not found."]),
        ):
            r = client.get("/production/jobs/nix/scene-plan")
        self.assertEqual(r.status_code, 404)

    def test_get_scene_plan_200_when_present(self):
        client = TestClient(app)
        plan = ScenePlan(
            id="p",
            production_job_id="p",
            generated_script_id="p",
            script_job_id="p",
            status="ready",
            plan_version=1,
            source_fingerprint="h",
            scenes=[],
            warnings=[],
            created_at="a",
            updated_at="a",
        )
        with patch(
            "app.routes.production.watchlist_service.get_scene_plan_for_production_job",
            return_value=ScenePlanGetResponse(scene_plan=plan),
        ):
            r = client.get("/production/jobs/p/scene-plan")
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
