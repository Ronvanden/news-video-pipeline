## Einordnung (BA 30.x–32.x vs. Fresh Preview)

- **Aktuelle Produktionslinie (lokal, Founder Dashboard):** **BA 30.x–31.x** bauen das **Fresh Preview Cockpit** — Diagnose, Readiness, Operator Review, Guided Flow, Final-Render-**Vorbereitung** und **CLI-Handoffs** (read-only im Browser, kein Final-Render-Start aus dem UI).
- **Direkter Langform-Pfad URL → `final_video.mp4`:** **BA 32.3** — Panel **„Video generieren“**, `POST /founder/dashboard/video/generate` → `run_ba265_url_to_final` → Ausgabe unter **`output/video_generate/<run_id>/`** (Default u. a. **600 s** Ziel-Länge). Das ist **nicht** der Fresh-Preview-Dry-Run; Fresh Preview bleibt für schnelle Gates und Preview-Smoke inkl. Open-Me.
- **Runway Live Motion:** **BA 32.1** — API liefert **Readiness/Blocking** (422/Warnungen), **keine** integrierte Runway-Clip-Erzeugung in `run_ba265_url_to_final` (siehe Abschnitt **BA 32.3** unten und [PIPELINE_PLAN.md](../../PIPELINE_PLAN.md)).
- **Nächster Fokus (Roadmap):** **BA 32.3+** — Zielbild „URL eingeben → Video generieren → **10-Minuten**-Produktionslauf“ weiter verfeinern; Teilentlastung bereits **BA 32.0** (Caps); vollständiger Longform-Smoke weiter **BA 26.8** (*planned*).

Kanone: [PIPELINE_PLAN.md](../../PIPELINE_PLAN.md) (Phasenübersicht + BA-Tabelle).

---

## BA 30.0 — Founder Dashboard: Produktionsfluss (read-only)

### Ziel
Im **Founder Dashboard** (`GET /founder/dashboard`) zeigt das Panel **„Produktionsfluss“** (read-only) den Stand von:
- Production Pack / Approval / Preflight
- Motion-Clips / Timeline-Pfad / Render-Input-Bundle-Verweis
- Lokale Vorschau (`local_preview_*`)
- `human_preview_review_result`
- `final_render_readiness_result`

### Datenquelle
Das Panel liest aus dem eingebetteten Export/Snapshot-Feld `production_summary` (oder kompakt `production_pack_summary`, sofern dort nichts Tieferes liegt — bevorzugt volles Summary).

### BA 30.1 — Preview Smoke Golden Path / Open-Me Report
Vollständiger kontrollierter Preview-Smoke inkl. BA-29.0-Pack und lokaler MP4-Vorschau: `scripts/run_preview_smoke_auto.py` (`--run-id`, `--output-root`). Ergebnis für den Founder zuerst in **`output/.preview_smoke_work/<run_id>/OPEN_PREVIEW_SMOKE.md`** (deutsch, welches Video öffnen, nächste Schritte); technische Details in `preview_smoke_auto_summary_<run_id>.json` (`open_preview_smoke_report_path`). Keine Live-Provider-Calls.

### BA 30.2 — Fresh Topic to Preview Smoke
Neues Thema oder URL ohne bestehendes Manifest: `scripts/run_fresh_topic_preview_smoke.py` erzeugt zuerst Skript/Pack/Placeholder-Assets, dann optional denselben Preview-Smoke wie BA 30.1. **`--dry-run`** stoppt nach dem Manifest (schneller Gate-Check). Live-Bildgenerierung nur mit **`--allow-live-assets`**.

### BA 30.3 — Fresh Preview im Dashboard
Nach einem Fresh-Smoke-Lauf zeigt das Founder-Dashboard-Panel **Fresh Preview Smoke** read-only den letzten Run unter `output/fresh_topic_preview/` inkl. Hinweis auf `OPEN_PREVIEW_SMOKE.md` und nächsten Operator-Schritt — ohne JSON-Dateien manuell zu suchen.

