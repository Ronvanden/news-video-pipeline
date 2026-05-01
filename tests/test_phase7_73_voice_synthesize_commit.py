"""Phase 7.3–7.4 — Voice-Synthese-Commit (`production_files`) und dünn zusammenhängende Checks."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.watchlist import service as watchlist_service
from app.watchlist.firestore_repo import FirestoreUnavailableError
from app.watchlist.models import (
    ProductionFileRecord,
    ProductionJob,
    Scene,
    SceneAssetItem,
    SceneAssets,
    ScenePlan,
    VoiceBlock,
    VoicePlan,
    VoiceSynthCommitRequest,
    VoiceSynthCommitResponse,
)
from app.watchlist.pipeline_audit_scan import scan_production_job_for_issues
from app.voice.contracts import VoiceSynthRequest
from tests.test_phase7_72_voice_provider_contract import QuietProvider


def _vp_two_blocks(pid: str = "pj1"):
    return VoicePlan(
        id=pid,
        production_job_id=pid,
        scene_assets_id=pid,
        generated_script_id=pid,
        script_job_id=pid,
        voice_profile="documentary",
        status="ready",
        voice_version=1,
        blocks=[
            VoiceBlock(
                scene_number=1,
                title="A",
                voice_text="Erster Block.",
                tts_provider_hint="openai",
            ),
            VoiceBlock(
                scene_number=2,
                title="B",
                voice_text="Zweiter Block.",
                tts_provider_hint="openai",
            ),
        ],
        warnings=[],
        created_at="",
        updated_at="",
    )


def _blank_row(*, doc_id: str, pid: str, sn: int) -> ProductionFileRecord:
    return ProductionFileRecord(
        id=doc_id,
        production_job_id=pid,
        file_type="voice",
        storage_path=f"voice/{pid}/scene_{sn:03d}.mp3",
        public_url="",
        status="planned",
        provider_name="openai",
        scene_number=sn,
        synthesis_byte_length=0,
        created_at="2026-01-01",
        updated_at="2026-01-01",
    )


class Phase73Commit(unittest.TestCase):
    def test_skipped_ready_when_no_overwrite(self):
        repo = MagicMock()
        repo.get_voice_plan.return_value = _vp_two_blocks()

        rid = watchlist_service._production_file_doc_id("pj1", "voice", 1)
        ready = ProductionFileRecord(
            id=rid,
            production_job_id="pj1",
            file_type="voice",
            storage_path="voice/pj1/scene_001.mp3",
            public_url="",
            status="ready",
            provider_name="openai",
            scene_number=1,
            synthesis_byte_length=128,
            created_at="a",
            updated_at="b",
        )

        def _get(cid: str):
            if cid == rid:
                return ready
            return None

        repo.get_production_file_by_id.side_effect = lambda x: _get(str(x))

        body, status = watchlist_service.synthesize_voice_commit(
            "pj1",
            VoiceSynthCommitRequest(max_blocks=1, overwrite=False, dry_run=False),
            repo=repo,
            provider=QuietProvider(blob=b"z"),
        )
        self.assertEqual(status, 200)
        repo.upsert_production_file.assert_not_called()
        self.assertTrue(any("skipped_ready" in w for w in body.warnings))
        self.assertEqual(body.scenes[0].file_status, "ready")
        self.assertEqual(body.scenes[0].synthesis_byte_length, 128)

    def test_commit_writes_ready_bytes(self):
        repo = MagicMock()
        vp = VoicePlan(
            id="pj1",
            production_job_id="pj1",
            scene_assets_id="pj1",
            generated_script_id="pj1",
            script_job_id="pj1",
            voice_profile="documentary",
            status="ready",
            voice_version=1,
            blocks=[
                VoiceBlock(
                    scene_number=7,
                    title="Z",
                    voice_text="Hallöchen.",
                    tts_provider_hint="openai",
                )
            ],
            warnings=[],
            created_at="",
            updated_at="",
        )
        repo.get_voice_plan.return_value = vp

        sid = watchlist_service._production_file_doc_id("pj1", "voice", 7)
        repo.get_production_file_by_id.return_value = None

        blob = b"pulse"
        body, status = watchlist_service.synthesize_voice_commit(
            "pj1",
            VoiceSynthCommitRequest(max_blocks=3, overwrite=True, dry_run=False),
            repo=repo,
            provider=QuietProvider(blob=blob),
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(body.scenes), 1)
        self.assertEqual(body.scenes[0].synthesis_byte_length, len(blob))
        self.assertEqual(body.scenes[0].production_file_id, sid)
        self.assertEqual(body.scenes[0].file_status, "ready")
        repo.upsert_production_file.assert_called_once()
        saved = repo.upsert_production_file.call_args[0][0]
        self.assertEqual(saved.status, "ready")
        self.assertEqual(saved.synthesis_byte_length, len(blob))

    def test_dry_run_resets_without_ready_meta(self):
        repo = MagicMock()
        repo.get_voice_plan.return_value = _vp_two_blocks()

        repo.get_production_file_by_id.return_value = None

        body, status = watchlist_service.synthesize_voice_commit(
            "pj1",
            VoiceSynthCommitRequest(max_blocks=1, dry_run=True),
            repo=repo,
            provider=None,
        )
        self.assertEqual(status, 200)
        self.assertTrue(repo.upsert_production_file.called)
        self.assertEqual(body.scenes[0].synthesis_byte_length, 0)
        self.assertTrue(any("voice_commit:dry_run" in w for w in body.warnings))

    @patch("app.watchlist.service.decide_manifest_status", return_value="incomplete")
    @patch("app.watchlist.service.build_timeline", return_value=([], 0))
    def test_render_manifest_voice_refs_sorted(self, _bt, _dm):
        repo = MagicMock()
        pid = "jobz"
        repo.get_render_manifest.return_value = None
        pj = ProductionJob(
            id=pid,
            generated_script_id="gs1",
            script_job_id="sj1",
            status="voice_ready",
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )
        repo.get_production_job.return_value = pj
        sp = ScenePlan(
            id=pid,
            production_job_id=pid,
            generated_script_id="gs1",
            script_job_id="sj1",
            scenes=[Scene(scene_number=1, title="Eins")],
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )
        sa = SceneAssets(
            id=pid,
            production_job_id=pid,
            scene_plan_id=pid,
            generated_script_id="gs1",
            script_job_id="sj1",
            scenes=[SceneAssetItem(scene_number=1, title="Eins")],
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )
        repo.get_scene_assets.return_value = sa
        repo.get_scene_plan.return_value = sp
        repo.get_voice_plan.return_value = None
        mf1 = ProductionFileRecord(
            id=f"pfile_{pid}_voice_0005",
            production_job_id=pid,
            file_type="voice",
            storage_path=f"voice/{pid}/scene_005.mp3",
            public_url="",
            status="planned",
            provider_name="openai",
            scene_number=5,
            synthesis_byte_length=0,
            created_at="",
            updated_at="",
        )
        mf2 = ProductionFileRecord(
            id=f"pfile_{pid}_voice_0002",
            production_job_id=pid,
            file_type="voice",
            storage_path=f"voice/{pid}/scene_002.mp3",
            public_url="",
            status="ready",
            provider_name="openai",
            scene_number=2,
            synthesis_byte_length=12,
            created_at="",
            updated_at="",
        )
        repo.list_production_files_for_job.return_value = [
            mf1,
            mf2,
            ProductionFileRecord(
                id=f"pfile_{pid}_export_json_0000",
                production_job_id=pid,
                file_type="export_json",
                storage_path=f"exports/{pid}/production.json",
                status="planned",
                provider_name="generic",
                scene_number=0,
                created_at="",
                updated_at="",
            ),
        ]

        resp = watchlist_service.generate_render_manifest(pid, repo=repo)

        refs = resp.render_manifest.voice_production_file_refs
        self.assertEqual([r.scene_number for r in refs], [2, 5])
        self.assertEqual(refs[1].production_file_status, "planned")


class Phase73AuditVoiceFiles(unittest.TestCase):
    def _repo_base(self):
        repo = MagicMock()
        vp = _vp_two_blocks("p_audit")
        repo.get_voice_plan.return_value = vp
        repo.get_scene_plan.return_value = MagicMock()
        repo.get_scene_assets.return_value = MagicMock()
        repo.get_render_manifest.return_value = MagicMock()
        repo.get_production_checklist.return_value = None
        repo.get_generated_script.return_value = MagicMock()
        repo.get_production_costs.return_value = MagicMock()
        repo.list_execution_jobs_for_job.return_value = [MagicMock()]
        return repo

    def test_audit_missing_voice_production_files_row(self):
        repo = self._repo_base()
        repo.list_production_files_for_job.return_value = []

        drafts = scan_production_job_for_issues(
            repo,
            pj_id="p_audit",
            pj_status="voice_ready",
            generated_script_ref="g9",
        )
        types = {d.audit_type for d in drafts}
        self.assertIn("missing_voice_production_files", types)

    def test_audit_voice_rows_not_ready(self):
        repo = self._repo_base()
        repo.list_production_files_for_job.return_value = [
            _blank_row(
                doc_id="pfile_p_audit_voice_0001",
                pid="p_audit",
                sn=1,
            ),
            _blank_row(
                doc_id="pfile_p_audit_voice_0002",
                pid="p_audit",
                sn=2,
            ),
        ]

        drafts = scan_production_job_for_issues(
            repo,
            pj_id="p_audit",
            pj_status="voice_ready",
            generated_script_ref="g9",
        )
        types = {d.audit_type for d in drafts}
        self.assertIn("voice_production_files_not_ready", types)


class Phase73RouteSmoke(unittest.TestCase):
    def test_route_503_firestore(self):
        with patch.object(
            watchlist_service,
            "synthesize_voice_commit",
            side_effect=FirestoreUnavailableError("down"),
        ):
            client = TestClient(app)
            r = client.post("/production/jobs/pj1/voice/synthesize", json={})
            self.assertEqual(r.status_code, 503)

    def test_route_404_json(self):
        with patch.object(
            watchlist_service,
            "synthesize_voice_commit",
            return_value=(
                VoiceSynthCommitResponse(scenes=[], warnings=["x"]),
                404,
            ),
        ):
            client = TestClient(app)
            r = client.post("/production/jobs/pj1/voice/synthesize", json={})
            self.assertEqual(r.status_code, 404)
            data = r.json()
            self.assertIn("warnings", data)
            self.assertIn("scenes", data)


class Phase73CostsVoiceWarnings(unittest.TestCase):
    def test_partial_voice_warning_when_rows_incomplete(self):
        from app.watchlist.cost_calculator import build_production_costs_document
        from app.watchlist.models import GeneratedScript, ProductionJob

        pj = ProductionJob(
            id="pj_cost_voice",
            generated_script_id="pj_cost_voice",
            script_job_id="sj99",
            status="queued",
            created_at="2026-04-30T10:00:00Z",
            updated_at="2026-04-30T10:00:00Z",
        )
        repo = MagicMock()
        gs = GeneratedScript(
            id="pj_cost_voice",
            script_job_id="sj99",
            source_url="u",
            title="t",
            hook="h",
            chapters=[],
            full_script=("word ") * 200,
            warnings=[],
            word_count=200,
            created_at="c",
        )
        spa = MagicMock()
        spa.scenes = [MagicMock(), MagicMock()]
        repo.get_generated_script.return_value = gs
        repo.get_scene_assets.return_value = spa
        repo.get_voice_plan.return_value = _vp_two_blocks("pj_cost_voice")
        repo.list_production_files_for_job.return_value = [
            ProductionFileRecord(
                id="pfile_pj_cost_voice_voice_0001",
                production_job_id="pj_cost_voice",
                file_type="voice",
                storage_path="x",
                status="planned",
                provider_name="openai",
                scene_number=1,
                synthesis_byte_length=0,
                created_at="",
                updated_at="",
            ),
        ]

        doc = build_production_costs_document(
            repo=repo, pj=pj, now_iso="2026-04-30T12:00:00Z"
        )
        joined = "\n".join(doc.warnings)
        self.assertIn("costs:voice_partial", joined)


class Phase73QuietProviderSynth(unittest.TestCase):
    """Stellt sicher, dass neue warning_codes Konstanten weiterhin Teilstrings der Meldungen sind."""

    def test_quiet_returns_bytes_without_extra_warns(self):
        p = QuietProvider(blob=b"ok")
        r = p.synthesize(VoiceSynthRequest(text="hallo"))
        self.assertEqual(r.audio_bytes, b"ok")
        self.assertFalse(r.warnings)


if __name__ == "__main__":
    unittest.main()
