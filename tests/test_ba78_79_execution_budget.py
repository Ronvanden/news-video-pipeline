"""BA 7.8–7.9: Execution Queue und Budget-Schätzung (Mocks, keine Firestore-Verbindung)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.watchlist import service as watchlist_service
from app.watchlist.cost_calculator import EUR_PER_IMAGE, EUR_PER_VIDEO_CLIP
from app.watchlist.execution_queue import execution_job_document_id_from_production_file
from app.watchlist.models import (
    GeneratedScript,
    ProductionCostsGetResponse,
    ProductionFileRecord,
    ProductionJob,
)

client = TestClient(app)


def _pj(pid: str = "pj1") -> ProductionJob:
    return ProductionJob(
        id=pid,
        generated_script_id=pid,
        script_job_id="sj1",
        status="queued",
        created_at="2026-04-02T12:00:00Z",
        updated_at="2026-04-02T12:00:00Z",
    )


def _pfile_thumbnail(pid: str) -> ProductionFileRecord:
    now = "2026-04-03T08:00:00Z"
    return ProductionFileRecord(
        id=f"pfile_{pid}_thumbnail_0000",
        production_job_id=pid,
        file_type="thumbnail",
        storage_path=f"thumbnails/{pid}/thumbnail.png",
        provider_name="generic",
        scene_number=0,
        status="planned",
        created_at=now,
        updated_at=now,
    )


class Ba78ExecutionQueue(unittest.TestCase):
    def test_execution_doc_id_stable(self):
        rec = ProductionFileRecord(
            id="pfile_dev_fixture_demo1_image_0001",
            production_job_id="dev_fixture_demo1",
            file_type="image",
            storage_path="/x",
            scene_number=1,
            created_at="a",
            updated_at="b",
        )
        self.assertEqual(
            execution_job_document_id_from_production_file(rec),
            "exjob_dev_fixture_demo1_image_0001",
        )

    def test_init_requires_production_job(self):
        repo = MagicMock()
        repo.get_production_job.return_value = None
        out = watchlist_service.init_execution_queue_service("missing", repo=repo)
        self.assertTrue(any("not found" in w for w in out.warnings))

    def test_init_idempotent_writes(self):
        repo = MagicMock()
        pj = _pj("z99")
        repo.get_production_job.return_value = pj
        gs = GeneratedScript(
            id="z99",
            script_job_id="sj",
            source_url="u",
            title="t",
            hook="h",
            chapters=[],
            full_script="wort " * 200,
            warnings=[],
            word_count=200,
            created_at="x",
        )
        repo.get_generated_script.return_value = gs

        spa = MagicMock()
        spa.scenes = [MagicMock(), MagicMock()]
        repo.get_scene_assets.return_value = spa
        vp = MagicMock()
        vp.blocks = []
        repo.get_voice_plan.return_value = vp

        f1 = _pfile_thumbnail("z99")
        repo.list_production_files_for_job.return_value = [f1]

        store: dict = {}

        def ups(job):
            store[job.id] = job

        def gj(doc_id: str):
            return store.get(doc_id)

        repo.upsert_execution_job.side_effect = ups
        repo.get_execution_job.side_effect = gj

        out = watchlist_service.init_execution_queue_service("z99", repo=repo)
        self.assertEqual(out.created_new, 1)

        out2 = watchlist_service.init_execution_queue_service("z99", repo=repo)
        self.assertEqual(out2.created_new, 0)
        self.assertGreaterEqual(out2.reused_existing, 1)


class Ba79Costs(unittest.TestCase):
    def test_calculate_formula(self):
        repo = MagicMock()
        pj = _pj("cost1")
        repo.get_production_job.return_value = pj
        repo.get_production_costs.return_value = None
        gs = GeneratedScript(
            id="cost1",
            script_job_id="s",
            source_url="u",
            title="x",
            hook="y",
            chapters=[],
            full_script="a " * 2000,
            warnings=[],
            word_count=2000,
            created_at="c",
        )
        repo.get_generated_script.return_value = gs

        spa = MagicMock()
        spa.scenes = [MagicMock(), MagicMock()]
        repo.get_scene_assets.return_value = spa

        out = watchlist_service.calculate_production_costs_service("cost1", repo=repo)
        self.assertIsNotNone(out.costs)
        c = out.costs
        assert c is not None
        scenes = len(spa.scenes)
        self.assertAlmostEqual(c.video_cost_estimate, scenes * EUR_PER_VIDEO_CLIP)
        self.assertAlmostEqual(c.image_cost_estimate, scenes * EUR_PER_IMAGE)
        repo.upsert_production_costs.assert_called_once()


class Routes(unittest.TestCase):
    def test_costs_404_when_missing_job(self):
        with patch(
            "app.routes.production.watchlist_service.get_production_costs_service",
            return_value=ProductionCostsGetResponse(costs=None, warnings=["not found"]),
        ):
            r = client.get("/production/jobs/absent/costs")
            self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
