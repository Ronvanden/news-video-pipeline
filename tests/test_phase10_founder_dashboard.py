"""BA 10.6–11.2 — Founder Dashboard Routen."""

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
        self.assertIn("Prompt Lab", text)
        self.assertIn("Batch Template Compare", text)
        self.assertIn("pq-badge", text)
        self.assertIn("tb-copy", text)
        self.assertIn("is-loading", text)
        self.assertIn("is-success", text)
        self.assertIn("is-error", text)
        self.assertIn("Noch kein Ergebnis", text)
        self.assertIn("scrollIntoView", text)
        self.assertIn("openPanelAndScroll", text)
        self.assertIn("Download Production Bundle", text)
        self.assertIn("Copy All Prompts", text)
        self.assertIn("Save Session Snapshot", text)
        self.assertIn("Production Ready Checklist", text)
        self.assertIn("Warning Center", text)
        self.assertIn("buildMarkdownBriefing", text)
        self.assertIn("localStorage", text)
        self.assertIn("provider-prompt-cards", text)
        self.assertIn("Load Last Snapshot", text)
        self.assertIn("Clear Snapshot", text)
        self.assertIn("Founder Strategic Summary", text)
        self.assertIn('id="founder-strategic-summary"', text)
        self.assertNotIn("position: sticky", text)
        self.assertNotIn("position: fixed", text)
        self.assertNotIn("founder-compact-bar", text)
        self.assertIn("Founder Mode", text)
        self.assertIn("Raw Mode", text)
        self.assertIn("Next Best Action", text)
        self.assertIn("Opportunity", text)
        self.assertIn("Weakness", text)
        self.assertIn("Strategic Badge", text)
        self.assertIn("Source Intake (BA 11.0)", text)
        self.assertIn("Run Full Pipeline (BA 11.1)", text)
        self.assertIn('id="pipeline-timeline"', text)
        self.assertIn('id="intake-source-type"', text)
        self.assertIn('id="btn-intake-body"', text)
        self.assertIn('id="btn-full-pipeline"', text)
        self.assertIn("runFullPipelineOrchestrator", text)
        self.assertIn("persistSessionSnapshotSilent", text)
        self.assertIn("Operator Clarity (BA 11.2)", text)
        self.assertIn("Executive Scorecard", text)
        self.assertIn("Rewrite Recommendation Engine", text)
        self.assertIn("Opportunity Radar", text)
        self.assertIn('id="fd-kill-switch"', text)
        self.assertIn("btn-operator-mode", text)
        self.assertIn("refreshOperatorClarity", text)
        self.assertIn("isKillSwitchActive", text)
        self.assertIn('id="coll-input-panel"', text)
        self.assertIn('id="coll-warning-center"', text)

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
