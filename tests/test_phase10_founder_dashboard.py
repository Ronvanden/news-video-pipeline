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
        # Regression: Python """ must emit JS lines.join("\\n") not a literal newline inside the string
        self.assertGreaterEqual(text.count('lines.join("\\n")'), 2, msg="fresh preview / prod flow join must emit valid JS")
        # BA 30.6 — Visual Upgrade (Design-Marker, keine Screenshot-Tests)
        self.assertIn("VideoPipe Founder Cockpit", text)
        self.assertIn("Production Ready", text)
        self.assertIn("Local Preview Pipeline", text)
        self.assertIn("data-ba306-exec-strip", text)
        self.assertIn("data-ba306-header-cta", text)
        # BA 30.6b — Cockpit-Layout (Executive Row, breitere Fläche)
        self.assertIn("Start, prüfe und steuere Fresh Preview Runs", text)
        self.assertIn("Zum Fresh Preview Panel", text)
        self.assertIn("Fresh Preview Status", text)
        self.assertIn("Readiness Score", text)
        self.assertIn("Latest Run", text)
        self.assertIn("Next Operator Step", text)
        self.assertIn("data-ba306b-exec-row", text)
        self.assertIn("fd-dashboard-main", text)
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
        # BA 26.4c — Visual Policy Summary sichtbar (minimal-invasiv)
        self.assertIn("Visual Policy Summary", text)
        # BA 26.4d — Quellenanzeige-String muss im HTML/JS vorhanden sein
        self.assertIn("Visual Policy Source", text)
        self.assertIn("lastOptimize", text)
        self.assertIn("lastExport", text)
        self.assertIn("provider_prompts", text)
        # BA 27.5b — Scene-level Reference Provider display strings
        self.assertIn("Referenz-Provider", text)
        self.assertIn("Bildreferenz vorbereitet", text)
        self.assertIn("Kein Live-Upload", text)
        # BA 28.1 — Motion clip status strings (pack meta)
        self.assertIn("Motion Clips", text)
        self.assertIn("Missing inputs", text)
        self.assertIn("Dry-run", text)
        # BA 30.0 — Production flow panel (German operator labels)
        self.assertIn("Produktionsfluss", text)
        self.assertIn("Lokale Vorschau", text)
        self.assertIn("Finale Render-Freigabe", text)
        self.assertIn("Nächste Schritte", text)
        self.assertIn("refreshProductionFlowPanel", text)
        # BA 31.0 — Operator Review (Fresh Preview Snapshot)
        self.assertIn("Operator Review", text)
        self.assertIn("data-ba310-operator-review", text)
        self.assertIn("data-review-decision-marker", text)
        # BA 31.1 — Guided Production Flow
        self.assertIn("Production Flow", text)
        self.assertIn("data-ba311-guided-flow", text)
        self.assertIn("Snapshot = aktueller Dashboard-Abgleich", text)
        self.assertIn("fd-guided-flow-microcopy-help", text)
        # BA 31.2 — Final Render Preparation Gate
        self.assertIn("Final Render Preparation", text)
        self.assertIn("data-ba312-final-render-gate", text)
        self.assertIn("fdFpApplyFinalRenderGate", text)
        self.assertIn("fdFpApplyGuidedFlow", text)
        # BA 30.3–30.8 — Fresh Preview + Dry-Run + CLI-Handoff
        self.assertIn("Fresh Preview Smoke (BA 30.3–30.8)", text)
        self.assertIn("Dry-Run starten", text)
        self.assertIn("data-ba307-start-dry-run", text)
        self.assertIn("/founder/dashboard/fresh-preview/start-dry-run", text)
        self.assertIn("Nächster Schritt: Full Preview Smoke lokal starten", text)
        self.assertIn("CLI-Befehl kopieren", text)
        self.assertIn("data-ba308-handoff", text)
        self.assertIn("fdLoadFreshPreviewSnapshot", text)
        self.assertIn("fresh-preview/snapshot", text)
        self.assertIn("Preview Power", text)
        self.assertIn("fp-preview-power-gauge", text)
        self.assertIn("data-ba306c-preview-power", text)
        self.assertIn("fd-sidebar", text)
        self.assertIn("data-ba306c-sidebar", text)
        self.assertIn("fd-score-gauge", text)
        self.assertIn("data-ba306d-score-gauge", text)
        self.assertIn("Noch kein Score", text)
        self.assertIn("Fresh Preview", text)
        self.assertIn("data-ba304-readiness-marker", text)
        self.assertIn("Fresh Preview aktualisieren", text)
        self.assertIn("data-ba305-copy-markers", text)
        self.assertIn("operator_next_step", text)
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

    def test_emergency_dom_bootstrap_and_dom_test_button(self):
        client = TestClient(app)
        r = client.get("/founder/dashboard")
        self.assertEqual(r.status_code, 200, msg=r.text)
        text = r.text
        self.assertIn("FD_BOOTSTRAP_START", text)
        self.assertIn("BTN_MISSING: btn-intake-body", text)
        self.assertIn("BTN_CLICK_RAW", text)
        self.assertIn("GLOBAL_JS_FAIL:", text)
        self.assertIn('id="btn-dom-test"', text)
        self.assertIn("DOM_TEST_OK", text)
        self.assertIn("fdBootstrapDashboard", text)

    def test_intake_hard_debug_fill_test_body_and_field_debug(self):
        client = TestClient(app)
        r = client.get("/founder/dashboard")
        self.assertEqual(r.status_code, 200, msg=r.text)
        text = r.text
        self.assertIn("Fill Test Body", text)
        self.assertIn('id="btn-fill-test-body"', text)
        self.assertIn("Auto Body geklickt", text)
        self.assertIn("Quelle erkannt:", text)
        self.assertIn('id="intake-field-debug"', text)
        self.assertIn("summary_len=", text)
        self.assertIn("chapters_count=", text)
        self.assertIn("commitIntakePayloadToInputPanel", text)
        self.assertIn("fillTestBodyIntoInputPanel", text)
        self.assertIn("applyIntakeToForm", text)
        self.assertIn("getRequiredInputEl(\"fd-title\")", text)
        self.assertIn("getRequiredInputEl(\"fd-topic\")", text)
        self.assertIn("getRequiredInputEl(\"fd-summary\")", text)
        self.assertIn("getRequiredInputEl(\"fd-chapters\")", text)

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
        self.assertEqual(
            data["production_proof_summary_relative"]["path"],
            "/founder/production-proof/summary",
        )

    def test_production_proof_summary_200(self):
        client = TestClient(app)
        r = client.get("/founder/production-proof/summary")
        self.assertEqual(r.status_code, 200, msg=r.text)
        data = r.json()
        self.assertEqual(data["summary_version"], "production-proof-v1")
        self.assertIn("canonical_spine", data)
        self.assertEqual(
            data["canonical_spine"]["primary_http"]["path"],
            "/story-engine/prompt-plan",
        )
        self.assertIn("manual_source_url", data["canonical_spine"]["primary_http"]["required_for_full_plan"])

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
        self.assertIn("fdBootstrapDashboard", text)
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