### BA 30.4 — Readiness-Interpretation (Operator)
- **blocked:** Pflichtartefakte fehlen oder JSON ungültig/leer (Skript ohne nutzbaren Text, Pack ohne Szenen, Manifest unlesbar). → Smoke erneut oder Artefakte reparieren.
- **warning:** Kern vorhanden, aber Preview-Summary/Open-Me fehlt, Summary `ok != true`, oder Manifest wirkt nur Placeholder (keine externen/Clip-Pfade). → Lauf ohne `--dry-run` / Pfade prüfen / optional Live-Assets nur mit Keys.
- **ready:** Skript, Pack, Manifest, Summary und Open-Me konsistent, Summary `ok`, keine Gate-Blocker. → Video/Open-Me öffnen, Human Review-Workflow.

### BA 30.5 — Fresh Preview: Operator Controls (read-only)
Im Panel **Fresh Preview Smoke**: **„Fresh Preview aktualisieren“** holt nur den Snapshot erneut (kein Smoke-Start im Browser). Copy-Buttons kopieren absolute Pfade in die Zwischenablage; fehlende Dateien sind als „nicht vorhanden“ gekennzeichnet, Copy ist deaktiviert. **Nächster Schritt (Operator)** und die drei Listen (**blockierende Gründe**, **Readiness-Hinweise**, **Scan-/Datei-Warnungen**) unterstützen die Einordnung ohne neue Server-Endpunkte oder Schreibzugriffe.

### BA 30.6 — Founder Dashboard: Visual Upgrade V1
Gleiche Daten und Endpunkte wie BA 30.3–30.5; **nur** UI: moderneres Operator-Cockpit (Tokens `--vp-*`, Karten/Schatten, Hero mit **VideoPipe Founder Cockpit**, Pills **Production Ready** / **Local Preview Pipeline**), klareres Fresh-Preview-Panel inkl. kompaktem Status-Strip. Keine neuen Writes, keine Provider-Calls; Header-**„Zum Preview-Panel“** = Scroll zum Local-Preview-Panel, kein automatisierter Smoke.

### BA 30.7 — Operator: Fresh Preview Dry-Run im Browser
Im Panel **Fresh Preview starten**: **„Dry-Run starten“** sendet `POST /founder/dashboard/fresh-preview/start-dry-run` (genau **Topic** oder **URL**, nie beides; optional Dauer/Max-Szenen). Der Server führt nur die BA-30.2-Kette bis **Manifest** aus (`dry_run=True`, Placeholder-Assets). Anschließend **Fresh-Preview-Snapshot** im Panel aktualisieren (automatisch nach Erfolg). Für vollen Preview-Smoke inkl. MP4 weiterhin CLI `scripts/run_fresh_topic_preview_smoke.py` **ohne** `--dry-run`.

### BA 30.8 — Handoff: Full Preview Smoke nach Dry-Run
Nach erfolgreichem Dry-Run zeigt das Dashboard einen **kopierbaren** PowerShell-/POSIX-CLI-Befehl (`handoff_cli_command_*`) mit neuer Run-ID `…_full`, gleicher Topic/URL-Logik und Parametern — **ohne** Dashboard-Ausführung, **ohne** `--allow-live-assets` im generierten Text. Vollständiger Lauf nur lokal im Terminal; Live-Assets nur bei manueller Ergänzung von `--allow-live-assets`.

### BA 30.9 — Artifact Access: Textdateien im Browser
**„Öffnen“** im Fresh-Preview-Pfad-Grid startet `GET /founder/dashboard/fresh-preview/file?path=…` (nur **`.md`/`.json`/`.txt`**, read-only, max. 1 MB, Whitelist-Pfade unter `output` wie Fresh-Run, Summary-JSON, `OPEN_PREVIEW_SMOKE.md`). Keine Videos über diese Route; keine Writes.

