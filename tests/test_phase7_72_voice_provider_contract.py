"""Phase 7.2 — VoiceSynthProvider-Vertrag, OpenAI-Adapter, Preview-Service und Route."""

from __future__ import annotations

import base64
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.voice.contracts import VoiceSynthChunkResult, VoiceSynthRequest
from app.voice.openai_tts import OpenAiTtsProvider
from app.watchlist import service as watchlist_service
from app.watchlist.firestore_repo import FirestoreUnavailableError
from app.watchlist.models import (
    VoiceBlock,
    VoicePlan,
    VoiceSynthPreviewRequest,
    VoiceSynthPreviewResponse,
)


def _vp(pid: str = "pj1", *, blocks=None, status="ready", hint="openai"):
    return VoicePlan(
        id=pid,
        production_job_id=pid,
        scene_assets_id=pid,
        generated_script_id=pid,
        script_job_id=pid,
        voice_profile="documentary",
        status=status,
        voice_version=1,
        blocks=blocks
        if blocks is not None
        else [
            VoiceBlock(
                scene_number=1,
                title="A",
                voice_text="Hallo Test.",
                tts_provider_hint=hint,
            )
        ],
        warnings=[],
        created_at="",
        updated_at="",
    )


class QuietProvider:
    """Strukturell VoiceSynthProvider — liefert feste Audiobytes für Tests."""

    def __init__(self, blob: bytes = b"x"):
        self._blob = blob

    def synthesize(self, request: VoiceSynthRequest) -> VoiceSynthChunkResult:
        return VoiceSynthChunkResult(audio_bytes=self._blob, mime_type="audio/mpeg")


class Phase72OpenAiAdapter(unittest.TestCase):
    def test_missing_key_returns_warning(self):
        p = OpenAiTtsProvider("", default_voice="alloy", default_model="tts-1")
        r = p.synthesize(VoiceSynthRequest(text="Hi"))
        self.assertFalse(r.audio_bytes)
        self.assertTrue(any("missing_api_key" in w for w in r.warnings))

    def test_empty_text(self):
        p = OpenAiTtsProvider("sk-x", default_voice="alloy", default_model="tts-1")
        r = p.synthesize(VoiceSynthRequest(text="   "))
        self.assertFalse(r.audio_bytes)
        self.assertTrue(any("empty_text" in w for w in r.warnings))

    def test_mock_http_200(self):
        with patch("httpx.Client") as CC:
            inst = MagicMock()
            CM = MagicMock()
            CC.return_value = CM
            CM.__enter__.return_value = inst
            post_resp = MagicMock()
            post_resp.status_code = 200
            post_resp.content = b"mp3data"
            inst.post.return_value = post_resp

            p = OpenAiTtsProvider("sk-test", default_voice="alloy", default_model="tts-1")
            r = p.synthesize(VoiceSynthRequest(text="Say hi"))
            self.assertEqual(r.audio_bytes, b"mp3data")
            inst.post.assert_called_once()

    def test_mock_http_429(self):
        with patch("httpx.Client") as CC:
            inst = MagicMock()
            CM = MagicMock()
            CC.return_value = CM
            CM.__enter__.return_value = inst
            inst.post.return_value = MagicMock(status_code=429, content=b"")
            p = OpenAiTtsProvider("sk-test", default_voice="alloy", default_model="tts-1")
            r = p.synthesize(VoiceSynthRequest(text="Hi"))
            self.assertFalse(r.audio_bytes)
            self.assertTrue(any("openai_http_error" in w for w in r.warnings))


