"""BA 10.6–11.2 — Founder Dashboard Routen."""

from __future__ import annotations

import unittest
import os
import shutil
import subprocess
import tempfile
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import GenerateScriptResponse


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
        self.assertIn("Starte und prüfe Vorschau-Prüfläufe", text)
        self.assertIn("Zum Vorschau-Panel", text)
        self.assertIn("Vorschau-Status", text)
        self.assertIn("Readiness Score", text)
        self.assertIn("Letzter Lauf", text)
        self.assertIn("Nächster Schritt", text)
        self.assertIn("Zum nächsten Schritt", text)
        self.assertIn("Video-Status: Fallback-Preview erstellt", text)
        self.assertIn("Fallback-Preview erstellt. Provider/Assets prüfen oder Preview öffnen.", text)
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
        self.assertIn("Status aktualisieren", text)
        self.assertIn("liest den aktuellen Projektstand", text)
        self.assertIn("fd-guided-flow-microcopy-help", text)
        # BA 31.2 — Final Render Preparation Gate
        self.assertIn("Final Render Preparation", text)
        self.assertIn("data-ba312-final-render-gate", text)
        self.assertIn("fdFpApplyFinalRenderGate", text)
        # BA 31.3 — Final Render Input Checklist
        self.assertIn("Final Render Input Checklist", text)
        self.assertIn("data-ba313-final-render-input-checklist", text)
        self.assertIn("fdFpApplyFinalRenderInputChecklist", text)
        # BA 31.4 — Safe Final Render Handoff
        self.assertIn("Safe Final Render Handoff", text)
        self.assertIn("data-ba314-safe-final-render-handoff", text)
        self.assertIn("fp-safe-final-render-cli", text)
        self.assertIn("fp-safe-final-render-copy", text)
        self.assertIn("fdFpApplySafeFinalRenderHandoff", text)
        self.assertIn("fdFpApplyGuidedFlow", text)
        # BA 30.3–30.8 — Fresh Preview + Dry-Run + CLI-Handoff
        # BA 32.3 — URL → Video (eigenes Panel, nicht Fresh Preview)
        self.assertIn("panel-ba323-video-generate", text)
        self.assertIn("fd-video-generate-form", text)
        self.assertIn("fd-video-generate-url", text)
        self.assertIn("fd-video-generate-submit", text)
        self.assertIn("fd-video-generate-clear", text)
        self.assertIn("data-ba323-video-generate", text)
        self.assertIn("Zurücksetzen", text)
        self.assertIn("/founder/dashboard/video/generate", text)
        # BA 32.5 — Real Assets Activation Gate (UI copy)
        self.assertIn("Echte Assets erzeugen", text)
        self.assertIn("Ohne Aktivierung wird eine Fallback-Preview mit Platzhaltern erstellt", text)
        self.assertIn("Preview/Fallback-Modus", text)
        # BA 32.6 — Provider Readiness Panel (UI)
        self.assertIn("Provider-Readiness", text)
        self.assertIn("Live Assets", text)
        self.assertIn("ElevenLabs Voice", text)
        self.assertIn("OpenAI TTS", text)
        self.assertIn("Runway Motion", text)
        self.assertIn("Bereit", text)
        self.assertIn("Fehlt", text)
        self.assertIn("Optional fehlt", text)
        self.assertIn("Unbekannt", text)
        self.assertIn("Echte Assets sind angefordert, aber der Asset-Provider ist nicht konfiguriert", text)
        self.assertIn("ElevenLabs ist nicht konfiguriert. Der Lauf nutzt voraussichtlich Dummy-Voice.", text)
        # BA 32.7 — Preflight + Fix Checklist
        self.assertIn("Preflight", text)
        self.assertIn("Preview-Modus bereit", text)
        self.assertIn("Real-Assets-Modus nicht vollständig bereit", text)
        self.assertIn("Fix Checklist", text)
        self.assertIn("Live Assets konfigurieren", text)
        self.assertIn("ElevenLabs konfigurieren", text)
        self.assertIn("OpenAI TTS konfigurieren", text)
        self.assertIn("Runway optional konfigurieren", text)
        self.assertIn("LEONARDO_API_KEY", text)
        self.assertIn("ELEVENLABS_API_KEY", text)
        self.assertIn("OPENAI_API_KEY", text)
        self.assertIn("RUNWAY_API_KEY", text)
        self.assertIn("Status aktualisieren", text)
        # BA 32.8 — Voice Mode Selector + Preflight Sync
        self.assertIn("Voice-Modus", text)
        self.assertIn("Dummy Voice / Testmodus", text)
        self.assertIn("Keine Voice", text)
        self.assertIn("ElevenLabs", text)
        self.assertIn("OpenAI TTS", text)
        self.assertIn("Dummy Voice aktiv – geeignet für Tests.", text)
        self.assertIn("OpenAI TTS ist nicht konfiguriert", text)
        # BA 32.9 — Voice Artifact Wiring (Operator-Karte)
        self.assertIn("Voice", text)
        self.assertIn("Echte Voice-Datei vorhanden", text)
        self.assertIn("Echte Voice-Datei vorhanden.", text)
        self.assertIn("Dummy Voice verwendet", text)
        self.assertIn("Dummy Voice verwendet.", text)
        self.assertIn("Keine Voice ausgewählt", text)
        self.assertIn("Keine Voice ausgewählt.", text)
        self.assertIn("Voice-Datei fehlt", text)
        self.assertIn("Voice-Datei fehlt.", text)
        self.assertIn("Voice Artifact", text)
        # BA 32.10 — Real Production Smoke Checklist + Ergebnis
        self.assertIn("Real Production Smoke", text)
        # BA 32.25 — Real Leonardo Live Smoke (Operator-Checkliste, kein Provider in CI)
        self.assertIn("Real Leonardo Live Smoke", text)
        self.assertIn("voice_mode=none", text)
        self.assertIn("Max. Live-Assets = 1", text)
        self.assertIn("generation_modes", text)
        self.assertIn("leonardo_live", text)
        self.assertIn("real_leonardo_live_smoke.md", text)
        # BA 32.72 — Founder OpenAI Image Dashboard-Mini-Smoke (Markup/JS, kein Live-Call)
        self.assertIn("Founder OpenAI Image Smoke (BA 32.72)", text)
        self.assertIn("fdApplyOpenAiImageMiniSmokePreset", text)
        self.assertIn('id="fd-vg-live-assets"', text)
        self.assertIn("fdVgDispatchInputChange", text)
        self.assertIn('oaiSize.value = "1024x1024"', text)
        self.assertIn('body.openai_image_model = oaiModel || "gpt-image-2"', text)
        self.assertIn("allow_live_assets:", text)
        # BA 32.72b — Dev-only Provider Key Override Panel (nur transient per Request)
        self.assertIn("Provider Keys / Local Test (dev-only)", text)
        self.assertIn('id="fd-vg-dev-openai-api-key"', text)
        self.assertIn('type="password" id="fd-vg-dev-openai-api-key"', text)
        self.assertIn("dev_openai_api_key", text)
        self.assertIn("fdVgApplyDevKeyOverrideHint", text)
        self.assertIn("image_asset_audit", text)
        self.assertIn("Teilweise Platzhalter, weil Live-Asset-Limit erreicht wurde oder der Provider nicht alle Szenen erzeugt hat.", text)
        self.assertIn("Live Assets angefordert", text)
        self.assertIn("Asset Provider bereit", text)
        self.assertIn("Voice-Modus produktiv gewählt", text)
        self.assertIn("Voice Provider bereit", text)
        self.assertIn("Timing / Voice Fit", text)
        self.assertIn("toFixed(2)", text)
        self.assertIn("Motion optional", text)
        self.assertIn("Bereit für Real Production Smoke", text)
        self.assertIn("Noch nicht production-ready", text)
        self.assertIn("Nur Preview/Fallback-Smoke", text)
        self.assertIn("Smoke-Ergebnis", text)
        # BA 32.16 — Asset Manifest Quality Gate (minimal UI marker)
        self.assertIn("Asset Quality", text)
        self.assertIn("mixed_assets", text)
        self.assertIn("placeholder_only", text)
        self.assertIn("production_ready", text)
        self.assertIn("Echte Assets vorhanden, aber noch Placeholder im Manifest.", text)
        # BA 32.17 — Asset Quality Gate in Real Smoke Checklist
        self.assertIn("Asset Quality strict/loose", text)
        self.assertIn("Asset Manifest enthält echte Assets ohne Placeholder.", text)
        self.assertIn("Nur Placeholder-Assets vorhanden.", text)
        self.assertIn("Keine Asset-Dateien im Manifest.", text)
        self.assertIn("Asset-Qualität noch nicht verfügbar.", text)
        self.assertIn("Asset-Gate bestanden.", text)
        self.assertIn("Zwischenstufe: Live Assets funktionieren teilweise, aber Placeholder müssen noch ersetzt werden.", text)
        # BA 32.18 — Persist Last Run Summary (localStorage)
        self.assertIn("FD_VG_LAST_VIDEO_GENERATE", text)
        self.assertIn("Letzter gespeicherter Video-Lauf", text)
        self.assertIn("Aus lokalem Browser-Speicher.", text)
        self.assertIn("Letzten Lauf vergessen", text)
        self.assertIn("fdVgBuildLastRunSummary", text)
        self.assertIn("fdVgSaveLastRunSummary", text)
        self.assertIn("fdVgLoadLastRunSummary", text)
        self.assertIn("fdVgForgetLastRunSummary", text)
        # Data minimization markers
        self.assertIn("warnings_count", text)
        self.assertIn("blocking_reasons_count", text)
        # BA 32.19 — Restore Asset Quality from Last Run Summary
        self.assertIn("(local)", text)
        self.assertIn("aus letztem gespeicherten Lauf", text)
        self.assertIn("fdVgIsLastRunSummaryExpired", text)
        self.assertIn("fdVgGetRestoredAssetQualityGate", text)
        # BA 32.27 — Asset-Qualität vs. Render-Layer (Produktions-Check)
        self.assertIn("Render-Layer", text)
        self.assertIn("Render-Layer nutzt noch Placeholder/Cinematic-Fallback.", text)
        self.assertIn("Render-Layer nutzt keine Placeholder-Signale.", text)
        self.assertIn("Live Asset erfolgreich, aber Render/Audio nutzt noch Fallbacks.", text)
        self.assertIn("Asset Quality Gate strict_ready (Manifest) — unabhängig von Render-Warnungen", text)
        self.assertIn("FD_VG_RENDER_LAYER_PLACEHOLDER_SIGNALS", text)
        self.assertIn("fdVgRenderLayerPlaceholderHit", text)
        # BA 32.29 — Dashboard Voice QC: readiness_audit-Fallback wenn voice_artifact fehlt
        self.assertIn("fdVgVoiceQcRowTuple", text)
        self.assertIn("fdVgVoiceArtifactPresent", text)
        self.assertIn("voice_artifact hat Vorrang vor readiness_audit", text)
        self.assertIn("effective_voice_mode", text)
        self.assertIn("voice_is_dummy", text)
        self.assertIn("voice_file_ready", text)
        self.assertIn("voice_file_path_present", text)
        self.assertLess(
            text.find("if (fdVgVoiceArtifactPresent(j))"),
            text.find("raV.voice_is_dummy"),
            msg="voice_artifact-Zweig muss in fdVgVoiceQcRowTuple vor readiness_audit liegen",
        )
        # BA 32.31 — Silent Render mit voice_mode=none: kein Fallback-Preview allein wegen audio_missing_silent_render
        self.assertIn("fdVgWarnTriggersFallbackPreview", text)
        self.assertIn("fdVgVideoGenerateRunStatusFromPayload", text)
        self.assertIn("fdVgIsOkRunFallbackPreview", text)
        self.assertIn("fdVgEffectiveVoiceMode", text)
        self.assertIn("fdVgAudioSilentIsExpectedFallback", text)
        self.assertIn("BA 32.31", text)
        self.assertIn("Smoke erfolgreich; Silent Render erwartet.", text)
        self.assertIn("Keine Voice ausgewählt; Silent Render ist erwartet.", text)
        # BA 32.32 — readiness_audit.silent_render_expected (Dashboard bevorzugt Feld, Heuristik Fallback)
        self.assertIn("silent_render_expected", text)
        self.assertIn("BA 32.32", text)
        # BA 32.80b — Voice-Escape + harmlose ``fallback``-Namen in Warn-Join
        self.assertIn("fdVgVoiceEscapeOkBa3280", text)
        self.assertIn("fdVgSanitizeJoinedForFallbackPreview", text)
        # BA 32.11 — One-Click Preset
        self.assertIn("Real Production Smoke Preset", text)
        self.assertIn("Preset aktiviert: Live Assets an, produktive Voice gewählt. Mögliche Provider-Kosten wurden bestätigt.", text)
        self.assertIn("Preset aktiviert: Live Assets an, Kosten bestätigt, aber kein Voice-Provider bereit – Dummy Voice bleibt aktiv.", text)
        self.assertIn("Asset-Provider fehlt – der Lauf kann weiterhin auf Platzhalter zurückfallen.", text)
        self.assertIn("voice_elevenlabs", text)
        self.assertIn("voice_openai", text)
        self.assertIn("chosenVoice = \"dummy\"", text)
        self.assertIn("chosenVoice = \"elevenlabs\"", text)
        self.assertIn("chosenVoice = \"openai\"", text)
        # BA 32.12 — Confirm Costs Assist
        self.assertIn("Mögliche Provider-Kosten bestätigen", text)
        self.assertIn("Kostenbestätigung fehlt – Real-Assets-Lauf kann blockiert werden.", text)
        self.assertIn("Kosten bestätigt", text)
        # BA 32.13 — Inline 422 Prevention Copy
        self.assertIn(
            "Ohne Kostenbestätigung kann der Server den Real-Assets- oder Thumbnail-Pack-Lauf mit 422 ablehnen.",
            text,
        )
        self.assertIn("Kostenbestätigung aktiv.", text)
        self.assertIn("Preview/Fallback-Modus – keine Live-Asset-Kosten erwartet.", text)
        self.assertIn("fdApplyInline422Hint", text)
        # BA 32.14 — Inline 422 Detail Decode
        self.assertIn("confirm_provider_costs_required_when_live_flags", text)
        self.assertIn("Kostenbestätigung fehlt: Für Live Assets oder Thumbnail Pack musst du zuerst", text)
        self.assertIn("Zur Kostenbestätigung", text)
        self.assertIn("fdScrollToConfirmCosts", text)
        self.assertIn("fdVgErrorDetailContains", text)
        self.assertIn("fdUpdateVideoGenerateExecutiveState", text)
        self.assertIn("fdRenderVideoGenerateOperatorResult", text)
        self.assertIn("fd-video-generate-result", text)
        self.assertIn("fd-vg-operator-result", text)
        self.assertIn("Video-Generierung abgeschlossen", text)
        self.assertIn("Video konnte nicht erzeugt werden", text)
        self.assertIn("Fallback-Preview erstellt", text)
        self.assertIn("Fallback / Preview", text)
        self.assertIn("placeholder", text)
        self.assertIn("dummy", text)
        self.assertIn("fallback", text)
        self.assertIn("Keine Live-Motion-Clips verfügbar.", text)
        self.assertIn("Final Video", text)
        self.assertIn("Output-Ordner", text)
        self.assertIn("Script", text)
        self.assertIn("Scene Asset Pack", text)
        self.assertIn("Asset Manifest", text)
        self.assertIn("OPEN_ME Ergebnisbericht", text)
        # BA 32.77 — Thumbnail Pack Summary im Video-Generate-Panel
        self.assertIn("Thumbnail Pack (BA 32.77)", text)
        self.assertIn("data-ba3277-thumbnail-pack", text)
        # BA 32.78 — Thumbnail Pack Auto-Attach Optionen
        self.assertIn("fd-vg-generate-thumbnail-pack", text)
        self.assertIn("data-ba3278-thumbnail-pack", text)
        # BA 32.79 — Production Bundle Ergebnisanzeige
        self.assertIn("Production Bundle (BA 32.79)", text)
        self.assertIn("data-ba3279-production-bundle", text)
        self.assertIn("fd-vg-production-bundle-wrap", text)
        self.assertIn("Dieser Lauf nutzt Platzhalter/Fallbacks", text)
        self.assertIn("Finales Video prüfen", text)
        self.assertIn("Blocker beheben und erneut starten", text)
        self.assertIn("Produktions-Check", text)
        self.assertIn("Script erstellt", text)
        self.assertIn("Scene Asset Pack erstellt", text)
        self.assertIn("Asset Manifest vorhanden", text)
        self.assertIn("Final Video Pfad vorhanden", text)
        self.assertIn("Echte Assets verwendet", text)
        self.assertIn("Echte Voice verwendet", text)
        self.assertIn("Live Motion verfügbar", text)
        self.assertIn("OK", text)
        self.assertIn("Prüfen", text)
        self.assertIn("Nicht verfügbar", text)
        self.assertIn("Raw JSON (Debug)", text)
        # BA 32.91 — Founder Dashboard Timeline Preview Layer
        self.assertIn("Production Timeline", text)
        self.assertIn('data-ba3291-production-timeline="1"', text)
        self.assertIn("fdVgBuildProductionTimeline", text)
        self.assertIn("fdVgRenderProductionTimeline", text)
        self.assertIn("motion_requested_but_no_clip_fallback_to_image", text)
        self.assertIn("Motion übersprungen / Fallback auf Bild", text)
        self.assertIn("skipped", text)
        self.assertIn("Advanced artifacts & debug details", text)
        self.assertIn('data-fd-nav-scroll="panel-ba323-video-generate"', text)
        self.assertGreaterEqual(text.count("Video generieren"), 2)
        self.assertIn("Vorschau-Prüflauf (BA 30.3–30.8)", text)
        self.assertIn("Struktur-Test starten", text)
        self.assertIn("data-ba307-start-dry-run", text)
        self.assertIn("/founder/dashboard/fresh-preview/start-dry-run", text)
        self.assertIn("Nächster Schritt: vollen Vorschau-Prüflauf lokal starten", text)
        self.assertIn("Befehl zum Kopieren", text)
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
        self.assertIn("Vorschau-Prüflauf", text)
        self.assertIn("data-ba304-readiness-marker", text)
        self.assertIn("Status aktualisieren", text)
        # BA 32.3b — Dashboard-Reset & verständlichere Begriffe
        self.assertIn("Dashboard zurücksetzen", text)
        self.assertIn("Setzt nur die Ansicht zurück", text)
        self.assertIn("Struktur-Test", text)
        self.assertIn("fdResetDashboardView", text)
        self.assertIn("fd_dashboard_manual_reset", text)
        self.assertIn("fdApplyDashboardNeutralView", text)
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
        self.assertIn("Legacy Source Intake / Debug (BA 11.0)", text)
        self.assertIn("Für neue Produktionen nutze oben „Video generieren“", text)
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
        # Storyboard Orchestration V1 — Dashboard-Anschluss, plan-only.
        self.assertIn("Storyboard erstellen", text)
        self.assertIn("Storyboard Plan", text)
        self.assertIn("Storyboard prüfen", text)
        self.assertIn("Storyboard Readiness", text)
        self.assertIn("Asset Plan erstellen", text)
        self.assertIn("Asset Plan", text)
        self.assertIn("Asset Tasks simulieren", text)
        self.assertIn("Asset Execution Stub", text)
        self.assertIn("OpenAI Bild erzeugen", text)
        self.assertIn("OpenAI Image Live", text)
        self.assertIn('id="btn-storyboard-plan"', text)
        self.assertIn('id="btn-storyboard-readiness"', text)
        self.assertIn('id="btn-asset-generation-plan"', text)
        self.assertIn('id="btn-asset-execution-stub"', text)
        self.assertIn('id="btn-openai-image-live"', text)
        self.assertIn('id="storyboard-openai-confirm-costs"', text)
        self.assertIn('id="storyboard-plan-summary"', text)
        self.assertIn('id="storyboard-readiness-summary"', text)
        self.assertIn('id="asset-generation-plan-summary"', text)
        self.assertIn('id="asset-execution-stub-summary"', text)
        self.assertIn('id="openai-image-live-summary"', text)
        self.assertIn('id="out-storyboard-plan"', text)
        self.assertIn('id="out-storyboard-readiness"', text)
        self.assertIn('id="out-asset-generation-plan"', text)
        self.assertIn('id="out-asset-execution-stub"', text)
        self.assertIn('id="out-openai-image-live"', text)
        self.assertIn("/story-engine/storyboard-plan", text)
        self.assertIn("/story-engine/storyboard-readiness", text)
        self.assertIn("/story-engine/asset-generation-plan", text)
        self.assertIn("/story-engine/asset-execution-stub", text)
        self.assertIn("/story-engine/openai-image-live-execution", text)
        self.assertIn("runStoryboardOnlyInternal", text)
        self.assertIn("runStoryboardReadinessOnlyInternal", text)
        self.assertIn("runAssetGenerationPlanOnlyInternal", text)
        self.assertIn("runAssetExecutionStubOnlyInternal", text)
        self.assertIn("runOpenAIImageLiveOnlyInternal", text)
        self.assertIn("buildStoryboardRequestFromDashboardState", text)
        self.assertIn("renderStoryboardPlanSummary", text)
        self.assertIn("renderStoryboardReadinessSummary", text)
        self.assertIn("renderAssetGenerationPlanSummary", text)
        self.assertIn("renderAssetExecutionStubSummary", text)
        self.assertIn("renderOpenAIImageLiveSummary", text)
        self.assertIn("3. Storyboard Plan", text)
        self.assertIn("4. Storyboard Readiness", text)
        self.assertIn("5. Asset Plan", text)
        self.assertIn("6. Asset Execution Stub", text)
        orch = text[text.find("async function runFullPipelineOrchestrator") : text.find("function applyInputSnapshot")]
        self.assertLess(
            orch.find("await runExportOnlyInternal()"),
            orch.find("await runStoryboardOnlyInternal()"),
            msg="Full-Pipeline muss Storyboard nach Export erzeugen",
        )
        self.assertLess(
            orch.find("await runStoryboardOnlyInternal()"),
            orch.find("await runStoryboardReadinessOnlyInternal()"),
            msg="Full-Pipeline muss Storyboard Readiness nach Storyboard erzeugen",
        )
        self.assertLess(
            orch.find("await runStoryboardReadinessOnlyInternal()"),
            orch.find("await runAssetGenerationPlanOnlyInternal()"),
            msg="Full-Pipeline muss Asset Plan nach Storyboard Readiness erzeugen",
        )
        self.assertLess(
            orch.find("await runAssetGenerationPlanOnlyInternal()"),
            orch.find("await runAssetExecutionStubOnlyInternal()"),
            msg="Full-Pipeline muss Asset Execution Stub nach Asset Plan ausführen",
        )
        self.assertLess(
            orch.find("await runAssetExecutionStubOnlyInternal()"),
            orch.find("await runPreviewOnlyInternal()"),
            msg="Full-Pipeline muss Asset Execution Stub vor Preview/Readiness/Bundle ausführen",
        )
        self.assertIn('if (data.overall_status === "blocked")', text)
        self.assertIn('throw new Error(data.production_recommendation || "Storyboard Readiness blockiert.")', text)
        self.assertIn('Asset Plan blockiert: Storyboard Readiness ist blocked.', text)
        self.assertIn('if (data.execution_status === "failed")', text)
        self.assertIn("Asset Execution Stub fehlgeschlagen.", text)
        self.assertIn("confirm_provider_costs: confirmed", text)
        self.assertIn('openai_image_model: "gpt-image-2"', text)
        self.assertIn('openai_image_size: "1024x1024"', text)
        self.assertIn("Bilddatei gespeichert", text)
        self.assertIn("output_path:", text)
        self.assertIn("output_exists=false", text)
        self.assertIn("file_size_bytes=", text)
        self.assertIn("Warnings / Write failed", text)
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
        self.assertIn("provider_readiness", data)
        pr = data["provider_readiness"]
        self.assertIn("live_assets", pr)
        self.assertIn("voice_elevenlabs", pr)
        self.assertIn("voice_openai", pr)
        self.assertIn("motion_runway", pr)
        paths = data["story_engine_relative"]
        self.assertIn("export_package", paths)
        self.assertEqual(paths["export_formats"]["path"], "/story-engine/export-formats")
        self.assertEqual(
            data["production_proof_summary_relative"]["path"],
            "/founder/production-proof/summary",
        )
        self.assertEqual(
            data["video_generate_relative"]["path"],
            "/founder/dashboard/video/generate",
        )

    def test_dashboard_config_provider_readiness_missing_env_is_missing(self):
        client = TestClient(app)
        with patch.dict(
            os.environ,
            {
                "LEONARDO_API_KEY": "",
                "ELEVENLABS_API_KEY": "",
                "OPENAI_API_KEY": "",
                "RUNWAY_API_KEY": "",
            },
            clear=False,
        ):
            r = client.get("/founder/dashboard/config")
        self.assertEqual(r.status_code, 200, msg=r.text)
        pr = r.json().get("provider_readiness") or {}
        self.assertEqual((pr.get("live_assets") or {}).get("status"), "missing")
        self.assertEqual((pr.get("voice_elevenlabs") or {}).get("status"), "missing")
        self.assertEqual((pr.get("voice_openai") or {}).get("status"), "missing")
        # Runway ist optional: missing -> optional_missing
        self.assertEqual((pr.get("motion_runway") or {}).get("status"), "optional_missing")

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

    def test_storyboard_dashboard_markers_and_contract_guard(self):
        client = TestClient(app)
        r = client.get("/founder/dashboard")
        self.assertEqual(r.status_code, 200, msg=r.text)
        text = r.text
        self.assertIn("Storyboard erstellen", text)
        self.assertIn("Storyboard Plan", text)
        self.assertIn("Storyboard Readiness", text)
        self.assertIn("Asset Plan", text)
        self.assertIn("Asset Execution Stub", text)
        self.assertIn("OpenAI Image Live", text)
        self.assertIn("/story-engine/storyboard-plan", text)
        self.assertIn("/story-engine/storyboard-readiness", text)
        self.assertIn("/story-engine/asset-generation-plan", text)
        self.assertIn("/story-engine/asset-execution-stub", text)
        self.assertIn("/story-engine/openai-image-live-execution", text)
        self.assertIn("runStoryboardOnlyInternal", text)
        self.assertIn("runStoryboardReadinessOnlyInternal", text)
        self.assertIn("runAssetGenerationPlanOnlyInternal", text)
        self.assertIn("runAssetExecutionStubOnlyInternal", text)
        self.assertIn("runOpenAIImageLiveOnlyInternal", text)
        self.assertIn("lastStoryboard", text)
        self.assertIn("lastStoryboardReadiness", text)
        self.assertIn("lastAssetPlan", text)
        self.assertIn("lastAssetExecutionStub", text)
        self.assertIn("lastOpenAIImageLive", text)
        self.assertIn("Bilddatei gespeichert", text)
        self.assertIn("output_path:", text)
        self.assertIn("output_exists=false", text)
        self.assertEqual(
            set(GenerateScriptResponse.model_fields.keys()),
            {"title", "hook", "chapters", "full_script", "sources", "warnings"},
        )

    @unittest.skipUnless(shutil.which("node"), "node nicht im PATH — Syntaxcheck übersprungen")
    def test_dashboard_embedded_script_node_syntax_ok_and_video_handlers_wired(self):
        """HOTFIX-Regression: gebrochene Regex-Literals im Script blockieren gesamtes Dashboard-JS."""
        client = TestClient(app)
        r = client.get("/founder/dashboard")
        self.assertEqual(r.status_code, 200, msg=r.text)
        text = r.text
        self.assertIn("fdApplyOpenAiImageMiniSmokePreset", text)
        self.assertIn("fdSubmitVideoGenerate", text)
        self.assertIn('getElementById("fd-video-generate-submit")', text)
        self.assertIn("await fdSubmitVideoGenerate()", text)
        start = text.find("<script>")
        end = text.rfind("</script>")
        self.assertGreater(start, 0)
        self.assertGreater(end, start)
        js = text[start + len("<script>") : end]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as tf:
            tf.write(js)
            tpath = tf.name
        try:
            proc = subprocess.run(
                ["node", "--check", tpath],
                capture_output=True,
                text=True,
                timeout=90,
            )
            self.assertEqual(
                proc.returncode,
                0,
                msg=(proc.stderr or proc.stdout or "").strip() or "node --check fehlgeschlagen",
            )
        finally:
            try:
                os.unlink(tpath)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
