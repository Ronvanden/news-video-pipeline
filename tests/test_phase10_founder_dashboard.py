"""BA 10.6 — Founder Dashboard Routen."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class FounderDashboardRouteTests(unittest.TestCase):
    def test_dashboard_200_and_labels(self):
        client = TestClient(app)
        r = client.get("/founder/dashboard")
        self.assertEqual(r.status_code, 200, msg=r.text)
        text = r.text
        self.assertIn("Founder Dashboard", text)
        self.assertIn("Template", text)
        self.assertIn("Provider Readiness", text)

    def test_dashboard_config_200(self):
        client = TestClient(app)
        r = client.get("/founder/dashboard/config")
        self.assertEqual(r.status_code, 200, msg=r.text)
        data = r.json()
        self.assertIn("dashboard_version", data)
        self.assertIn("story_engine_relative", data)
        paths = data["story_engine_relative"]
        self.assertIn("export_package", paths)
        self.assertEqual(paths["export_formats"]["path"], "/story-engine/export-formats")


if __name__ == "__main__":
    unittest.main()