class Phase72ServicePreview(unittest.TestCase):
    def test_dry_run_no_external_synth(self):
        repo = MagicMock()
        repo.get_voice_plan.return_value = _vp()
        tracked = QuietProvider(blob=b"y")

        body, status = watchlist_service.synthesize_voice_plan_preview(
            "pj1",
            VoiceSynthPreviewRequest(dry_run=True),
            repo=repo,
            provider=tracked,
        )
        self.assertEqual(status, 200)
        self.assertEqual(body.chunks[0].byte_length, 0)
        self.assertTrue(any("dry_run" in w for w in body.warnings))

    def test_missing_voice_plan_404(self):
        repo = MagicMock()
        repo.get_voice_plan.return_value = None
        body, status = watchlist_service.synthesize_voice_plan_preview(
            "pj1",
            VoiceSynthPreviewRequest(),
            repo=repo,
        )
        self.assertEqual(status, 404)
        self.assertFalse(body.chunks)
        self.assertTrue(any("voice_plan_missing" in w for w in body.warnings))

    def test_empty_pid_404(self):
        repo = MagicMock()
        body, status = watchlist_service.synthesize_voice_plan_preview(
            "   ",
            VoiceSynthPreviewRequest(),
            repo=repo,
        )
        self.assertEqual(status, 404)
        self.assertFalse(body.chunks)
        repo.get_voice_plan.assert_not_called()

    def test_empty_blocks_404(self):
        repo = MagicMock()
        repo.get_voice_plan.return_value = _vp(blocks=[])
        body, status = watchlist_service.synthesize_voice_plan_preview(
            "pj1",
            VoiceSynthPreviewRequest(),
            repo=repo,
        )
        self.assertEqual(status, 404)
        self.assertTrue(any("no_blocks" in w for w in body.warnings))

    def test_non_openai_hint_warning(self):
        repo = MagicMock()
        repo.get_voice_plan.return_value = _vp(hint="elevenlabs")

        body, status = watchlist_service.synthesize_voice_plan_preview(
            "pj1",
            VoiceSynthPreviewRequest(dry_run=False),
            repo=repo,
            provider=QuietProvider(),
        )
        self.assertEqual(status, 200)
        self.assertTrue(any("provider_hint_ignored" in w for w in body.warnings))

    def test_missing_api_key_via_openai_adapter_200(self):
        repo = MagicMock()
        repo.get_voice_plan.return_value = _vp()
        body, status = watchlist_service.synthesize_voice_plan_preview(
            "pj1",
            VoiceSynthPreviewRequest(dry_run=False),
            repo=repo,
            provider=OpenAiTtsProvider("", default_voice="alloy", default_model="tts-1"),
        )
        self.assertEqual(status, 200)
        self.assertEqual(body.chunks[0].byte_length, 0)
        self.assertTrue(any("missing_api_key" in w for w in body.warnings))

    def test_failed_status_warning(self):
        repo = MagicMock()
        vp = VoicePlan(
            id="pj1",
            production_job_id="pj1",
            scene_assets_id="pj1",
            generated_script_id="pj1",
            script_job_id="pj1",
            voice_profile="documentary",
            status="failed",
            voice_version=1,
            blocks=[
                VoiceBlock(
                    scene_number=1,
                    title="X",
                    voice_text="Ein Satz.",
                    tts_provider_hint="openai",
                )
            ],
        )
        repo.get_voice_plan.return_value = vp
        body, status = watchlist_service.synthesize_voice_plan_preview(
            "pj1",
            VoiceSynthPreviewRequest(dry_run=True),
            repo=repo,
            provider=None,
        )
        self.assertEqual(status, 200)
        self.assertTrue(any("voice_plan_status_failed" in w for w in body.warnings))

    def test_base64_when_flag_enabled_under_cap(self):
        repo = MagicMock()
        repo.get_voice_plan.return_value = _vp()
        prev_b = settings.enable_voice_synth_preview_body
        prev_mb = settings.voice_synth_preview_max_bytes
        try:
            settings.enable_voice_synth_preview_body = True
            settings.voice_synth_preview_max_bytes = 8192
            body, status = watchlist_service.synthesize_voice_plan_preview(
                "pj1",
                VoiceSynthPreviewRequest(dry_run=False),
                repo=repo,
                provider=QuietProvider(blob=b"XYZ"),
            )
            self.assertEqual(status, 200)
            self.assertIsNotNone(body.chunks[0].audio_base64)
            self.assertEqual(
                body.chunks[0].audio_base64,
                base64.standard_b64encode(b"XYZ").decode("ascii"),
            )
        finally:
            settings.enable_voice_synth_preview_body = prev_b
            settings.voice_synth_preview_max_bytes = prev_mb

    def test_base64_omitted_over_limit_warning(self):
        repo = MagicMock()
        repo.get_voice_plan.return_value = _vp()
        big = b"z" * 4000

        prev_b = settings.enable_voice_synth_preview_body
        prev_mb = settings.voice_synth_preview_max_bytes
        try:
            settings.enable_voice_synth_preview_body = True
            settings.voice_synth_preview_max_bytes = 100
            body, status = watchlist_service.synthesize_voice_plan_preview(
                "pj1",
                VoiceSynthPreviewRequest(dry_run=False),
                repo=repo,
                provider=QuietProvider(blob=big),
            )
            self.assertEqual(status, 200)
            self.assertIsNone(body.chunks[0].audio_base64)
            self.assertEqual(body.chunks[0].byte_length, len(big))
            self.assertTrue(any("preview_audio_omitted" in w for w in body.warnings))
        finally:
            settings.enable_voice_synth_preview_body = prev_b
            settings.voice_synth_preview_max_bytes = prev_mb

    def test_default_meta_only_no_base64_when_flag_false(self):
        repo = MagicMock()
        repo.get_voice_plan.return_value = _vp()
        prev_b = settings.enable_voice_synth_preview_body
        try:
            settings.enable_voice_synth_preview_body = False
            body, status = watchlist_service.synthesize_voice_plan_preview(
                "pj1",
                VoiceSynthPreviewRequest(dry_run=False),
                repo=repo,
                provider=QuietProvider(blob=b"ABC"),
            )
            self.assertEqual(status, 200)
            self.assertIsNone(body.chunks[0].audio_base64)
            self.assertEqual(body.chunks[0].byte_length, 3)
        finally:
            settings.enable_voice_synth_preview_body = prev_b


class Phase72RouteSmoke(unittest.TestCase):
    def test_health_unchanged(self):
        client = TestClient(app)
        r = client.get("/health")
        self.assertEqual(r.status_code, 200)

    def test_route_404_returns_json_payload(self):
        with patch.object(
            watchlist_service,
            "synthesize_voice_plan_preview",
            return_value=(
                VoiceSynthPreviewResponse(chunks=[], warnings=["[voice_synth:test]"]),
                404,
            ),
        ):
            client = TestClient(app)
            r = client.post("/production/jobs/pj1/voice/synthesize-preview", json={})
            self.assertEqual(r.status_code, 404)
            data = r.json()
            self.assertIn("chunks", data)
            self.assertIn("warnings", data)

    def test_route_503_firestore(self):
        with patch.object(
            watchlist_service,
            "synthesize_voice_plan_preview",
            side_effect=FirestoreUnavailableError("down"),
        ):
            client = TestClient(app)
            r = client.post("/production/jobs/pj1/voice/synthesize-preview", json={})
            self.assertEqual(r.status_code, 503)


if __name__ == "__main__":
    unittest.main()
