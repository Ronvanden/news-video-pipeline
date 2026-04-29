"""BA 6.7: Scene Asset Prompts (Service + Routen mit Mocks)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.watchlist.models import (
    ProductionJob,
    Scene,
    SceneAssets,
    SceneAssetsGenerateRequest,
    SceneAssetsGenerateResponse,
    SceneAssetsGetResponse,
    ScenePlan,
)
from app.watchlist import service as watchlist_service
from app.watchlist.scene_asset_prompts import build_scene_asset_items


def _pj(pid: str = "pj1") -> ProductionJob:
    return ProductionJob(
        id=pid,
        generated_script_id=pid,
        script_job_id=pid,
        status="queued",
        created_at="2026-04-02T12:00:00Z",
        updated_at="2026-04-02T12:00:00Z",
    )


def _plan_with_scenes(pid: str = "pj1") -> ScenePlan:
    return ScenePlan(
        id=pid,
        production_job_id=pid,
        generated_script_id=pid,
        script_job_id=pid,
        status="ready",
        plan_version=1,
        source_fingerprint="fp",
        scenes=[
            Scene(
                scene_number=1,
                title="Intro",
                voiceover_text="Willkommen zur Story. Hier geht es weiter.",
                visual_summary="Einleitung visuell.",
                duration_seconds=30,
                asset_type="generated",
                mood="neutral",
                source_chapter_title="A",
                source_chapter_index=0,
            ),
        ],
        warnings=["plan-hinweis"],
        created_at="2026-04-02T12:00:00Z",
        updated_at="2026-04-02T12:00:00Z",
    )


class Ba67SceneAssetsService(unittest.TestCase):
    def test_generate_success(self):
        repo = MagicMock()
        repo.get_scene_assets.return_value = None
        repo.get_production_job.return_value = _pj()
        repo.get_scene_plan.return_value = _plan_with_scenes()

        out = watchlist_service.generate_scene_assets("pj1", repo=repo)

        self.assertIsNotNone(out.scene_assets)
        assert out.scene_assets is not None
        self.assertEqual(out.scene_assets.production_job_id, "pj1")
        self.assertEqual(out.scene_assets.style_profile, "documentary")
        self.assertEqual(len(out.scene_assets.scenes), 1)
        self.assertEqual(out.scene_assets.status, "ready")
        self.assertIn("plan-hinweis", out.scene_assets.warnings)
        repo.upsert_scene_assets.assert_called_once()

    def test_generate_missing_production_job(self):
        repo = MagicMock()
        repo.get_scene_assets.return_value = None
        repo.get_production_job.return_value = None

        out = watchlist_service.generate_scene_assets("missing", repo=repo)

        self.assertIsNone(out.scene_assets)
        self.assertIn("Production job not found", out.warnings[0])
        repo.upsert_scene_assets.assert_not_called()

    def test_generate_missing_scene_plan(self):
        repo = MagicMock()
        repo.get_scene_assets.return_value = None
        repo.get_production_job.return_value = _pj()
        repo.get_scene_plan.return_value = None

        out = watchlist_service.generate_scene_assets("pj1", repo=repo)

        self.assertIsNone(out.scene_assets)
        self.assertIn("Scene plan not found", out.warnings[0])

    def test_generate_idempotent(self):
        repo = MagicMock()
        existing = SceneAssets(
            id="pj1",
            production_job_id="pj1",
            scene_plan_id="pj1",
            generated_script_id="pj1",
            script_job_id="pj1",
            style_profile="news",
            status="ready",
            asset_version=1,
            scenes=[],
            warnings=[],
            created_at="x",
            updated_at="x",
        )
        repo.get_scene_assets.return_value = existing

        out = watchlist_service.generate_scene_assets("pj1", repo=repo)

        self.assertIs(out.scene_assets, existing)
        self.assertEqual(len(out.warnings), 1)
        self.assertIn("idempotent", out.warnings[0].lower())
        repo.get_production_job.assert_not_called()
        repo.upsert_scene_assets.assert_not_called()

    def test_style_profile_variations(self):
        sc = Scene(
            scene_number=1,
            title="T",
            voiceover_text="Neutraler Text ohne besondere Keywords.",
            visual_summary="Szene Kurzbeschreibung.",
            duration_seconds=20,
            asset_type="stock",
            mood="neutral",
            source_chapter_title="",
            source_chapter_index=-1,
        )
        doc_items, _ = build_scene_asset_items([sc], style_profile="documentary")
        news_items, _ = build_scene_asset_items([sc], style_profile="news")
        self.assertIn("Documentary", doc_items[0].image_prompt)
        self.assertIn("News broadcast", news_items[0].image_prompt)
        tc, _ = build_scene_asset_items([sc], style_profile="true_crime")
        self.assertIn("True-crime", tc[0].image_prompt)

    def test_generate_respects_request_style_profile(self):
        repo = MagicMock()
        repo.get_scene_assets.return_value = None
        repo.get_production_job.return_value = _pj()
        repo.get_scene_plan.return_value = _plan_with_scenes()
        req = SceneAssetsGenerateRequest(style_profile="faceless_youtube")
        out = watchlist_service.generate_scene_assets("pj1", req, repo=repo)
        assert out.scene_assets is not None
        self.assertEqual(out.scene_assets.style_profile, "faceless_youtube")
        self.assertIn("Faceless YouTube", out.scene_assets.scenes[0].image_prompt)

    def test_get_scene_assets_ok(self):
        repo = MagicMock()
        sa = SceneAssets(
            id="pj1",
            production_job_id="pj1",
            scene_plan_id="pj1",
            generated_script_id="pj1",
            script_job_id="pj1",
            scenes=[],
            warnings=[],
            created_at="a",
            updated_at="a",
        )
        repo.get_scene_assets.return_value = sa
        out = watchlist_service.get_scene_assets_for_production_job("pj1", repo=repo)
        self.assertIs(out.scene_assets, sa)


class Ba67ProductionRoutes(unittest.TestCase):
    def test_post_generate_404_missing_job(self):
        client = TestClient(app)
        with patch(
            "app.routes.production.watchlist_service.generate_scene_assets",
            return_value=SceneAssetsGenerateResponse(
                scene_assets=None,
                warnings=["Production job not found."],
            ),
        ):
            r = client.post("/production/jobs/xyz/scene-assets/generate")
        self.assertEqual(r.status_code, 404)

    def test_get_scene_assets_404(self):
        client = TestClient(app)
        with patch(
            "app.routes.production.watchlist_service.get_scene_assets_for_production_job",
            return_value=SceneAssetsGetResponse(scene_assets=None, warnings=["Scene assets not found."]),
        ):
            r = client.get("/production/jobs/nix/scene-assets")
        self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
