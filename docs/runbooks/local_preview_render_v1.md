## BA 29.2 — Lokale Preview aus `render_input_bundle.json`

### Ziel
Operator-sichtbare, **vereinfachte MP4-Vorschau** (Stillframes / kurze Clip-Segmente) aus dem Render-Input-Bundle — **kein** finales YouTube-Master, **keine** Live-Provider-Calls.

### Voraussetzungen
- FFmpeg im `PATH` (`ffmpeg -version` muss funktionieren). Ohne FFmpeg: kontrollierter Abbruch mit `error_code: ffmpeg_missing` (kein Stacktrace-Pflicht).
- Bilder (`png`/`jpg`/…) und/oder echte Videoclips (`mp4`/…); JSON-„Placeholder“-Clips werden wie Stubs behandelt → Stillbild fallback.

### BA 29.2b — Medienpfade im `render_input_bundle.json`
Wenn `image_paths` / `clip_paths` leer waren, aber `asset_manifest_path` gesetzt ist, füllt `build_render_input_bundle` (siehe `app/production_assembly/render_input_bundle.py`) die Listen aus `asset_manifest.assets[]`: Bildpriorität `selected_asset_path` → `generated_image_path` → `image_path`; Clips `video_path`, dann `clip_path`. Relative Pfade werden relativ zum Ordner der `asset_manifest.json` aufgelöst. Zusammenfassung: `media_path_hydration_summary` (`hydration_version: ba29_2b_v1`).

### BA 29.2d — Preview-Smoke: Medienpfade beim Prepared-Manifest
Der Auto-Runner (`scripts/run_preview_smoke_auto.py` / `prepare_asset_manifest_for_smoke`) legt eine Kopie des Manifests unter `output/.preview_smoke_work/<run_id>/` ab. Relative Einträge in `assets[]` würden dort sonst gegen den **Work-Ordner** statt gegen den ursprünglichen Pack-Ordner aufgelöst werden → `images_collected` > 0, aber `images_found`/`clips_found` = 0 und Local Preview endet in `no_media_segments_built`.

Vor dem Schreiben des prepared Manifests wendet die Pipeline **`preserve_or_absolutize_asset_media_paths`** an (Felder u. a. `selected_asset_path`, `generated_image_path`, `image_path`, `video_path`, `clip_path`, `voice_path`): relative Pfade werden gegen den Ordner der **Quell**-`asset_manifest.json` geprüft und bei existierender Datei als **absoluter** Pfad gespeichert. Zusammenfassung: `media_path_preservation_summary` (`media_path_preservation_version: ba29_2d_v1`, Zähler + optional `warnings`).

### BA 30.1 — Preview Smoke: Open-Me-Report (`OPEN_PREVIEW_SMOKE.md`)
Nach einem Lauf von `scripts/run_preview_smoke_auto.py` wird (Erfolg oder Fehler) versucht, unter `output/.preview_smoke_work/<run_id>/OPEN_PREVIEW_SMOKE.md` einen **deutschsprachigen** Operator-Report zu schreiben: Status, Run-ID, Pfade zu Video/JSON/Bundle/Production-Pack (falls vorhanden), Kennzahlen (Dauer, Szenen, Bilder/Clips, FFmpeg), Blocker, Warnungen und **Nächste Schritte** (Video öffnen, Preview prüfen, Human Review oder erneuter Smoke). Die JSON-Summary `preview_smoke_auto_summary_<run_id>.json` enthält `open_preview_smoke_report_path`. Bei Schreibfehlern: `open_preview_smoke_write_warnings` im Summary, kein Abbruch des Smoke-Laufs.

### BA 30.2 — Fresh Topic / URL → Preview Smoke
End-to-End ohne zuvor vorhandenes `asset_manifest`: `scripts/run_fresh_topic_preview_smoke.py` mit genau einer Eingabe (`--topic`, `--url` oder `--script-json`). Es wird unter `output/fresh_topic_preview/<run_id>/` ein Skript + `scene_asset_pack.json` erzeugt, der Asset-Runner legt `generated_assets_<run_id>/asset_manifest.json` an (Standard: **placeholder**, keine Live-Provider ohne `--allow-live-assets`). Ohne `--dry-run` folgt dieselbe Kette wie `run_preview_smoke_auto.py` inkl. `OPEN_PREVIEW_SMOKE.md`. Motion/Clips in BA 29.0 bleiben Dry-Run-tauglich; `--provider` wird nur durchgereicht.

