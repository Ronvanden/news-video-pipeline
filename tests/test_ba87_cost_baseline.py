"""BA 8.7: Kosten-Baseline und Profit-Hinweis (Heuristik)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from app.watchlist.cost_calculator import build_production_costs_document
from app.watchlist.models import GeneratedScript, ProductionJob


class Ba87CostBaseline(unittest.TestCase):
    def test_baseline_variance_populated(self):
        repo = MagicMock()
        pj = ProductionJob(
            id="pj_ba87",
            generated_script_id="pj_ba87",
            script_job_id="sj1",
            status="queued",
            created_at="2026-04-30T10:00:00Z",
            updated_at="2026-04-30T10:00:00Z",
        )
        repo.get_production_job.return_value = pj
        gs = GeneratedScript(
            id="pj_ba87",
            script_job_id="sj1",
            source_url="u",
            title="t",
            hook="h",
            chapters=[],
            full_script="word " * 800,
            warnings=[],
            word_count=800,
            created_at="c",
        )
        repo.get_generated_script.return_value = gs
        spa = MagicMock()
        spa.scenes = [MagicMock(), MagicMock(), MagicMock()]
        repo.get_scene_assets.return_value = spa

        doc = build_production_costs_document(
            repo=repo,
            pj=pj,
            now_iso="2026-04-30T11:00:00Z",
        )
        self.assertGreater(doc.cost_baseline_expected, 0.0)
        self.assertIn("voice", doc.step_cost_breakdown)
        self.assertTrue(len(doc.estimated_profitability_hint) > 0)
        self.assertIsInstance(doc.over_budget_flag, bool)


if __name__ == "__main__":
    unittest.main()
