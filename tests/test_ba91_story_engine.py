"""BA 9.1 — Blueprints, Warning-Präfixe, Katalog-Endpoint."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.story_engine.conformance import (
    conformance_warnings_for_template,
    template_conformance_warning,
)
from app.story_engine.templates import (
    chapter_band_for_template_duration,
    public_story_template_catalog,
    story_template_blueprint_prompt_de,
)


class Ba91Blueprint(unittest.TestCase):
    def test_band_monotonic_longform(self):
        a = chapter_band_for_template_duration("true_crime", 6)
        b = chapter_band_for_template_duration("true_crime", 15)
        self.assertLessEqual(a[0], b[0])

    def test_blueprint_nonempty_for_format(self):
        self.assertIn("Kapitel", story_template_blueprint_prompt_de("true_crime", 10))
        self.assertIn("Kapitel", story_template_blueprint_prompt_de("documentary_story", 10))
        self.assertEqual(story_template_blueprint_prompt_de("generic", 10), "")

    def test_public_catalog_includes_documentary_and_real_estate(self):
        c = public_story_template_catalog()
        ids = {x["id"] for x in c}
        self.assertEqual(
            ids,
            {
                "generic",
                "true_crime",
                "mystery_explainer",
                "history_deep_dive",
                "documentary",
                "real_estate_story",
            },
        )
        for row in c:
            self.assertIn("duration_examples", row)
            self.assertGreaterEqual(len(row["duration_examples"]), 1)

    def test_warning_prefix_helper(self):
        s = template_conformance_warning("chapter_count", "Zu wenig.")
        self.assertTrue(s.startswith("[template_conformance:chapter_count]"))

    def test_chapter_too_few_warns(self):
        w = conformance_warnings_for_template(
            template_id="mystery_explainer",
            hook="Dies ist ein ausreichend langer Hook mit genug Wörtern hier.",
            chapters=[{"t": 1}],
            full_script="wort " * 800,
            duration_minutes=10,
        )
        self.assertTrue(
            any("[template_conformance:chapter_count]" in x for x in w), w
        )


class Ba91Http(unittest.TestCase):
    def test_get_templates(self):
        client = TestClient(app)
        r = client.get("/story-engine/templates")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("templates", data)
        self.assertEqual(len(data["templates"]), 6)


if __name__ == "__main__":
    unittest.main()
