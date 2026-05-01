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
        self.assertIn('value="raw_text"', text)
        self.assertIn('value="youtube"', text)
        self.assertIn('value="news"', text)
        self.assertIn('id="intake-source-debug"', text)
        self.assertIn("Quelle erkannt:", text)
        self.assertIn("getIntakeSourceTypeNormalized", text)
        self.assertIn("isIntakeRawMode", text)
        self.assertIn("applyIntakeToForm", text)
        self.assertIn("validateFormAfterIntake", text)
        self.assertIn("normalizeIntakePayloadFromResponse", text)
        self.assertIn("normalizeChapterListForIntake", text)
        self.assertIn("Input Panel aktualisiert:", text)
        self.assertIn("response.title", text)
        self.assertIn("response.chapters", text)
        self.assertIn("Bitte zuerst Auto Body aus Quelle erfolgreich ausführen", text)
        self.assertIn('id="fd-intake-apply-badge"', text)
        self.assertIn("raw_text_client_segmented", text)
        self.assertIn('id="intake-status"', text)
        self.assertIn("setIntakeStatus", text)
        self.assertIn("runBuildBodyFromIntake", text)
        self.assertIn("validateIntakeBeforeFullPipeline", text)
        self.assertIn("validateScriptResponseForIntake", text)
        self.assertIn("resetPipelineStoryOutputs", text)
        self.assertIn("buildRawHeadline", text)
        self.assertIn("buildRawSourceSummary", text)
        self.assertIn("client_summary", text)
        self.assertIn("Title (Headline)", text)
        self.assertIn("Topic (optional Kategorie/Thema)", text)
        self.assertIn("Source summary (Kurzfassung)", text)
        self.assertIn("Titel automatisch aus Rohtext erzeugt", text)
        self.assertIn('addEventListener("click"', text)
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

    def test_dashboard_contains_story_engine_request_builder_and_validation(self):
        client = TestClient(app)
        r = client.get("/founder/dashboard")
        self.assertEqual(r.status_code, 200, msg=r.text)
        text = r.text
        self.assertIn("buildCurrentExportRequestFromForm", text)
        self.assertIn("validateExportFormForStoryEngine", text)
        self.assertIn("assertCompleteStoryResponse", text)
        self.assertIn('id="story-engine-request-debug"', text)
        self.assertIn("Export Request gebaut:", text)
        self.assertIn("normalizeStoryTemplateId", text)
        self.assertIn("Endpoint antwortet leer oder unvollständig:", text)
        self.assertIn("runExportOnlyInternal", text)

    def test_build_export_package_button_binding_and_export_summary_ui(self):
        client = TestClient(app)
        r = client.get("/founder/dashboard")
        self.assertEqual(r.status_code, 200, msg=r.text)
        text = r.text
        self.assertIn('id="btn-export-package"', text)
        self.assertIn("DEBUG: Build Export Button ausgelöst", text)
        self.assertIn("bindBuildExportPackageButton", text)
        self.assertIn("fdBootstrapStoryActions", text)
        self.assertIn("onBuildExportPackageClick", text)
        self.assertIn('addEventListener("click"', text)
        self.assertIn("renderExportScenePlanSummary", text)
        self.assertIn('id="export-scene-plan-summary"', text)
        self.assertIn('id="export-action-status"', text)
        self.assertIn("Export Request ungültig:", text)
        self.assertIn("coll-export", text)

    def test_story_engine_post_endpoints_return_fields_expected_by_dashboard(self):
        client = TestClient(app)
        base = {
            "video_template": "generic",
            "duration_minutes": 10,
            "title": "Dashboard Contract Test",
            "topic": "test",
            "source_summary": "Kurzfassung für den Export.",
            "provider_profile": "openai",
            "continuity_lock": True,
            "chapters": [
                {"title": "Teil 1", "content": "Inhalt mit genug Zeichen für eine Szene. " * 3},
            ],
        }
        r = client.post("/story-engine/export-package", json=base)
        self.assertEqual(r.status_code, 200, msg=r.text)
        data = r.json()
        self.assertIsInstance(data.get("hook"), dict)
        self.assertIsInstance(data.get("scene_plan"), dict)
        self.assertIsInstance(data.get("scene_prompts"), dict)
        rp = client.post("/story-engine/export-package/preview", json=base)
        self.assertEqual(rp.status_code, 200, msg=rp.text)
        pj = rp.json()
        self.assertIsInstance(pj.get("prompt_quality_score"), int)
        rr = client.post("/story-engine/provider-readiness", json=base)
        self.assertEqual(rr.status_code, 200, msg=rr.text)
        self.assertIsInstance(rr.json().get("scores"), dict)
        op = client.post("/story-engine/provider-prompts/optimize", json=base)
        self.assertEqual(op.status_code, 200, msg=op.text)
        self.assertIsInstance(op.json().get("optimized_prompts"), dict)
        ctr_body = {
            "title": base["title"],
            "hook": data["hook"]["hook_text"],
            "video_template": "generic",
            "thumbnail_prompt": data.get("thumbnail_prompt") or "",
            "chapters": base["chapters"],
        }
        ctr = client.post("/story-engine/thumbnail-ctr", json=ctr_body)
        self.assertEqual(ctr.status_code, 200, msg=ctr.text)
        self.assertIsInstance(ctr.json().get("ctr_score"), int)


if __name__ == "__main__":
    unittest.main()