### BA 30.3 — Founder Dashboard: Fresh-Preview-Snapshot
Das Founder Dashboard (`GET /founder/dashboard`) lädt beim Start read-only `GET /founder/dashboard/fresh-preview/snapshot` und zeigt im Panel **Fresh Preview Smoke (BA 30.3–30.5)** an, ob unter `output/fresh_topic_preview/` der jüngste Run existiert und welche Artefakte (`script.json`, Pack, Manifest, `preview_smoke_auto_summary_*.json`, `OPEN_PREVIEW_SMOKE.md`) vorliegen. Kein Schreibzugriff, keine externen Calls. Meta: `GET /founder/dashboard/config` → `fresh_preview_snapshot_relative`.

### BA 30.4 — Fresh Preview Readiness Gate
Derselbe Snapshot-Endpunkt liefert additiv **Readiness** (`readiness_status`: ready / warning / blocked, `readiness_score`, `readiness_reasons`, `blocking_reasons`) aus Pflichtdateien, optionalen JSON-Inhaltschecks (Titel/Hook/Kapitel, Szenen im Pack, Manifest-Assets) und dem Zustand der Preview-Smoke-Summary (`ok`). Im Dashboard: Badge, Score, Blocking-/Hinweiszeilen. Keine Provider-Calls.

### BA 30.5 — Fresh Preview: Operator Controls im Dashboard
Im Panel **Fresh Preview Smoke** (Founder Dashboard): Schaltfläche **„Fresh Preview aktualisieren“** lädt den Snapshot erneut (read-only `GET /founder/dashboard/fresh-preview/snapshot`). Copy-Buttons für die wichtigsten absoluten Pfade (Run-Ordner, `script.json`, Pack, Manifest, Summary, `OPEN_PREVIEW_SMOKE.md`); fehlende Pfade als „nicht vorhanden“, Copy deaktiviert. **Nächster Schritt** und Readiness-Listen (Blocker vs. Hinweise vs. Scan-Warnungen) bleiben rein anzeigend — keine Datei-Download-Route, keine Firestore-/Provider-Calls.

### BA 30.6 — Founder Dashboard: Visual Upgrade (ohne neue Pipeline-Logik)
Nur Darstellung in `app/founder_dashboard/html.py`: dunkles Cockpit-Layout, einheitliche Karten/Schatten, Hero **VideoPipe Founder Cockpit** mit Status-Pills; Fresh-Preview-Panel optisch strukturierter (Kurz-Strip, Readiness-Banner, getrennte Hinweis-Boxen). **Kein** zusätzlicher Smoke-Start im Browser — der Header-Link **„Zum Preview-Panel“** scrollt nur zum bestehenden Local-Preview-Bereich.

### BA 30.7 — Fresh Preview Dry-Run aus dem Founder Dashboard
`POST /founder/dashboard/fresh-preview/start-dry-run` mit JSON-Body: genau eines von `topic` oder `url`, optional `duration_target_seconds` (Default 45), `max_scenes` (Default 6). Immer **Dry-Run** (Stopp nach `asset_manifest.json`), **placeholder**-Asset-Runner, kein `live`-Modus aus dem Dashboard. Run-ID `fresh_dash_<timestamp_ms>`. Nach Erfolg im UI: Snapshot per **„Fresh Preview aktualisieren“** bzw. automatischer Refresh. Meta: `GET /founder/dashboard/config` → `fresh_preview_start_dry_run_relative`.

### BA 30.8 — CLI-Handoff nach Dashboard-Dry-Run (Full Preview Smoke lokal)
Bei **ok: true** liefert dieselbe Response additiv `handoff_cli_command` / `handoff_cli_command_powershell` für `scripts/run_fresh_topic_preview_smoke.py` mit Run-ID `<dry_run_id>_full`, **ohne** `--dry-run`, **ohne** `--allow-live-assets`, `--provider placeholder`. Der Operator kopiert den Befehl ins Terminal (Repo-Root). Hinweis im UI: für Live-Assets nur bei bewusstem `--allow-live-assets` + Keys.

### BA 30.9 — Fresh Preview: Artefakte im Browser öffnen (read-only)
`GET /founder/dashboard/fresh-preview/file?path=<URL-encoded absoluter Pfad>` liefert Textartefakte (**`.md`**, **`.json`**, **`.txt`**) nur aus den vom Snapshot genutzten Bereichen: Unterbaum **`output/fresh_topic_preview/`**, **`output/preview_smoke_auto_summary_*.json`**, **`output/.preview_smoke_work/<run_id>/OPEN_PREVIEW_SMOKE.md`**. Max. **1 MB** pro Datei; keine Symlinks; kein Zugriff auf beliebige andere `output`-Dateien oder außerhalb von `output`. Fehler: **404** (nicht gefunden), **403** (Policy), **413** (zu groß). Im Dashboard neben **Kopieren** der Link **„Öffnen“** (neuer Tab) — **kein** MP4 über diese Route in BA 30.9. Meta: `GET /founder/dashboard/config` → `fresh_preview_file_relative`.

