"""BA 10.5 — Thumbnail CTR."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class ThumbnailCTRRouteTests(unittest.TestCase):
    def test_thumbnail_ctr_contract(self):
        client = TestClient(app)
        r = client.post(
            "/story-engine/thumbnail-ctr",
            json={
                "title": "Was passiert wirklich?",
                "hook": "Kurzer Aufreger! Dann Fakten.",
                "video_template": "true_crime",
                "thumbnail_prompt": "x" * 130,
                "chapters": [{"title": "A", "content": "word " * 120}],
            },
        )
        self.assertEqual(r.status_code, 200, msg=r.text)
        data = r.json()
        self.assertIn("ctr_score", data)
        self.assertIn("thumbnail_variants", data)
        self.assertIn("warnings", data)
        self.assertGreaterEqual(data["ctr_score"], 0)
        self.assertLessEqual(data["ctr_score"], 100)
        self.assertEqual(len(data["thumbnail_variants"]), 3)
        v0 = data["thumbnail_variants"][0]
        self.assertIn("headline", v0)
        self.assertIn("overlay_text", v0)
        self.assertIn("emotion_type", v0)

    def test_thumbnail_ctr_deterministic(self):
        client = TestClient(app)
        body = {"title": "Heute: ein Update", "hook": "Hinweis?"}
        a = client.post("/story-engine/thumbnail-ctr", json=body).json()
        b = client.post("/story-engine/thumbnail-ctr", json=body).json()
        self.assertEqual(a["ctr_score"], b["ctr_score"])
        self.assertEqual(a["thumbnail_variants"], b["thumbnail_variants"])


if __name__ == "__main__":
    unittest.main()
