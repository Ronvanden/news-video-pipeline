"""Smoke tests for POST /review-script (Phase 4 V1)."""

import unittest

from fastapi.testclient import TestClient

from app.main import app


class TestReviewScriptEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_a_identical_text_high_risk(self):
        text = (
            "Die Regierung kündigte heute neue Maßnahmen an. "
            "Experten sehen darin einen wichtigen Schritt für die kommenden Monate."
        )
        r = self.client.post(
            "/review-script",
            json={
                "source_url": "https://example.com/a",
                "source_type": "news_article",
                "source_text": text,
                "generated_script": text,
                "target_language": "de",
                "prior_warnings": [],
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data["risk_level"], "high")
        self.assertLessEqual(data["originality_score"], 10)
        codes = {i["code"] for i in data["issues"]}
        self.assertIn("identical_to_source", codes)

    def test_b_light_rephrase_medium_or_high(self):
        src = (
            "Die Zentralbank erhöhte den Leitzins um 25 Basispunkte. "
            "Marktteilnehmer reagierten vorsichtig auf die Entscheidung."
        )
        gen = (
            "Die Zentralbank hat den Leitzins um 25 Basispunkte angehoben. "
            "An den Märkten kam die Entscheidung vorsichtig an."
        )
        r = self.client.post(
            "/review-script",
            json={
                "source_type": "news_article",
                "source_text": src,
                "generated_script": gen,
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertIn(data["risk_level"], ("medium", "high"))
        self.assertTrue(len(data["similarity_flags"]) >= 1)

    def test_c_independent_script_lower_risk(self):
        src = (
            "Bauernproteste führten zu Sperren auf mehreren Autobahnen. "
            "Die Polizei war im Großeinsatz."
        )
        gen = (
            "Willkommen zum Deep Dive: Wir ordnen heute ein, warum Klimapolitik und "
            "Landwirtschaft in Europa so schwer verzahnbar sind. "
            "Zuerst der Kontext: Viele Staaten subventionieren unterschiedlich — "
            "das erzeugt Wettbewerbsfragen. "
            "Einordnung: langfristig entscheidend bleibt, ob Reformen tragfähig sind. "
            "Offen bleibt, wie schnell sich Märkte anpassen. "
            "Fazit: Die Debatte bleibt politisch brisant; wir bleiben am Ball."
        )
        r = self.client.post(
            "/review-script",
            json={
                "source_type": "news_article",
                "source_text": src,
                "generated_script": gen,
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertIn(data["risk_level"], ("low", "medium"))
        self.assertGreaterEqual(data["originality_score"], 55)

    def test_d_youtube_extra_warning(self):
        r = self.client.post(
            "/review-script",
            json={
                "source_type": "youtube_transcript",
                "source_text": "a b c d e f g h i j k l m n o p q r s t u v w x y z",
                "generated_script": "Ein anderer Absatz ohne Überlappung mit dem Quelltext.",
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        w = " ".join(data["warnings"])
        self.assertIn("YouTube transcript source", w)

    def test_e_short_source_warning(self):
        r = self.client.post(
            "/review-script",
            json={
                "source_type": "news_article",
                "source_text": "Kurz.",
                "generated_script": (
                    "Längerer generierter Text ohne Bezug zum kurzen Stück — "
                    "wir erklären Hintergrund und Einordnung ausführlicher."
                ),
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        w = " ".join(data["warnings"])
        self.assertIn("Source text is short", w)

    def test_both_empty_422(self):
        r = self.client.post(
            "/review-script",
            json={
                "source_text": "",
                "generated_script": "",
            },
        )
        self.assertEqual(r.status_code, 422)

    def test_empty_generated_returns_high(self):
        r = self.client.post(
            "/review-script",
            json={
                "source_text": "Ein bisschen Quelle für die Validierung.",
                "generated_script": "",
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data["risk_level"], "high")
        self.assertEqual(data["originality_score"], 0)


if __name__ == "__main__":
    unittest.main()