### BA 31.0 — Operator Review (Full Preview Smoke, read-only)
Der Fresh-Preview-Snapshot (`GET /founder/dashboard/fresh-preview/snapshot`) enthält additiv eine **Review-Empfehlung** aus vorhandenen Artefakten: `review_decision` (approve / rework / blocked / pending), kurze Gründe und `review_next_action`. **Keine** persistierte Freigabe, **keine** Buttons zum Freischalten — nur Orientierung nach Readiness, Summary-`ok` und OPEN_PREVIEW-Pfaden. UI: Karte **Operator Review** im Fresh-Preview-Cockpit. Logik: `evaluate_operator_review` in `app/production_assembly/fresh_preview_snapshot.py` (`operator_review_version: ba31_0_v1`).

### BA 31.1 — Guided Production Flow
Der Snapshot liefert additiv `guided_flow_steps` (Input → Dry-Run → Snapshot → Full Preview → Review → Final Render) mit Status pro Schritt sowie **Nächster Schritt** (`guided_flow_next_step_action`). Rein read-only aus bestehenden Snapshot-Feldern; keine neuen Writes. UI im Founder Dashboard: **Production Flow** direkt unter der Executive Row.

### BA 31.1b — Guided Flow Microcopy
Schritt **Snapshot** erklärt den Bezug zu **„Fresh Preview aktualisieren“** (`detail` im Snapshot); bei nur Dry-Run beschreibt der nächste Schritt explizit CLI-Handoff, lokales Ausführen und erneutes Aktualisieren. Zusätzliche Hilfezeile in der Production-Flow-Card und Hinweis in der Handoff-Box nach dem CLI-Befehl. `guided_flow_version: ba31_1b_v1`.

### BA 31.2 — Final Render Preparation Gate
Der Fresh-Preview-Snapshot enthält additiv `final_render_gate_*`: read-only, ob die **Vorbereitung** für einen sicheren Final Render sinnvoll freigegeben ist (locked / ready / blocked / needs_rework) — **kein** Render-Start im Browser. UI: Karte **Final Render Preparation** unter Operator Review. Logik gekoppelt an Operator Review + Readiness + Summary/Open-Me. `final_render_gate_version: ba31_2_v1`.

### BA 31.3 — Final Render Input Checklist
Read-only Liste typischer Render-Inputs (Skript, Pack, Manifest, Summary, Open-Me, `render_input_bundle_<run_id>.json`, Motion-Manifeste, Production-Pack-Ordner, optional Local-Preview-Result). Gesamtstatus ready/warning/blocked/pending abhängig vom Preparation Gate und Dateipräsenz. UI unter **Final Render Preparation**. `final_render_input_checklist_version: ba31_3_v1`.

### BA 31.4 — Safe Final Render Handoff
Wenn **Final Render Preparation** **ready** ist und die **Input Checklist** mindestens **ready** oder **warning** (nicht pending/blocked), liefert der Snapshot additiv einen **kopierbaren** CLI-Handoff für `scripts/run_safe_final_render.py`: `--production-summary output/production_pack_<run_id>/production_summary.json`, `--output-dir output/safe_final_render_<run_id>` (PowerShell-Variante mit Zeilenfortsetzung im Dashboard). **Kein** `--execute` im generierten Text; kein Final-Render-Start im Browser. Fehlt `production_summary.json` noch, erscheint ein Hinweis im Snapshot/UI (`safe_final_render_handoff_warning`). `safe_final_render_handoff_version: ba31_4_v1`.

### CLI
```powershell
python scripts/render_local_preview_from_bundle.py `
  --bundle output/render_input_bundle_<run_id>.json `
  --output-dir output/preview_<run_id> `
  --timeline output/motion_timeline_manifest_<run_id>.json
```

### Output (typisch)
- `local_preview.mp4` (oder `--output-name`)
- `local_preview_render_result.json`
- `README_PREVIEW.md`, `OPEN_PREVIEW.txt`

### Nächste Schritte
- BA 29.3: Artefakte in den Production Pack legen (`build_production_pack_v1.py` Optionen).
- BA 29.4/29.5: Human Review + Final-Render-Readiness vor einem expliziten Final-Render.
