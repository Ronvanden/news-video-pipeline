"""BA 8.4 LIGHT — Founder Control Panel Summary (Aggregation, leere Collections, keine API-Regression)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.watchlist import service as watchlist_service
from app.watchlist.control_panel import build_control_panel_summary
from app.watchlist.models import (
    GeneratedScript,
    PipelineAudit,
    PipelineEscalation,
    ProductionCosts,
    ProductionJob,
    ProviderConfig,
    RecoveryAction,
    ScriptJob,
)


def _audit_open(sev: str) -> PipelineAudit:
    return PipelineAudit(
        id=f"aud_{sev}",
        severity=sev,  # type: ignore[arg-type]
        status="open",
        detected_at="2026-04-30T12:00:00Z",
    )


def _esc() -> PipelineEscalation:
    return PipelineEscalation(
        escalation_id="esc1",
        severity="high",
        category="cost_anomaly",
        created_at="2026-04-30T12:00:00Z",
    )


class Ba84ControlPanelAggregate(unittest.TestCase):
    def test_service_aggregates_audits_escalations_recovery_providers_costs(self):
        repo = MagicMock()
        repo.stream_pipeline_audits_recent.return_value = [
            _audit_open("critical"),
            _audit_open("warning"),
            _audit_open("info"),
        ]
        repo.stream_pipeline_escalations_recent.return_value = [_esc()]
        repo.stream_recovery_actions_recent.return_value = [
            RecoveryAction(
                id="r1",
                production_job_id="pj1",
                action_kind="retry_scene_plan",
                created_at="2026-04-30T11:00:00Z",
                finished_at="2026-04-30T11:01:00Z",
            )
        ]
        repo.stream_production_jobs_for_summary.return_value = [
            ProductionJob(
                id="pj1",
                generated_script_id="g1",
                script_job_id="sj1",
                status="failed",
                created_at="2026-04-30T10:00:00Z",
                updated_at="2026-04-30T10:05:00Z",
                error_code="x",
            ),
            ProductionJob(
                id="pj2",
                generated_script_id="g2",
                script_job_id="sj2",
                status="queued",
                created_at="2026-04-30T10:00:00Z",
                updated_at="2026-04-30T10:05:00Z",
            ),
        ]
        repo.list_script_jobs.return_value = [
            ScriptJob(
                id="sj9",
                video_id="sj9",
                channel_id="c1",
                video_url="https://youtu.be/sj9",
                status="stuck",
                created_at="2026-04-30T09:00:00Z",
                error_code="stuck",
            )
        ]
        repo.count_script_jobs_by_status.side_effect = lambda s: {
            "pending": 2,
            "running": 1,
            "completed": 10,
            "failed": 0,
            "skipped": 1,
            "stuck": 3,
        }.get(s, 0)
        repo.list_provider_configs.return_value = [
            ProviderConfig(
                id="elevenlabs",
                provider_name="elevenlabs",
                enabled=True,
                dry_run=True,
                status="ready",
                created_at="",
                updated_at="",
            ),
            ProviderConfig(
                id="kling",
                provider_name="kling",
                enabled=False,
                dry_run=False,
                status="error",
                created_at="",
                updated_at="",
            ),
        ]
        repo.stream_production_costs_recent.return_value = [
            ProductionCosts(
                id="pj_cost",
                production_job_id="pj1",
                estimated_total_cost=12.5,
                created_at="",
                updated_at="",
            )
        ]
        repo.stream_generated_scripts_sample.return_value = [
            GeneratedScript(
                id="gs1",
                script_job_id="sj1",
                source_url="https://youtu.be/x",
                title="Sample",
                hook="Hook text here for fixture",
                full_script="body " * 50,
                created_at="2026-04-30T12:00:00Z",
                hook_type="cold_open_news",
                video_template="true_crime",
                template_conformance_gate="failed",
                experiment_id="exp_hook_ab_v1",
                hook_variant_id="hv_tension_arc_v1",
            )
        ]

        out = watchlist_service.get_control_panel_summary_service(repo=repo)

        self.assertEqual(out.audit.open_critical, 1)
        self.assertEqual(out.audit.open_warning, 1)
        self.assertEqual(out.audit.open_info, 1)
        self.assertEqual(len(out.escalation.recent_escalations), 1)
        self.assertEqual(out.escalation.count_by_severity.get("high"), 1)
        self.assertEqual(out.escalation.count_by_category.get("cost_anomaly"), 1)
        self.assertEqual(len(out.recovery.recent_actions), 1)
        self.assertEqual(out.jobs.production_jobs_by_status.get("failed"), 1)
        self.assertEqual(out.jobs.production_jobs_by_status.get("queued"), 1)
        self.assertEqual(out.jobs.script_jobs_by_status.get("pending"), 2)
        self.assertEqual(out.providers.total_configs, 2)
        self.assertEqual(out.providers.enabled, 1)
        self.assertEqual(out.providers.status_error, 1)
        self.assertEqual(out.costs.cost_records_count, 1)
        self.assertGreater(out.costs.estimated_total_eur, 0)
        self.assertEqual(out.costs.cost_anomaly_escalations, 1)
        kinds = {p.kind for p in out.recent_problems.items}
        self.assertIn("production_job", kinds)
        self.assertIn("script_job", kinds)
        self.assertEqual(out.story_engine.sampled_scripts, 1)
        self.assertEqual(out.story_engine.template_gate_failed_scripts, 1)
        self.assertIn("true_crime", out.story_engine.by_video_template)
        self.assertEqual(out.story_engine.template_optimization.sample_scripts, 1)
        self.assertGreaterEqual(len(out.story_engine.template_optimization.scores), 1)

    def test_empty_collections_returns_stable_shape(self):
        repo = MagicMock()
        repo.stream_pipeline_audits_recent.return_value = []
        repo.stream_pipeline_escalations_recent.return_value = []
        repo.stream_recovery_actions_recent.return_value = []
        repo.stream_production_jobs_for_summary.return_value = []
        repo.list_script_jobs.return_value = []
        repo.count_script_jobs_by_status.return_value = 0
        repo.list_provider_configs.return_value = []
        repo.stream_production_costs_recent.return_value = []

        repo.stream_generated_scripts_sample.return_value = []

        out = build_control_panel_summary(repo=repo)
        self.assertEqual(out.audit.open_critical, 0)
        self.assertEqual(out.escalation.count_by_severity, {})
        self.assertEqual(out.jobs.production_jobs_sampled, 0)
        self.assertEqual(out.providers.total_configs, 0)
        self.assertEqual(out.costs.cost_records_count, 0)
        self.assertEqual(out.recent_problems.items, [])
        self.assertEqual(out.story_engine.sampled_scripts, 0)

    def test_health_endpoint_still_ok(self):
        client = TestClient(app)
        r = client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json().get("status"), "healthy")


if __name__ == "__main__":
    unittest.main()
