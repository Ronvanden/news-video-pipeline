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

### Operator-Workflow (CLI, keine Dashboard-Writes)
1. Neu von Thema/URL/Skript bis Preview + Open-Me: `scripts/run_fresh_topic_preview_smoke.py` (siehe BA 30.2)
2. Oder Preview-Smoke nur mit bestehendem Manifest: `scripts/run_preview_smoke_auto.py`
3. Oder nur Preview aus Bundle: `scripts/render_local_preview_from_bundle.py`
4. Optional Pack aktualisieren: `scripts/build_production_pack_v1.py` mit `--local-preview-render-result` / `--preview-video`
5. Human Review patchen: `scripts/patch_human_preview_review.py`
6. Readiness: `scripts/run_final_render_readiness_gate.py`
7. Final lokal (nur explizit): `scripts/run_safe_final_render.py --execute`

### Tests
`tests/test_phase10_founder_dashboard.py` prüft u. a. die deutschen Basis-Strings und `refreshProductionFlowPanel`.
