"""BA 7.5–7.7: Daily Cycle, Provider-Readiness, Storage Foundation (ohne echte Provider/Firestore)."""

from __future__ import annotations

import unittest
from typing import Optional
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.watchlist import service as watchlist_service
from app.watchlist.models import (
    GeneratedScript,
    PlanProductionFilesResponse,
    ProductionJob,
    ProductionJobActionResponse,
    ProviderConfig,
    ProviderConfigUpsertRequest,
    Scene,
    SceneAssets,
    SceneAssetItem,
    ScenePlan,
    ScriptJob,
    WatchlistChannel,
    ListWatchlistChannelsResponse,
)


client = TestClient(app)


def _script_job(jid: str, status: str = "completed", gid: Optional[str] = "gs1") -> ScriptJob:
    return ScriptJob(
        id=jid,
        video_id=f"v_{jid}",
        channel_id="UCx",
        video_url="https://youtu.be/x",
        status=status,
        target_language="de",
        duration_minutes=10,
        created_at="2026-04-01T10:00:00Z",
        completed_at="2026-04-01T10:05:00Z" if status == "completed" else None,
        generated_script_id=gid,
    )


def _pj(pid: str = "pj1") -> ProductionJob:
    return ProductionJob(
        id=pid,
        generated_script_id=pid,
        script_job_id="sj1",
        status="queued",
        created_at="2026-04-02T12:00:00Z",
        updated_at="2026-04-02T12:00:00Z",
    )


