"""BA 10.4 — Provider Readiness."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class ProviderReadinessRouteTests(unittest.TestCase):
    def test_readiness_response_contract(self):
        client = TestClient(app)
        r = client.post(
            "/story-engine/provider-readiness",
            json={
                "video_template": "generic",
                "duration_minutes": 10,
                "title": "Titel",
                "topic": "Topic",
                "source_summary": "Zusammenfassung.",
                "provider_profile": "openai",
                "continuity_lock": True,
                "chapters": [
                    {"title": "A", "content": "Text genug für Blueprint. " * 10},
                    {"title": "B", "content": "Mehr Text hier. " * 12},
                ],
            },
        )
        self.assertEqual(r.status_code, 200, msg=r.text)
        data = r.json()
        for key in (
            "overall_status",
            "scores",
            "blocking_issues",
            "warnings",
            "recommended_next_step",
        ):
            self.assertIn(key, data)
        self.assertIn(data["overall_status"], ("ready", "partial_ready", "not_ready"))
        sc = data["scores"]
        for k in ("leonardo", "kling", "openai"):
            self.assertIn(k, sc)
            self.assertGreaterEqual(sc[k], 0)
            self.assertLessEqual(sc[k], 100)
        self.assertTrue(isinstance(data["recommended_next_step"], str))

    def test_readiness_no_scenes_not_ready(self):
        client = TestClient(app)
        r = client.post(
            "/story-engine/provider-readiness",
            json={"video_template": "generic", "chapters": []},
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["overall_status"], "not_ready")
        self.assertIn("blueprint:no_scenes", data["blocking_issues"])


if __name__ == "__main__":
    unittest.main()
