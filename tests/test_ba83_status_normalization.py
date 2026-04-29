"""BA 8.3 Status-Normalisierung & Eskalationen — mit Mock-Repository."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from app.watchlist import service as watchlist_service
from app.watchlist.models import (
    ExecutionJob,
    ProductionCosts,
    ProductionFileRecord,
    ProductionJob,
    ScriptJob,
    StatusNormalizeRunRequest,
)
from app.watchlist.status_normalizer import (
    detect_orphaned_jobs,
    escalate_document_id,
    escalation_document_id,
    exponential_backoff_seconds,
    hard_fail_after_max_retries,
    normalize_pipeline_status,
)


def _pj(pid: str = "pj1", *, status: str = "queued", created_old: bool = False) -> ProductionJob:
    ts = (
        "2024-01-01T08:00:00Z"
        if created_old
        else "2026-05-01T10:00:00Z"
    )
    return ProductionJob(
        id=pid,
        generated_script_id="gs1",
        script_job_id="sj1",
        status=status,
        created_at=ts,
        updated_at="2026-05-01T10:10:00Z",
    )


def _sj(job_id: str = "jid1", *, status: str = "running", retries: dict | None = None) -> ScriptJob:
    return ScriptJob(
        id=job_id,
        video_id=job_id,
        channel_id="c1",
        video_url=f"https://youtu.be/{job_id}",
        status=status,
        created_at="2026-05-01T09:50:00Z",
        started_at="2020-01-01T00:00:00Z",
        last_attempt_at=None,
        generated_script_id="gs1",
        pipeline_step_retry_counts=retries or {},
    )


class Ba83Detection(unittest.TestCase):
    def test_orphan_detect(self):
        repo = MagicMock()
        pj = _pj("p_miss")
        repo.list_production_jobs.return_value = [pj]
        repo.get_script_job.return_value = None

        findings = detect_orphaned_jobs(repo, production_job_limit=10)
        self.assertTrue(any(f.kind == "script_job_missing" for f in findings))

    def test_escalation_id_deterministic(self):
        a = escalation_document_id(
            category="repairable_gap",
            production_job_id="p1",
            script_job_id="s1",
            reason_key="x",
        )
        b = escalation_document_id(
            category="repairable_gap",
            production_job_id="p1",
            script_job_id="s1",
            reason_key="x",
        )
        self.assertEqual(a, b)


class Ba83Normalizer(unittest.TestCase):
    def test_escalate_doc_id_alias_equals_module(self):
        """Alias escalate_document_id (Auftrag) → escalation_document_id."""
        self.assertEqual(
            escalate_document_id(
                category="cost_anomaly",
                production_job_id="a",
                script_job_id="b",
                reason_key="k",
            ),
            escalation_document_id(
                category="cost_anomaly",
                production_job_id="a",
                script_job_id="b",
                reason_key="k",
            ),
        )

    def test_stuck_normalized(self):
        repo = MagicMock()
        repo.stream_recovery_actions_recent.return_value = []
        repo.list_production_jobs.return_value = []
        repo.list_running_script_jobs.return_value = [_sj("jid_stuck")]
        repo.list_script_jobs.return_value = []
        repo.list_production_files_for_job.return_value = []
        repo.list_execution_jobs_for_job.return_value = []

        out, esc = normalize_pipeline_status(
            repo,
            opts=StatusNormalizeRunRequest(
                stuck_running_minutes=30,
                production_job_scan_limit=20,
            ),
            utc_now_iso="2026-05-02T12:00:00Z",
        )
        self.assertGreaterEqual(out.stuck_normalized, 1)
        repo.patch_script_job.assert_called()

    def test_escalation_repairable_gap(self):
        repo = MagicMock()
        repo.stream_recovery_actions_recent.return_value = []
        repo.list_running_script_jobs.return_value = []

        pj = _pj("keep_linked")
        sj_done = ScriptJob(
            id="orph_completed",
            video_id="orph_completed",
            channel_id="c1",
            video_url="https://youtu.be/orph_completed",
            status="completed",
            created_at="2026-04-01T10:00:00Z",
            completed_at="2026-04-02T12:00:00Z",
        )
        repo.list_production_jobs.return_value = [pj]
        repo.get_script_job.return_value = MagicMock(id=pj.script_job_id)
        repo.get_generated_script.return_value = MagicMock(id=pj.generated_script_id)

        repo.list_script_jobs.return_value = [sj_done]
        repo.get_scene_plan.return_value = None
        repo.list_production_files_for_job.return_value = []
        repo.list_execution_jobs_for_job.return_value = []

        out, esc = normalize_pipeline_status(
            repo,
            opts=StatusNormalizeRunRequest(
                stuck_running_minutes=45,
                production_job_scan_limit=20,
                script_job_scan_limit=50,
            ),
            utc_now_iso="2026-05-03T08:00:00Z",
        )
        self.assertGreaterEqual(out.repairable_gap_escalations, 1)


class Ba83Retry(unittest.TestCase):
    def test_exponential_backoff(self):
        self.assertEqual(exponential_backoff_seconds(0, 60), 60)
        self.assertEqual(exponential_backoff_seconds(3, 60), 480)

    def test_hard_fail_after_retries(self):
        self.assertFalse(hard_fail_after_max_retries(3, 3))
        self.assertTrue(hard_fail_after_max_retries(4, 3))

    def test_retry_cap_hard_fail(self):
        repo = MagicMock()
        repo.stream_recovery_actions_recent.return_value = []
        sj = _sj("heavy", retries={"stuck_normalize": 3})
        repo.list_running_script_jobs.return_value = [sj]
        repo.list_production_jobs.return_value = []
        repo.list_script_jobs.return_value = []
        repo.list_production_files_for_job.return_value = []
        repo.list_execution_jobs_for_job.return_value = []

        out, _ = normalize_pipeline_status(
            repo,
            opts=StatusNormalizeRunRequest(max_step_retries=3),
            utc_now_iso="2026-05-03T09:00:00Z",
        )
        self.assertGreaterEqual(out.hard_fails_retry_cap, 1)
        kw = repo.patch_script_job.call_args[0][1]
        self.assertEqual(kw.get("status"), "failed")


class Ba83Provider(unittest.TestCase):
    def test_provider_failure_cluster_escalation(self):
        repo = MagicMock()
        repo.stream_recovery_actions_recent.return_value = []
        repo.list_running_script_jobs.return_value = []

        pj = _pj("pprov", status="in_progress")

        repo.list_production_jobs.return_value = [pj]
        repo.list_script_jobs.return_value = []
        repo.list_production_files_for_job.return_value = []
        exe = ExecutionJob(
            id="ej1",
            production_job_id=pj.id,
            job_type="image_generate",
            provider_name="kling",
            status="failed",
            created_at="2026-01-01",
            updated_at="2026-01-02",
        )
        repo.list_execution_jobs_for_job.return_value = [
            ExecutionJob(
                id=f"ej{i}",
                production_job_id=pj.id,
                job_type="image_generate",
                provider_name="kling",
                status="failed",
                created_at="2026-01-01",
                updated_at="2026-01-02",
            )
            for i in range(3)
        ]

        out, _ = normalize_pipeline_status(
            repo,
            opts=StatusNormalizeRunRequest(provider_failed_cluster_threshold=3),
            utc_now_iso="2026-05-03T10:00:00Z",
        )
        self.assertGreaterEqual(out.escalations_upserted, 1)


if __name__ == "__main__":
    unittest.main()