class Ba75DailyCycle(unittest.TestCase):
    def test_dry_run_does_not_call_writes(self):
        repo = MagicMock()
        repo.list_script_jobs.return_value = []
        repo.list_production_jobs.return_value = []
        repo.get_production_job.return_value = None

        with patch.object(
            watchlist_service,
            "list_channels",
            return_value=ListWatchlistChannelsResponse(channels=[], warnings=[]),
        ):
            out = watchlist_service.run_daily_production_cycle(
                dry_run=True,
                repo=repo,
            )
        self.assertTrue(any("dry_run" in w for w in out.warnings))
        repo.set_last_automation_cycle_at.assert_not_called()
        repo.upsert_watch_channel.assert_not_called()
        repo.create_production_job.assert_not_called()
        repo.upsert_scene_plan.assert_not_called()

    def test_daily_cycle_summary_fields(self):
        repo = MagicMock()
        ch = WatchlistChannel(
            id="UCa",
            channel_url="https://www.youtube.com/channel/UCa",
            channel_id="UCa",
            channel_name="Chan",
            status="active",
            check_interval="manual",
            max_results=5,
            target_language="de",
            duration_minutes=10,
            min_score=40,
            ignore_shorts=True,
            created_at="a",
            updated_at="b",
        )
        j = _script_job("job99", gid="gs99")
        repo.list_script_jobs.return_value = [j]
        repo.get_production_job.return_value = None  # no PJ yet
        gs = GeneratedScript(
            id="gs99",
            script_job_id=j.id,
            source_url="https://youtu.be/z",
            title="T",
            hook="H",
            chapters=[],
            full_script="ein zwei drei " * 40,
            sources=[],
            warnings=[],
            word_count=120,
            created_at="c",
        )
        repo.get_generated_script.return_value = gs
        plan = ScenePlan(
            id="gs99",
            production_job_id="gs99",
            generated_script_id="gs99",
            script_job_id=j.id,
            scenes=[
                Scene(
                    scene_number=1,
                    title="A",
                    duration_seconds=30,
                ),
            ],
            created_at="z",
            updated_at="z",
        )
        pj = _pj("gs99")
        repo.list_production_jobs.return_value = [pj]
        repo.get_scene_plan.return_value = None
        repo.get_scene_assets.return_value = None
        repo.get_voice_plan.return_value = None
        repo.get_render_manifest.return_value = None
        repo.get_production_checklist.return_value = None

        with patch.object(
            watchlist_service,
            "list_channels",
            return_value=ListWatchlistChannelsResponse(channels=[ch], warnings=[]),
        ):
            out = watchlist_service.run_daily_production_cycle(
                channel_limit=5,
                production_limit=1,
                dry_run=True,
                repo=repo,
            )
        self.assertEqual(out.checked_channels, 1)
        self.assertGreaterEqual(out.production_jobs_created, 1)
        self.assertGreaterEqual(out.scene_plans_created, 1)

    def test_daily_cycle_single_step_failure_does_not_abort_batch(self):
        pj_a = _pj("pja").model_copy(update={"created_at": "2026-01-02T12:00:00Z"})
        pj_b = _pj("pjb").model_copy(update={"created_at": "2026-01-01T12:00:00Z"})
        repo = MagicMock()
        repo.list_script_jobs.return_value = []
        repo.list_production_jobs.return_value = [pj_a, pj_b]
        repo.get_production_checklist.return_value = MagicMock()

        call = {"n": 0}

        def fake_generate_scene_plan(pid: str, **_):
            call["n"] += 1
            if pid == "pja":
                raise RuntimeError("boom")

            from app.watchlist.models import ScenePlanGenerateResponse

            return ScenePlanGenerateResponse(
                scene_plan=ScenePlan(
                    id=pid,
                    production_job_id=pid,
                    generated_script_id=pid,
                    script_job_id="s",
                    scenes=[
                        Scene(
                            scene_number=1,
                            title="S",
                            duration_seconds=30,
                        ),
                    ],
                    created_at="z",
                    updated_at="z",
                ),
                warnings=[],
            )

        real_sa = SceneAssets(
            id="pjb",
            production_job_id="pjb",
            scene_plan_id="pjb",
            generated_script_id="pjb",
            script_job_id="s",
            scenes=[
                SceneAssetItem(
                    scene_number=1,
                    title="one",
                ),
            ],
            created_at="z",
            updated_at="z",
        )

        def fake_generate_scene_assets(pid: str, **_):
            from app.watchlist.models import SceneAssetsGenerateResponse

            return SceneAssetsGenerateResponse(scene_assets=real_sa, warnings=[])

        repo.get_scene_plan.return_value = MagicMock(
            scenes=[Scene(scene_number=1, title="x", duration_seconds=5)]
        )
        repo.get_scene_assets.return_value = real_sa

        with patch.object(
            watchlist_service,
            "list_channels",
            return_value=ListWatchlistChannelsResponse(channels=[], warnings=[]),
        ), patch.object(
            watchlist_service,
            "run_automation_cycle",
            return_value=MagicMock(
                checked_channels=0,
                completed_jobs=0,
                failed_jobs=0,
                warnings=[],
                channel_results=[],
                job_results=[],
            ),
        ), patch.object(
            watchlist_service, "generate_scene_plan", side_effect=fake_generate_scene_plan
        ), patch.object(
            watchlist_service,
            "generate_scene_assets",
            side_effect=fake_generate_scene_assets,
        ), patch.object(
            watchlist_service, "generate_voice_plan"
        ) as gvp, patch.object(
            watchlist_service, "generate_render_manifest"
        ) as grm:
            from app.watchlist.models import (
                RenderManifest,
                RenderManifestGenerateResponse,
                VoicePlanGenerateResponse,
                VoicePlan,
            )

            gvp.return_value = VoicePlanGenerateResponse(
                voice_plan=VoicePlan(
                    id="pjb",
                    production_job_id="pjb",
                    scene_assets_id="pjb",
                    generated_script_id="pjb",
                    script_job_id="s",
                    blocks=[],
                    created_at="z",
                    updated_at="z",
                ),
                warnings=[],
            )
            grm.return_value = RenderManifestGenerateResponse(
                render_manifest=RenderManifest(
                    id="pjb",
                    production_job_id="pjb",
                    timeline=[],
                    created_at="z",
                    updated_at="z",
                ),
                warnings=[],
            )

            out = watchlist_service.run_daily_production_cycle(
                dry_run=False,
                repo=repo,
                production_limit=5,
            )

        self.assertGreaterEqual(len(out.warnings), 1)
        gvp.assert_called()
        self.assertEqual(call["n"], 2)


