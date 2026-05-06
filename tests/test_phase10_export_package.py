"""BA 10.3 — Export-Paket Endpoint."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class ExportPackageRouteTests(unittest.TestCase):
    def test_export_package_keys_and_providers(self):
        client = TestClient(app)
        r = client.post(
            "/story-engine/export-package",
            json={
                "video_template": "generic",
                "duration_minutes": 10,
                "title": "Testtitel",
                "topic": "Thema",
                "source_summary": "Kurz zusammengefasst.",
                "provider_profile": "openai",
                "continuity_lock": True,
                "chapters": [
                    {"title": "Kapitel 1", "content": "Inhalt genug für eine Szene. " * 8},
                    {"title": "Kapitel 2", "content": "Weiterer Inhalt. " * 10},
                ],
            },
        )
        self.assertEqual(r.status_code, 200, msg=r.text)
        data = r.json()
        for key in (
            "hook",
            "rhythm",
            "scene_plan",
            "scene_prompts",
            "provider_prompts",
            "thumbnail_prompt",
            "prompt_quality",
            "warnings",
        ):
            self.assertIn(key, data, msg=f"missing {key}")
        pp = data["provider_prompts"]
        self.assertIn("leonardo", pp)
        self.assertIn("openai", pp)
        self.assertIn("kling", pp)
        self.assertEqual(len(pp["openai"]), len(data["scene_prompts"]["scenes"]))
        self.assertIsNotNone(data["scene_prompts"].get("prompt_quality"))
        self.assertEqual(
            data["prompt_quality"]["summary"],
            data["scene_prompts"]["prompt_quality"]["summary"],
        )

    def test_export_empty_chapters_still_200(self):
        client = TestClient(app)
        r = client.post(
            "/story-engine/export-package",
            json={
                "video_template": "generic",
                "chapters": [],
                "provider_profile": "kling",
            },
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["scene_plan"]["scenes"], [])
        self.assertEqual(data["provider_prompts"]["kling"], [])


if __name__ == "__main__":
    unittest.main()
