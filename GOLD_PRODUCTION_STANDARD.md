# Gold Production Standard (Referenzlauf)

Dieses Dokument beschreibt den **einen** definierten Gold-Pfad: von gespeichertem Skript bis zu Kostenmetadaten und Control-Panel-Sicht — **ohne echte Provider-Aufrufe** und **ohne Video-Render** (Stand BA 8.8).

## Voraussetzungen

- Firestore erreichbar (Named Database wie in `DEPLOYMENT.md` / `FIRESTORE_DATABASE`).
- `production_jobs`-Dokument mit gültigen `generated_script_id` und `script_job_id`.
- `generated_scripts` mit nutzbarem `full_script` (oder Kapiteln, aus denen der Szenenplan ableitbar ist).

## Pflichtstufen (Reihenfolge)

1. **Intake** — Script-Job und gespeichertes Skript liegen vor (`script_jobs` / `generated_scripts`).
2. **Script** — `generated_scripts` entspricht dem festen `/generate-script`-Vertrag.
3. **Scene Plan** — `POST /production/jobs/{id}/scene-plan/generate` → Collection `scene_plans`.
4. **Assets** — `POST …/scene-assets/generate` → `scene_assets` (Prompt-Entwürfe).
5. **Voice** — `POST …/voice-plan/generate` → `voice_plans`.
6. **Render Manifest** — `POST …/render-manifest/generate` → `render_manifests`.
7. **Files** — `POST …/files/plan` → `production_files`.
8. **Costs** — `POST …/costs/calculate` → `production_costs` (Heuristik in EUR, inkl. Baseline/Varianz ab BA 8.7).
9. **Audit** — optional `POST /production/audit/run` für strukturierte Befunde.
10. **Control Panel** — `GET /production/control-panel/summary` für Founder-Übersicht.

## Akzeptanz

- Alle obigen Schritte sind **idempotent** beim erneuten Aufruf (Warnhinweise statt harter Fehler, sofern Daten konsistent).
- Kein HTTP **500** bei erwartbaren Qualitätslücken (Transkript, kurze Quelle) — siehe Input-Quality-Guard (BA 8.5) und `warnings`.
- Referenz-Test: `tests/test_ba88_full_production_run.py` (gemocktes Repository).

## Nicht-Ziel

- Automatisches Publishing, echtes TTS, echtes Rendering, Upload zu Drittplattformen.
