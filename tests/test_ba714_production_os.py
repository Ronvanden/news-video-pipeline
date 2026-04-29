"""BA 7.1–7.4 Production OS: Export-Download, Provider-Templates, Checkliste, Status-Sync."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.watchlist import service as watchlist_service
from app.watchlist.export_download import build_provider_templates as build_provider_templates_dict
from app.watchlist.models import (
    Chapter,
    GeneratedScript,
    ProductionChecklist,
    ProductionChecklistUpdateRequest,
    ProductionJob,
    RenderManifest,
    TimelineItem,
    VoiceBlock,
    VoicePlan,
)
from app.watchlist.production_checklist import compute_target_production_status


def _pj(pid: str = "pj_os") -> ProductionJob:
    return ProductionJob(
        id=pid,
        generated_script_id=pid,
        script_job_id=pid,
        status="queued",
        narrator_style="warm",
        thumbnail_prompt="thumb hint",
        created_at="2026-04-02T12:00:00Z",
        updated_at="2026-04-02T12:00:00Z",
    )


def _manifest(pid: str = "pj_os") -> RenderManifest:
    return RenderManifest(
        id=pid,
        production_job_id=pid,
        production_job=None,
        scene_plan=None,
        scene_assets=None,
        voice_plan=None,
        timeline=[
            TimelineItem(
                scene_number=1,
                voice_text="Voice Zeile",
                image_prompt="Bildprompt",
                video_prompt="Videoprompt",
                duration_seconds=15,
            )
        ],
        estimated_total_duration_seconds=15,
        export_version="7.0.0",
        status="ready",
        warnings=[],
        created_at="a",
        updated_at="b",
    )


def _voice(pid: str = "pj_os") -> VoicePlan:
    return VoicePlan(
        id=pid,
        production_job_id=pid,
        scene_assets_id=pid,
        generated_script_id=pid,
        script_job_id=pid,
        status="ready",
        voice_profile="documentary",
        voice_version=1,
        blocks=[
            VoiceBlock(
                scene_number=1,
                title="Szene 1",
                voice_text="Hallo aus Block eins.",
                estimated_duration_seconds=5,
                speaker_style="story",
                pause_after_seconds=0.25,
                tts_provider_hint="generic",
                pronunciation_notes="",
            ),
        ],
        warnings=[],
        created_at="a",
        updated_at="b",
    )


class ExportDownloadBa714(unittest.TestCase):
    def test_generate_export_json_manifest_and_templates(self):
        repo = MagicMock()
        repo.get_production_job.return_value = _pj()
        repo.get_render_manifest.return_value = _manifest()
        repo.get_voice_plan.return_value = _voice()
        repo.get_generated_script.return_value = GeneratedScript(
            id="pj_os",
            script_job_id="pj_os",
            source_url="https://youtu.be/x",
            title="Video Titel",
            hook="Hook Line",
            chapters=[
                Chapter(title="Kapitel A", content=""),
                Chapter(title="Kapitel B", content=""),
            ],
            full_script="text",
            sources=[],
            warnings=[],
            word_count=10,
            created_at="z",
        )
        body, mt, fname, ws = watchlist_service.generate_export_download(
            "pj_os", "json", repo=repo
        )
        assert body is not None
        self.assertEqual(mt.split(";")[0].strip(), "application/json")
        self.assertTrue(fname.endswith(".json"))
        self.assertFalse(ws)
        data = json.loads(body.decode("utf-8"))
        self.assertIn("manifest", data)
        self.assertIn("provider_templates", data)
        pt = data["provider_templates"]
        self.assertIn("elevenlabs_ready", pt)
        self.assertEqual(pt["elevenlabs_ready"][0]["scene_number"], 1)
        self.assertEqual(pt["kling_ready"][0]["prompt"], "Videoprompt")
        self.assertEqual(pt["leonardo_ready"][0]["prompt"], "Bildprompt")
        self.assertEqual(pt["capcut_ready"]["timeline_order"], [1])
        self.assertEqual(pt["youtube_upload_ready"]["title"], "Video Titel")
        self.assertIn("Kapitel A", pt["youtube_upload_ready"]["tags"])

    def test_export_markdown_csv_txt(self):
        m = _manifest()
        tpl = build_provider_templates_dict(
            manifest=m,
            voice_plan=_voice(),
            production_job=_pj(),
            generated_script=None,
        )
        from app.watchlist.export_download import (
            build_csv_export,
            build_markdown_export,
            build_txt_export,
        )

        md = build_markdown_export(manifest=m, title="MD Title").decode("utf-8")
        self.assertIn("# MD Title", md)
        self.assertIn("## Szene 1", md)
        self.assertIn("Voice:", md)
        self.assertIn("Bildprompt", md)

        csv_b = build_csv_export(manifest=m).decode("utf-8-sig")
        lines = csv_b.strip().split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("scene_number", lines[0])
        self.assertIn("Voice Zeile", lines[1])

        txt = build_txt_export(manifest=m, title="CapCut").decode("utf-8")
        self.assertIn("CapCut", txt)
        self.assertIn("[1]", txt)
        self.assertIn("VO:", txt)

        self.assertTrue(tpl["elevenlabs_ready"])

    def test_export_404_missing_job(self):
        repo = MagicMock()
        repo.get_production_job.return_value = None
        body, _, _, warns = watchlist_service.generate_export_download(
            "missing", "json", repo=repo
        )
        self.assertIsNone(body)
        self.assertIn("Production job not found.", warns)

    def test_export_404_missing_manifest(self):
        repo = MagicMock()
        repo.get_production_job.return_value = _pj()
        repo.get_render_manifest.return_value = None
        body, _, _, warns = watchlist_service.generate_export_download(
            "pj_os", "json", repo=repo
        )
        self.assertIsNone(body)
        self.assertIn("Render manifest not found.", warns)


class ProviderTemplatesBa714(unittest.TestCase):
    def test_provider_templates_shapes(self):
        gs = GeneratedScript(
            id="x",
            script_job_id="x",
            source_url="",
            title="TT",
            hook="HH",
            chapters=[Chapter(title="tag1", content="")],
            full_script="",
            sources=[],
            warnings=[],
            word_count=1,
            created_at="z",
        )
        out = build_provider_templates_dict(
            manifest=_manifest(),
            voice_plan=_voice(),
            production_job=_pj(),
            generated_script=gs,
        )
        self.assertEqual(len(out["elevenlabs_ready"]), 1)
        self.assertEqual(out["elevenlabs_ready"][0]["voice_style"], "story")
        self.assertEqual(out["capcut_ready"]["duration_total"], 15)


class ChecklistBa714(unittest.TestCase):
    def test_initialize_idempotent_warning(self):
        repo = MagicMock()
        repo.get_production_job.return_value = _pj()
        existing = ProductionChecklist(
            id="pj_os",
            production_job_id="pj_os",
            script_ready=True,
            scene_plan_ready=True,
            scene_assets_ready=False,
            voice_plan_ready=False,
            render_manifest_ready=False,
            thumbnail_ready=False,
            editing_ready=False,
            upload_ready=False,
            published=False,
            notes="",
            created_at="a",
            updated_at="b",
        )
        repo.get_production_checklist.return_value = existing
        repo.get_generated_script.return_value = MagicMock()
        repo.get_scene_plan.return_value = MagicMock()
        repo.get_scene_assets.return_value = None
        repo.get_voice_plan.return_value = None
        repo.get_render_manifest.return_value = None

        out = watchlist_service.initialize_checklist("pj_os", repo=repo)
        self.assertIsNotNone(out.checklist)
        self.assertTrue(any("bereits" in w.lower() for w in out.warnings))
        repo.upsert_production_checklist.assert_called_once()

    def test_update_checklist_syncs_upload_ready(self):
        repo = MagicMock()
        repo.get_production_job.return_value = ProductionJob(
            id="pj_os",
            generated_script_id="pj_os",
            script_job_id="pj_os",
            status="voice_ready",
            narrator_style="",
            thumbnail_prompt="",
            created_at="a",
            updated_at="b",
        )
        repo.get_generated_script.return_value = MagicMock()
        repo.get_scene_plan.return_value = MagicMock()
        repo.get_scene_assets.return_value = MagicMock()
        repo.get_voice_plan.return_value = MagicMock()
        repo.get_render_manifest.return_value = MagicMock()

        existing = ProductionChecklist(
            id="pj_os",
            production_job_id="pj_os",
            script_ready=True,
            scene_plan_ready=True,
            scene_assets_ready=True,
            voice_plan_ready=True,
            render_manifest_ready=True,
            thumbnail_ready=False,
            editing_ready=False,
            upload_ready=False,
            published=False,
            notes="",
            created_at="a",
            updated_at="b",
        )
        repo.get_production_checklist.return_value = existing

        req = ProductionChecklistUpdateRequest(upload_ready=True)
        out = watchlist_service.update_checklist("pj_os", req, repo=repo)
        self.assertTrue(out.checklist.upload_ready)
        repo.patch_production_job.assert_called()
        patch_kw = repo.patch_production_job.call_args[0][1]
        self.assertEqual(patch_kw["status"], "upload_ready")


class StatusSyncBa714(unittest.TestCase):
    def test_compute_target_planning_then_voice(self):
        repo = MagicMock()
        repo.get_scene_plan.return_value = MagicMock()
        repo.get_scene_assets.return_value = None
        repo.get_voice_plan.return_value = None
        r = compute_target_production_status(
            current_status="queued",
            production_job_id="x",
            repo=repo,
            checklist=None,
        )
        self.assertEqual(r, "planning_ready")

        repo.get_scene_assets.return_value = MagicMock()
        r2 = compute_target_production_status(
            current_status="planning_ready",
            production_job_id="x",
            repo=repo,
            checklist=None,
        )
        self.assertEqual(r2, "assets_ready")

        repo.get_voice_plan.return_value = MagicMock()
        r3 = compute_target_production_status(
            current_status="assets_ready",
            production_job_id="x",
            repo=repo,
            checklist=None,
        )
        self.assertEqual(r3, "voice_ready")

    def test_sync_from_checklist_editing_ready(self):
        repo = MagicMock()
        repo.get_production_job.return_value = ProductionJob(
            id="pj_os",
            generated_script_id="pj_os",
            script_job_id="pj_os",
            status="voice_ready",
            narrator_style="",
            thumbnail_prompt="",
            created_at="a",
            updated_at="b",
        )
        repo.get_production_checklist.return_value = ProductionChecklist(
            id="pj_os",
            production_job_id="pj_os",
            script_ready=True,
            scene_plan_ready=True,
            scene_assets_ready=True,
            voice_plan_ready=True,
            render_manifest_ready=True,
            thumbnail_ready=False,
            editing_ready=True,
            upload_ready=False,
            published=False,
            notes="",
            created_at="a",
            updated_at="b",
        )
        repo.get_scene_plan.return_value = MagicMock()
        repo.get_scene_assets.return_value = MagicMock()
        repo.get_voice_plan.return_value = MagicMock()

        watchlist_service.sync_production_status_from_checklist("pj_os", repo=repo)
        repo.patch_production_job.assert_called_once()
        self.assertEqual(
            repo.patch_production_job.call_args[0][1]["status"], "editing_ready"
        )


class RoutesBa714(unittest.TestCase):
    def test_route_export_download_404_job(self):
        with patch.object(
            watchlist_service,
            "generate_export_download",
            return_value=(None, "", "", ["Production job not found."]),
        ):
            client = TestClient(app)
            r = client.get("/production/jobs/x/export/download?format=json")
            self.assertEqual(r.status_code, 404)

    def test_route_export_download_404_manifest(self):
        with patch.object(
            watchlist_service,
            "generate_export_download",
            return_value=(None, "", "", ["Render manifest not found."]),
        ):
            client = TestClient(app)
            r = client.get("/production/jobs/x/export/download?format=csv")
            self.assertEqual(r.status_code, 404)