class Ba76Providers(unittest.TestCase):
    def test_list_upsert_and_status(self):
        repo = MagicMock()
        repo.list_provider_configs.return_value = [
            ProviderConfig(
                id="generic",
                provider_name="generic",
                enabled=True,
                dry_run=True,
                monthly_budget_limit=10,
                current_month_estimated_cost=0,
                status="ready",
                notes="",
                created_at="a",
                updated_at="b",
            )
        ]
        repo.get_provider_config.return_value = None
        with patch(
            "app.watchlist.service.FirestoreWatchlistRepository",
            return_value=repo,
        ):
            lst = watchlist_service.list_provider_configs_service(repo=repo)
            self.assertEqual(len(lst.configs), 1)
            u = watchlist_service.upsert_provider_config_service(
                "openai",
                ProviderConfigUpsertRequest(enabled=True, status="ready"),
                repo=repo,
            )
            self.assertEqual(u.provider_name, "openai")
            self.assertTrue(u.enabled)
            st = watchlist_service.get_provider_status_service(repo=repo)
            self.assertEqual(len(st.providers), 7)

    def test_provider_upsert_extra_field_rejected(self):
        with self.assertRaises(Exception):
            ProviderConfigUpsertRequest.model_validate({"enabled": True, "api_key": "x"})


class Ba77Files(unittest.TestCase):
    def test_plan_expected_paths(self):
        repo = MagicMock()
        repo.get_production_job.return_value = _pj("jid1")
        repo.get_scene_plan.return_value = ScenePlan(
            id="jid1",
            production_job_id="jid1",
            generated_script_id="jid1",
            script_job_id="sj",
            scenes=[
                Scene(scene_number=1, title="one", duration_seconds=10),
                Scene(scene_number=2, title="two", duration_seconds=10),
            ],
            created_at="z",
            updated_at="z",
        )
        repo.get_scene_assets.return_value = None
        repo.get_production_file_by_id.return_value = None

        out = watchlist_service.plan_production_files_service("jid1", repo=repo)
        paths = {f.storage_path for f in out.files}
        self.assertIn("exports/jid1/manifest.json", paths)
        self.assertIn("exports/jid1/production.md", paths)
        self.assertIn("exports/jid1/production.csv", paths)
        self.assertIn("voice/jid1/scene_001.mp3", paths)
        self.assertIn("images/jid1/scene_002.png", paths)
        self.assertIn("videos/jid1/scene_002.mp4", paths)
        self.assertIn("thumbnails/jid1/thumbnail.png", paths)
        self.assertEqual(out.planned_new, len(out.files))

    def test_plan_idempotent_skips_planned(self):
        repo = MagicMock()
        repo.get_production_job.return_value = _pj("z1")
        repo.get_scene_plan.return_value = ScenePlan(
            id="z1",
            production_job_id="z1",
            generated_script_id="z1",
            script_job_id="s",
            scenes=[Scene(scene_number=1, title="a", duration_seconds=5)],
            created_at="z",
            updated_at="z",
        )
        repo.get_production_file_by_id.return_value = None

        first = watchlist_service.plan_production_files_service("z1", repo=repo)
        self.assertGreater(first.planned_new, 0)
        known = {f.id: f for f in first.files}

        def gf(doc_id: str):
            return known.get(doc_id)

        repo.get_production_file_by_id.side_effect = gf
        second = watchlist_service.plan_production_files_service("z1", repo=repo)
        self.assertEqual(second.planned_new, 0)
        self.assertEqual(second.skipped_existing_planned, len(known))

    def test_files_routes_404(self):
        with patch(
            "app.routes.production.watchlist_service.plan_production_files_service",
            return_value=PlanProductionFilesResponse(
                files=[],
                planned_new=0,
                skipped_existing_planned=0,
                warnings=["not found"],
            ),
        ):
            r = client.post("/production/jobs/missing-xyz/files/plan", json={})
            self.assertEqual(r.status_code, 404)

        with patch(
            "app.routes.production.watchlist_service.get_production_job_detail",
            return_value=ProductionJobActionResponse(job=None, warnings=["not found"]),
        ):
            r2 = client.get("/production/jobs/missing-xyz/files")
            self.assertEqual(r2.status_code, 404)


if __name__ == "__main__":
    unittest.main()
