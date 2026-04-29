"""BA 8.0–8.2: Audit, Recovery, Monitoring — mit Mocks."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from app.watchlist import service as watchlist_service
from app.watchlist.models import (
    PipelineAuditDraft,
    PipelineAuditRunRequest,
    ProductionJob,
    ProductionRecoveryRetryRequest,
)


def _pj(pid: str = "pj1", status: str = "planning_ready") -> ProductionJob:
    return ProductionJob(
        id=pid,
        generated_script_id="gs1",
        script_job_id="sj1",
        status=status,
        created_at="2026-05-01T10:00:00Z",
        updated_at="2026-05-01T10:00:00Z",
    )


class Ba80Audit(unittest.TestCase):
    def test_run_audit_persists_minimum(self):
        repo = MagicMock()
        repo.get_production_job.return_value = _pj("p1", status="planning_ready")
        pj = _pj("p1", status="planning_ready")
        repo.list_production_jobs.return_value = [pj]
        repo.list_running_script_jobs.return_value = []
        repo.get_generated_script.return_value = MagicMock(id="gs1")
        repo.get_scene_plan.return_value = None
        repo.get_scene_assets.return_value = None
        repo.get_voice_plan.return_value = None
        repo.get_render_manifest.return_value = None
        repo.get_production_checklist.return_value = None
        repo.get_production_costs.return_value = None
        repo.list_production_files_for_job.return_value = []
        repo.list_execution_jobs_for_job.return_value = []
        repo.get_pipeline_audit.return_value = None

        out = watchlist_service.run_pipeline_audit_service(
            repo=repo,
            body=PipelineAuditRunRequest(production_job_limit=10, resolve_missing_from_scan_set=False),
        )
        self.assertGreaterEqual(out.audits_written, 1)
        repo.upsert_pipeline_audit.assert_called()

    def test_doc_id_stable(self):
        d = PipelineAuditDraft(
            audit_type="dead_job",
            severity="critical",
            detected_issue="x",
            recommended_action="reset_pipeline_step",
            auto_repairable=False,
            production_job_id=None,
            script_job_id="job_xyz",
            extra_slug="stuck_running",
        )
        from app.watchlist.pipeline_audit_scan import pipeline_audit_document_id_from_draft

        self.assertTrue(pipeline_audit_document_id_from_draft(d).startswith("aud_sj_job_xyz"))


class Ba81Recovery(unittest.TestCase):
    def test_normalize_step_aliases(self):
        fn = getattr(watchlist_service, "_normalize_recovery_step")
        self.assertEqual(fn("scene-assets"), "scene_assets")

    def test_recovery_unknown_step_fails_logged(self):
        repo = MagicMock()
        pj = _pj()
        repo.get_production_job.return_value = pj
        repo.upsert_recovery_action.side_effect = lambda x: x
        resp = watchlist_service.retry_production_pipeline_step_service(
            "pj1",
            ProductionRecoveryRetryRequest(step="nope"),
            repo=repo,
        )
        self.assertEqual(resp.action.status, "failed")


if __name__ == "__main__":
    unittest.main()
