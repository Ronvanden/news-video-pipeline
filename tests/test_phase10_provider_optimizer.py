"""BA 10.5 — Provider-Prompt-Optimize."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


_BODY = {
    "video_template": "generic",
    "duration_minutes": 10,
    "title": "Testtitel mit Frage?",
    "hook": "Ein Hook mit genug Wörtern hier drin.",
    "topic": "Thema",
    "source_summary": "Kurz.",
    "provider_profile": "leonardo",
    "continuity_lock": True,
    "chapters": [
        {"title": "Kapitel 1", "content": "Inhalt genug für eine Szene. " * 8},
        {"title": "Kapitel 2", "content": "Weiterer Inhalt. " * 12},
    ],
}


class ProviderOptimizerRouteTests(unittest.TestCase):
    def test_optimize_contract_and_leonardo_keywords(self):
        client = TestClient(app)
        r = client.post("/story-engine/provider-prompts/optimize", json=_BODY)
        self.assertEqual(r.status_code, 200, msg=r.text)
        data = r.json()
        for key in (
            "provider_profile",
            "optimized_prompts",
            "thumbnail_variants",
            "capcut_shotlist",
            "csv_shotlist",
            "warnings",
        ):
            self.assertIn(key, data)
        self.assertEqual(data["provider_profile"], "leonardo")
        op = data["optimized_prompts"]
        for k in ("leonardo", "kling", "openai"):
            self.assertIn(k, op)
        self.assertEqual(len(op["leonardo"]), 2)
        leo0 = op["leonardo"][0]["positive_optimized"].lower()
        self.assertIn("photoreal", leo0)
        self.assertIn("continuity", leo0)
        k0 = op["kling"][0]
        for fld in ("motion_prompt", "camera_path", "transition_hint"):
            self.assertIn(fld, k0)
            self.assertTrue(isinstance(k0[fld], str))
        self.assertEqual(len(data["capcut_shotlist"]), 2)
        self.assertEqual(len(data["csv_shotlist"]), 2)
        self.assertEqual(len(data["thumbnail_variants"]), 3)

    def test_optimize_deterministic_twice(self):
        client = TestClient(app)
        a = client.post("/story-engine/provider-prompts/optimize", json=_BODY).json()
        b = client.post("/story-engine/provider-prompts/optimize", json=_BODY).json()
        self.assertEqual(a["optimized_prompts"], b["optimized_prompts"])
        self.assertEqual(a["capcut_shotlist"], b["capcut_shotlist"])

    def test_openai_sanitized_term(self):
        client = TestClient(app)
        body = dict(_BODY)
        body["chapters"] = [
            {
                "title": "X",
                "content": "The scene mentions blood on the floor as metaphor. " * 6,
            },
        ]
        r = client.post("/story-engine/provider-prompts/optimize", json=body)
        self.assertEqual(r.status_code, 200)
        o0 = r.json()["optimized_prompts"]["openai"][0]["positive_optimized"].lower()
        self.assertNotIn("blood", o0)
        self.assertIn("muted documentary red accent", o0)


if __name__ == "__main__":
    unittest.main()