### BA 32.1 — Runway Live Motion: Readiness & Blocking (kein Fake-Live)
Vor **`POST /founder/dashboard/video/generate`** (**BA 32.3**) prüft die API: Live-Flags (`allow_live_assets` / `allow_live_motion`) erfordern **`confirm_provider_costs`** (sonst **422** `confirm_provider_costs_required_when_live_flags`). **`allow_live_motion`** ohne nicht-leeres **`RUNWAY_API_KEY`** → **422** `live_motion_requires_runway_connector`. **BA 32.63:** Ist **`max_motion_clips` ≥ 1** und **`RUNWAY_API_KEY`** gesetzt, plant **`run_ba265_url_to_final`** nach Fit-to-Voice höchstens **einen** Runway Image-to-Video-Clip für den ersten Motion-Slot und schreibt **`video_path`** + **`generation_mode: runway_video_live`** in **`asset_manifest.json`** (Details: `docs/runbooks/real_video_build_wiring_map.md`, **BA 32.63**). **BA 32.64** trennt **`allow_live_motion_requested`** (Checkbox) von **`motion_requested`** / **`motion_rendered`** / **`motion_ready`** im `readiness_audit`. Ohne Key oder bei **`max_motion_clips=0`**: kein Runway-Render; optional **`runway_key_missing_motion_skipped`** bzw. Hinweis, wenn Live-Motion gewünscht war aber **`max_motion_clips=0`**.

### BA 32.3 — Dashboard: URL → `final_video.mp4` (eigenes Panel)
Im Founder Dashboard liegt **oberhalb** des Fresh-Preview-Panels die Karte **„Video generieren“** (`panel-ba323-video-generate`). **„Video generieren“** sendet `POST /founder/dashboard/video/generate` mit URL, Dauer (Default 600 s), Szenen-/Live-Asset-Caps und Motion-Strategie-Parametern (Metadaten im `scene_asset_pack` unter `metadata.ba323_motion_strategy`). Der Server ruft **`run_ba265_url_to_final`** (`scripts/run_url_to_final_mp4.py`) auf; Ausgabe unter **`output/video_generate/<run_id>/`** inkl. `final_video.mp4` und `run_summary.json`. **Fresh Preview** bleibt das Diagnose-/Review-Cockpit (Dry-Run, Snapshot, Readiness); dieser Flow ist der **kontrollierte Longform-Produktionsbutton**. Live-Bilder nur mit Checkbox **Provider-Kosten bestätigen** + `asset_runner_mode=live`. Live-Motion / Runway: siehe **BA 32.1** / **BA 32.63** (`max_motion_clips` ≥ 1 + `RUNWAY_API_KEY` → optional ein Clip in `asset_manifest`). Readiness-Felder **BA 32.64**; Erstlauf-Chronik **BA 32.65** in `docs/runbooks/real_video_build_wiring_map.md`. Meta: `GET /founder/dashboard/config` → `video_generate_relative`.

### BA 32.65 — Erster erfolgreicher Runway Hybrid Smoke (Doku)

**Kurz:** Erster nachweislicher Hybrid-Lauf über **Video generieren**: ein geplanter Motion-Slot → echter Runway-Clip als `video_path` im Manifest, **zwei** `gemini_image_live`-Stills, **ElevenLabs**-Voice, **`final_video.mp4`** ohne Render-Placeholder; `readiness_audit` mit **`motion_ready`/`motion_rendered`/`motion_requested`** konsistent (**BA 32.64**), `provider_blockers` leer im Referenzlauf.

**Referenz:** `run_id` **`video_gen_10m_1778273622251`** — vollständige Kennzahlen-Tabelle, Was-beweist-/Was-nicht-, Readiness-Semantik und **BA 32.66**-Ausblick: [docs/runbooks/real_video_build_wiring_map.md](real_video_build_wiring_map.md) Abschnitt **„BA 32.65 — Erster erfolgreicher Runway Hybrid Smoke“**.

