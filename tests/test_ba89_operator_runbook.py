"""BA 8.9: Pflichtsektionen der Operator-Dokumentation (Smoke)."""

from __future__ import annotations

import pathlib
import unittest


class Ba89Docs(unittest.TestCase):
    def test_operator_runbook_headings(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        text = (root / "OPERATOR_RUNBOOK.md").read_text(encoding="utf-8")
        for phrase in (
            "Daily Check",
            "Dry Run",
            "Monitoring",
            "Audit",
            "Recovery",
            "Transcript Missing",
            "Provider Failure",
            "Cost Spike",
            "Failed Script",
            "Stuck Job",
            "Golden Run Check",
        ):
            self.assertIn(phrase, text)

    def test_gold_production_standard(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        text = (root / "GOLD_PRODUCTION_STANDARD.md").read_text(encoding="utf-8")
        for phrase in (
            "Intake",
            "Script",
            "Scene Plan",
            "Voice",
            "Render Manifest",
            "Costs",
            "Control Panel",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
