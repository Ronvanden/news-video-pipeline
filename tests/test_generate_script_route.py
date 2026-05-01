"""POST /generate-script — HTTP-Semantik (kein Maskieren von HTTPException)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class GenerateScriptRouteHttp(unittest.TestCase):
    def test_empty_extract_returns_400_not_500(self):
        with patch(
            "app.routes.generate.extract_text_from_url",
            return_value=("", []),
        ):
            client = TestClient(app)
            r = client.post(
                "/generate-script",
                json={
                    "url": "https://example.com/article",
                    "target_language": "de",
                    "duration_minutes": 10,
                },
            )
        self.assertEqual(r.status_code, 400)
        self.assertIn("Could not extract", r.json().get("detail", ""))


if __name__ == "__main__":
    unittest.main()