### BA 31.0 — Operator Review Loop (nach Full Preview Smoke)
Nach einem vollständigen Preview-Smoke (Summary unter `output/preview_smoke_auto_summary_<run_id>.json`, optional `OPEN_PREVIEW_SMOKE.md`) zeigt das Dashboard im Panel **Fresh Preview** die Karte **Operator Review**: Status-Badge (approve / rework / blocked / pending), Gründe und empfohlene nächste Aktion — **rein read-only**, keine gespeicherte Freigabe und keine Freigabe-Schaltflächen. Daten kommen aus dem gleichen Snapshot-Endpunkt wie BA 30.3–30.4 (`evaluate_operator_review`).

### BA 31.1 — Guided Production Flow
Oben im Hauptbereich (unter Executive Row) zeigt **Production Flow** die Schritte vom Input bis Final Render mit Status-Badges und einer Box **Nächster Schritt** — abgeleitet aus dem Fresh-Preview-Snapshot (`guided_flow_*`, `build_guided_production_flow`). Keine Persistenz neuer Entscheidungen; Fokus Orientierung für den Operator.

### BA 31.1b — Guided Flow Microcopy
Klarstellung für Operatoren: **Snapshot** = Dashboard-Abgleich per **„Fresh Preview aktualisieren“**; nach lokalem Full Preview den Handoff-Befehl ausführen und danach im Dashboard aktualisieren. Handoff-Box mit Kurz-Hinweis nach dem kopierbaren CLI-Befehl.

### BA 31.2 — Final Render Preparation Gate
Die Karte **Final Render Preparation** zeigt read-only, ob der nächste Schritt „Final Render vorbereiten“ fachlich freigegeben ist oder blockiert bleibt — abgeleitet aus dem gleichen Snapshot wie Operator Review (kein Button zum Starten eines Final Renders im Dashboard in dieser BA).

### BA 31.3 — Final Render Input Checklist
Unter dem Preparation Gate: **Final Render Input Checklist** — welche konkreten Artefakte unter `output/` (und Fresh-Preview-Pfaden) vorhanden sind; Öffnen/Kopieren für zugelassene Text/JSON-Dateien wie bei BA 30.9 (erweiterte Root-JSONs und Local-Preview-Result im Preview-Work-Ordner).

### BA 31.4 — Safe Final Render Handoff
Unter der Input Checklist: Karte **Safe Final Render Handoff** — nur **Text/CLI zum Kopieren** für `scripts/run_safe_final_render.py` (Production Summary unter `output/production_pack_<run_id>/production_summary.json`, Ausgabeordner z. B. `output/safe_final_render_<run_id>`). Sichtbar, wenn Gate **ready** und Checkliste **ready** oder **warning**; bei Sperre Gründe und feste Kurzmeldung. **Kein** Final-Render-Start im Dashboard, keine Provider-Calls, keine neuen Writes — reiner Operator-Handoff.

### Operator-Workflow (CLI, keine Dashboard-Writes)
0. URL direkt bis **`final_video.mp4`** (clean Render-Pfad, ohne Fresh-Preview-Paket): `python scripts/run_url_to_final_mp4.py --url …` (siehe `--help`; gleiche Kernlogik wie Dashboard **BA 32.3**)
1. Neu von Thema/URL/Skript bis Preview + Open-Me: `scripts/run_fresh_topic_preview_smoke.py` (siehe BA 30.2)
2. Oder Preview-Smoke nur mit bestehendem Manifest: `scripts/run_preview_smoke_auto.py`
3. Oder nur Preview aus Bundle: `scripts/render_local_preview_from_bundle.py`
4. Optional Pack aktualisieren: `scripts/build_production_pack_v1.py` mit `--local-preview-render-result` / `--preview-video`
5. Human Review patchen: `scripts/patch_human_preview_review.py`
6. Readiness: `scripts/run_final_render_readiness_gate.py`
7. Final lokal (nur explizit): `scripts/run_safe_final_render.py --execute`

### Tests
`tests/test_phase10_founder_dashboard.py` prüft u. a. die deutschen Basis-Strings und `refreshProductionFlowPanel`.
