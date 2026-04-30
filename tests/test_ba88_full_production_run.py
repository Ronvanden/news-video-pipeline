"""BA 8.8: Goldener Referenzpfad — logischer Durchlauf mit Mocks (kein Live-Firestore)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from app.watchlist import service as watchlist_service
from app.watchlist.models import GeneratedScript, ProductionJob


def _gs(pid: str) -> GeneratedScript:
    return GeneratedScript(
        id=pid,
        script_job_id=f"sj_{pid}",
        source_url="https://youtu.example/test",
        title="Gold",
        hook="H",
        chapters=[],
        full_script="Intro " * 120,
        warnings=[],
        word_count=240,
        created_at="2026-04-30T09:00:00Z",
    )


class Ba88GoldenProductionPath(unittest.TestCase):
    def test_sequenced_mocked_pipeline_steps(self):
        """Reihenfolge gemäss GOLD_PRODUCTION_STANDARD: Plan → Assets → Voice → Manifest → Files → Costs."""
        repo = MagicMock()
        pid = "gold_pj_1"
        pj = ProductionJob(
            id=pid,
            generated_script_id=pid,
            script_job_id="sj_gold",
            status="queued",
            created_at="2026-04-30T08:00:00Z",
            updated_at="2026-04-30T08:00:00Z",
        )
        repo.get_production_job.return_value = pj
        repo.get_generated_script.return_value = _gs(pid)
        repo.get_scene_plan.return_value = None
        repo.get_scene_assets.return_value = None
        repo.get_voice_plan.return_value = None
        repo.get_render_manifest.return_value = None
        repo.get_production_costs.return_value = None
        repo.get_production_file_by_id.return_value = None

        watchlist_service.generate_scene_plan(pid, repo=repo)
        self.assertTrue(repo.upsert_scene_plan.called)
        sp = repo.upsert_scene_plan.call_args[0][0]
        repo.get_scene_plan.return_value = sp

        watchlist_service.generate_scene_assets(pid, repo=repo)
        self.assertTrue(repo.upsert_scene_assets.called)
        sa = repo.upsert_scene_assets.call_args[0][0]
        repo.get_scene_assets.return_value = sa

        watchlist_service.generate_voice_plan(pid, repo=repo)
        self.assertTrue(repo.upsert_voice_plan.called)
        vp = repo.upsert_voice_plan.call_args[0][0]
        repo.get_voice_plan.return_value = vp

        watchlist_service.generate_render_manifest(pid, repo=repo)
        self.assertTrue(repo.upsert_render_manifest.called)

        watchlist_service.plan_production_files_service(pid, repo=repo)
        self.assertTrue(repo.upsert_production_file.called)

        watchlist_service.calculate_production_costs_service(pid, repo=repo)
        self.assertTrue(repo.upsert_production_costs.called)


if __name__ == "__main__":
    unittest.main()
