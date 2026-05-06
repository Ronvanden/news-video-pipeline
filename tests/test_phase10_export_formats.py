"""BA 10.5 — Export-Formats Registry."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class ExportFormatsRouteTests(unittest.TestCase):
    def test_export_formats_registry(self):
        client = TestClient(app)
        r = client.get("/story-engine/export-formats")
        self.assertEqual(r.status_code, 200, msg=r.text)
        data = r.json()
        for key in (
            "json_export",
            "capcut_shotlist",
            "csv_shotlist",
            "thumbnail_variants",
            "provider_prompt_bundle",
            "warnings",
        ):
            self.assertIn(key, data)
        for block in (
            data["json_export"],
            data["capcut_shotlist"],
            data["provider_prompt_bundle"],
        ):
            self.assertIn("id", block)
            self.assertIn("source_endpoint", block)


if __name__ == "__main__":
    unittest.main()
