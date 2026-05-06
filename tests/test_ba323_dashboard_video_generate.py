"""BA 32.3 — Founder Dashboard POST /founder/dashboard/video/generate."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class Ba323VideoGenerateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_missing_url_body_422(self) -> None:
        r = self.client.post("/founder/dashboard/video/generate", json={})
        self.assertEqual(r.status_code, 422)

    def test_blank_url_422(self) -> None:
        r = self.client.post("/founder/dashboard/video/generate", json={"url": "   "})
        self.assertEqual(r.status_code, 422)

    def test_live_assets_without_cost_confirm_422(self) -> None:
        r = self.client.post(
            "/founder/dashboard/video/generate",
            json={
                "url": "https://example.com/article",
                "allow_live_assets": True,
                "confirm_provider_costs": False,
            },
        )
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json().get("detail"), "confirm_provider_costs_required_when_live_flags")

    def test_live_motion_without_runway_422(self) -> None:
        with patch.dict(os.environ, {"RUNWAY_API_KEY": ""}, clear=False):
            r = self.client.post(
                "/founder/dashboard/video/generate",
                json={
                    "url": "https://example.com/article",
                    "allow_live_motion": True,
                    "confirm_provider_costs": True,
                },
            )
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.json().get("detail"), "live_motion_requires_runway_connector")

    @patch("app.routes.founder_dashboard.execute_dashboard_video_generate")
    def test_forwards_duration_and_scene_caps(self, mock_exec) -> None:
        mock_exec.return_value = {
            "ok": True,
            "run_id": "video_gen_10m_test",
            "output_dir": "/tmp/out",
            "final_video_path": "/tmp/final.mp4",
            "script_path": "/tmp/script.json",
            "scene_asset_pack_path": "/tmp/pack.json",
            "asset_manifest_path": "/tmp/manifest.json",
            "duration_target_seconds": 600,
            "max_scenes": 24,
            "max_live_assets": 24,
            "motion_strategy": {},
            "warnings": [],
            "blocking_reasons": [],
            "next_action": "Final Video prüfen",
        }
        r = self.client.post(
            "/founder/dashboard/video/generate",
            json={"url": "https://example.com/a", "duration_target_seconds": 600, "max_scenes": 24},
        )
        self.assertEqual(r.status_code, 200, msg=r.text)
        mock_exec.assert_called_once()
        kw = mock_exec.call_args.kwargs
        self.assertEqual(kw["duration_target_seconds"], 600)
        self.assertEqual(kw["max_scenes"], 24)
        self.assertEqual(kw["max_live_assets"], 24)

    @patch("app.routes.founder_dashboard.execute_dashboard_video_generate")
    def test_response_includes_version(self, mock_exec) -> None:
        mock_exec.return_value = {
            "ok": False,
            "run_id": "x",
            "output_dir": "",
            "final_video_path": "",
            "script_path": "",
            "scene_asset_pack_path": "",
            "asset_manifest_path": None,
            "duration_target_seconds": 600,
            "max_scenes": 24,
            "max_live_assets": 24,
            "motion_strategy": {"live_motion_available": False},
            "warnings": [],
            "blocking_reasons": ["x"],
            "next_action": "Fehler prüfen",
        }
        r = self.client.post("/founder/dashboard/video/generate", json={"url": "https://example.com/b"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("video_generate_version"), "ba32_3_v1")


if __name__ == "__main__":
    unittest.main()
