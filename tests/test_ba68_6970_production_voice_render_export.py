"""BA 6.8 Voice-Plan, 6.9 Render-Manifest, 7.0 Connector-Export — Service-/Route-Mocks."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.watchlist import service as watchlist_service
from app.watchlist.connector_export import build_connector_export_payload
from app.watchlist.models import (
    ConnectorExportPayload,
    ProductionConnectorExportResponse,
    ProductionJob,
    RenderManifest,
    RenderManifestGenerateResponse,
    Scene,
    SceneAssetItem,
    SceneAssets,
    ScenePlan,
    TimelineItem,
    VoiceBlock,
    VoicePlan,
    VoicePlanGenerateResponse,
)
from app.watchlist.render_manifest import build_timeline, decide_manifest_status
from app.watchlist.voice_plan import estimate_speech_seconds_from_text


def _pj(pid: str = "pj_test") -> ProductionJob:
    return ProductionJob(
        id=pid,
        generated_script_id=pid,
        script_job_id=pid,
        status="queued",
        narrator_style="",
        thumbnail_prompt="",
        created_at="2026-04-02T12:00:00Z",
        updated_at="2026-04-02T12:00:00Z",
    )


def _assets(pid: str, scenes: list[SceneAssetItem]) -> SceneAssets:
    return SceneAssets(
        id=pid,
        production_job_id=pid,
        scene_plan_id=pid,
        generated_script_id=pid,
        script_job_id=pid,
        style_profile="documentary",
        status="ready",
        asset_version=1,
        scenes=scenes,
        warnings=[],
        created_at="a",
        updated_at="b",
    )


class VoicePlanBa68(unittest.TestCase):
    def test_generate_success_and_duration(self):
        repo = MagicMock()
        repo.get_voice_plan.return_value = None
        repo.get_production_job.return_value = _pj()
        word140 = ("wort " * 140).strip()
        sa = _assets(
            "pj1",
            [
                SceneAssetItem(
                    scene_number=2,
                    title="Mitte",
                    voiceover_chunk=word140,
                    mood="neutral",
                    image_prompt="img",
                    video_prompt="vid",
                    camera_direction="pan",
                    asset_type="generated",
                ),
                SceneAssetItem(
                    scene_number=1,
                    title="Start",
                    voiceover_chunk="kurz.",
                    mood="dramatic",
                    image_prompt="i2",
                    video_prompt="v2",
                    camera_direction="",
                    asset_type="generated",
                ),
            ],
        )
        repo.get_scene_assets.return_value = sa

        class Req:
            voice_profile = "documentary"

        out = watchlist_service.generate_voice_plan("pj1", Req(), repo=repo)
        assert out.voice_plan is not None
        self.assertEqual(out.voice_plan.status, "ready")
        nums = sorted(b.scene_number for b in out.voice_plan.blocks)
        self.assertEqual(nums, [1, 2])
        b_long = next(
            x for x in out.voice_plan.blocks if x.scene_number == 2
        )
        self.assertEqual(b_long.estimated_duration_seconds, 60)
        repo.upsert_voice_plan.assert_called_once()

        self.assertEqual(estimate_speech_seconds_from_text("eins zwei drei vier"), 2)

    def test_missing_scene_assets(self):
        repo = MagicMock()
        repo.get_voice_plan.return_value = None
        repo.get_production_job.return_value = _pj()
        repo.get_scene_assets.return_value = None
        out = watchlist_service.generate_voice_plan("x", repo=repo)
        self.assertIsNone(out.voice_plan)
        repo.upsert_voice_plan.assert_not_called()

    def test_idempotent_voice_plan(self):
        repo = MagicMock()
        existing = VoicePlan(
            id="p",
            production_job_id="p",
            scene_assets_id="p",
            generated_script_id="p",
            script_job_id="p",
            status="ready",
            voice_profile="news",
            voice_version=1,
            blocks=[VoiceBlock(scene_number=1, title="T", voice_text="hallo.")],
            warnings=[],
            created_at="a",
            updated_at="b",
        )
        repo.get_voice_plan.return_value = existing
        out = watchlist_service.generate_voice_plan("p", repo=repo)
        self.assertIs(out.voice_plan, existing)
        self.assertTrue(any("idempotent" in w.lower() for w in out.warnings))


class VoiceProfileVariation(unittest.TestCase):
    def test_documentary_vs_news_speaker_styles(self):
        repo = MagicMock()
        repo.get_voice_plan.return_value = None
        pj = _pj()
        pj.narrator_style = ""
        repo.get_production_job.return_value = pj
        sc = SceneAssetItem(
            scene_number=1,
            title="A",
            voiceover_chunk="Etwas deutscher Fließtext für den Test.",
            mood="neutral",
            image_prompt="",
            video_prompt="",
            camera_direction="",
            asset_type="generated",
        )
        repo.get_scene_assets.return_value = _assets("pj_vp", [sc])

        class NewsReq:
            voice_profile = "news"

        class DocReq:
            voice_profile = "documentary"

        o_news = watchlist_service.generate_voice_plan("pj_vp", NewsReq(), repo=repo)
        repo.reset_mock()
        repo.get_voice_plan.return_value = None
        repo.get_production_job.return_value = pj
        repo.get_scene_assets.return_value = _assets("pj_vp", [sc])
        o_doc = watchlist_service.generate_voice_plan(
            "pj_vp", DocReq(), repo=repo
        )
        sn = (
            (o_news.voice_plan.blocks[0].speaker_style.lower())
            if o_news.voice_plan
            else ""
        )
        sd = (
            (o_doc.voice_plan.blocks[0].speaker_style.lower())
            if o_doc.voice_plan
            else ""
        )
        self.assertTrue(sn)
        self.assertTrue(sd)
        self.assertNotEqual(sn, sd)


class RenderManifestBa69(unittest.TestCase):
    def test_timeline_sorted(self):
        sa = _assets(
            "p",
            [
                SceneAssetItem(
                    scene_number=3,
                    title="three",
                    voiceover_chunk="drei vier",
                    mood="dramatic",
                    image_prompt="i3",
                    video_prompt="v3",
                    camera_direction="c3",
                    asset_type="stock",
                ),
                SceneAssetItem(
                    scene_number=1,
                    title="one",
                    voiceover_chunk="eins",
                    mood="neutral",
                    image_prompt="i1",
                    video_prompt="v1",
                    camera_direction="c1",
                    asset_type="generated",
                ),
            ],
        )
        sp = ScenePlan(
            id="p",
            production_job_id="p",
            generated_script_id="p",
            script_job_id="p",
            status="ready",
            plan_version=1,
            scenes=[
                Scene(
                    scene_number=1,
                    title="",
                    duration_seconds=20,
                    voiceover_text="",
                    mood="neutral",
                    asset_type="generated",
                    source_chapter_index=0,
                ),
                Scene(
                    scene_number=3,
                    title="",
                    duration_seconds=25,
                    voiceover_text="",
                    mood="dramatic",
                    asset_type="stock",
                    source_chapter_index=1,
                ),
            ],
            warnings=[],
            created_at="a",
            updated_at="b",
        )
        vp = VoicePlan(
            id="p",
            production_job_id="p",
            scene_assets_id="p",
            generated_script_id="p",
            script_job_id="p",
            status="ready",
            voice_profile="documentary",
            voice_version=1,
            blocks=[
                VoiceBlock(
                    scene_number=1,
                    title="",
                    voice_text="ein satz fuer eins.",
                    estimated_duration_seconds=5,
                    speaker_style="s",
                    pause_after_seconds=0.25,
                    tts_provider_hint="generic",
                    pronunciation_notes="",
                ),
                VoiceBlock(
                    scene_number=3,
                    title="",
                    voice_text="drei fuer drei.",
                    estimated_duration_seconds=5,
                    speaker_style="s",
                    pause_after_seconds=0.35,
                    tts_provider_hint="generic",
                    pronunciation_notes="",
                ),
            ],
            warnings=[],
            created_at="a",
            updated_at="b",
        )
        tl, total = build_timeline(sp, sa, vp)
        order = [t.scene_number for t in tl]
        self.assertEqual(order, [1, 3])
        self.assertGreaterEqual(total, sum(t.duration_seconds for t in tl))

    def test_manifest_success_via_service(self):
        repo = MagicMock()
        repo.get_render_manifest.return_value = None
        repo.get_production_job.return_value = _pj()
        repo.get_scene_plan.return_value = ScenePlan(
            id="pj1",
            production_job_id="pj1",
            generated_script_id="pj1",
            script_job_id="pj1",
            status="ready",
            plan_version=1,
            scenes=[
                Scene(
                    scene_number=1,
                    title="Intro",
                    duration_seconds=10,
                    voiceover_text="v",
                    mood="neutral",
                    asset_type="generated",
                    source_chapter_index=0,
                )
            ],
            warnings=[],
            created_at="a",
            updated_at="b",
        )
        repo.get_scene_assets.return_value = _assets(
            "pj1",
            [
                SceneAssetItem(
                    scene_number=1,
                    title="Intro",
                    voiceover_chunk="Hallo Welt und willkommen.",
                    mood="neutral",
                    image_prompt="ip",
                    video_prompt="vp",
                    camera_direction="steady",
                    asset_type="generated",
                ),
            ],
        )
        vp = VoicePlan(
            id="pj1",
            production_job_id="pj1",
            scene_assets_id="pj1",
            generated_script_id="pj1",
            script_job_id="pj1",
            status="ready",
            voice_profile="documentary",
            voice_version=1,
            blocks=[
                VoiceBlock(
                    scene_number=1,
                    title="Intro",
                    voice_text="Hallo Welt und willkommen.",
                    estimated_duration_seconds=5,
                    speaker_style="doc",
                    pause_after_seconds=0.25,
                    tts_provider_hint="generic",
                    pronunciation_notes="",
                )
            ],
            warnings=[],
            created_at="a",
            updated_at="b",
        )
        repo.get_voice_plan.return_value = vp
        out = watchlist_service.generate_render_manifest("pj1", repo=repo)
        assert out.render_manifest is not None
        self.assertEqual(out.render_manifest.status, "ready")
        self.assertEqual(len(out.render_manifest.timeline), 1)

    def test_missing_voice_plan_incomplete(self):
        pj = _pj()
        sa = _assets(
            "pjx",
            [
                SceneAssetItem(
                    scene_number=2,
                    title="",
                    voiceover_chunk="t",
                    mood="neutral",
                    image_prompt="",
                    video_prompt="",
                    camera_direction="",
                    asset_type="generated",
                )
            ],
        )
    def test_missing_voice_plan_incomplete(self):
        pj = _pj()
        sa = _assets(
            "pjx",
            [
                SceneAssetItem(
                    scene_number=2,
                    title="",
                    voiceover_chunk="t",
                    mood="neutral",
                    image_prompt="",
                    video_prompt="",
                    camera_direction="",
                    asset_type="generated",
                )
            ],
        )
        sp = ScenePlan(
            id="pjx",
            production_job_id="pjx",
            generated_script_id="pjx",
            script_job_id="pjx",
            status="ready",
            plan_version=1,
            scenes=[
                Scene(
                    scene_number=2,
                    title="",
                    duration_seconds=10,
                    voiceover_text="t",
                    mood="neutral",
                    asset_type="generated",
                    source_chapter_index=0,
                )
            ],
            warnings=[],
            created_at="a",
            updated_at="b",
        )

        repo = MagicMock()
        repo.get_render_manifest.return_value = None
        repo.get_production_job.return_value = pj
        repo.get_scene_assets.return_value = sa
        repo.get_voice_plan.return_value = None
        repo.get_scene_plan.return_value = sp

        out = watchlist_service.generate_render_manifest("pjx", repo=repo)
        assert out.render_manifest is not None
        self.assertEqual(out.render_manifest.status, "incomplete")
        merged = " ".join(out.render_manifest.warnings).lower()
        self.assertIn("voice plan", merged)

        st = decide_manifest_status(
            production_job=pj, scene_plan=sp, scene_assets=sa, voice_plan=None
        )
        self.assertEqual(st, "incomplete")

    def test_missing_scene_assets_generates_none(self):
        repo = MagicMock()
        repo.get_render_manifest.return_value = None
        repo.get_production_job.return_value = _pj()
        repo.get_scene_assets.return_value = None
        out = watchlist_service.generate_render_manifest("nosa", repo=repo)
        self.assertIsNone(out.render_manifest)
        repo.upsert_render_manifest.assert_not_called()


class ConnectorExportBa70(unittest.TestCase):
    def test_export_success_structure(self):
        pj = _pj("ex1")
        vp = VoicePlan(
            id="ex1",
            production_job_id="ex1",
            scene_assets_id="ex1",
            generated_script_id="ex1",
            script_job_id="ex1",
            status="ready",
            voice_profile="documentary",
            voice_version=1,
            blocks=[
                VoiceBlock(
                    scene_number=1,
                    title="Intro",
                    voice_text="ein und zwei drei.",
                    estimated_duration_seconds=3,
                    speaker_style="neutral",
                    pause_after_seconds=0.25,
                    tts_provider_hint="elevenlabs",
                    pronunciation_notes="",
                )
            ],
            warnings=[],
            created_at="a",
            updated_at="b",
        )
        rm = RenderManifest(
            id="ex1",
            production_job_id="ex1",
            production_job=pj,
            scene_plan=None,
            scene_assets=None,
            voice_plan=vp,
            timeline=[
                TimelineItem(
                    scene_number=1,
                    voice_text="x",
                    image_prompt="leonardo-stil",
                    video_prompt="kling-motion",
                    camera_direction="",
                    duration_seconds=3,
                    asset_type="generated",
                    transition_hint="cut",
                )
            ],
            estimated_total_duration_seconds=10,
            status="ready",
            warnings=[],
            created_at="a",
            updated_at="b",
        )
        px = build_connector_export_payload(
            production_job=pj,
            manifest=rm,
            voice_plan=vp,
            scene_assets=None,
            generated_script=None,
            render_manifest_warnings=[],
        )
        self.assertIsInstance(px, ConnectorExportPayload)
        self.assertEqual(len(px.elevenlabs_blocks), 1)
        self.assertGreaterEqual(len(px.kling_prompts), 1)
        self.assertIn("prompt", px.kling_prompts[0])

    def test_export_incomplete_with_warnings(self):
        p = build_connector_export_payload(
            production_job=_pj(),
            manifest=None,
            voice_plan=None,
            scene_assets=_assets(
                "a",
                [
                    SceneAssetItem(
                        scene_number=9,
                        title="nine",
                        voiceover_chunk="neun",
                        mood="neutral",
                        image_prompt="img9",
                        video_prompt="vid9",
                        camera_direction="",
                        asset_type="generated",
                    )
                ],
            ),
            generated_script=None,
            render_manifest_warnings=[],
        )
        mw = str(p.metadata.warnings).lower()
        self.assertIn("manifest", mw)
        self.assertGreaterEqual(len(p.kling_prompts), 1)

    def test_no_external_http_on_export_builder(self):
        with patch("urllib.request.urlopen") as u:
            build_connector_export_payload(
                production_job=None,
                manifest=None,
                voice_plan=None,
                scene_assets=None,
                generated_script=None,
                render_manifest_warnings=["x"],
            )
        u.assert_not_called()


class ProductionRoutesBa6870(unittest.TestCase):
    def test_post_voice_plan_404_when_missing_assets(self):
        client = TestClient(app)
        with patch(
            "app.routes.production.watchlist_service.generate_voice_plan",
            return_value=VoicePlanGenerateResponse(
                voice_plan=None,
                warnings=["Scene assets not found"],
            ),
        ):
            r = client.post("/production/jobs/z/voice-plan/generate")
        self.assertEqual(r.status_code, 404)

    def test_post_render_manifest_404_when_no_scene_assets(self):
        client = TestClient(app)
        with patch(
            "app.routes.production.watchlist_service.generate_render_manifest",
            return_value=RenderManifestGenerateResponse(
                render_manifest=None,
                warnings=["Scene assets"],
            ),
        ):
            r = client.post("/production/jobs/z/render-manifest/generate")
        self.assertEqual(r.status_code, 404)

    def test_export_returns_200(self):
        client = TestClient(app)
        with patch(
            "app.routes.production.watchlist_service.get_production_connector_export",
            return_value=ProductionConnectorExportResponse(
                export=build_connector_export_payload(
                    production_job=None,
                    manifest=None,
                    voice_plan=None,
                    scene_assets=None,
                    generated_script=None,
                    render_manifest_warnings=["w"],
                ),
                warnings=["w"],
            ),
        ):
            r = client.get("/production/jobs/ab/export")
        self.assertEqual(r.status_code, 200)
        js = r.json()
        self.assertIn("export", js)
        self.assertIn("warnings", js)


if __name__ == "__main__":
    unittest.main()