"""BA 10.4 — Template-Selector Registry."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class TemplateSelectorRouteTests(unittest.TestCase):
    def test_selector_lists_six_templates(self):
        client = TestClient(app)
        r = client.get("/story-engine/template-selector")
        self.assertEqual(r.status_code, 200, msg=r.text)
        data = r.json()
        self.assertIn("templates", data)
        self.assertEqual(len(data["templates"]), 6)
        ids = [t["template_id"] for t in data["templates"]]
        self.assertEqual(
            ids[0],
            "generic",
            msg="Stabile Reihenfolge: generic zuerst.",
        )
        for tid in (
            "generic",
            "true_crime",
            "mystery_explainer",
            "history_deep_dive",
            "breaking_news",
            "philosophy",
        ):
            self.assertIn(tid, ids)
        row = data["templates"][1]
        for k in ("label", "style", "ideal_use_case", "hook_bias", "pacing_bias"):
            self.assertIn(k, row)
            self.assertTrue((row[k] or "").strip(), msg=k)


if __name__ == "__main__":
    unittest.main()
