"""BA 10.4 — Export-Paket Preview."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class ExportPreviewRouteTests(unittest.TestCase):
    def test_preview_shape_and_stable_keys(self):
        client = TestClient(app)
        r = client.post(
            "/story-engine/export-package/preview",
            json={
                "video_template": "true_crime",
                "duration_minutes": 10,
                "title": "Testtitel",
                "topic": "Thema",
                "source_summary": "Kurz.",
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
            "template_id",
            "hook_score",
            "hook_type",
            "thumbnail_strength",
            "prompt_quality_score",
            "scene_count",
            "provider_profiles",
            "provider_stub_warnings",
            "readiness_status",
            "top_warnings",
            "export_ready",
        ):
            self.assertIn(key, data, msg=key)
        self.assertEqual(data["template_id"], "true_crime")
        self.assertIn(data["thumbnail_strength"], ("low", "medium", "high"))
        self.assertIn(data["readiness_status"], ("ready", "partial_ready", "not_ready"))
        pp = data["provider_profiles"]
        self.assertIn("openai", pp)
        self.assertIn("leonardo", pp)
        self.assertIn("kling", pp)
        self.assertIsInstance(pp["openai"], bool)

    def test_preview_empty_chapters_not_ready(self):
        client = TestClient(app)
        r = client.post(
            "/story-engine/export-package/preview",
            json={"video_template": "generic", "chapters": []},
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["scene_count"], 0)
        self.assertFalse(data["export_ready"])


if __name__ == "__main__":
    unittest.main()
