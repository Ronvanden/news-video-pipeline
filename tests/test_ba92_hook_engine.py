"""BA 9.2 — Hook Engine V1 (regelbasiert, Nebenkanal)."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.story_engine.hook_engine import generate_hook_v1


class Ba92HookCore(unittest.TestCase):
    def test_true_crime_vermisst_shock_reveal(self):
        r = generate_hook_v1(
            video_template="true_crime",
            topic="Vermisstenfall",
            title="Verschwundener Mann — Spurensuche nach 14 Jahren",
            source_summary="Die Familie sucht weiterhin nach Hinweisen. Die Polizei bestätigt nur wenig.",
        )
        self.assertEqual(r.hook_type, "shock_reveal")
        self.assertEqual(r.template_match, "true_crime")
        self.assertGreaterEqual(r.hook_score, 6.0)
        self.assertIn("Wendung", r.hook_text)

    def test_history_potsdam_forgotten_power(self):
        r = generate_hook_v1(
            video_template="history_deep_dive",
            topic="Stadtbild",
            title="Das Rote Haus in Potsdam",
            source_summary="Ein Gebäude, das oft übersehen wird, obwohl es politische Spuren trägt.",
        )
        self.assertEqual(r.hook_type, "forgotten_power")
        self.assertEqual(r.template_match, "history_deep_dive")
        self.assertIn("Gebäude", r.hook_text)

    def test_unknown_template_generic_curiosity_warning(self):
        r = generate_hook_v1(
            video_template="not_a_valid_template",
            topic="Straße ins Nichts",
            title="Mystery ohne klare Zuordnung",
            source_summary="Viele Fragen, wenig Antworten.",
        )
        self.assertEqual(r.template_match, "generic")
        self.assertEqual(r.hook_type, "generic_curiosity")
        self.assertTrue(any("Unbekanntes video_template" in w for w in r.warnings))

    def test_documentary_story_no_unknown_template_warning(self):
        r = generate_hook_v1(
            video_template="documentary_story",
            topic="Report",
            title="Chronik einer Entscheidung",
            source_summary="Die Zeitlinie zeigt mehrere Wendepunkte.",
        )
        self.assertEqual(r.template_match, "documentary")
        self.assertFalse(any("Unbekanntes video_template" in w for w in r.warnings))
        self.assertIn(r.hook_type, ("forgotten_power", "timeline_twist"))


class Ba92Http(unittest.TestCase):
    def test_post_generate_hook(self):
        c = TestClient(app)
        r = c.post(
            "/story-engine/generate-hook",
            json={
                "video_template": "mystery_explainer",
                "topic": "Straße ins Nichts",
                "title": "Warum endet die Straße plötzlich?",
                "source_summary": "Anwohner berichten von seltsamen Kartenfehlern.",
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        d = r.json()
        self.assertIn(d["hook_type"], ("question_gap", "unexplained_event"))
        self.assertGreaterEqual(d["hook_score"], 6.0)
        self.assertIn("hook_text", d)


if __name__ == "__main__":
    unittest.main()
