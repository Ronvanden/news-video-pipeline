"""BA 8.6: Provider-Seed und Laufzeit-Gesundheit (ohne Firestore)."""

from __future__ import annotations

import unittest

from app.watchlist.models import ProviderConfig
from app.watchlist.provider_discipline import (
    seed_default_provider_configs,
    validate_provider_runtime_health,
)


class Ba86ProviderSeed(unittest.TestCase):
    def test_seed_four_defaults(self):
        rows = seed_default_provider_configs(now_iso="2026-04-30T12:00:00Z")
        self.assertEqual(len(rows), 4)
        names = {r.provider_name for r in rows}
        self.assertEqual(
            names,
            {"openai", "voice_default", "image_default", "render_default"},
        )
        for r in rows:
            self.assertFalse(r.enabled)
            self.assertTrue(r.dry_run)

    def test_validate_health_budget_breach(self):
        ok, issues = validate_provider_runtime_health(
            [
                ProviderConfig(
                    id="x",
                    provider_name="openai",
                    enabled=True,
                    dry_run=False,
                    monthly_budget_limit=10,
                    current_month_estimated_cost=50,
                    status="ready",
                    notes="",
                    created_at="a",
                    updated_at="b",
                )
            ]
        )
        self.assertFalse(ok)
        self.assertTrue(any("über monthly_budget_limit" in i for i in issues))

    def test_validate_ok_minimal(self):
        ok, issues = validate_provider_runtime_health([])
        self.assertTrue(ok)
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
