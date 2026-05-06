# Pipeline-Plan — News- und YouTube-to-Video

Ziel dieses Dokuments ist eine **kontrollierte Weiterentwicklung**: Phasen, Status, Akzeptanzkriterien, Tests und dokumentierter Fehler-Rücklauf (siehe [ISSUES_LOG.md](ISSUES_LOG.md)).  
Neue fachliche Bausteine werden idealerweise zuerst mit [MODULE_TEMPLATE.md](MODULE_TEMPLATE.md) skizziert.

---

## Gesamtziel

Eine **zuverlässige, modulare Pipeline** von **Quellen** (Nachrichten-URLs, YouTube) zu **strukturierten, redaktionell nutzbaren Skripten** für längere Videoformate — mit **optionaler LLM-Nutzung**, **stabilem Fallback ohne API-Key**, **festem JSON-Vertrag** für Skript-Endpoints und klarer **Warn- und Fehlerlogik**. Spätere Phasen erweitern um Prüfung, Monitoring, Persistenz, Medienproduktion und Veröffentlichungsvorbereitung — ohne die bestehenden API-Verträge ungeplant zu brechen.

---

## Aktueller Stand (Kurz)

### BA 0.0 — Prompt Operating System (PPOS) V1 (**done / meta**)

**Zweck:** Meta-Governance-Layer für zukünftige BA-Prompts: **Global Prompt Ruleset**, Pattern Library, Token-Compression-Makros und Standard-BA-/Suite-Contracts. **Nicht Teil der Produktionsausführung**; keine Runtime-, API-, Firestore-, Frontend- oder `GenerateScriptResponse`-Änderung. Kanonische Dokumente: [docs/PROMPT_OPERATING_SYSTEM.md](docs/PROMPT_OPERATING_SYSTEM.md), [docs/PROMPT_PATTERNS.md](docs/PROMPT_PATTERNS.md), optionaler Effizienzleitfaden [docs/TOKEN_EFFICIENCY_GUIDE.md](docs/TOKEN_EFFICIENCY_GUIDE.md).

| Bereich | Stand |
|--------|--------|
| FastAPI, Health | Lokal und Cloud Run MVP v1 nutzbar |
| Skript aus Artikel-URL | `POST /generate-script` — Extraktion, LLM optional, Fallback |
| YouTube Transkript → Skript | `POST /youtube/generate-script` — gleicher Response-Vertrag wie Generate |
| Kanal-Discovery | `POST /youtube/latest-videos` — RSS, Scoring, ohne Data API |
| Review / Originalität | `POST /review-script` — V1 heuristisch (Phase 4 **done**) |
| Persistenz Jobs / Watchlist / Voice / Bild / Render / Publish | Teilweise (Phase 5 Schritt 1–4: Watchlist **CRUD** + **`/check`** + Firestore `watch_channels` / **`processed_videos`** / **`script_jobs`** + manueller **`POST /watchlist/jobs/{job_id}/run`** → **`generated_scripts`** — **kein** Scheduler/Auto-Run bis später geplant) |

Details zu Deploy und Tests: [README.md](README.md), [DEPLOYMENT.md](DEPLOYMENT.md).  
Agenten- und Qualitätsregeln: [AGENTS.md](AGENTS.md).

### Nächste Priorität (Ausrichtung)

| Strang | Rolle | Kurzhinweis |
|--------|--------|-------------|
| **BA 9.x Story Engine Kern** (**9.7–9.9**) | **abgeschlossen** | Umsetzung: **`GET /story-engine/template-health`**, Control-Panel **`template_optimization`** / **`story_intelligence`**; Canonical **„Story OS“:** [docs/STORY_ENGINE_OS.md](docs/STORY_ENGINE_OS.md). **`GenerateScriptResponse`** weiterhin **6 Felder**. |
| **Phase 7** — Voiceover (TTS) | **primär Makro-Produkt nach Story-Kern** | Ausführungsplan **Baustein 7.1–7.8:** [docs/phases/phase7_voice_bauplan.md](docs/phases/phase7_voice_bauplan.md); erste Provider-Wahl + Secret-Setup ohne Repo-Secrets ([DEPLOYMENT.md](DEPLOYMENT.md)). |
| **Betrieb** — Cloud Scheduler (+ optional IAP/OAuth) | **alternativ Betrieb** | HTTP-Endpunkte **`POST /watchlist/automation/run-cycle`** und **`POST /production/automation/run-daily-cycle`** existieren; zeitgesteuerte oder abgesicherte Aufrufe sind **Deploymentsache**, kein eigener Pipeline-Baustein in diesem Repo ohne separates Deliverable. |

*Reihenfolge-Hinweis:* Die **Story-Engine-Maturity-Linie bis 9.9** ist dokumentarisch/im Code **geschlossen**; neue Priorität liegt typischerweise bei **Phase 7 (Voice)** oder bei **GCP-Scheduling** entscheidbar (siehe Tabelle).

---

## Phasenübersicht

| # | Phase | Status |
|---|--------|--------|
| 1 | Skriptmotor | **done** |
| 2 | YouTube Channel Discovery | **done** |
| 3 | YouTube Transcript-to-Script | **done** |
| 4 | Script Review / Originality Check | **done** |
| 5 | Watchlist / Channel Monitoring | **next** |
| 6 | Script Job Speicherung | **planned** |
| 7 | Voiceover | **in progress** |
| 8 | Bild- / Szenenplan | **in progress** |
| 9 | Video Packaging | **planned** |
| 10 | Veröffentlichungsvorbereitung | **planned** |

**Hinweis zur Nummerierung:** Die **BA 9.x**-Bausteine (**Template Engine / Story Engine** in `app/story_engine/`) sind eine **eigene Produkt-Release-Linie** und **nicht** dasselbe wie **Phase 9** in dieser Tabelle (MP4/Packaging). Ausführlicher Bauplan: [PIPELINE_PLAN.md](PIPELINE_PLAN.md) (Abschnitt **„BA 9 — Template Engine / Story Engine (Produktachse)“**).

---

### Phase 1 — Skriptmotor

| | |
|--|--|
| **Status** | **done** |
| **Ziel** | Aus einer Nachrichten-URL ein strukturiertes Skript (Titel, Hook, Kapitel, `full_script`, Quellen, Warnungen) erzeugen; Dauer- und Wortlogik; LLM optional; Fallback ohne OpenAI. |
| **Endpoints** | `GET /health`, `POST /generate-script` |
| **Relevante Dateien** | `app/main.py`, `app/routes/generate.py`, `app/utils.py`, `app/models.py`, `app/config.py` |
| **Akzeptanzkriterien** | Fester JSON-Vertrag unverändert; kein HTTP 500 bei LLM-Fehler; `warnings` bei Fallback und Qualitätslücken; `python -m compileall app` grün. |
| **Bekannte Grenzen** | Qualität abhängig von Extraktion und Quelltext; kein automatischer Faktencheck. |
| **Nächster Schritt** | Phase 1 nur bei Regression oder Vertragsänderung anfassen; Änderungen mit README/AGENTS abstimmen. |

---

### Phase 2 — YouTube Channel Discovery

| | |
|--|--|
| **Status** | **done** |
| **Ziel** | Kanal identifizieren, neueste Videos per öffentlichem RSS listen, Heuristik-Score und Kurzbegründung für Auswahl langer Formate (inkl. Shorts-Abwertung). |
| **Endpoints** | `POST /youtube/latest-videos` |
| **Relevante Dateien** | `app/routes/youtube.py`, `app/youtube/service.py`, `app/youtube/rss.py`, `app/youtube/resolver.py`, `app/youtube/scoring.py`, `app/models.py` (`LatestVideos*`) |
| **Akzeptanzkriterien** | Response-Struktur stabil; sinnvolle `warnings` bei Auflösungs-/Feed-Fehlern; keine YouTube Data API Pflicht; Tests laut README/Agent-Regeln. |
| **Bekannte Grenzen** | `@handle`-Auflösung kann an Cookie-/Consent-Seiten scheitern; `/channel/UC…` bevorzugen; `summary` nur aus Metadaten, nicht aus Transkript. |
| **Nächster Schritt** | Optional Feintuning Scoring nur mit Plan-Eintrag und ISSUES_LOG bei Bugs. |

---

### Phase 3 — YouTube Transcript-to-Script

| | |
|--|--|
| **Status** | **done** |
| **Ziel** | YouTube-Video-URL → Transkript (öffentliche Untertitel) → gleiches Skript-Format wie Artikel-Pipeline; redaktionell als eigene Story, nicht Abschrift. |
| **Endpoints** | `POST /youtube/generate-script` |
| **Relevante Dateien** | `app/routes/youtube.py`, `app/utils.py` (Transkript, gemeinsame Skript-Pipeline), `app/models.py` |
| **Akzeptanzkriterien** | Gleicher Response-Vertrag wie `/generate-script`; bei fehlendem Transkript 200 mit leerem/minimalem Vertrag und klarer `warning`; keine Data API Pflicht. |
| **Bekannte Grenzen** | Nicht jedes Video hat Untertitel; Sprachen und Verfügbarkeit variieren. |
| **Nächster Schritt** | Nur bei Transkript-/Parsing-Problemen ändern; Vorgänge in ISSUES_LOG festhalten. |

---

### Phase 4 — Script Review / Originality Check

| | |
|--|--|
| **Status** | **done** (V1 heuristisch, Stand siehe README und `tests/test_review_script.py`) |
| **Ziel** | Zusätzliche Prüfstufe vor Voiceover/Bild/Video: Nähe zum Quelltext, lange gemeinsame Wortfolgen, Satz-Ähnlichkeit, grobe Einordnungs-Signale. Architektur **hybrid-fähig**; **V1 nur lokal** (kein `llm_review.py`). **`GenerateScriptResponse` unverändert**; Review eigener Vertrag. |
| **Endpoints** | `POST /review-script` — Request: `source_url`, `source_type`, `source_text`, `generated_script`, `target_language`, `prior_warnings`; Response: `risk_level`, `originality_score` (0–100, höher = eigenständiger), `similarity_flags`, `issues`, `recommendations`, `warnings`. |
| **Relevante Dateien** | `app/models.py` (`ReviewScriptRequest`, `ReviewScriptResponse`, …), `app/review/__init__.py`, `app/review/originality.py`, `app/review/service.py`, `app/routes/review.py`, `app/main.py` (Router), `README.md`, Tests: `tests/test_review_script.py`. |
| **Akzeptanzkriterien (V1)** | 200 + strukturiertes JSON; 422 wenn `source_text` und `generated_script` beide leer; kein Secret-/.env-Zugriff im Review-Modul; kein Volltext-Logging; LLM-Fehler irrelevant (kein LLM in V1); bei identischem Text `high` / niedriger Score; eigenständiges Skript `low` oder `medium` möglich; `python -m compileall app` grün; Unittests für Kernfälle grün. |
| **Bekannte Grenzen (V1)** | Rein **heuristisch**; **keine Rechtsberatung**; False Positives/Negatives möglich; **qualitatives LLM-Review** bewusst **nicht** in V1 — in `warnings` dokumentiert; für V1.1 optional `app/review/llm_review.py` nach MODULE_TEMPLATE. |
| **Nächster Schritt** | Feintuning Schwellen nur mit Plan-Eintrag; LLM-Review optional Phase 4.x / V1.1; bei Incidents [ISSUES_LOG.md](ISSUES_LOG.md). |

---

### Phase 5 — Watchlist / Channel Monitoring

| | |
|--|--|
| **Status** | **next** (Phase 5 weiterhin aktiv; Schritt 1 wie unten dokumentiert vorhanden; Gesamtphase **nicht** `done`) |
| **Umsetzungsstand** | **Schritt 1–4 umgesetzt** (CRUD, Check, Jobs, **`POST …/jobs/{job_id}/run`**, **`generated_scripts`**). **BA 5.5–5.7:** Recheck, **`run-pending`**, **`run-cycle`**, **`POST …/jobs/{job_id}/review`**. **BA 5.8–6.2:** Pending-Query, Dashboard, Errors-Summary, Governance, **`production_jobs`**-Stub. **BA 6.3–6.5:** Dashboard-Aggregationsfix + Stream-Fallback, **`review_results`** + Verknüpfungen, **`GET/POST /production/jobs`** (Liste, Detail, Skip, Retry ohne Render). **BA 6.6:** Collection **`scene_plans`** Script-to-Szenenplan ohne LLM (**`/production/jobs/{id}/scene-plan/*`**); **`generated_scripts`** unverändert. **BA 6.7:** Collection **`scene_assets`**, Prompt-Entwürfe aus **`scene_plans`** (**`/production/jobs/{id}/scene-assets/*`**), ohne externe Bild-/Video-Generatoren. **BA 6.8–7.0:** **`voice_plans`**, **`render_manifests`**, Connector-Export (**`/production/jobs/{id}/voice-plan/*`**, **`render-manifest/*`**, **`GET …/export`**) — Datenstrukturen und JSON, **ohne** echtes TTS/Video/Provider-Upload. **BA 6.6.1:** Dev-Endpoint **`/dev/fixtures/completed-script-job`** (nur wenn **`ENABLE_TEST_FIXTURES`**) zur Erzeugung abgeschlossener Test-Jobs ohne YouTube. **BA 7.1–7.4:** Collection **`production_checklists`** (Doc-ID = **`production_job_id`**); **`GET …/export/download?format=json|markdown|csv|txt`** (Manifest-Paket + `provider_templates`-Blöcke); **`POST/GET …/checklist/init|GET|update`**; **`production_jobs.status`** Workflow (**`planning_ready`** … **`published`**). **BA 7.5–7.7:** **`POST /production/automation/run-daily-cycle`** ( **`run_automation_cycle`** + Pending Jobs + Production-Artefakte bis Checkliste; **`dry_run`** ohne Schreibzugriffe); Collections **`provider_configs`** / **`production_files`** (Konfig-Status, geplante Pfade); **`GET/POST /providers/*`**, **`POST/GET …/production/jobs/{id}/files/plan|GET …/files`** — ohne echte Provider-Aufrufe und ohne Cloud Scheduler Deploy. **BA 7.8–7.9:** Collections **`execution_jobs`**, **`production_costs`**; **`execution_queue.py`-Logik**, **`cost_calculator.py`**; **`POST …/production/jobs/{id}/execution/init`**, **`GET …/execution`**, **`POST …/costs/calculate`**, **`GET …/costs`** — Queue ohne Provider-Dispatch; Budget nur Heuristik (EUR). **BA 8.0–8.2:** **`pipeline_audits`**, **`recovery_actions`**, Audit-/Recovery-/Monitoring-Endpunkte (**`/production/audit/*`**, **`…/recovery/retry`**, **`/production/monitoring/summary`**). **BA 8.3:** Collection **`pipeline_escalations`**, Modul **`status_normalizer.py`** — Status-Normalisierung (**`stuck`**, **`retryable`**, **`partial_failed`**, Gap-Erkennung), Escalation Cases, Retry-Disziplin; **`POST /production/status/normalize/run`**, **`GET /production/status/escalations`**. **BA 8.4 LIGHT:** **`GET /production/control-panel/summary`**, Modul **`control_panel.py`** — read-only Founder-Übersicht (bestehende Collections aggregiert). **BA 8.5:** **`input_quality_guard.py`** — Transkript-/Eingangsqualität (`transcript_missing` \| `transcript_blocked` \| `transcript_partial` \| `source_low_quality`), **`input_quality_status`** auf **`script_jobs`** / **`processed_videos`** / Check-Items; keine unnötige Eskalation bei erwartbarem Fehlen von Untertiteln. **BA 8.6:** **`provider_discipline.py`** — **`seed_default_provider_configs`**, **`validate_provider_runtime_health`**; **`POST /providers/configs/seed-defaults`** (optional `apply_writes`); erweiterte Provider-Namen **`voice_default`**, **`image_default`**, **`render_default`**. **BA 8.7:** **`production_costs`** um **`cost_baseline_expected`**, **`cost_variance`**, **`over_budget_flag`**, **`step_cost_breakdown`**, **`estimated_profitability_hint`** (grob). **BA 8.8:** Referenzdoku **`GOLD_PRODUCTION_STANDARD.md`**; Test-Goldpfad **`tests/test_ba88_full_production_run.py`**. **BA 8.9:** **`OPERATOR_RUNBOOK.md`** (Daily Check, Dry Run, Incidents). **BA 9.0 (Template Engine):** **`app/story_engine/`**, optional **`video_template`**, Persistenz/Connector, Downstream-Profile, Tests **`tests/test_ba90_story_engine.py`**. **BA 9.1:** Blueprints, **`[template_conformance:…]`**, **`GET /story-engine/templates`**, **`tests/test_ba91_story_engine.py`**. **BA 9.2:** Hook Engine (**`POST /story-engine/generate-hook`**, Persistenz-Meta auf **`generated_scripts`**), **`tests/test_ba92_hook_engine.py`**. **BA 9.3–9.6:** Conformance/Gate, **`story_structure`**, **`POST /story-engine/rhythm-hint`**, Story-Observability (**Control Panel**), Story-Pack im Export, Experiment-Registry (**`GET /story-engine/experiment-registry`**) — **done** (Details **BA 9** unten; Tests u. a. **`tests/test_ba9396_story_maturity.py`**). **BA 9.7–9.9:** Adaptive Optimization, Story Intelligence und Story-Engine-Ops-Reife — **done** (**`GET /story-engine/template-health`**, Control-Panel `template_optimization` / `story_intelligence`, **[docs/STORY_ENGINE_OS.md](docs/STORY_ENGINE_OS.md)**, **[OPERATOR_RUNBOOK.md](OPERATOR_RUNBOOK.md)** Abschnitt Story Engine). |
| **Ziel (Kurz)** | YouTube-Kanäle dauerhaft speichern, regelmäßig oder manuell prüfen, neue Videos erkennen, Kandidaten bewerten, Script-Jobs vorbereiten und Status führen — aufbauend auf bestehender RSS-/Discovery-Logik (`POST /youtube/latest-videos`). |
| **Relevante Dateien** | `app/youtube/*` (Resolver, RSS für Kanalnamen bei Create), **implementiert:** `app/story_engine/` (**BA 9** inkl. **`hook_engine`**, **`hook_library`**, BA 9.2), **`app/routes/story_engine.py`** (**`GET /story-engine/templates`**, **`POST /story-engine/generate-hook`**, **`POST /story-engine/rhythm-hint`**, **`POST /story-engine/scene-plan`** (Makro‑Phase 8.1 Visual Blueprint, ohne Bildprovider/Persistenz), **`POST /story-engine/scene-prompts`** (Makro‑Phase 8.2 Prompt Engine V1, **[docs/modules/phase8_82_prompt_engine_v1.md](docs/modules/phase8_82_prompt_engine_v1.md)**), **`GET /story-engine/experiment-registry`**, **`GET /story-engine/template-health`** (BA 9.7/9.8)), **`app/visual_plan/`**, `app/watchlist/` (inkl. `scene_plan.py` BA 6.6, `scene_asset_prompts.py` BA 6.7, `voice_plan.py` BA 6.8, `render_manifest.py`, `connector_export.py` BA 6.9–7.0, **`export_download.py`**, **`production_checklist.py`** BA 7.1–7.4, `dev_fixture_seed.py` BA 6.6.1, **`execution_queue.py`**, **`cost_calculator.py`** BA 7.8–7.9 / **8.7**, **`pipeline_audit_scan.py`** BA 8.0, **`status_normalizer.py`** BA 8.3, **`control_panel.py`** BA 8.4, **`input_quality_guard.py`** BA 8.5, **`provider_discipline.py`** BA 8.6), `app/routes/watchlist.py`, `app/routes/dev_fixtures.py`, **`app/routes/production.py`**, **`app/routes/providers.py`** (BA 7.5–8.6), `tests/test_watchlist_*.py`, `tests/test_ba66_scene_plan.py`, `tests/test_ba67_scene_assets.py`, `tests/test_ba68_6970_production_voice_render_export.py`, **`tests/test_ba714_production_os.py`**, **`tests/test_ba75_77_automation_provider_storage.py`**, **`tests/test_ba78_79_execution_budget.py`**, **`tests/test_ba80_82_hardening.py`**, **`tests/test_ba83_status_normalization.py`**, **`tests/test_ba84_control_panel.py`**, **`tests/test_ba85_input_quality_guard.py`**, **`tests/test_ba86_provider_seed.py`**, **`tests/test_ba87_cost_baseline.py`**, **`tests/test_ba88_full_production_run.py`**, **`tests/test_ba89_operator_runbook.py`**, **`tests/test_ba90_story_engine.py`**, **`tests/test_ba91_story_engine.py`**, **`tests/test_ba92_hook_engine.py`**, **`tests/test_ba9396_story_maturity.py`**, **`tests/test_ba97_template_optimization.py`**, **`tests/test_ba98_story_intelligence.py`**, **`tests/test_phase8_81_visual_contract.py`**, **`tests/test_phase8_82_prompt_engine.py`**, `tests/test_ba661_dev_fixtures.py`; `app/models.py` (**`GenerateScriptResponse`**-Vertrag unverändert) |
| **Bekannte Grenzen** | YouTube-RSS liefert keine Echtzeit-Garantie; `@handle`-Auflösung bleibt fragiler als `/channel/UC…` (wie Phase 2). |

#### Zielbild Phase 5

- Nutzer hinterlegen YouTube-Kanäle (**Watchlist**); das System löst **`channel_id`** / Anzeigenamen wo möglich auf und persistiert Kanalparameter (Prüfintervall, `max_results`, Schwellen, Shorts-Verhalten, Zielsprache/Dauer für spätere Jobs).
- **Prüfen** nutzt dieselbe fachliche Basis wie **`POST /youtube/latest-videos`** (Resolver, RSS-Feed, Heuristik-**Score**/**reason**).
- **Neue** Videos gegenüber bereits bekannten Einträgen erkennen; **Duplicate Prevention** über gespeicherte **`video_id`**.
- Bei passenden/neuen Videos können **Script-Jobs** entstehen; Ausführung und Speicherung folgen den V1-Regeln unten.
- **Nicht Ziel von Phase 5 V1:** automatische Veröffentlichung; Voiceover; Video-Rendering/Produktion; eigenes Frontend-Dashboard; Nutzerverwaltung; YouTube Data API; Aufbewahrung großer Roh-Transkripte ohne Nutzen für die Pipeline.

#### Speicher — Empfehlung

- **Firestore (Native Mode)** als empfohlene Speicherlösung: Cloud Run bleibt zustandslos; strukturierte Entitäten, Abfragen (Kanäle, Jobs, Duplikate); IAM über GCP-Service-Account; passt zu Watchlist-, Job- und Review-Persistenz.
- JSON-Datei oder Roh-GCS ohne Index sind für Status/Queues und Konkurrenz auf Cloud Run ungeeignet.

#### Firestore — geplante Collections

| Collection | Zweck |
|------------|--------|
| **watch_channels** | Überwachte Kanäle: u. a. URL, `channel_id`, Name, Status (`active` / `paused` / `error`), `check_interval`, `max_results`, Flags `auto_generate_script`, `auto_review_script`, Zielsprache/Dauer/Schwellen, `ignore_shorts`, Zeitstempel, letzte Fehler-/Check-Infos (`last_checked_at`, `last_error`, …). |
| **processed_videos** | Bekannte Videos: `video_id`, Zuordnung zum Kanal, URL/Titel, `published_at`, Status (z. B. seen / skipped / …), Score/Grund/Short-Hinweis, Verweise auf Job/Review-IDs. |
| **script_jobs** | Jobs zur Skripterzeugung: Status (`pending`, `running`, `completed`, `failed`, …), Verknüpfung zu Video/Kanal, Parameter, Zeitstempel, Verweise auf Ergebnis-IDs/Fehler. |
| **generated_scripts** | Persistenz generierter Skripte im Sinne des festen **`GenerateScriptResponse`** (Titel, Hook, Kapitel, `full_script`, Quellen, Warnungen — Vertrag bestehender Skript-Endpoints nicht brechen). |
| **review_results** | Ergebnisse analog **`POST /review-script`** — persistiert durch **`POST /watchlist/jobs/{job_id}/review`** wenn Job **`completed`** + **`generated_script_id`**. Verknüpfung **`script_jobs.review_result_id`**, optional **`processed_videos.review_result_id`**. |
| **watchlist_meta** | Kleines Metadokument (z. B. Doc **`automation`**: `last_run_cycle_at` nach erfolgreichem **`run-cycle`-Durchlauf). |
| **production_jobs** | Vorbereitung späterer Produktion (Voice/Render): Status, Verweise auf **`generated_script_id`** / **`script_job_id`**, Platzhalterfelder — **kein** Rendern in dieser BA. |
| **scene_plans** | BA 6.6: strukturierter Szenenplan je Production Job (**Document-ID** = **`production_job_id`**), Verknüpfung zu **`generated_script_id`** / **`script_job_id`**; keine Änderung an **`generated_scripts`**. Deterministische Erzeugung, idempotent beim erneuten Aufruf. |
| **scene_assets** | BA 6.7: strukturierte Prompt-Entwürfe (Bild/Video/Thumbnail/Kamera) je Szene, **Document-ID** = **`production_job_id`**, Verknüpfung zu **`scene_plan_id`**, **`generated_script_id`**, **`script_job_id`**, **`style_profile`**, **`asset_version`**; keine Ausführung bei Leonardo/Kling o. Ä. |
| **voice_plans** | BA 6.8: Voice-Blöcke je Szene aus **`voiceover_chunk`** (kein TTS); **Document-ID** = **`production_job_id`**, Verknüpfung zu **`scene_assets_id`**, optionaler Body **`voice_profile`**, **`voice_version`**, **`blocks[]`**, **`warnings`**. |
| **render_manifests** | BA 6.9 + 7.0: gebündeltes Maschinenmanifest und Export-Basis (`production_job`, `scene_plan`, `scene_assets`, `voice_plan`, **`timeline[]`**, **`estimated_total_duration_seconds`**, **`export_version`**, Status **`ready` \| incomplete \| failed`); **Document-ID** = **`production_job_id`**. |
| **production_checklists** | BA 7.1–7.4: Freigaben/Workflow (**Document-ID** = **`production_job_id`**). |
| **provider_configs** | BA 7.6: **`provider_name`** (elevenlabs, openai, …); **`enabled`**, **`dry_run`**, Budgetfelder (**keine** API-Secrets). |
| **production_files** | BA 7.7: geplante Artefakt-Pfade pro **`production_job_id`** (**`storage_path`**, **`file_type`**, **`status`** `planned` \| …); **ohne** GCS/GCS-Upload im MVP. |
| **execution_jobs** | BA 7.8: aus **`production_files`** abgeleitete ausführbare Tasks (**Doc-ID** typ. **`exjob_*`**, deterministisch ab **`pfile_*`**); Status **`queued` \| running \| …**; keine echten Provider-Calls aus diesem Endpoint. |
| **production_costs** | BA 7.9: geschätztes Budget je **`production_job_id`** (**Document-ID** = Job-ID): Voice/Bild/Video/Thumbnail/Buffer (**EUR**); **`actual_total_cost`** Vorbereitung für spätere echte Ist-Kosten — **nicht** angebunden an API-Abbuchungen. |
| **pipeline_audits** | BA 8.0: persistierte Audit-Befunde (fehlende Artefakte, **`dead_job`**, Drift-Hinweise); deterministic **`aud_pj_*` / `aud_sj_*`** Dokument-IDs. |
| **recovery_actions** | BA 8.1: Protokolle gezielter Recovery-Schritte ( **`retry_*`**, **`full_rebuild`**). |
| **pipeline_escalations** | BA 8.3: Eskalationen (Severity, Kategorie, Retry-Zähler, Provider-Flag, Verknüpfungen); deterministische **`esc_*`** Doc-IDs. |

#### Watchlist-Endpunkte (Phase 5 — Stand Code)

| Methode | Pfad | Zweck |
|---------|------|--------|
| `POST` | `/watchlist/channels` | Kanal in Watchlist anlegen |
| `GET` | `/watchlist/channels` | Watchlist auflisten |
| `POST` | `/watchlist/channels/{channel_id}/check` | Einen Kanal manuell prüfen |
| `POST` | `/watchlist/channels/{channel_id}/recheck-video/{video_id}` | **Ops/Dev:** Ein einzelnes Video erneut gegen die gleiche Pipeline-Logik prüfen (Warnung bei Löschen genau eines `processed_videos`-Docs; keine Massenaktion). |
| `GET` | `/watchlist/jobs` | Script-Jobs auflisten |
| `POST` | `/watchlist/jobs/run-pending` | Pending Jobs nacheinander ausführen (Query **`limit`** Default 3, Max 10; Batch bricht nicht bei Einzelfehlern ab). |
| `POST` | `/watchlist/automation/run-cycle` | Aktive Kanäle prüfen (Cap **`channel_limit`**), anschließend **`run_pending`** (Cap **`job_limit`**) — **ohne** Cloud Scheduler, nur Endpoint für spätere IAP/Cron-Anbindung. |
| `POST` | `/watchlist/jobs/{job_id}/run` | Einen Script-Job manuell ausführen (**`generated_scripts`**). |
| `POST` | `/watchlist/jobs/{job_id}/review` | Heuristik wie **`POST /review-script`** aus gespeichertem Skript; Persistenz **`review_results`** bei **`completed`** + **`generated_script_id`**; **keine** Änderung des ScriptJob-Status bei Review-/Speicherfehlern. |
| `GET` | `/watchlist/dashboard` | Snapshot: Zähler Kanäle/Videos/Jobs/Skripte, Health (`last_successful_job_at`, `last_run_cycle_at`, Warnungen). |
| `GET` | `/watchlist/errors/summary` | Stichprobe: Aggregation **`error_code`** / **`skip_reason`** mit Beispiel-IDs (`max_docs`). |
| `POST` | `/watchlist/jobs/{job_id}/retry` | **`failed`**/**`skipped`** → **`pending`**, Fehlerfelder leeren. |
| `POST` | `/watchlist/jobs/{job_id}/skip` | **`pending`**/**`failed`** → **`skipped`**, **`manual_skip`**. |
| `POST` | `/watchlist/channels/{channel_id}/pause` | Kanal **`paused`**. |
| `POST` | `/watchlist/channels/{channel_id}/resume` | Kanal **`active`** (nur aus **`paused`**). |
| `POST` | `/watchlist/jobs/{job_id}/create-production-job` | **`production_jobs`** anlegen (idempotent), nur **`completed`** + **`generated_script_id`**. |
| `GET` | `/production/jobs` | Produktions-Stubs auflisten (**`limit`**, Default 50, Max 200). |
| `GET` | `/production/jobs/{production_job_id}` | Ein Produktions-Job lesen (**404**, wenn nicht vorhanden). |
| `POST` | `/production/jobs/{production_job_id}/skip` | **`queued`**/**`failed`** → **`skipped`** (**keine** Videoproduktion). |
| `POST` | `/production/jobs/{production_job_id}/retry` | **`failed`**/**`skipped`** → **`queued`**. |
| `POST` | `/production/jobs/{production_job_id}/scene-plan/generate` | Deterministischen Szenenplan erzeugen / vorhandenen zurückgeben (idempotent); persistiert **`scene_plans`**. |
| `GET` | `/production/jobs/{production_job_id}/scene-plan` | Szenenplan lesen (**404**, wenn nicht vorhanden). |
| `POST` | `/production/jobs/{production_job_id}/scene-assets/generate` | Prompt-Entwürfe je Szene erzeugen / vorhandenes **`scene_assets`**-Dokument zurückgeben (idempotent); optionaler Body `style_profile` (`documentary` Default). Persistenz **`scene_assets`**. |
| `GET` | `/production/jobs/{production_job_id}/scene-assets` | Scene-Assets lesen (**404**, wenn nicht vorhanden). |
| `POST` | `/production/jobs/{production_job_id}/voice-plan/generate` | Voice-Plan aus **`scene_assets`** erzeugen (**idempotent** wenn vorhanden); optionaler Body **`voice_profile`** (`documentary` \| `news` \| `dramatic` \| `soft`); persistiert **`voice_plans`**. |
| `GET` | `/production/jobs/{production_job_id}/voice-plan` | Voice-Plan lesen (**404**, wenn nicht vorhanden). |
| `POST` | `/production/jobs/{production_job_id}/voice/synthesize-preview` | Phase 7.2: TTS‑Preview (**OpenAI Speech**) aus bestehendem **`voice_plan`**, keine Audio‑Persistenz; Body **`dry_run`**, **`max_blocks`** (1–5), optional **`voice`**; Default **Metadata only** (optional **`audio_base64`** nur mit **`ENABLE_VOICE_SYNTH_PREVIEW_BODY`** und Byte‑Limit); ohne API‑Key weiterhin HTTP **200** mit **`warnings`**, kein blindes HTTP 500. |
| `POST` | `/production/jobs/{production_job_id}/voice/synthesize` | Phase 7.3: Voice‑Commit (**OpenAI Speech**) aus **`voice_plan`** → **`production_files`** (`file_type=voice`): Metadaten u. a. **`status`**, **`synthesis_byte_length`**; **keine** Audioblobs in Firestore; Body **`dry_run`**, **`max_blocks`** (1–50), **`overwrite`**, optional **`voice`**; Idempotenz: **`skipped_ready`** bei bestehendem **`ready`** + Bytes ohne **`overwrite`**; Firestore‑Fehler **503** wie andere Produktions‑Routen. |
| `POST` | `/production/jobs/{production_job_id}/render-manifest/generate` | Render-Manifest (**`render_manifests`**) aus Bausteinen zusammenstellen (**404** ohne **`scene_assets`**); enthält **`voice_production_file_refs`** aus **`production_files`**. |
| `GET` | `/production/jobs/{production_job_id}/render-manifest` | Render-Manifest lesen (**404**, wenn nicht vorhanden). |
| `GET` | `/production/jobs/{production_job_id}/export` | BA 7.0 / Phase 7.7: connector-ready JSON (**`generic_manifest`**, Provider-Stubs, **`metadata`**, **`voice_artefakte`** aus **`production_files`**, Typ **`voice`**) — **ohne** echte Provider-Aufrufe. |
| `GET` | `/production/jobs/{production_job_id}/export/download` | BA 7.1 / Phase 7.7: Manifest + Templates als Download (`format=json|markdown|csv|txt`); JSON‑Paket kann **`voice_artefakte`** in **`provider_templates`** spiegeln. |
| `POST` | `/production/jobs/{production_job_id}/checklist/init` | BA 7.3: Checkliste anlegen/idempotent zurückgeben. |
| `GET` | `/production/jobs/{production_job_id}/checklist` | Checkliste lesen (**404**, wenn keine). |
| `POST` | `/production/jobs/{production_job_id}/checklist/update` | Manuelle Booleans (**`thumbnail_ready`**, …). |
| `POST` | `/production/automation/run-daily-cycle` | BA 7.5: Watchlist **`run-cycle`** + Pending Jobs + Produktions-Schritte; Body **`channel_limit`**, **`job_limit`**, **`production_limit`**, **`dry_run`** (read-only ohne Firestore-Schreibvorgänge). |
| `GET` | `/providers/configs` | BA 7.6: Liste **`provider_configs`**. |
| `POST` | `/providers/configs/seed-defaults` | BA 8.6: Standard-Slots **`openai`**, **`voice_default`**, **`image_default`**, **`render_default`** (Query **`apply_writes`**, Default false — Vorschau ohne Schreibzugriff). |
| `GET` | `/providers/status` | BA 7.6: Aktiv-/Dry-run-Übersicht (alle registrierten Provider). |
| `POST` | `/production/jobs/{production_job_id}/files/plan` | BA 7.7: Geplante Storage-Pfade in **`production_files`** (**404** ohne Job). |
| `GET` | `/production/jobs/{production_job_id}/files` | BA 7.7: Artefakte pro Job (**404** ohne Job). |
| `POST` | `/production/jobs/{production_job_id}/execution/init` | BA 7.8: Aus **`production_files`** ausführbare **`execution_jobs`** erzeugen (idempotent bei bestehenden IDs). Ohne echte Provider-Calls — **Warnung**, wenn bereits Jobs existieren oder keine **`production_files`** geplant wurden. |
| `GET` | `/production/jobs/{production_job_id}/execution` | BA 7.8: Liste **`execution_jobs`** (**404** ohne **`production_jobs`**). |
| `POST` | `/production/jobs/{production_job_id}/costs/calculate` | BA 7.9: Heuristische Kostenschätzung (EUR) berechnen und **`production_costs`** speichern (**404** ohne Job). |
| `GET` | `/production/jobs/{production_job_id}/costs` | BA 7.9: **`production_costs`** lesen (leer ohne vorheriges **`calculate`**, dann Hinweis in **`warnings`**). |
| `POST` | `/production/audit/run` | BA 8.0: Pipeline-Scan gegen Production-/Script-Artefakte (`pipeline_audits` upsert, optional Resolver offene Befunde). |
| `GET` | `/production/audit` | BA 8.0: Liste **pipeline_audits** (Filter **`status`**, **`severity`**). |
| `POST` | `/production/jobs/{production_job_id}/recovery/retry` | BA 8.1: Body **`step`** (`scene_plan`, `scene_assets`, `voice_plan`, `render_manifest`, `execution`, `costs`, `files`, `full_rebuild`) — **nicht** der Legacy- **`POST …/retry`** zur Status-Anhebung. |
| `GET` | `/production/monitoring/summary` | BA 8.2: Aggregation offener Schweregrade + kleine Probe **`resolved`** & **`recovery_actions`**. |
| `POST` | `/production/status/normalize/run` | BA 8.3: Status-Normalisierung/Eskalationen (Body u. a. Schwellen, **`dry_run`**, **`retry_reason`**). |
| `GET` | `/production/status/escalations` | BA 8.3: letzte **`pipeline_escalations`** (Query **`limit`**). |
| `GET` | `/production/control-panel/summary` | BA 8.4 LIGHT: Founder Control Panel — Aggregation (**`pipeline_audits`**, **`pipeline_escalations`**, **`recovery_actions`**, **`production_jobs`** Stichprobe, **`script_jobs`** Zähler, **`provider_configs`**, **`production_costs`**, Problemfälle). Read-only. |
| `POST` | `/dev/fixtures/completed-script-job` | **Nur wenn `ENABLE_TEST_FIXTURES=true`:** Completed **`script_jobs`** + **`generated_scripts`** (+ optional **`production_jobs`**) ohne Transkript; Präfix **`dev_fixture_`** (**403** ohne Flag; **409** bei Kollision). |

(Response-Verträge der Watchlist-/Production-Endpunkte ergänzend; Kern-Endpoints **`/generate-script`**, **`/youtube/*`**, **`/review-script`** bleiben unverändert.)

#### V1-Entscheidungen (Pflichtlage Plan)

| Thema | Entscheid |
|-------|-----------|
| Neue Videos → Ausführung | Nach Check entstehen **nur `pending` Script-Jobs** — **keine** automatische Ausführung aller Jobs in V1. |
| Job-Ausführung | **Manuell** über **`POST /watchlist/jobs/{job_id}/run`** (Kosten-/Kontrollgründe, weniger Blind-LLM-Last). |
| Veröffentlichung | **Kein Auto-Publish** |
| Produktion | **Keine Voiceover-/Video-Produktion** in Phase 5 |

#### Scheduler und Auth (nach V1)

- **Cloud Scheduler:** erst **ab V1.1** vorgesehen (z. B. wiederkehrender Aufruf von **`POST /watchlist/automation/run-cycle`** mit Auth-Header/Secret). Der **Endpoint** existiert bereits (Phase 5.6); **Deploy/Trigger** in GCP ist noch **nicht** Teil des Repos.
- In V1 wird `check_interval` nur gespeichert/ausgewertet, wo die Implementierung es vorsieht; kein Produktzwang Scheduler in V1.
- **Absicherung:** Öffentlicher Cloud-Run-Service erfordert für Scheduler später **klare Auth** (z. B. gemeinsamer Request-Header mit Secret nur in Secret Manager, oder geschützte Invoker-Only-Variante mit Dienstkonto/IAM — Details bei Implementierung, **keine** Secret-Werte in Repo-Doku).

#### Firestore Setup (Plan, keine Secrets)

| Thema | Vorgabe |
|-------|---------|
| Modus | **Native Mode** |
| Client-Bibliothek | **`google-cloud-firestore`** (Python) |
| Cloud Run | Dienst-Service-Account mit Rolle **`roles/datastore.user`** (bzw. vergleichbar für Firestore-Zugriff) |
| Lokal | **Application Default Credentials** (z. B. über `gcloud auth application-default login`) oder **Firestore Emulator** für Tests |

#### Kosten- und Sicherheitsregeln (Plan)

- Obergrenzen für `max_results` und **pro Run** maximal erzeugbare Jobs (`max_jobs_per_run` / ähnliche Caps in der Implementierung).
- Short optional ignorieren; RSS-Score unter `min_score` → keine Job-Erstellung bzw. explizit skipped.
- Duplikate über **`video_id`** verhindern.
- Kein unkontrolliertes LLM-Generating: **Queue** statt sofortiger Massen-Generierung.
- Keine Volltexte sensibler Inhalte in Logs; **AGENTS.md** zu Secrets und Logging beachten.
- Review bleibt redaktionelle Hilfsstufe — **keine** automatische Freigabe zur Veröffentlichung.

#### Akzeptanzkriterien (Phase 5 V1, wenn implementiert)

- Kanal kann gespeichert und gelistet werden.
- Kanal kann manuell geprüft werden; neue Videos werden erkannt, bekannte `video_id` nicht erneut als „neu“ für die gleiche Pipeline-Logik.
- Shorts können per Konfiguration ignoriert werden.
- Bei aktiviertem Auto-Generate: **Jobs** werden angelegt (**pending**); Ausführung nur über **`/watchlist/jobs/{job_id}/run`** (V1-Entscheid).
- Gespeichertes Skript und optionales Review-Resultat wie geplant persistiert.
- Kein Auto-Publish; keine Voiceover-/Video-Produktion in dieser Phase.
- `python -m compileall app` grün; Tests für Kernflows; Deploy Cloud Run weiter nutzbar; Firestore Zugriff lokal/GCP lauffähig nach Doku-Schritt.

#### Testplan (V1 — wenn implementiert)

- Kanal mit `/channel/UC…` hinzufügen; Kanal mit `@handle` mit erwarteten `warnings`.
- Erster Check: neue Videos erkannt.
- Zweiter Check: keine Duplikat-Doppel-Verarbeitung als „neu“.
- `ignore_shorts`: Shorts übersprungen.
- `auto_generate_script` aus: keine neuen Jobs, nur Tracking wie spezifiziert.
- `auto_generate_script` an: **pending** Jobs erstellt, nicht ohne `run`-Call vollständig durch die Pipeline geschleust (V1).
- Job manuell: `generated_scripts` konsistent zum Skript-Vertrag.
- Review-Pfad: `review_results` gespeichert wenn aktiviert.
- Fehler: Transkript fehlt — erwartbare Degradation, keine unsauberen Produkt-Leaks von Secrets.
- Firestore unreachable: definierbare Fehlerantwort/`warnings`/HTTP-Verhalten nach Implementierung wählen — **keine** blinden HTTP-500 durch erwartbare Ausfälle (analog AGENTS-Leitlinie).

#### Schrittweise Umsetzung (Empfehlung)

1. ~~Firestore aktivieren — Repository — **Watchlist CRUD**~~ **(Schritt 1 erledigt, siehe Umsetzungsstand)**.
2. ~~**Manueller Channel Check** — **`processed_videos`** füllen / Duplikatlogik~~ **(Schritt 2 erledigt: `POST …/check`, siehe README / Umsetzungsstand).**
3. ~~**Script-Jobs anlegen** bei neuen Videos (Konfigurationsabhängig)~~ **(Schritt 3 erledigt: Firestore `script_jobs`, `pending`; Ausführung erst Schritt 4).**
4. ~~**Job manuell ausführen** — **`generated_scripts`** persistieren (intern Logik wie `/youtube/generate-script`).~~ **(Schritt 4 umgesetzt: `POST /watchlist/jobs/{job_id}/run`, siehe README.)**
5. ~~Optional **Review** aus Job heraus (**`POST /watchlist/jobs/{job_id}/review`**) ruft **`review_script`** wie **`/review-script`** auf; Persistenz **`review_results`**~~ **done** (Firestore **`review_results`**, **`script_jobs.review_result_id`**).
6. **Scheduler / Cron in GCP** — **`run-cycle`** kann extern getriggert werden; Produkt-Timing & Auth später (V1.1+) mit Absicherung.

#### Stabilisierung zwischen Schritt 4 und Schritt 5 (Quality Gate: Transcript-Preflight, Job-Fehlercodes)

| | |
|--|--|
| **Status** | **done** (Qualitätssicherung; **keine** neue Hauptphase; Gesamt-Phase 5 weiterhin **nicht** `done`) |
| **Ziel** | Vor **`pending`**-Job-Anlage beim Kanal-Check prüfen, ob ein **öffentliches Transkript** für das Video abrufbar ist (gleicher Abrufpfad wie **`POST /youtube/generate-script`**); transcriptlose oder technisch nicht prüfbare Videos **ohne** **`pending`**-Job erfassen (**`processed_videos`** **`skipped`** mit **`skip_reason`**). Job-Run-Fehler **`failed`** mit standardisierten **`error`** / **`error_code`** statt nur Freitext. |
| **Nicht-Ziel** | Scheduler, Review-Persistenz (bleibt Schritt **5** geplant), neue große Features. |
| **Akzeptanz** | Keine Roh-Transkript-Persistenz durch Preflight; **`/generate-script`**-Verträge unverändert; Watchlist-Tests mit Mocks grün; Dokumentation/README ergänzt. |

---

### Phase 6 — Script Job Speicherung

| | |
|--|--|
| **Status** | **planned** |
| **Hinweis zur Abgrenzung** | Persistenz von Script-Jobs, generierten Skripten und Review-Ergebnissen wird in **Phase 5** (Firestore-Collections `script_jobs`, `generated_scripts`, `review_results` u. a.) bereits **mitgeplant und umgesetzt**. **Phase 6** bleibt für **Erweiterungen** reserviert: z. B. **`production_jobs`**-Weiterführung (echte Render-/Voice-Pipeline), explizite **Job-Versionierung**, erweiterte **Re-Runs**/Historie, alternative Backends — ohne Phase-5-V1 doppelt zu definieren. |
| **Ziel** | Über Phase 5 hinaus: erweiterte Job-Lifecycle-/Versionierungskonzepte (Details bei Bedarf MODULE_TEMPLATE). |
| **Endpoints** | *abhängig von Erweiterung* |
| **Relevante Dateien** | Anknüpfung an Phase-5-Watchlist/Job-Speicher; ggf. `app/config.py` |
| **Akzeptanzkriterien** | Keine Secrets im Repo; Migration/Schema dokumentiert; idempotente Job-Erstellung wo sinnvoll. |
| **Bekannte Grenzen** | Cloud Run bleibt zustandslos; persistente Arbeit liegt in Phase 5/externem Store. |
| **Nächster Schritt** | Nach Abschluss der Phase-5-Grundfunktion entscheiden, ob Phase 6 nur dokumentarisch zusammengeführt wird oder eigenes Increment. |

---

### Phase 7 — Voiceover

**Strukturierte Abarbeitung:** Bauplan mit **Baustein 7.1–7.8**, Qualitäts-Gates (`compileall`, `pytest`, keine blinden HTTP-500), Testnamenskonvention und Abgrenzung zu **BA 9.x** / **Phase 10** siehe **[docs/phases/phase7_voice_bauplan.md](docs/phases/phase7_voice_bauplan.md)**.  
*(**Baustein 7.x** = Ausführungsinkremente **unter** dieser Makrophase — **nicht** verwechseln mit **BA 9.x Story Engine** oder **Phase 10 Publishing**.)*

| | |
|--|--|
| **Status** | **done** (V1 ohne optionalen zweiten Provider **7.6**; umgesetzt: **7.2** Preview, **7.3** Persistenz‑Metadaten, **7.4** konsolidierte Voice‑Warnungen + dünn Audit, **7.5** Kostentransparenz Voice, **7.7** Manifest/Export‑Refs, **7.8** Ops‑Doku) |
| **Ziel** | Aus **`voice_plans`** **wahres TTS** ausführen; **Metadaten** in **`production_files`** ohne Blobs im Doc; später optional zweiter Provider (**7.6**). **`GenerateScriptResponse`** unberührt — Voice nur über Produktionsrouten. |
| **Voraussetzungen im Repo** | Strukturen für Voice‑Pipeline: **`voice_plans`**, **`POST …/voice-plan/*`**, **`provider_configs`**, **`production_files`**, **`render_manifests`**, Export — siehe Phase‑5‑Tabelle und **[docs/phases/phase7_voice_bauplan.md](docs/phases/phase7_voice_bauplan.md)**. |
| **Endpoints** | **`POST …/voice/synthesize-preview`**, **`POST …/voice/synthesize`** ([Phase‑5‑Tabelle](#watchlist-endpunkte-phase-5--stand-code)); MODULE **7.3** [docs/modules/phase7_73_voice_synthesize_commit.md](docs/modules/phase7_73_voice_synthesize_commit.md); Connector‑Payload **`voice_artefakte`**; Manifest **`voice_production_file_refs`** (`export_version` **7.1.0**). |
| **Relevante Dateien** | Neu: Voice/TTS-Modul (Pfad im ersten PR festlegen); bestehend: `app/watchlist/voice_plan.py`, `app/routes/production.py`, `app/routes/providers.py`, `cost_calculator.py`, `connector_export.py` / Render-Manifest. |
| **Akzeptanzkriterien (global Phase 7 V1)** | Gates laut Bauplan (**`compileall`**, **`pytest`**, `GET /health` + geänderte Routen); Secrets nur Secret Manager / `.env`; **`GenerateScriptResponse`** unverändert, sofern nicht separat beschlossen. |
| **Bekannte Grenzen** | Stimmenlizenzen Drittanbieter; keine Rechts-/Marken-Garantie durch die Pipeline; Binärdaten nicht dauerhaft in Firestore-Feldern vorhalten. |
| **Nächster Schritt** | Optional **Baustein 7.6** (zweiter TTS‑Provider). **Makro‑Phase 8** „Bild/Szenenplan“ **planen und bauen** nur in einem **gesonderten Schnitt**: **[docs/phases/phase8_image_sceneplan_bauplan.md](docs/phases/phase8_image_sceneplan_bauplan.md)** — **nicht** mit BA 8.0 (Audit) verwechseln. |

**Baustein-Übersicht (Ausführung Phase 7)**

| Baustein | Inhalt |
|----------|--------|
| **7.1** | Scope, Secrets-/Config-Namen (`voice_default`, ENV) |
| **7.2** | TTS-Adapter + erster Provider + **Preview-Vertical-Slice** — Steckbrief [docs/modules/phase7_72_voice_provider_minimal_slice.md](docs/modules/phase7_72_voice_provider_minimal_slice.md) |
| **7.3** | `voice_plan` → Synthese + Persistenz-Metadaten |
| **7.4** | Fehlerpfade / `warnings` / kein unkontrolliertes HTTP 500 |
| **7.5** | Kostenschätzung Voice-Anteil (`production_costs`) |
| **7.6** | *(optional)* zweiter Provider |
| **7.7** | Render-Manifest / Export-Anbindung |
| **7.8** | Runbook, Deploy-Hinweise, Smoke |

---

### Phase 8 — Bild- / Szenenplan

| | |
|--|--|
| **Status** | **in progress** (8.1 **`POST /story-engine/scene-plan`** — `app/visual_plan/builder.py`; 8.2 **`POST /story-engine/scene-prompts`** — `app/visual_plan/prompt_engine.py`; kein Bild-API/Persistenz; Makro‑Bausteine **8.3+** / Production‑`/visual-plan` geplant) |
| **Ziel** | Szenen aus Kapiteln ableiten (Bildprompts, Stock, generierte Bilder — policyabhängig). |
| **Endpoints** | **Live:** `POST /story-engine/scene-plan` (Scene‑Blueprint, **[docs/modules/phase8_81_visual_contract_minimal_slice.md](docs/modules/phase8_81_visual_contract_minimal_slice.md)**); **`POST /story-engine/scene-prompts`** (Prompt Engine V1 inkl. Provider‑Stubs, Continuity Lock, Safety‑Negative, **[docs/modules/phase8_82_prompt_engine_v1.md](docs/modules/phase8_82_prompt_engine_v1.md)**); Production‑Persistenz/Firestore folgt (**8.3**). |
| **Relevante Dateien** | `app/visual_plan/` (`builder.py`, `prompt_engine.py`, `policy.py`), `app/routes/story_engine.py`, `app/models.py`; Tests `tests/test_phase8_81_visual_contract.py`, `tests/test_phase8_82_prompt_engine.py`; später `production.py` / Repo bei Persistenz. |
| **Akzeptanzkriterien** | Lizenz und Quellenangaben pro Asset nachvollziehbar; keine ungeprüften Rechtsclaims in der Pipeline. |
| **Bekannte Grenzen** | Stock-APIs und Generatoren haben Nutzungsbedingungen. |
| **Nächster Schritt** | Nach Voiceover oder parallel nur mit klarem Schnitt. |

---

### Phase 9 — Video Packaging

| | |
|--|--|
| **Hinweis** | **BA 9.x „Template Engine“** (Story-/Video-Format in `app/story_engine/`) ist eine **eigene Produktachse** und **nicht** identisch mit dieser klassischen **Phase 9** (MP4/Packaging). |
| **Status** | **planned** |
| **Ziel** | Schnitt, Untertitel, Branding, Export (z. B. MP4) — lokal oder Cloud-Job. |
| **Endpoints** | *geplant* |
| **Relevante Dateien** | *neu*; ggf. FFmpeg in Container |
| **Akzeptanzkriterien** | Reproduzierbarer Build; Ressourcenlimits Cloud Run beachten. |
| **Bekannte Grenzen** | Schwere Videoverarbeitung oft nicht auf kleinen Cloud-Run-Instanzen. |
| **Nächster Schritt** | Architektur: Batch-Worker vs. dedizierter Render-Service. |

---

### Phase 10 — Veröffentlichungsvorbereitung

| | |
|--|--|
| **Status** | **planned** |
| **Ziel** | Metadaten (Titel, Beschreibung, Tags), Thumbnails, optionale Upload-Helfer — **ohne** unkontrollierte Auto-Publizierung ohne redaktionellen Freigabekanal. |
| **Endpoints** | *geplant* |
| **Relevante Dateien** | *neu* |
| **Akzeptanzkriterien** | OAuth/Plattform-Keys nur als Secrets; Upload-Workflow dokumentiert. |
| **Bekannte Grenzen** | Plattform-APIs (YouTube u. a.) haben Quoten und Richtlinien. |
| **Nächster Schritt** | Ob Upload im MVP gewünscht oder nur Export für manuelles Publishing. |

---

## BA 9 — Template Engine / Story Engine (Produktachse)

Diese Achse liefert **wiedererkennbare Video-/Erzählformate** (Hooks, Kapitellogik, Tonfall-Hinweise) über ein optionales Feld **`video_template`**, **ohne** den festen Sechs-Felder-JSON-Vertrag von **`POST /generate-script`** und **`POST /youtube/generate-script`** zu brechen (`title`, `hook`, `chapters`, `full_script`, `sources`, `warnings`).  
**Abgrenzung:** „**Phase 9**“ im Phasenplan oben meint **technisches Video-Packaging** (Schnitt, Export, MP4); „**Phase 10**“ meint **Veröffentlichungsvorbereitung**. **BA 9.x** meint ausschließlich **Story Engine / Template / Hook / Review / Optimierung** — **BA** = modulare Bauphase im Modul; **Phase** = Makro-Roadmap (**BA 9.x** ist **nicht** Phase 9 oder 10). **BA 9.9** schließt das Story-Kernmodul **innerhalb der BA-9.x-Linie** ab; es gibt **kein „BA 10“** für Story Engine, solange diese Achse nicht bewusst neu nummeriert wird.  
**Hinweis (Namensgebung):** Ein **Prompt-Planning-System V1** wird produktseitig mitunter als „**BA 9.1**“ beschriftet; **im Kanon dieses Repos** ist es **BA 9.10** (siehe unten), damit **BA 9.1** unverändert die historische Stufe **Operable Templates** bezeichnet.

### Übersicht Release-Stufen

| Stufe | Status | Kurzbeschreibung |
|-------|--------|------------------|
| **BA 9.0** | **done** | Modul `app/story_engine/`: Template-IDs, Normalisierung, Prompt-Zusätze (LLM + Fallback), `style_profile`/`voice_profile`-Hilfen, leichte Heuristiken → **`warnings`**; **`video_template`** durchgängig bis Watchlist/Production/Connector wo sinnvoll; Tests `tests/test_ba90_story_engine.py`. |
| **BA 9.1** | **done** | **Operable Templates:** Kapitel-Bands + Hook-Schwellen pro Template/Dauer; **Struktur-Blueprint** im LLM-Prompt; Kapitelanzahl-Clamping im `ScriptGenerator`; einheitliche **`[template_conformance:…]`**-Präfixe; **`GET /story-engine/templates`** (read-only Katalog); Tests **`tests/test_ba91_story_engine.py`**. |
| **BA 9.2** | **done** | **Hook Engine V1 (Opening-Line):** regelbasierte **`hook_type`** / **`hook_text`** / **`hook_score`** / **`rationale`** — **`POST /story-engine/generate-hook`** (Nebenkanal, `GenerateScriptResponse` unverändert); optionale Meta-Felder auf **`generated_scripts`**; Review-Heuristik Hook↔Template; Tests **`tests/test_ba92_hook_engine.py`**. |
| **BA 9.3** | **done** | **Conformance-Level** (`off`/`warn`/`strict`), **Gate** auf `generated_scripts`, **`template_definition_version`**, automatischer **Review nach Job** (Kanal `auto_review_script`), **`story_structure`**-Nebenkanal (`build_story_structure_v1`); Doku **`docs/modules/story_structure_sidechannel.md`**; Tests **`tests/test_ba9396_story_maturity.py`**. |
| **BA 9.4** | **done** | **`app/story_engine/rhythm_engine.py`** + **`POST /story-engine/rhythm-hint`**; Persistenz `generated_scripts.rhythm_hints`; keine Generate-Pflichtfelder. |
| **BA 9.5a** | **done** | **`ControlPanelSummaryResponse.story_engine`** (Hook-/Template-/Gate-/Experiment-Aggregate aus `generated_scripts`-Stichprobe). |
| **BA 9.5b** | **done** | **`ConnectorExportPayload.story_pack`** und **`provider_templates[\"story_pack\"]`** im Download-Export. |
| **BA 9.6** | **done** | **`GET /story-engine/experiment-registry`**, **`experiment_id`/`hook_variant_id`** auf `generated_scripts` (Zuordnung `experiment_registry`), Control-Panel-Zähler. |
| **BA 9.7** | **done** | **Adaptive Template Optimization:** Drift je `video_template` (`distinct_nonempty_template_definition_versions`, Dispersion), interne Health-/Performance-Scores, Refinement-Hinweise (`[template_refinement:…]`); **`GET /story-engine/template-health`** und Einbettung in **`GET /production/control-panel/summary`** → `story_engine.template_optimization`. Module: `template_drift.py`, `template_health_score.py`, `refinement_signals.py`, `template_optimization_aggregate.py`; Tests **`tests/test_ba97_template_optimization.py`**. Steckbrief: [docs/modules/ba97_adaptive_template_optimization.md](docs/modules/ba97_adaptive_template_optimization.md). |
| **BA 9.8** | **done** | **Story Intelligence Layer:** Read-only Narrative-/Cross-Template-Hinweise, Self-Learning-Readiness-Checkliste ohne Closed-Loop; gleicher Health-Endpoint + Control-Panel **`story_engine.story_intelligence`**. **`story_intelligence_layer.py`**; **[docs/modules/ba98_story_intelligence_layer.md](docs/modules/ba98_story_intelligence_layer.md)**; Tests **`tests/test_ba98_story_intelligence.py`**. |
| **BA 9.9** | **done** | **Story Engine Operations Maturity:** Canonical **Story OS** [docs/STORY_ENGINE_OS.md](docs/STORY_ENGINE_OS.md); Runbook-Reife [OPERATOR_RUNBOOK.md](OPERATOR_RUNBOOK.md) „Story Engine (Daily)“; Deploy-Verweis [docs/runbooks/cloud_run_deploy_runbook.md](docs/runbooks/cloud_run_deploy_runbook.md); Abschlusskriterien dokumentiert (**kein BA 10** für Story-, **Phase 9/10** unverändert Packaging/Publishing). Modulüberblick: [docs/modules/ba99_story_engine_operations_maturity.md](docs/modules/ba99_story_engine_operations_maturity.md). |
| **BA 9.10** | **done** | **Prompt Planning System V1:** Topic-getriebenes, **deterministisches** Produktions-Blueprint (`template_type`, `tone`, `hook`, `chapter_outline`, `scene_prompts`, `voice_style`, `thumbnail_angle`); Module **`app/prompt_engine/`**, JSON-Templates **`app/templates/prompt_planning/`** (V1: `true_crime`, `mystery_history`); Hook-Schritt delegiert an **BA 9.2** `generate_hook_v1`; **`POST /story-engine/prompt-plan`**; Tests **`tests/test_ba910_prompt_planning.py`**. **`GenerateScriptResponse`** unverändert. |
| **BA 9.11** | **done** | **Prompt Plan Quality Check V1:** Heuristische **Produktionsreife** (`PromptPlanQualityResult`: `score`, `status` pass/warning/fail, `warnings`, `blocking_issues`, `checked_fields`); Modul **`app/prompt_engine/quality_check.py`**, Funktion **`evaluate_prompt_plan_quality`**; in **`POST /story-engine/prompt-plan`** als Feld **`quality_result`** im **`ProductionPromptPlan`**; Tests **`tests/test_ba911_prompt_plan_quality.py`**. **`GenerateScriptResponse`** unverändert. |
| **BA 9.12** | **done** | **Narrative Scoring V1:** Erzählerische **Zugkraft** (`NarrativeScoreResult`: Aggregat + Teilscores Hook/Curiosity, Emotion, Eskalation, Kapitel-Progression, Thumbnail-Potenzial); **`app/prompt_engine/narrative_scoring.py`**, **`evaluate_narrative_score`**; Feld **`narrative_score_result`** in **`ProductionPromptPlan`** / **`POST /story-engine/prompt-plan`**; Tests **`tests/test_ba912_narrative_scoring.py`**. **`GenerateScriptResponse`** unverändert. |
| **BA 9.13** | **done** | **Performance Learning Loop V1:** Logisches **`performance_records`**-Modell (`PerformanceRecord`, KPI-Optionalfelder), Builder **`build_performance_record_from_prompt_plan`**, **`evaluate_performance_snapshot`**, **`summarize_template_performance`** in **`app/prompt_engine/performance_learning.py`**; optional **`include_performance_record`** auf **`PromptPlanRequest`** → Feld **`performance_record`** im Plan (ohne Firestore/Migration V1); Tests **`tests/test_ba913_performance_learning.py`**. **Keine YouTube-API**. **`GenerateScriptResponse`** unverändert. |
| **BA 9.14** | **done** | **Prompt Plan Review Gate V1:** Operative Ampel **`go` / `revise` / `stop`** aus Quality (9.11), Narrative (9.12), optional Performance-Hinweis (9.13); **`PromptPlanReviewGateResult`** (`decision`, `confidence`, `reasons`, `required_actions`, `checked_signals`); **`app/prompt_engine/review_gate.py`**, Feld **`review_gate_result`** auf **`ProductionPromptPlan`** / **`POST /story-engine/prompt-plan`**; Tests **`tests/test_ba914_prompt_plan_review_gate.py`**. **`GenerateScriptResponse`** unverändert. |
| **BA 9.15** | **done** | **Prompt Repair Suggestions V1:** Konkrete, priorisierte Reparatur-To-dos aus Gate **`revise`/`stop`**, Quality (`blocking_issues`, Warnungsbudget), Narrativ (Schwächen, Teilscores), Struktur (Hook/Kapitel/Szenen/Voice/Thumbnail) und optionalem Performance-**`pending_data`**-Hinweis; **`PromptRepairSuggestion`** / **`PromptRepairSuggestionsResult`**, **`app/prompt_engine/repair_suggestions.py`** (`build_prompt_repair_suggestions`), Feld **`repair_suggestions_result`**; Tests **`tests/test_ba915_prompt_repair_suggestions.py`**. Kein LLM, keine Firestore-Writes. **`GenerateScriptResponse`** unverändert. |
| **BA 9.16** | **done** | **Repair Preview / Auto-Revision V1:** Deterministische **Vorschau** eines reparierten Plans (**`PromptRepairPreviewResult`**: `preview_available` / `not_needed` / `not_possible`, **`preview_plan`**, **`applied_repairs`**, **`remaining_issues`**, **`warnings`**); Modul **`app/prompt_engine/repair_preview.py`** (`build_repair_preview`); Hook-/Kapitel-/Szenen-/Voice-/Thumbnail-Heuristiken, Narrativ-**weak** nur als Hinweis; Re-Evaluation von Quality/Narrative/Gate/Suggestions auf der Preview mit **`preview_plan.repair_preview_result = None`** (keine Rekursion); **`POST /story-engine/prompt-plan`** additiv **`repair_preview_result`**; Tests **`tests/test_ba916_repair_preview.py`**. Kein Auto-Overwrite, kein LLM/Firestore. **`GenerateScriptResponse`** unverändert. |
| **BA 9.17** | **done** | **Human Approval Layer V1:** Freigabe-Vorbereitung (**`HumanApprovalState`**: `pending_review` / `approved` / `rejected` / `needs_revision`, **`recommended_action`**, **`approval_required`**, **`reasons`**, **`checklist`**, optional **`approved_by`**/**`approved_at`**/**`rejected_reason`**); **`app/prompt_engine/human_approval.py`** (`build_human_approval_state`); Mapping aus Review Gate (9.14) + Repair-Summary (9.15); **`human_approval_state`** auf **`ProductionPromptPlan`** / **`POST /story-engine/prompt-plan`**; Tests **`tests/test_ba917_human_approval_layer.py`**. Keine Persistenz, kein Auth, keine User-Aktion in V1. **`GenerateScriptResponse`** unverändert. |
| **BA 9.18** | **done** | **Production Handoff V1:** Übergabepaket (**`ProductionHandoffResult`**: `handoff_status` ready/blocked/needs_review/needs_revision, **`production_ready`**, **`summary`**, **`package`** mit Plan-/Quality-/Narrative-/Gate-/Approval-Metadaten, **`warnings`**, **`blocking_reasons`**, **`checked_sources`**); **`app/prompt_engine/production_handoff.py`** (`build_production_handoff`); konservativ: **`pending_review`** → nicht **`production_ready`**; **`approved`** → **`ready`**; **`POST /story-engine/prompt-plan`** additiv **`production_handoff_result`**; Tests **`tests/test_ba918_production_handoff.py`**. Kein Produktionsstart, kein Firestore. **`GenerateScriptResponse`** unverändert. |
| **BA 9.19** | **done** | **Production Handoff Export Contract V1:** Versionierter JSON-Vertrag (**`ProductionExportContractResult`**, **`export_contract_version`** `9.19-v1`, **`handoff_package_id`**, **`export_ready`**/**`export_status`**, **`export_payload`** mit vollem Plan-/Quality-/Narrative-/Gate-/Approval-/Handoff-Inhalt, ohne Secrets); **`app/prompt_engine/production_export_contract.py`** (`build_production_export_contract`); abbildet **`production_handoff_result`**; fehlendes Handoff → **`blocked`**; **`POST /story-engine/prompt-plan`** additiv **`production_export_contract_result`**; Tests **`tests/test_ba919_production_export_contract.py`**. Kein Provider/Firestore/Produktionsstart. **`GenerateScriptResponse`** unverändert. |
| **BA 9.20** | **done** | **Connector Packaging / Provider Mapping V1:** Rolle **`ProviderPackage`** (image/video/voice/thumbnail/render), **`ProviderPackagingResult`** (`packaging_status` ready/partial/blocked); Mapping Leonardo/Kling/Voice-Stubs/Thumbnail/Render-Timeline aus Plan + Export-Contract-Gate; **`app/prompt_engine/provider_packaging.py`**; Feld **`provider_packaging_result`**; Tests **`tests/test_ba920_provider_packaging.py`**. Keine echten Provider-Calls. |
| **BA 9.21** | **done** | **Multi-Provider Export Bundle V1:** **`ProviderExportBundleResult`** (`bundle_version` **`9.21-v1`**, **`bundle_id`**, **`providers`** mit fünf Slots); **`app/prompt_engine/provider_export_bundle.py`**; Feld **`provider_export_bundle_result`**; Tests **`tests/test_ba921_provider_export_bundle.py`**. |
| **BA 9.22** | **done** | **Production Package Validation V1:** **`PackageValidationResult`** (`validation_status`, **`production_safety`**, **`missing_components`**, **`recommendations`**); **`app/prompt_engine/package_validation.py`**; Feld **`package_validation_result`**; Tests **`tests/test_ba922_package_validation.py`**. |
| **BA 9.23** | **done** | **Production Timeline Builder V1:** **`TimelineScene`** / **`ProductionTimelineResult`** (Rollen Hook→Outro, geschätzte Sekunden, **`target_video_length_category`** short/medium/long); **`app/prompt_engine/timeline_builder.py`** (`build_production_timeline`); Feld **`production_timeline_result`**; Tests **`tests/test_ba923_timeline_builder.py`**. Kein Render-Start. |
| **BA 9.24** | **done** | **Cost Projection V2:** **`ProviderCostEstimate`** / **`CostProjectionResult`** (EUR-Heuristik Leonardo/Kling/Voice/Thumbnail/Render); **`app/prompt_engine/cost_projection.py`**; Feld **`cost_projection_result`**; Tests **`tests/test_ba924_cost_projection.py`**. Keine API-Preise. |
| **BA 9.25** | **done** | **Final Production Readiness Gate V1:** **`FinalProductionReadinessResult`** (`readiness_decision`, Score, Blocker, Review-Flags, Strengths); **`app/prompt_engine/final_readiness_gate.py`**; Feld **`final_readiness_gate_result`**; Tests **`tests/test_ba925_final_readiness_gate.py`**. Operative Freigabe ohne Produktionsstart. |
| **BA 9.26** | **done** | **Template Performance Comparison V1:** **`TemplatePerformanceEntry`** / **`TemplatePerformanceComparisonResult`**; **`app/prompt_engine/template_performance_comparison.py`** (`compare_template_performance`); Feld **`template_performance_comparison_result`** (optional leer); Tests **`tests/test_ba926_template_performance_comparison.py`**. |
| **BA 9.27** | **done** | **Auto Template Recommendation V1:** **`TemplateRecommendationResult`** (Basis topic_match / historical_performance / narrative_fit); **`app/prompt_engine/template_recommendation.py`**; Feld **`template_recommendation_result`**; Tests **`tests/test_ba927_template_recommendation.py`**. |
| **BA 9.28** | **done** | **Provider Strategy Optimizer V1:** **`ProviderStrategyOptimizerResult`** (Kosten-Priorität, Stub-Provider, Reasoning); **`app/prompt_engine/provider_strategy_optimizer.py`**; Feld **`provider_strategy_optimizer_result`**; Tests **`tests/test_ba928_provider_strategy_optimizer.py`**. |
| **BA 9.29** | **done** | **Production OS Dashboard Summary V1:** **`ProductionOSDashboardResult`** (Gesundheit, Readiness, Kosten, Risiken, Executive Summary); **`app/prompt_engine/production_os_dashboard.py`**; Feld **`production_os_dashboard_result`**; Tests **`tests/test_ba929_production_os_dashboard.py`**. |
| **BA 9.30** | **done** | **Story-to-Production Master Orchestrator V1:** **`MasterOrchestrationResult`** (Launch-Empfehlung proceed/revise/hold); **`app/prompt_engine/master_orchestrator.py`**; Feld **`master_orchestration_result`**; Tests **`tests/test_ba930_master_orchestrator.py`**. |
| **BA 10.0** | **done** | **Production Connector Layer V1:** **`app/production_connectors/`** (Base, Registry, **`dry_run_provider_bundle`**, Provider-Stubs Leonardo/Kling/Voice/Thumbnail/Render); Schema **`ConnectorExecutionRequest`**/**`ConnectorExecutionResult`**/**`ProductionConnectorSuiteResult`**; Feld **`production_connector_suite_result`** auf **`POST /story-engine/prompt-plan`**; Tests **`tests/test_ba100_*.py`**. Nur Dry-Run — keine Live-APIs. |
| **BA 10.1** | **done** | **Live Connector Auth Contract V1:** **`ConnectorAuthContractResult`** / **`ConnectorAuthContractsResult`**; **`app/production_connectors/auth_contract.py`** (`build_connector_auth_contract`, `build_connector_auth_contracts_result`); Felder **`connector_auth_contracts_result`** + optional **`auth_contracts`** in **`ProductionConnectorSuiteResult`**; Tests **`tests/test_ba101_auth_contract.py`**. Keine ENV-Lesung, kein Secret-Logging. |
| **BA 10.2** | **done** | **Provider Execution Queue V1:** **`ExecutionQueueJob`** / **`ProviderExecutionQueueResult`**; **`app/production_connectors/execution_queue.py`** (`build_provider_execution_queue`); Feld **`provider_execution_queue_result`** + optional **`execution_queue_result`** in Suite; Tests **`tests/test_ba102_execution_queue.py`**. Deterministische Reihenfolge, kein Queue-Backend. |
| **BA 10.3** | **done** | **Asset Return Normalization V1:** **`NormalizedAssetResult`**; **`app/production_connectors/asset_normalization.py`** (`normalize_provider_asset_result`); Utility + Tests **`tests/test_ba103_asset_normalization.py`**. Keine Downloads/Uploads. |
| **BA 15.0–15.9** | **done** | **First Production Acceleration Suite V1:** **`app/production_acceleration/`** macht aus Live-/Smoke-Assets eine reproduzierbare lokale Demo-Produktion: Demo-Video-Automation, Asset-Downloader-Plan, Voice Registry, Scene Stitcher, Subtitle Draft, Thumbnail Extract, Founder Local Dashboard, Batch Topic Runner, Cost Snapshot, Viral Prototype Presets; Felder **`*_result`** additiv auf **`POST /story-engine/prompt-plan`**; Tests **`tests/test_ba150_production_acceleration.py`**. Kein Firestore-/YouTube-/Frontend-Zwang. |
| **BA 16.0–16.9** | **done** | **Monetization & Scale Operating System V1:** **`app/monetization_scale/`** bereitet Revenue, Channel Portfolio, Multi-Platform, Opportunity Scanning, Founder KPI, Scale Blueprint, Sponsorship Readiness, Content Investment, Scale Risks und Founder Summary strategisch vor; Felder **`*_result`** additiv auf **`POST /story-engine/prompt-plan`**; Tests **`tests/test_ba160_monetization_scale.py`**. Kein Upload, keine Pflicht-Analytics, keine Business-Automation. |
| **BA 17.0** | **done** | **Viral Upgrade Layer V1 (Founder-only, Lean):** **`app/viral_upgrade/`** — advisory Verpackung (3 Titelvarianten, Hook-Intensität 0–100, 3 Thumbnail-Winkel, emotionaler Treiber, Audience-Mode, Caution-Flags) aus Rewrite-Preview + Prompt-Plan; Feld **`viral_upgrade_layer_result`** auf **`POST /story-engine/prompt-plan`** **vor** Production Assembly; **keine** Skript-Überschreibung, **keine** externen APIs, **kein** Auto-Publish. |
| **BA 18.0** | **done** | **Multi-Scene Asset Expansion Layer V1:** **`app/scene_expansion/`** — pro Kapitel **2–3** produktionsnahe Visual-Beats (`expanded_scene_assets`: chapter/beat index, visual_prompt, camera_motion_hint, duration_seconds, asset_type, continuity_note, safety_notes) aus **`scene_prompts`** + **`chapter_outline`**; Feld **`scene_expansion_result`** additiv **vor** Production Assembly; **keine** Leonardo-/HTTP-Calls, nur Plan. |
| **BA 18.1** | **done** | **Scene Expansion CLI Visibility:** **`scripts/run_url_to_demo.py`** erweitert um **`scene_expansion_asset_count`**, **`beats_per_chapter_default`**, **`first_visual_beats_preview`** (max. 3); graceful Fallback wenn **`scene_expansion_result`** fehlt; Tests **`tests/test_run_url_to_demo_cli_payload.py`**. |
| **BA 18.2** | **done** | **Scene Asset Export Pack (Founder):** **`scripts/export_scene_asset_pack.py`** — URL oder Prompt-Plan-JSON → **`output/scene_asset_pack_<run_id>/`** mit **`scene_asset_pack.json`**, **`leonardo_prompts.txt`**, **`shot_plan.md`**, **`founder_summary.txt`**; Leonardo-Zeilen bereinigt; Tests **`tests/test_export_scene_asset_pack.py`**. |
| **BA 19.0** | **done** | **Local Asset Runner V1:** **`scripts/run_asset_runner.py`** — liest **`scene_asset_pack.json`** (BA 18.2) → **`output/generated_assets_<run_id>/`** mit **`scene_001.png`** …, **`asset_manifest.json`** (`run_id`, `source_pack`, `asset_count`, `assets[]` inkl. `generation_mode`); **`--mode placeholder`** (Default): PIL-Placeholder mit Szenen-/Kapitel-/Beat-Info + Prompt-Snippet; **`--mode live`**: ohne **`LEONARDO_API_KEY`** nur Warnung/Manifest ohne Bilder — **kein** SaaS, **kein** Auto-Publish. |
| **BA 19.1** | **done** | **Timeline Builder V1:** **`scripts/build_timeline_manifest.py`** — **`asset_manifest.json`** → **`output/timeline_<run_id>/timeline_manifest.json`** (Szenen mit start/end/duration, **fade**, **zoom_type**, **pan_direction**, chapter/beat); optional **`--audio-path`**; **kein** Video-Render. Tests **`tests/test_ba191_ba192_timeline_build_and_render.py`**. |
| **BA 19.2** | **done** | **Final Video Render V1 (ffmpeg):** **`scripts/render_final_story_video.py`** — **`timeline_manifest.json`** + Bilder + optional Audio → **`output/final_story_video.mp4`** (concat, scale/pad **1920×1080**, H.264; ohne gültiges Audio → stumm + Warnung **`audio_missing_silent_render`**); bei fehlendem ffmpeg **`blocking_reasons: ["ffmpeg_missing"]`**; stdout JSON mit **`video_created`**, **`scene_count`**, **`warnings`**, **`blocking_reasons`**. Tests **`tests/test_ba191_ba192_timeline_build_and_render.py`**. |
| **BA 20.0** | **done** | **Founder Real Voiceover Generator V1:** **`scripts/build_full_voiceover.py`** — **`--url`** oder **`--prompt-plan-json`** → **`output/full_voice_<run_id>/`** mit **`narration_script.txt`**, **`full_voiceover.mp3`** (Smoke: ffmpeg **`anullsrc`**, Dauer ~**145 W/min**), **`voice_manifest.json`**; Textpriorität **full_script** (JSON) → **Kapitel-Summaries** → **Hook + Summaries** — **kein** SaaS, **kein** Auto-Publish. Tests **`tests/test_build_full_voiceover.py`**. |
| **BA 20.1** | **done** | **Founder Real TTS (ElevenLabs / OpenAI):** Erweiterung **`scripts/build_full_voiceover.py`** — **`--voice-mode smoke|elevenlabs|openai`** (Default smoke); **ElevenLabs:** **`ELEVENLABS_API_KEY`**, optional **`ELEVENLABS_VOICE_ID`**, **`ELEVENLABS_MODEL_ID`**, Chunking (~**4500** Zeichen), Merge per ffmpeg; ohne Key Warnung **`elevenlabs_env_missing_fallback_smoke`** → Smoke; **OpenAI Speech:** **`OPENAI_API_KEY`**, optional **`OPENAI_TTS_VOICE`**, **`OPENAI_TTS_MODEL`**, Chunking (~**3800** Zeichen); ohne Key **`openai_tts_env_missing_fallback_smoke`**; Manifest **`provider_used`**, **`chunk_count`**, **`real_tts_generated`**, **`fallback_used`**; Retries pro Chunk, Mid-Run-Fehler → Smoke-Fallback. Tests **`tests/test_build_full_voiceover.py`**. |
| **BA 20.2** | **done** | **Leonardo Real Image Assets V1:** Erweiterung **`scripts/run_asset_runner.py`** — **`--mode live`** mit **`LEONARDO_API_KEY`** (optional **`LEONARDO_API_ENDPOINT`**, Default **`cloud.leonardo.ai/.../generations`**), **`LEONARDO_MODEL_ID`**; **`--max-assets`** (Default **3** im live-Modus) begrenzt API-Läufe, übrige Beats **Placeholder**; ohne Key Warnung **`leonardo_env_missing_fallback_placeholder`** + vollständige Placeholder-Pipeline (**`ok: true`**); pro Beat: **`leonardo_generate_image_to_path`** (POST + **`fetch_leonardo_generation_result`** Poll) oder Placeholder bei Fehler (**`leonardo_live_beat_failed_fallback_placeholder:<n>`**); Manifest **`generation_mode`:** **`leonardo_live`** | **`leonardo_fallback_placeholder`** | **`placeholder`** je Asset; Top-Level entsprechend. Tests **`tests/test_run_asset_runner.py`**. |
| **BA 20.2b** | **done** | **Placeholder-Visual Polish:** **`_draw_placeholder_png`** in **`run_asset_runner.py`** — dunkler Kino-Verlauf, **`SCENE nnn`**, lesbare **Chapter/Beat**-Labels, **Asset-Typ-Badge**, **Prompt-Snippet**, optional **Camera**-Zeile, Fußzeile *Draft placeholder*; **960×540** unverändert; **`asset_manifest`**-Form unverändert; kein Leonardo. Tests **`tests/test_run_asset_runner.py`**. |
| **BA 20.3** | **done** | **Voice & Visual Style Calibration (Founder-lokal):** Modul **`app/founder_calibration/ba203_presets.py`** — **`scripts/build_full_voiceover.py`** **`--voice-preset`** (`documentary_de` \| `dramatic_documentary_de` \| `calm_explainer_de`): OpenAI-Stimme aus Preset bzw. **`OPENAI_TTS_VOICE`** (Env hat Vorrang + Warnung); ElevenLabs **`voice_settings`** pro Preset, Voice-ID weiter über Env; unbekannt → Default + Warnung **`voice_preset_unknown_*`**. **`scripts/run_asset_runner.py`** **`--visual-style-preset`** (`documentary_news` \| `cinematic_explainer` \| `social_media_policy`): Stil-Präfix nur für **Leonardo**-Prompt; **`asset_manifest.assets[]`** unverändert; unbekannt → Default + Warnung **`visual_style_preset_unknown_*`**. Keine zusätzlichen Live-Bilder per Default. Tests **`tests/test_ba203_presets.py`**. |
| **BA 20.4** | **done** | **Motion & Transition Layer V1 (Founder-lokal):** Erweiterung **`scripts/render_final_story_video.py`** — **`--motion-mode static|basic`** (Default **basic**); **basic:** pro Szene aus **`zoom_type`** / **`pan_direction`** / Fallback aus **`camera_motion_hint`** (`slow_push` / `slow_pull` / `static` + Pan links/rechts), **`xfade`** anhand **`transition`** (fade vs. kurzer Schnitt), optional **`tpad`** damit Videolänge der **Timeline-Summe** entspricht (Audio-Trim wie BA 19.2); bei ffmpeg-Fehler Fallback auf BA-19.2-**concat**-Pfad + Warnung **`motion_render_failed_fallback_static`**; **static:** unverändert BA 19.2. JSON-Felder **`motion_mode`**, **`motion_applied`**. Tests **`tests/test_ba191_ba192_timeline_build_and_render.py`**. |
| **BA 20.5** | **done** | **Subtitle / Caption Layer V1 (Founder-lokal):** Skript **`scripts/build_subtitle_file.py`** — **`--narration-script`**, optional **`--timeline-manifest`**, **`--subtitle-mode none|simple`** (Default **simple**), **`--out-root`** / **`--run-id`** → **`output/subtitles_<run_id>/subtitles.srt`** + **`subtitle_manifest.json`** (Felder laut Spec inkl. **`source_narration_script`**, **`timeline_manifest`**, **`subtitle_count`**, **`estimated_duration_seconds`**); Chunking + gleitmäßige Zeitverteilung anhand Timeline-Summe oder Wort-Schätzung. **`scripts/render_final_story_video.py`** **`--subtitle-path`**: Burn-in per **`subtitles`**-Filter + **`force_style`** (Arial, weiß, Outline, unterer Safe-Bereich); Pfad-Escaping für Windows; bei Fehler erneuter Lauf ohne Untertitel + Warnung **`subtitle_burn_failed_fallback_no_subtitles`**; Felder **`subtitle_path_requested`**, **`subtitles_burned`**. Tests **`tests/test_ba205_subtitles.py`**, **`tests/test_ba191_ba192_timeline_build_and_render.py`**. |
| **BA 20.5b** | **done** | **Subtitle Timing Calibration:** Erweiterung **`scripts/build_subtitle_file.py`** — Gesamtdauer-Priorität: **`ffprobe`** auf **`timeline_manifest.audio_path`** (Warnung **`subtitle_audio_duration_used`**) → Timeline-Szenensumme (**`subtitle_timeline_duration_used`**) → Wort-Schätzung (**`subtitle_duration_estimate_used`**); kürzere Cues (ca. **6–10 Wörter**, Zeichenlimit), pro-Cue-Dauer **clamp + Normalisierung** auf Zielgesamtlänge, letzter Cue endet ≤ Audio/Timeline; gültiges SRT. **`render_final_story_video.py`** unverändert kompatibel. Tests **`tests/test_ba205_subtitles.py`**. |
| **BA 20.5c** | **done** | **Audio-Transkription → Untertitel:** Erweiterung **`scripts/build_subtitle_file.py`** — **`--subtitle-source narration|audio`** (Default **narration**), bei **audio** **`--audio-path`** (z. B. `full_voiceover.mp3`); **`OPENAI_API_KEY`**: **`POST /v1/audio/transcriptions`** (`whisper-1`, **`verbose_json`**), Segment-Zeiten → SRT, sonst Volltext kürzer chunkiert über **ffprobe**-Audiolänge; ohne Key Warnung **`subtitle_audio_transcription_env_missing_fallback_narration`** + Narration-Modus; Cues **4–8 Wörter**; Manifest **`subtitle_source`**, **`transcription_provider`**, **`transcription_used`**, **`fallback_used`**, **`audio_path`**. Kein Wispr, kein SaaS. Tests **`tests/test_ba205_subtitles.py`**. |
| **BA 20.5d** | **done** | **Subtitle Render Style Contract (V1, kein Video-Renderer):** **`scripts/build_subtitle_file.py`** — **`--subtitle-style classic|word_by_word|typewriter|karaoke|none`** (Default **classic**); Normalisierung **`_normalize_subtitle_style`**; Manifest und CLI-JSON **`subtitle_style`**, **`subtitle_render_contract`** (`style`, **`recommended_renderer`**, **`requires_word_timing`**, **`requires_character_timing`**, **`max_words_per_cue`**, **`fallback_style`**, **`warnings`**). **`none`:** keine SRT-Cues, Warnung **`subtitle_style_none_visual_suppressed`**, kein Transkript-API-Lauf; ungültiger Style (programmatisch) → **classic** + Warnung **`subtitle_style_unknown_defaulting_classic`**. Tests **`tests/test_ba205_subtitles.py`**. |
| **BA 20.6** | **done** | **Subtitle Burn-in Preview:** Skript **`scripts/burn_in_subtitles_preview.py`** — **`--input-video`**, **`--subtitle-manifest`** (JSON aus BA 20.5), optional **`--out-root`** (Default **`output`**), **`--run-id`**, **`--force`**; Ausgabe **`output/subtitle_burnin_<run_id>/preview_with_subtitles.mp4`**; **classic** = libass-**`subtitles`**-Burn-in (h264/aac bzw. **`-an`** ohne Tonspur); **word_by_word** / **typewriter** / **karaoke** → gleicher SRT-Burn-in + dokumentierte Warnungen / **`fallback_used`**; **`none`** → **`skipped: true`**, kein ffmpeg. stdout-JSON (**`ok`**, **`skipped`**, Pfade, **`subtitle_style`**, **`fallback_used`**, **`warnings`**, **`blocking_reasons`**). Keine neuen API-Calls; **`render_final_story_video.py`** unverändert. Tests **`tests/test_ba206_subtitle_burnin_preview.py`**. |
| **BA 20.6a** | **done** | **Subtitle Burn-in Safe Style:** **`scripts/burn_in_subtitles_preview.py`** — **`_build_ffmpeg_subtitle_filter`**: **`force_style`** mit Arial, FontSize **22**, Ränder **MarginV=45** / **MarginL/R=40**, **Alignment=2**, **BorderStyle=1**, Outline/Shadow; Windows-taugliches Escapen des SRT-Pfads; optional **Cue-Text-Wrap** (ca. **42** Zeichen, nur Text, Zeiten unverändert) → **`preview_subtitles_wrapped.srt`** + Warnungen **`subtitle_burnin_safe_style_applied`**, **`subtitle_srt_wrapped_for_burnin`**. Tests **`tests/test_ba206_subtitle_burnin_preview.py`**. |
| **BA 20.6b** | **done** | **True Typewriter Subtitle Renderer (Preview):** **`scripts/burn_in_subtitles_preview.py`** — bei **`subtitle_style=typewriter`**: SRT parsen (**`_parse_srt_cues`**), **`preview_typewriter.ass`** mit progressiven **Dialogue**-Zeilen (wachsender Text-Prefix, **`_wrap_typewriter_visible_text`**, **`_escape_ass_text`**), ffmpeg **`ass=`** (Pfad wie SRT escaped); Warnung **`subtitle_typewriter_ass_renderer_used`**, JSON **`renderer_used`:** **`ass_typewriter`**, **`ass_subtitle_path`**; bei Fehler Fallback SRT + **`subtitle_typewriter_ass_failed_fallback_srt`**. **classic** / **word_by_word** / **karaoke** weiter **`srt_burnin`** (bzw. **`none`**). Tests **`tests/test_ba206_subtitle_burnin_preview.py`**, **`tests/test_ba206b_typewriter_ass.py`**. |
| **BA 20.6c** | **done** | **Clean Render Contract (Preview):** **`scripts/burn_in_subtitles_preview.py`** — **`_classify_input_video_role`**: Heuristik auf Pfad/Dateiname (**`preview_with_subtitles`**, **`subtitle_burnin`**, **`with_subtitles`**, **`burned`**) → **`input_video_role`:** **`possibly_burned`** + Warnung **`input_video_may_already_have_burned_subtitles`**; ohne **`--force`** Block **`input_video_possibly_burned_subtitles_use_clean_or_force`** (kein erneutes Burn-in auf mutmaßlich bereits gebrannter Quelle). JSON: **`input_video_role`**, **`output_video_role`**, **`subtitle_delivery_mode`**, **`clean_video_required`**. Tests **`tests/test_ba206c_render_contract.py`**. |
| **BA 20.7** | **done** | **Final Render Output Contract (V1):** **`scripts/render_final_story_video.py`** — optional **`render_output_manifest.json`** unter **`output/render_<run_id>/`** (CLI: **`--run-id`**, Manifest per Default **an**); Felder u. a. **`clean_video_path`**, **`clean_video_role`**, **`subtitle_burnin_video_path`**, **`subtitle_sidecar_srt_path`**, **`subtitle_sidecar_ass_path`**, **`subtitle_delivery_mode`** (**`none`** \| **`sidecar_srt`** \| **`burn_in`** \| **`both`**), **`subtitle_style`**, **`renderer_used`**; **`--subtitle-path`** = **Legacy**-Inline-Burn-in + Warnung **`legacy_subtitle_path_burnin_used`** (primärer Flow: **clean** render, Burn-in separat). **`scripts/burn_in_subtitles_preview.py`** schreibt bei **`ok: true`** **`burnin_output_manifest.json`** + stdout **`burnin_output_manifest_path`**. Kein Auto-Orchestrierungs-Flow. Tests **`tests/test_ba207_final_render_output_contract.py`**. |
| **BA 20.8** | **done** | **Production Output Bundle Validator:** neues Skript **`scripts/validate_production_output_bundle.py`** mit CLI **`--render-manifest`**, **`--subtitle-manifest`**, **`--burnin-manifest`**, **`--output-json`**, **`--strict`**; validiert Dateiexistenz, Delivery-/Rollen-Konsistenz, Typewriter-ASS-Regeln, Burn-in-Contract (`clean_video_required`/`clean_input_video_path`) und erzeugt standardisierte JSON-Ausgabe (**`ok`**, **`status`**, **`warnings`**, **`blocking_reasons`**, **`summary`**). Tests **`tests/test_ba208_production_output_bundle_validator.py`**. |
| **BA 20.9** | **done** | **One Command Local Preview Pipeline:** **`scripts/run_local_preview_pipeline.py`** — ein CLI-Aufruf: **`build_subtitle_file`** → **`render_final_story_video`** (clean, ohne Legacy-**`--subtitle-path`**) → **`burn_in_subtitles_preview`**; gemeinsames **`run_id`**, stdout-JSON (**`ok`**, **`run_id`**, **`pipeline_dir`**, **`steps`**, **`paths`**, **`warnings`**, **`blocking_reasons`**). Tests **`tests/test_ba209_local_preview_pipeline.py`**. |
| **BA 20.10** | **done** | **Local Preview Founder Report:** Nach jedem Lauf generiert **`build_local_preview_founder_report` / `write_local_preview_founder_report`** in **`scripts/run_local_preview_pipeline.py`** ein Markdown mit **Verdict** (PASS/WARNING/FAIL), **Preview-Datei**, **Run**, **Steps**, **Warnings**, **Blocking Reasons**, **Next Step**; optional **`local_preview_report.md`** im Pipeline-Ordner, CLI-Flag **`--print-report`**. Tests **`tests/test_ba2010_local_preview_founder_report.py`**. |
| **BA 20.11** | **done** | **Local Preview Smoke Command:** **`scripts/run_local_preview_smoke.py`** — ruft **`run_local_preview_pipeline`** auf, kompakte Ausgabe (**Status**, **Preview öffnen**, **Report öffnen**, **Open-Me Datei**, **Nächster Schritt**), optional **`--print-json`**; Exit Codes **PASS 0**, **WARNING 2**, **FAIL 1** (Smoke-Konvention, abweichend von **`run_local_preview_pipeline`** Exit 3 bei Fehler). Tests **`tests/test_ba2011_local_preview_smoke.py`**. |
| **BA 20.12** | **done** | **Local Preview Artefact Index / OPEN_ME.md:** **`build_local_preview_open_me` / `write_local_preview_open_me`** in **`scripts/run_local_preview_pipeline.py`**; nach Founder Report wird **`OPEN_ME.md`** im Pipeline-Ordner geschrieben (Keys **`open_me_path`**, **`open_me_markdown`**, **`paths[\"open_me\"]`**). Finalisierung **`finalize_local_preview_operator_artifacts`**. Zentrale Pfad-Helfer **`resolve_local_preview_video_path`**, **`resolve_local_preview_report_path`**, **`resolve_local_preview_open_me_path`**. Tests **`tests/test_ba2012_local_preview_open_me.py`**. |
| **BA 20.13** | **done** | **Local Preview Cleanup / Retention Guard:** **`scripts/cleanup_local_previews.py`** — listet/löscht nur direkte **`local_preview_*`**-Ordner unter **`--out-root`**; Standard **Dry-Run**, **`--apply`** zum Löschen; **`--keep-latest`**, **`--max-delete`**; Symlinks und Nicht-Kinder werden übersprungen; optional **`--print-json`** (ohne **`discovered_paths`**-Ballast). Tests **`tests/test_ba2013_local_preview_cleanup.py`**. |
| **BA 21** | **planned** | **Local Preview Reality & Quality Loop:** Überbau nach **BA 20.9–20.13** — Übergang von „lokal erzeugbar“ zu „lokal real prüfbar“; Unter-BAs **21.0–21.7**; Masterplan **BA 21.4–22.x** (Dashboard-Preview-Übergang); Details im Abschnitt **BA 21** und **BA 21.4–22.x** direkt unterhalb dieser Tabelle. |
| **BA 21.0** | **done** | **Mini E2E Fixture / Real Operator Smoke:** **`fixtures/local_preview_mini/`** (Timeline, Narration, PNGs, README); Shortcut **`scripts/run_local_preview_mini_fixture.py`** delegiert an **`run_local_preview_smoke`**. Tests **`tests/test_ba210_local_preview_mini_fixture.py`**. |
| **BA 21.0c** | **done** | **Preview Artifact Co-location / Path Alignment:** Nach Burn-in wird **`preview_with_subtitles.mp4`** zusätzlich in **`output/local_preview_<run_id>/`** kopiert; **`paths[\"preview_video\"]`** / **`preview_with_subtitles`** zeigen dort hin, optional **`burnin_preview_source`** für den ursprünglichen Pfad; OPEN_ME, Founder Report und Smoke-Summary nutzen die zentrale Kopie. Tests **`tests/test_ba210c_preview_artifact_colocation.py`**. |
| **BA 21.0d** | **done** | **Local FFmpeg Preflight / Setup Guard:** **`check_local_ffmpeg_tools`** / **`build_ffmpeg_setup_hint`** in **`scripts/run_local_preview_pipeline.py`**; Mini-Fixture **`scripts/run_local_preview_mini_fixture.py`** prüft standardmäßig **ffmpeg/ffprobe** vor Smoke, klare Ausgabe und Exit **1** bei fehlenden Tools, **`--skip-preflight`** für bewusstes Umgehen. Tests **`tests/test_ba210d_ffmpeg_preflight.py`**. |
| **BA 21.0e** | **done** | **Idempotent Preview / Existing File:** Bereits vorhandenes **`preview_with_subtitles.mp4`** ist kein Blocker mehr (**`burn_in_subtitles_preview`** liefert **ok** + Warnung); **`sanitize_local_preview_blocking_reasons`** für Verdict/Reports/Pipeline-Aggregat. Tests **`tests/test_ba210e_idempotent_preview_existing.py`**. |
| **BA 21.1** | **done** | **Preview Quality Checklist:** Artefakt- und Bedienbarkeitsprüfung nach lokalem Preview-Lauf; Ergebnis in **`quality_checklist`**, Abschnitt in **Founder Report** / **OPEN_ME**, optional **Quality:** in Smoke. Tests **`tests/test_ba211_preview_quality_checklist.py`**. |
| **BA 21.2** | **done** | **Subtitle Timing Quality Check:** Heuristischer Subtitle-/Cue-Check (Manifest, Dauer, Text, Timing); **`subtitle_quality_check`**, Checklist, Founder Report, **OPEN_ME**, Smoke **Subtitle Quality:**. Tests **`tests/test_ba212_subtitle_timing_quality.py`**. |
| **BA 21.3** | **done** | **Audio/Video Sync Guard:** Grobe Abgleich von Timeline-, Subtitle-, Audio- und Video-Dauern per **ffprobe** (tolerant); **`sync_guard`**, Checklist, Founder Report, **OPEN_ME**, Smoke **Sync Guard:**. Tests **`tests/test_ba213_audio_video_sync_guard.py`**. |
| **BA 21.4–22.x** | **planned** | **From Local Quality Logic to Dashboard Preview Control:** Masterplan für den Übergang von lokaler Preview-/Quality-Logik (**BA 20/21**) zu einem **Dashboard Preview Control System**; Abschnitt **BA 21.4–22.x** mit Leitprinzipien Founder/Operator/Raw, Unter-BAs **21.4–22.6** und Execution-Regel. |
| **BA 19.3** | **planned** | **Quality Polish (optional):** Intro/Outro, Lower Thirds, Subtitle-Burn-in, Thumbnail-Export — **nicht** nötig für ersten Proof. |
| **BA 17.1–17.9** | **planned** | **Media OS / SaaS / Platform Empire Blueprint:** strategische Produktisierungsschicht für White-Label, SaaS Dashboard, API Productization, Licensing, Agency Mode, Marketplace, Investor Readiness, Founder Replacement, Acquisition Funnel und Exit Blueprint. **Blueprint first:** noch keine Runtime-Implementierung, keine SaaS-Billing-/Mandantenpflicht, keine Plattform-Automation. |

### BA 21 — Local Preview Reality & Quality Loop (**planned**)

**Hinweis:** **BA 21** baut auf **BA 20.9–20.13** auf und ist der Übergang von „lokal erzeugbar“ zu „lokal real prüfbar“.

**Status:** **planned** (Gesamtblock)

**Ziel:** Nach dem **Local Preview Operator Block** soll der lokale Preview-Lauf nicht nur Dateien erzeugen, sondern **real bedienbar** und **qualitativ prüfbar** werden.

**Leitfrage:** Kann ein Founder/Operator mit einem **kleinen echten Beispiel-Lauf** lokal prüfen:

- Wird ein Preview-Ordner erzeugt?
- Sind Preview, Report und **OPEN_ME** vorhanden?
- Sind Bild/Ton/Untertitel grob plausibel?
- Sind Warnungen verständlich klassifiziert?
- Gibt es eine klare nächste Handlung?

**Unter-BAs:**

| BA | Titel | Status | Ziel |
|----|-------|--------|------|
| **BA 21.0** | Mini E2E Fixture / Real Operator Smoke | **done** | **`fixtures/local_preview_mini/`** + **`scripts/run_local_preview_mini_fixture.py`**: reproduzierbarer Mini-Lauf, dokumentierte Smoke-/PowerShell-Befehle, Tests **`tests/test_ba210_local_preview_mini_fixture.py`**. |
| **BA 21.0c** | Preview Artifact Co-location / Path Alignment | **done** | Zentrales Paket unter **`local_preview_<run_id>/`**: erzeugte Preview-Datei wird dorthin kopiert (Quelle bleibt), Pfade und Operator-Artefakte (OPEN_ME, Report, Smoke) bevorzugen diesen Ordner; Tests **`tests/test_ba210c_preview_artifact_colocation.py`**. |
| **BA 21.0d** | Local FFmpeg Preflight / Setup Guard | **done** | Mini-Fixture prüft **ffmpeg/ffprobe** (PATH, **`-version`**, Timeout) vor dem Render-Start; bei Fehlen klare Meldung inkl. **winget**-Hinweis und Exit **1**; **`--skip-preflight`** = früheres Verhalten. Tests **`tests/test_ba210d_ffmpeg_preflight.py`**. |
| **BA 21.0e** | Idempotent Preview / Existing File | **done** | Wiederholter Lauf mit gleichem **run_id**: bestehende Preview-Datei blockiert nicht; Warnung bleibt möglich, **Verdict** **WARNING**/PASS statt FAIL nur deswegen. Tests **`tests/test_ba210e_idempotent_preview_existing.py`**. |
| **BA 21.1** | Preview Quality Checklist | **done** | Lokale Artefakt-Checkliste (**`build_local_preview_quality_checklist`**): Preview-Datei, Größe, **OPEN_ME**/Founder-Report, Blocking (sanitized), Warnungen; Einbindung in **`finalize_local_preview_operator_artifacts`**, Founder-Report und **OPEN_ME**; Smoke-Zeile **Quality:**. Tests **`tests/test_ba211_preview_quality_checklist.py`**. |
| **BA 21.2** | Subtitle Timing Quality Check | **done** | Heuristischer Subtitle-Timing-Quality-Check für lokale Preview-Läufe: prüft Subtitle-Manifest, Cue-Anzahl, Cue-Dauer, Textlänge, Wortanzahl und Timing-Reihenfolge; Ergebnis in **`subtitle_quality_check`**, Einbindung in **`quality_checklist`**, Founder Report, **OPEN_ME** und Smoke-Zeile **Subtitle Quality:**. Tests **`tests/test_ba212_subtitle_timing_quality.py`**. |
| **BA 21.3** | Audio/Video Sync Guard | **done** | Audio/Video Sync Guard vergleicht grob Timeline-, Subtitle-, Audio-, Clean- und Preview-Dauer, nutzt **ffprobe** tolerant (nur bei vorhandenen Dateien) und schreibt Status in **`sync_guard`**, Quality Checklist (**`sync_guard`**), Founder Report, **OPEN_ME** und Smoke-Zeile **Sync Guard:**. Tests **`tests/test_ba213_audio_video_sync_guard.py`**. |
| **BA 21.4** | Render Warning Classification | **done** | **`classify_local_preview_warning`**, **`build_local_preview_warning_classification`**, Aggregation aus Top-/Step-Warnungen plus **`sync_guard`** / **`subtitle_quality_check`** / **`quality_checklist`**; Feld **`warning_classification`** in **`finalize_local_preview_operator_artifacts`**; Abschnitte in Founder-Report und **OPEN_ME**; Smoke-Zeile **Warning level:**; Tests **`tests/test_ba214_render_warning_classification.py`**. |
| **BA 21.5** | Founder Quality Decision Layer | **done** | **`build_founder_quality_decision`**: Codes **BLOCK** / **REVIEW_REQUIRED** / **GO_PREVIEW** aus Verdict, Checkliste, Subtitle Quality, Sync Guard und **warning_classification**; Feld **`founder_quality_decision`** in **`finalize_local_preview_operator_artifacts`**; Abschnitte in Founder-Report und **OPEN_ME**; Smoke-Zeile **Founder decision:**; Tests **`tests/test_ba215_founder_quality_decision.py`**. |
| **BA 21.6** | Local Preview Runbook | **done** | Bedienungsdoku für Preview starten, prüfen, reparieren und cleanup: **`docs/runbooks/local_preview_runbook.md`**. |
| **BA 21.7** | Local Preview Result Contract Stabilization | **done** | Stabiles JSON für Dashboard: **`apply_local_preview_result_contract`** am Ende von **`finalize_local_preview_operator_artifacts`**; Felder **`result_contract`** (`id` **`local_preview_result_v1`**, **`schema_version`**), **`verdict`**, kanonische **`paths`**-Schlüssel (**`LOCAL_PREVIEW_RESULT_PATH_KEYS`**), immer **`steps.build_subtitles` / `render_clean` / `burnin_preview`**. Tests **`tests/test_ba217_local_preview_result_contract.py`**. |
| **BA 22.0** | Dashboard Local Preview Panel | **done** | **GET `/founder/dashboard/local-preview/panel`** (JSON: ``out_root``, ``runs`` mit Artefakt-Flags, ``actions``, ``result_contract``-Referenz); Modul **`app/founder_dashboard/local_preview_panel.py`**; Abschnitt im HTML unter **GET `/founder/dashboard`**; Config-Key **`local_preview_panel_relative`**. Tests **`tests/test_ba220_local_preview_panel.py`**. |
| **BA 22.1** | Dashboard Preview Status Cards | **done** | Status-Karten + Tabellenspalten im Founder-Dashboard (**GET `/founder/dashboard`**, Panel **GET `/founder/dashboard/local-preview/panel`** mit ``status_cards`` / ``latest_status_cards``); optional **`local_preview_result.json`** (Snapshot) wird bei Pipeline-Finalize geschrieben (**`scripts/run_local_preview_pipeline.py`**). Tests **`tests/test_ba221_dashboard_preview_status_cards.py`**. |
| **BA 22.2** | Dashboard Preview Video Embed / Open Button | **done** | **GET `/founder/dashboard/local-preview/file/{run_id}/{filename}`** (Whitelist, nur unter Repo-**`output/local_preview_*`**, keine Symlinks); Panel **`file_urls`** / **`latest_file_urls`**; Dashboard: **`<video controls>`** + Links Preview/Report/OPEN_ME/JSON. Tests **`tests/test_ba222_dashboard_preview_video_embed.py`**. |
| **BA 22.3** | Dashboard Preview Start Button | **done** | Preview-Lauf aus dem Dashboard starten. |
| **BA 22.4** | Dashboard Cost Card / Production Estimate | **done** | Geschätzte Produktionskosten als Founder-/Operator-Karte anzeigen. |
| **BA 22.5** | Dashboard Human Approval Gate | **done** | Preview-Freigabe vor finalem Render erfassen. |
| **BA 22.6** | Final Render Button Preparation | **done** | Final-Render-Button vorbereiten, abhängig von Quality, Approval und Kostenstatus. |
| **BA 23.0** | Dashboard Local Preview UX Polish / Control Review | **done** | Local Preview Bereich im Dashboard gliedern (Founder Summary, Aktionen, Diagnostics, Approval, Final Render Readiness, Recent Runs) und Labels/Fehlertexte beruhigen — ohne neue Produktionslogik. |

**Nicht-Ziele BA 21:**

- Kein Cloud/GCP.
- Keine Provider-Calls.
- Kein Upload/Publishing.
- Kein großes Frontend.
- Kein perfektes Produktionsvideo erzwingen.
- Keine Änderung an bestehenden **API-Verträgen**.

**Akzeptanz für den Gesamtblock:**

- Lokaler Mini-Lauf ist **reproduzierbar**.
- Operator bekommt **klare Dateien** und **klare Entscheidung**.
- Quality-Warnings sind **verständlich**.
- Bestehende **Local Preview**-Tests bleiben grün.
- Keine **Secrets** / **`.env`**.

## BA 21.4–22.x — From Local Quality Logic to Dashboard Preview Control

**Status:** planned

**Ziel:**  
Der lokale Preview- und Quality-Loop wird von CLI/Output-Ordnern schrittweise in ein Dashboard-basiertes Founder-/Operator-Cockpit überführt.

**Leitprinzip:**

- **Founder Mode** zeigt Entscheidung, Top Issue und nächsten Schritt.
- **Operator Mode** zeigt Dateien, Checks, Warnings und Reparaturhinweise.
- **Raw Mode** zeigt JSON, Steps und Debug-Daten.
- **CLI** bleibt weiterhin nutzbar, auch wenn Dashboard-Funktionen hinzukommen.

**Voraussetzung:**

- **BA 21.1–21.3** liefern Artefakt-, Untertitel- und Sync-Prüfungen.
- **BA 21.4–21.7** übersetzen diese Informationen in verständliche Entscheidungen und stabile Result-Strukturen.
- **BA 22.x** bringt diese Informationen ins Dashboard.

**Unter-BAs:**

| BA | Titel | Status | Ziel |
|----|-------|--------|------|
| BA 21.4 | Render Warning Classification | done | Local-Preview-Warnings in INFO/CHECK/WARNING/BLOCKING klassifizieren; stabiles **`warning_classification`**-Objekt für Dashboard/Operator. |
| BA 21.5 | Founder Quality Decision Layer | done | Stabiles **`founder_quality_decision`**-Objekt (Top-Thema, nächster Schritt, Signale) für Founder/Dashboard. |
| BA 21.6 | Local Preview Runbook | done | Bedienungsdoku für Preview starten, prüfen, reparieren und cleanup: **`docs/runbooks/local_preview_runbook.md`**. |
| BA 21.7 | Local Preview Result Contract Stabilization | done | Stabiles JSON: **`result_contract`**, **`verdict`**, **`LOCAL_PREVIEW_RESULT_PATH_KEYS`**; **`apply_local_preview_result_contract`** in **`finalize_local_preview_operator_artifacts`**; Tests **`tests/test_ba217_local_preview_result_contract.py`**. |
| BA 22.0 | Dashboard Local Preview Panel | done | **GET `/founder/dashboard/local-preview/panel`**, Modul **`app/founder_dashboard/local_preview_panel.py`**, Panel im Founder-Dashboard-HTML; Tests **`tests/test_ba220_local_preview_panel.py`**. |
| BA 22.1 | Dashboard Preview Status Cards | done | Status-Karten aus Snapshot/Contract-JSON; alte Runs ohne JSON → UNKNOWN; Tests **`tests/test_ba221_dashboard_preview_status_cards.py`**. |
| BA 22.2 | Dashboard Preview Video Embed / Open Button | done | Sichere File-Route + Video-Embed/Open-Links im Founder-Dashboard; Tests **`tests/test_ba222_dashboard_preview_video_embed.py`**. |
| BA 22.3 | Dashboard Preview Start Button | done | Preview-Lauf aus dem Dashboard starten. |
| BA 22.4 | Dashboard Cost Card / Production Estimate | done | Geschätzte Produktionskosten als Founder-/Operator-Karte anzeigen. |
| BA 22.5 | Dashboard Human Approval Gate | done | Preview-Freigabe vor finalem Render erfassen. |
| BA 22.6 | Final Render Button Preparation | done | Final-Render-Button vorbereiten, abhängig von Quality, Approval und Kostenstatus. |
| BA 23.0 | Dashboard Local Preview UX Polish / Control Review | done | Local Preview Bereich im Dashboard gliedern und Labels/Fehlertexte beruhigen — ohne neue Produktionslogik. |

**Nicht-Ziele:**

- Kein sofortiges Full-SaaS-Frontend.
- Kein YouTube-Upload.
- Kein Auto-Publishing.
- Keine Provider-Calls ohne Guard.
- Kein UI-Polish vor stabiler Funktion.
- Keine Entfernung der CLI-Workflows.

**Akzeptanz:**

- Local Preview bleibt per CLI bedienbar.
- Dashboard bekommt klare Founder-/Operator-Sicht.
- Raw-Daten bleiben für Debugging verfügbar.
- Jede Unter-BA bleibt einzeln testbar.
- Keine Secrets/.env.
- Bestehende Tests bleiben grün.

**Execution-Regel:**  
Dieser Abschnitt ist eine Landkarte. Die Umsetzung erfolgt strikt einzeln: **1 BA pro Cursor-Durchlauf.** Nach jeder BA: Tests, Difference-only Summary, Stop. Nicht eigenmächtig die nächste BA beginnen.

## BA 24 — Final Render Execution Layer

**Status:** planned

**Ziel:**  
Aus einem **geprüften** und **freigegebenen** Local-Preview-Run soll später ein **finaler Video-Export** erzeugt werden. BA 24 definiert den kontrollierten Übergang **Preview → Final Render** (lokal, ohne Upload).

**Leitprinzip:** Kein Final Render ohne:

- vorhandene Preview-Datei
- Quality nicht **FAIL**
- Founder Decision nicht **BLOCK**
- Human Approval **approved**
- Cost Status nicht **OVER_BUDGET** (oder später bewusst per Override freigegeben)
- klare Output-Pfade
- klare Fehler- und Wiederholungslogik (idempotent)

**Unter-BAs:**

| BA | Titel | Status | Ziel |
|----|-------|--------|------|
| **BA 24.0** | Final Render Execution Plan | **done** | Final-Render-Workflow, Gates, Inputs, Outputs und Fehlerlogik dokumentieren. |
| BA 24.1 | Final Render Contract | done | Stabiles Result-Schema für `final_render_result.json` definieren. |
| BA 24.2 | Final Render Dry-Run Endpoint | done | Dashboard-/Backend-Route, die Final Render readiness simuliert, ohne Video zu erzeugen. |
| BA 24.3 | Final Render Execution Script | done | Lokales Script, das aus freigegebenem Preview-Paket einen finalen Export erzeugt. |
| BA 24.4 | Final Render Dashboard Action | done | Dashboard-Button triggert echten Final Render kontrolliert. |
| BA 24.5 | Final Render Report / OPEN_ME Update | done | Report und OPEN_ME um finalen Export, Status und Pfade erweitern. |
| BA 24.6 | Final Render Error Recovery | done | Fehlerfälle, Retry und idempotentes Verhalten absichern. |
| BA 25.0 | Real Video Build Wiring Map | done | Dokumentiert die bestehende Script-Kette (Inputs/Outputs/Placeholder) und die fehlende Verkabelung. |
| BA 25.1 | Real Video Build Orchestrator CLI | **done** | `scripts/run_real_video_build.py` verbindet Asset Runner / Timeline / Voiceover-Smoke / Render / Subtitles / Burn-in mit **einer** `run_id` zu `output/real_build_<run_id>/real_video_build_result.json`. Kein URL-Input, kein Final Render. |
| BA 25.2 | Script/Story-Pack Input Adapter | **done** | Script/Story-Pack Input Adapter wandelt `GenerateScriptResponse`/Story-Pack in ein Orchestrator-kompatibles `scene_asset_pack.json` und stellt echten Narrationstext für den Real Video Build bereit. |
| BA 25.3 | URL-to-Script Bridge | **done** | URL-to-Script Bridge erzeugt aus Artikel-/YouTube-URLs eine lokale `GenerateScriptResponse`-kompatible JSON-Datei für den BA-25.2-Adapter; kein Render, kein Publishing. |
| BA 25.4 | Real Local Preview Run | **done** | `scripts/run_ba_25_4_local_preview.py` verbindet `generate_script_response.json` (BA 25.3) → BA 25.2 Adapter → BA 25.1 Orchestrator zu `output/real_local_preview_<run_id>/` mit `scene_asset_pack.json`, `real_video_build_result.json` und `preview_with_subtitles.mp4`. Keine neuen Provider-Calls, keine Vertragsänderung. |
| BA 25.5 | URL-to-Final-Video Smoke | **done** | End-to-End lokal: URL → preview_with_subtitles.mp4 → final_video.mp4 (ohne Publishing). |
| BA 25.6 | URL-to-Final-Video Smoke Hardening | **done** | Stabilisierung/Idempotenz/strukturierte Fehler/Operator-OPEN_ME für `run_ba_25_5_url_to_final_video_smoke.py`; Auto-Approve klar gekennzeichnet; `--no-auto-approve` ohne Final Render. **Local URL-to-Final-Video MVP: completed.** |
| BA 26.0 | Live Smoke Scope Freeze | **done** | Scope festgezurrt: echte Artikel-URL, Leonardo Live-Bilder, Video-Provider-Spike Runway vs. Google Veo (ein Provider), kein Sora-Primärpfad; lokal 2–3 Min., kein Upload. Details: **BA 26.0** unter Abschnitt **BA 26**. |
| BA 26.2 | Runway Image-to-Video Smoke | **done** | Isolierter lokaler Testclip: `scripts/runway_image_to_video_smoke.py`, `RUNWAY_API_KEY`; keine Pipeline-Integration. |
| BA 26.3 | Runway Clip Asset Ingest (lokal) | **done** | Lokale MP4/MOV/WebM aus `scene_asset_pack` → `asset_manifest` / `timeline_manifest` → `render_final_story_video.py`; kein neuer Provider-API-Call. |
| BA 26.3R | Reality Check & Pipeline Plan Sync | **done** | Inventar BA 26.x vs. Code; dokumentierter Reality-Lauf mit vorhandenem lokalem Clip (kein neues Feature); siehe Abschnitt **BA 26.3R** unter **BA 26**. |
| BA 26.4 | Real Provider Smoke Test Mode | **done** | **Ist:** Dry-Run Default (kein HTTP); **Runway Live** möglich mit Flags + `RUNWAY_API_KEY` (delegiert BA 26.2). **Veo:** nur Dry-Run-Stub, Live blockt. Details: **BA 26.4R** unter **BA 26.x**. |
| BA 26.4b | Visual Provider Routing + No-Text Guard | **done** | Zentraler Router (`leonardo` / `openai_images` / `runway` / `render_layer`), No-Text-Guard an Prompts, `overlay_intent` bei Lesetext-Absicht; additive Felder in Prompt-/Watchlist-Modellen. Tests `tests/test_ba264b_visual_text_policy.py`. Siehe **Visual Text Policy** unter **BA 26**. |
| BA 26.4c | Manifest Effective Prompt + Dashboard Visual Policy Summary | **done** | Manifeste spiegeln `visual_prompt_raw` vs. `visual_prompt_effective` + Policy-Ampel (`safe`/`text_extracted`/`needs_review`) + Routing-Grund. Founder Dashboard zeigt Visual Policy Summary + per Szene Policy-Line in Prompt Cards. |
| BA 26.4d | Dashboard Visual Policy Fallback from Export | **done** | Dashboard-Summary nutzt Optimize-Daten bevorzugt, fällt aber auf `export-package.provider_prompts` und `scene_prompts.scenes` zurück; zeigt „Visual Policy Source: …“, damit Operator Policy auch vor Optimize sieht. |
| BA 26.4e | Provider Routing Acceptance Smoke | **done** | Trockener Acceptance-Smoke (Test) prüft Routing/Guard/Overlay-Auslagerung/Policy-Felder und Dashboard-kompatible Key-Namen; **BA 26.5 hängt davon ab** (keine Live-Calls, keine Kosten). |
| BA 26.4R | Real Provider Smoke Audit & Next-Step | **done** (Doku) | Code-/Test-Audit BA 26.4; keine neuen Features; Entscheidungsgrundlage für **BA 26.5** (siehe **Decision Summary** im Runbook / unten). |
| BA 26.6c | Scene Image Replacement / Manual Override | **done** | Pure Dict-Helper + CLI-Patch für `asset_manifest.json` (accepted/rejected/locked/needs_regeneration + selected_asset_path + manual provider/prompt override + history). Dashboard bleibt read-only; keine Provider-Calls. Tests `tests/test_ba266c_asset_override.py`. |
| BA 26.7c | Provider Quality Compare Smoke | **done** | Heuristischer Compare-Layer (keine Live-Calls) ergänzt `provider_candidates`, `recommended_provider`, `provider_compare_status` u. a. Optionales CLI `scripts/run_provider_quality_compare.py` patcht `asset_manifest.json`. Dashboard zeigt Compare-Line, falls Felder vorhanden. Tests `tests/test_ba267c_provider_quality_compare.py`. |
| BA 26.8c | Visual Cost Tracking | **done** | Heuristische Kosten pro Asset + Summary (EUR), keine Billing-API. CLI `scripts/run_visual_cost_tracking.py` patcht `asset_manifest.json` mit `visual_cost_*` Feldern und `visual_cost_summary`. Compare-Kandidaten erhalten echte `estimated_cost`. Tests `tests/test_ba268c_visual_costs.py`. |
| BA 26.9c | Production Asset Approval Gate | **done** | Gate prüft `asset_manifest.json` (Policy/Guard/Overrides/Overlay/Kostenwarnungen) und schreibt `production_asset_approval_result`. CLI `scripts/run_production_asset_approval_gate.py`. Tests `tests/test_ba269c_asset_approval_gate.py`. |
| BA 27.0 | Real End-to-End Production Pack V1 | **done** | File-basierter Pack-Build unter `output/production_pack_<run_id>/` bündelt `script.json`, `scene_asset_pack.json`, `asset_manifest.json`, `production_asset_approval.json`, `production_summary.json`, `README_PRODUCTION_PACK.md` und kopiert referenzierte Assets nach `assets/`. `ready_for_render` ist **nur** true bei `approval_status=="approved"`. Helper `app/real_video_build/production_pack.py`, CLI `scripts/build_production_pack_v1.py`, Tests `tests/test_ba270_production_pack_v1.py`. |
| BA 27.1 | Visual Reference Library / Continuity Anchors | **done** | File-basierte `reference_library.json` (Kontinuitätsanker) + additive Asset-Felder (`reference_asset_ids`, `continuity_strength`, `reference_policy_status`). Helper `app/visual_plan/reference_library.py`, CLI `scripts/build_reference_library_v1.py` (Attach unterstützt auch `prompt_hint` + `provider_status`). Production Pack kann optional `reference_library.json` kopieren und `reference_library_summary` in `production_summary.json` ergänzen. Tests `tests/test_ba271_reference_library.py`. |
| BA 27.2 | Continuity-Aware Prompt Wiring | **done** | Continuity-Wiring patcht `asset_manifest.json` additiv mit `continuity_reference_paths`, `continuity_reference_types`, `continuity_provider_preparation_status`, `continuity_provider_payload_stub` und `continuity_wiring_version`. CLI `scripts/run_continuity_prompt_wiring.py`. Production Pack Summary enthält optional `continuity_wiring_summary`. Tests `tests/test_ba272_continuity_prompt_wiring.py`. |
| BA 27.3 | Continuity Display in Prompt Cards / Exports | **done** | Operator-Sichtbarkeit für Continuity: Display-Helper `app/visual_plan/continuity_display.py`, Prompt Cards zeigen eine Continuity-Zeile wenn Felder vorhanden, Production Pack README enthält „Continuity“-Counts (aus `continuity_wiring_summary`). Tests `tests/test_ba273_continuity_display.py`. |
| BA 27.4 | Reference-Aware Provider Adapter Preparation | **done** | Provider-kompatible Reference-Payload-Stubs ohne Live-Uploads: `reference_provider_payloads` (openai_images/leonardo/runway/seedance) + `recommended_reference_provider_payload` + Summary. CLI `scripts/run_reference_provider_payloads.py`. Production Pack Summary kann `reference_provider_payload_summary` spiegeln. Real Provider Smoke zeigt Status/Feld-Auszug im dry-run. Tests `tests/test_ba274_reference_provider_payloads.py`. |
| BA 27.5 | Provider-Specific Reference Payload Formats | **done** | Verfeinert die BA‑27.4 Stubs provider-spezifisch (V1: `openai_images`): additiv `payload_format` + `payload` unter `reference_provider_payloads.openai_images`, ohne Live-Uploads/Calls. Tests erweitert in `tests/test_ba274_reference_provider_payloads.py`. |
| BA 27.5b | Dashboard Scene-Level Reference Provider Display | **done** | Founder Dashboard zeigt pro Szene/Prompt Card eine deutsche Operator-Zeile aus `recommended_reference_provider_payload`/`reference_provider_payloads` (Status/Provider/Modus/Kein Live-Upload). Read-only; keine Writes/Calls. Test erweitert in `tests/test_phase10_founder_dashboard.py`. |
| BA 27.6 | Reference Provider Payload Export/Pack Wiring | **done** | Additive Spiegelung/Pass-through der Reference-Payload-Felder entlang operator-sichtbarer Pfade: Mirror-Helper `app/visual_plan/reference_payload_mirror.py`, Production Pack Summary ergänzt `reference_payload_mirror_summary`, Provider Optimizer erhält Reference-Metafelder (wenn Source sie hat), Dashboard Prompt Cards können auf `asset_manifest` fallbacken. Tests `tests/test_ba276_reference_payload_wiring.py`. |
| BA 27.7 | Snapshot Contract for Asset Manifest Reference Index | **next** | Erzeugt kompakten `asset_manifest_reference_index` (by `scene_number`) aus `asset_manifest.assets[]` inkl. Reference-/Continuity-/Reference-Provider-Feldern für Dashboard-/Snapshot-Fallback. Optional CLI `scripts/build_asset_manifest_reference_index.py`. Production Pack kann Index als JSON-Datei ablegen und/oder im `production_summary.json` referenzieren. |
| BA 27.8 | Runway / Seedance / Leonardo Reference Payload Formats | **planned** | Ergänzt provider-spezifische Payload-Stubs unter `reference_provider_payloads[provider]` via `payload_format` + `payload` (Runway/Seedance/Leonardo), kompatibel zu OpenAI Images (BA 27.5). Keine Live-Uploads/Calls. |
| BA 27.9 | Visual Production Preflight Summary | **planned** | Kompakter Preflight-Status (`ready|needs_review|blocked`) als additive Summary (`visual_production_preflight_result`) basierend auf Approval Gate, Costs, Continuity/Reference-Index/Reference-Payloads. Ändert `ready_for_render` nicht. Optional CLI. |
| BA 28.0 | Motion Provider Layer V1 / Clip Generation Contract | **planned** | Dry-Run Motion-Provider-Vertrag für Runway/Seedance (kein echter Clip, kein Render): `motion_clip_result` pro Szene + `motion_clip_manifest.json` via CLI `scripts/run_motion_provider_dry_run.py`. Referenzen nur als Stub (`no_live_upload: true`). |
| BA 29.1 | Legacy Manifest Upgrade + Pack Wiring | **done** | Additive Modernisierung älterer `asset_manifest.json` (Effective-Prompt/No-Text-Guard/Policy-Warnungen/Override-Defaults + Manifest-Marker `legacy_manifest_upgrade_*`) für Production-Run-/Gate-Pfade; Pure Helpers `app/visual_plan/legacy_manifest_upgrade.py`, CLI `scripts/upgrade_legacy_asset_manifest.py` (`--dry-run`, optional `--run-cost-tracking`, `--run-approval-gate`). Keine Live-Calls/Uploads. Tests `tests/test_ba291_legacy_manifest_upgrade.py`. |
| BA 29.2 | Actual Local Preview Render from Bundle | **done** | `app/production_assembly/local_preview_render.py` + CLI `scripts/render_local_preview_from_bundle.py`: einfache lokale MP4-Vorschau aus `render_input_bundle.json` (Stillframes/Clips, Timeline-Dauer, kein Audio-Zwang); bei fehlendem FFmpeg `error_code=ffmpeg_missing` ohne Crash; Artefakte `local_preview.mp4`, `local_preview_render_result.json`, `README_PREVIEW.md` / `OPEN_PREVIEW.txt`. Tests `tests/test_ba292_local_preview_render.py`. Runbook `docs/runbooks/local_preview_render_v1.md`. |
| BA 29.2b | Render Input Bundle Media Path Hydration | **done** | `build_render_input_bundle` lädt optional `asset_manifest` (Pfad und/oder Dict) und füllt `image_paths`/`clip_paths` aus `assets[]` (Priorität Bild: selected/generated/image; Clip: video_path, clip_path), löst relative Pfade zum Manifest-Ordner auf, Deduplizierung, `media_path_hydration_summary` (`ba29_2b_v1`). Keine Änderung der Ready-for-Render-Regeln. Tests `tests/test_ba292b_render_input_bundle_hydration.py`. |
| BA 29.2c | Preview Smoke Auto-Runner | **done** | `app/production_assembly/preview_smoke_auto.py`: neuestes nutzbares `asset_manifest.json` unter `output/`, optional Legacy-Upgrade/Cost/Approval via `prepare_asset_manifest_for_smoke`, BA-29.0-Lauf, Bundle-Rehydration `ensure_bundle_has_media_paths`, lokale Preview wie `scripts/render_local_preview_from_bundle.py` (gleiche Library), Summary `output/preview_smoke_auto_summary_<run_id>.json`, CLI `scripts/run_preview_smoke_auto.py` (`--run-id`, `--output-root`, optional `--asset-manifest`). Keine Live-Provider-Calls. Tests `tests/test_ba292c_preview_smoke_auto.py`. |
| BA 29.2d | Preview Smoke Media Path Preservation | **done** | Vor dem Schreiben des prepared Manifests: `preserve_or_absolutize_asset_media_paths` löst relative Medienfelder in `assets[]` gegen den **Quell**-Ordner der `asset_manifest.json` auf (nicht gegen `.preview_smoke_work`), setzt existierende Dateien als absolute Pfade; fehlende Dateien → Warning + Zähler, kein Crash. Summary-Felder `media_path_preservation_summary` (`media_path_preservation_version: ba29_2d_v1`). Bundle-Hydration (`images_found`/`clips_found`) und Local Preview vermeiden damit falsch aufgelöste Pfade unter dem Work-Ordner. Tests `tests/test_ba292d_preview_smoke_media_path_preservation.py`. |
| BA 29.3 | Preview Render Pack Wiring | **done** | Production Pack kopiert optional `local_preview_render_result.json` + `local_preview.mp4`; `production_summary.json` enthält `local_preview_*`; `build_production_pack_v1.py` mit `--local-preview-render-result` / `--preview-video`; Orchestrator `run_first_real_production_30_60.py` optional `--render-local-preview`. Tests `tests/test_ba293_preview_pack_wiring.py`. |
| BA 29.4 | Human Preview Review Gate | **done** | `human_preview_review_result` (`review_version: ba29_4_v1`) via `app/production_assembly/human_preview_review.py` + CLI `scripts/patch_human_preview_review.py` (file-based, keine Dashboard-Writes). Tests `tests/test_ba294_human_preview_review.py`. |
| BA 29.5 | Final Render Readiness After Human Review | **done** | `final_render_readiness_result` (`readiness_version: ba29_5_v1`) in `app/production_assembly/final_render_readiness.py`; CLI `scripts/run_final_render_readiness_gate.py`. Tests `tests/test_ba295_final_render_readiness.py`. |
| BA 29.6 | Final Render Execution Stub / Safe Local Render | **done** | `app/production_assembly/final_render_execution.py` + CLI `scripts/run_safe_final_render.py`: Default Dry-Run, echter Schritt nur mit `--execute` und `readiness_status==ready`. Tests `tests/test_ba296_final_render_execution.py`. |
| BA 30.0 | Founder Dashboard Production Flow V1 | **done** | Read-only Panel „Produktionsfluss“ in `app/founder_dashboard/html.py` (deutsche Status-Labels, keine Write-Buttons). Doku `docs/runbooks/founder_production_flow_v1.md`. Tests erweitert in `tests/test_phase10_founder_dashboard.py`. |
| BA 30.1 | Preview Smoke Golden Path / Open-Me Report | **done** | Nach Preview-Smoke (Erfolg oder Block): deutschsprachiger Operator-Report `OPEN_PREVIEW_SMOKE.md` unter `output/.preview_smoke_work/<run_id>/` via `write_preview_smoke_open_me_report`; Summary-Feld `open_preview_smoke_report_path`; Schreibfehler nur als `open_preview_smoke_write_warnings`, kein Crash. CLI `run_preview_smoke_auto.py` gibt optional `open_preview_smoke_report_path` auf stdout aus. Tests `tests/test_ba301_preview_smoke_open_me.py`. |
| BA 30.2 | Fresh Topic to Preview Smoke | **done** | Neu: `app/production_assembly/fresh_topic_preview_smoke.py` + CLI `scripts/run_fresh_topic_preview_smoke.py`: exklusiv `--topic` \| `--url` \| `--script-json` → Skript (`build_script_response_from_extracted_text` / URL-Extrakt / JSON) → BA-26.5-Helfer aus `run_url_to_final_mp4` (Szenezeilen, Pack) → `run_local_asset_runner` default **placeholder** (opt-in `--allow-live-assets` für `live`) → optional vollständiger `execute_preview_smoke_auto` (BA 29.0 + Preview + OPEN_PREVIEW_SMOKE). Arbeitsordner `output/fresh_topic_preview/<run_id>/`. `--dry-run` endet nach `asset_manifest.json`. Kein Upload/Publishing. Tests `tests/test_ba302_fresh_topic_preview_smoke.py`. |
| BA 30.3 | Fresh Preview Dashboard Snapshot | **done** | `build_latest_fresh_preview_snapshot` in `app/production_assembly/fresh_preview_snapshot.py`: read-only Scan von `output/fresh_topic_preview/<run_id>/` (neuester Ordner nach mtime), Pfad-Existenz für Skript/Pack/Manifest/Summary/Open-Me; optional kleines JSON-Lesen für `open_preview_smoke_report_path`. API `GET /founder/dashboard/fresh-preview/snapshot`, Config-Key `fresh_preview_snapshot_relative`; Founder Dashboard Panel „Fresh Preview Smoke (BA 30.3)“ lädt per fetch. Keine Provider/Secrets. Tests `tests/test_ba303_fresh_preview_dashboard_snapshot.py`. |
| BA 30.4 | Fresh Preview Readiness Gate | **done** | Additiv: `evaluate_fresh_preview_readiness` in `fresh_preview_snapshot.py` — `readiness_status` ready/warning/blocked, `readiness_score` 0–100, `readiness_reasons`, `blocking_reasons`, aktualisierte `operator_next_step`; begrenzte JSON-Prüfung (≤512 KB) für script/pack/manifest + Summary-`ok`. Dashboard-Badge/Score/Zeilen. Snapshot-Version `ba30_4_v1`. Tests `tests/test_ba304_fresh_preview_readiness.py` + Anpassungen `test_ba303`. |
| BA 30.5 | Fresh Preview Operator Controls (Dashboard) | **done** | Nur `app/founder_dashboard/html.py`: Button „Fresh Preview aktualisieren“ (erneuter read-only Snapshot-Fetch), Copy-Buttons für Kernpfade, prominente Next-Step-Box (Farben je Readiness), getrennte Listen für Blocking / Readiness-Hinweise / Scan-Warnungen. Keine neuen Routen, keine Writes, keine Provider. Tests: `test_phase10_founder_dashboard.py`, `test_ba303_*`. Runbooks: `local_preview_render_v1.md`, `founder_production_flow_v1.md`. |
| BA 30.6 | Founder Dashboard Visual Upgrade V1 | **done** | Minimal-invasiv in `app/founder_dashboard/html.py`: B2B-Dashboard-Tokens (`--vp-*`), vereinheitlichte Cards/Schatten, Hero mit **VideoPipe Founder Cockpit**, Status-Pills **Production Ready** / **Local Preview Pipeline**, Header-CTA scrollt nur zum bestehenden Local-Preview-Panel; Fresh-Preview-Panel: Executive-Strip, prominenteres Readiness-Badge, ruhigere Pfad-Copy-Buttons, klar getrennte Reason-Boxen. Keine neuen APIs, keine IDs entfernt, keine `sticky`/`fixed`. Tests: `test_phase10_founder_dashboard.py` (+ Design-Marker), `test_ba303_*`, `test_ba304_*`. Runbooks: `local_preview_render_v1.md`, `founder_production_flow_v1.md`. |
| BA 30.6b | Founder Cockpit Layout Realignment | **done** | Nur `app/founder_dashboard/html.py`: breitere Fläche (`max-width` ~1400px), radialer Hintergrund, größerer Hero + Operator-Subline, **Executive Row** (`Fresh Preview Status`, `Readiness Score`, `Latest Run`, `Next Operator Step`) direkt unter dem Header, **Fresh Preview** als Haupt-Cockpit zweispaltig (Dry-Run links, Readiness/Snapshot rechts), Founder Strategic Summary + Local Preview nach unten; Header-CTA **Zum Fresh Preview Panel** scrollt zu `panel-ba303-fresh-preview`. Keine API-/Routen-Änderungen, alle bestehenden IDs/`data-ba30x` erhalten. Tests: `test_phase10_founder_dashboard.py`. |
| BA 30.6d | Founder Dashboard Score Gauge Alignment | **done** | Nur `app/founder_dashboard/html.py`: **Score Gauge Alignment** für **Preview Power** (conic-gradient-Ring, ruhige Innenfläche), abgestimmte **Sidebar-Mini-Gauge** und **Executive-Mini-Gauge** für Readiness; wiederverwendbare CSS-Klassen (`fd-score-gauge*`). Anzeige nur aus dem bestehenden Snapshot-Feld **`readiness_score`** / **`readiness_status`** — **keine Fake-KPIs** oder erfundene Prozentwerte für andere Bereiche. Marker `data-ba306d-score-gauge`. Tests: `test_phase10_founder_dashboard.py`, `test_ba303_*`. |
| BA 30.7 | Fresh Preview Dry-Run Start (Dashboard) | **done** | `POST /founder/dashboard/fresh-preview/start-dry-run` in `app/routes/founder_dashboard.py`: genau eines von `topic` \| `url`, immer `dry_run=True`, `asset_runner_mode=placeholder`, `provider=placeholder`, Run-ID `fresh_dash_<ms>`; ruft `run_fresh_topic_preview_smoke` mit `default_local_preview_out_root()`. UI-Card im Fresh-Preview-Panel (`Dry-Run starten`, Hinweis Dry-Run-only), nach Erfolg `fdLoadFreshPreviewSnapshot()`. Config-Key `fresh_preview_start_dry_run_relative`. Tests `tests/test_ba307_fresh_preview_dashboard_start.py` + bestehende Dashboard-Tests. Runbooks: `local_preview_render_v1.md`, `founder_production_flow_v1.md`. |
| BA 30.8 | Full Preview Smoke CLI Handoff (Dashboard) | **done** | Additiv: erfolgreiche Dry-Run-Response liefert `handoff_cli_command`, `handoff_cli_command_powershell`, `handoff_note`, `handoff_warning` (Run-ID `<dry_run>_full`, `--output-root output`, `--provider placeholder`, **ohne** `--dry-run` und **ohne** `--allow-live-assets`). UI-Box „Nächster Schritt: Full Preview Smoke lokal starten“ + Kopieren-Button. Kein Full-Run im Browser. Response-Version `ba30_8_v1`. Tests `tests/test_ba308_fresh_preview_handoff.py`, Anpassungen `test_ba307`/`test_phase10`/`test_ba303`. Runbooks: `local_preview_render_v1.md`, `founder_production_flow_v1.md`. |
| BA 30.9 | Fresh Preview Artifact Access (Dashboard) | **done** | Read-only `GET /founder/dashboard/fresh-preview/file?path=…`: sichere Auslieferung von `.md`/`.json`/`.txt` nur aus zulässigen Fresh-Preview-Zonen unter `output/` (`fresh_topic_preview/**`, `preview_smoke_auto_summary_*.json`, `.preview_smoke_work/<run_id>/OPEN_PREVIEW_SMOKE.md`); Resolve + `relative_to`, keine Symlinks, max. 1 MB, Path Traversal blockiert; 403/404/413. Helper `app/founder_dashboard/fresh_preview_artifact_access.py`. UI: Link **„Öffnen“** (neuer Tab) neben Copy. Keine MP4-Auslieferung in BA 30.9. Config `fresh_preview_file_relative`. Tests `tests/test_ba309_fresh_preview_artifact_access.py`. Runbooks: `local_preview_render_v1.md`, `founder_production_flow_v1.md`. |

### BA 24.0 — Final Render Execution Plan (**done**)

**Was löst später der Klick auf „Finales Video erstellen“ aus?**  
Ein lokaler, kontrollierter Final-Render-Flow, der **nur** auf einem vorhandenen `output/local_preview_<run_id>/`-Paket arbeitet und alle Gates strikt prüft, bevor Render/Export ausgeführt wird (Umsetzung erst BA 24.3/24.4).

#### Voraussetzungen (Gates)

- **Run-Ordner:** `output/local_preview_<run_id>/`
- **Required artefacts (mindestens):**
  - `preview_with_subtitles.mp4` **oder** `preview_video.mp4` (Dashboard-Link genügt; Datei muss existieren)
  - `local_preview_result.json`
  - `local_preview_report.md`
  - `OPEN_ME.md`
  - `human_approval.json` mit `status == "approved"`
- **Required states:**
  - `verdict != FAIL`
  - `quality_checklist.status != fail`
  - `founder_quality_decision.decision_code != BLOCK`
  - `cost_card.status != OVER_BUDGET` (oder später explizites Override)
  - `final_render_gate.status == ready` (Dashboard-Aggregatregel aus BA 22.6)

**Blocker-Logik (klassisch):**

- Fehlende Preview → **BLOCK**
- Missing approval → **LOCKED**
- Quality FAIL / Founder BLOCK / Verdict FAIL → **BLOCK**
- Cost OVER_BUDGET → **LOCKED** („review required“)

#### Inputs (Quelle der Wahrheit)

- **Preview-Paket:** `output/local_preview_<run_id>/` (Artefakte + Report + Approval)
- **Contract/Result:** `local_preview_result.json` als strukturierte Basis (Paths/Warnings/Blocking)
- **Optional später:** Export-/Manifestdaten, falls im Preview-Run bereits vorhanden und referenziert

Kein Input aus `.env`, keine externen Provider-Calls, keine Cloud/GCP.

#### Geplante Outputs (Final Render Package)

- `output/final_render_<run_id>/final_video.mp4`
- `output/final_render_<run_id>/final_render_result.json`
- `output/final_render_<run_id>/FINAL_OPEN_ME.md`
- Optional (später, falls sinnvoll):
  - `output/final_render_<run_id>/export_manifest.json`
  - `output/final_render_<run_id>/final_quality_report.md`

#### Idempotenz / Wiederholung

- Existiert `final_video.mp4` bereits: **nicht blind überschreiben**.
- Default: **idempotent** (return „already exists“ + Pfade).
- Overwrite/force nur später per **explizitem Flag** (nicht BA 24.0).

#### Fehlerverhalten

- Fehler werden in `final_render_result.json` strukturiert erfasst (ab BA 24.1).
- Dashboard zeigt „locked/blocked“ + reason; keine globalen JS-Crashes.
- Ein fehlgeschlagener Lauf hinterlässt ein nachvollziehbares Paket (Result + Hinweise), ohne Output-Verzeichnis zu „verschmutzen“.

#### Explizite Nicht-Ziele BA 24.0

- Kein echter Render / kein ffmpeg-Lauf
- Kein Upload / kein Publishing / kein YouTube Scheduling
- Keine Provider-Calls / keine Billing-Integration
- Keine neuen UI-Flows außer Dokumentation
- Keine Änderung an bestehenden Core-API-Verträgen

**Akzeptanz:**

- Final-Render-Flow ist **vor** Umsetzung klar dokumentiert (Gates, Inputs, Outputs, Fehlerlogik, Idempotenz).
- BA 24.1–24.6 sind als kleine, testbare Schritte definiert.
- Bestehende Dashboard-/Preview-Logik bleibt unverändert.

## BA 24.x — Local Final Render MVP Freeze Plan

**Status:** active / frozen scope

**Ziel:**  
Der lokale MVP-Flow soll jetzt abgeschlossen werden, **ohne** neue Zwischen-BAs einzuschieben.

**MVP-Ziel (Operator im Dashboard):**

1. Preview erstellen
2. Preview ansehen
3. Quality/Warnings/Founder Decision prüfen
4. Preview freigeben
5. Final Render starten
6. Finales Video im Output-Ordner finden
7. Final Render Report / OPEN_ME lesen

**Verbindlicher Restplan:**

| BA | Titel | Status | Ziel |
|----|-------|--------|------|
| BA 24.3 | Final Render Execution Script | **done** | Lokales Script erzeugt aus freigegebenem Preview-Paket ein `final_render_<run_id>`-Paket mit `final_video.mp4`. |
| BA 24.4 | Dashboard Final Render Action | planned | Dashboard-Button startet kontrolliert den Final Render. |
| BA 24.5 | Final Render Report / OPEN_ME Update | done | Finales Paket erhält klare Bedienungsdateien und Report. |
| BA 24.6 | Final Render Error Recovery / Idempotenz | done | Retry, existing-file handling, force/overwrite und Fehlerausgaben stabilisieren. |

**Scope Freeze:**  
Bis BA 24.6 werden **keine** neuen Feature-BAs eingeschoben. Erlaubt sind nur:

- Bugfixes
- Testfixes
- kleine Doku-Korrekturen
- Sicherheitsfixes

**Nicht-Ziele bis Abschluss BA 24.6:**

- kein YouTube Upload
- kein Scheduling
- kein neues Dashboard-Redesign
- keine neue Cost-Engine
- keine neuen Provider-Integrationen
- keine neuen Quality-Layer außer Bugfix
- kein SaaS/User-System
- kein UI-Polish über notwendige Bedienbarkeit hinaus

**Definition of Done für Local Final Render MVP:**

- Preview kann im Dashboard erzeugt werden.
- Preview ist im Dashboard sichtbar/öffnbar.
- Quality/Warning/Founder Decision sichtbar.
- Human Approval funktioniert.
- Final Render kann gestartet werden.
- `final_video.mp4` wird erzeugt.
- `final_render_result.json` wird geschrieben.
- `FINAL_OPEN_ME.md` oder finaler Report erklärt den Output.
- Tests sind grün.
- CLI bleibt nutzbar.

**Execution-Regel:**  
Nach BA 24.6 wird der MVP-Block geschlossen (**Local Final Render MVP: completed**). Erst danach wird entschieden, ob der nächste Block Publishing, Dashboard Polish oder Provider-Integration ist.

## BA 25 — Real URL/Script-to-Local-Video Build

**Status:** planned

**Ziel:** Vom echten Script/Story-Pack (oder URL) zu einem lokal gespeicherten Video — Preview + Final-Package — **ohne** Upload/Publishing, **ohne** Provider-Zwang. Schließt die Verkabelungslücke zwischen vorhandenen Einzel-Scripts (BA 18.2 / 19 / 20 / 21 / 24) zu einem nutzbaren End-to-End-Lauf.

**Abgrenzung:**

- **BA 25** ist **nicht** Phase 9 (Video Packaging) und **nicht** Phase 10 (Publishing).
- **BA 25** baut **nicht** den Story-Engine-Kern aus (das bleibt BA 9.x).
- **BA 25** ändert **keine** Verträge (`GenerateScriptResponse`, `local_preview_result`, `final_render_result`).

**Unter-BAs:**

| BA | Titel | Status | Ziel |
|----|-------|--------|------|
| BA 25.0 | Real Video Build Wiring Map | **done** | Bestehende Script-Kette (Inputs/Outputs/Placeholder) und fehlende Verkabelung dokumentiert in [`docs/runbooks/real_video_build_wiring_map.md`](docs/runbooks/real_video_build_wiring_map.md). |
| BA 25.1 | Real Video Build Orchestrator CLI | **done** | [`scripts/run_real_video_build.py`](scripts/run_real_video_build.py) verbindet vorhandene Build-Scripts mit **einer** `run_id` zu einem `output/real_build_<run_id>/real_video_build_result.json`-Indexpaket; Steps: Asset Runner → Voiceover-Smoke → Timeline (mit `audio_path`) → Clean Render → Subtitles → Burn-in. Kein URL-Input, kein TTS-Live, kein Final Render. Tests `tests/test_ba251_real_video_build_orchestrator.py`. |
| BA 25.2 | Script/Story-Pack Input Adapter | **done** | Script/Story-Pack Input Adapter wandelt `GenerateScriptResponse`/Story-Pack in ein Orchestrator-kompatibles `scene_asset_pack.json` und stellt echten Narrationstext für den Real Video Build bereit. |
| BA 25.3 | URL-to-Script Bridge | **done** | [`scripts/run_url_to_script_bridge.py`](scripts/run_url_to_script_bridge.py) nimmt Artikel-/YouTube-URL und schreibt `output/url_script_<run_id>/generate_script_response.json` (kompatibel mit BA-25.2-Adapter); kein Render, kein Final Render, kein Orchestrator-Lauf, kein Publishing. Tests `tests/test_ba253_url_to_script_bridge.py`. |
| BA 25.4 | Real Local Preview Run | **done** | [`scripts/run_ba_25_4_local_preview.py`](scripts/run_ba_25_4_local_preview.py) nimmt `generate_script_response.json` (z. B. aus BA 25.3) und verdrahtet BA 25.2 Adapter → BA 25.1 Orchestrator zu `output/real_local_preview_<run_id>/` mit `scene_asset_pack.json`, Verweis auf `real_video_build_result.json` und `preview_with_subtitles.mp4`. Keine Vertragsänderung an `GenerateScriptResponse`/`scene_asset_pack.json`/`real_video_build_result.json`. Tests `tests/test_ba254_local_preview_run.py`. |
| BA 25.5 | URL-to-Final-Video Smoke | **done** | End-to-End lokal: URL → `preview_with_subtitles.mp4` → `final_video.mp4` (ohne Publishing). |
| BA 25.6 | URL-to-Final-Video Smoke Hardening | **done** | Result-Contract `ba_25_6_url_to_final_video_result_v1`, Pfad-Felder, `failure_stage`, Reality-Smoke-Doku; `--no-auto-approve` blockiert Final Render. **Local URL-to-Final-Video MVP: completed.** |

**Local URL-to-Final-Video MVP:** Abgeschlossen mit **BA 25.6** (Smoke-Runner + Tests + Runbook; kein Publishing, kein Upload in diesem MVP).

**Akzeptanz BA 25.0:** Wiring Map dokumentiert für jeden vorhandenen Schritt (1–9) Input/Output, kennzeichnet Placeholder-/Smoke-/Copy-V1-Punkte und nennt konkrete Verkabelungslücken sowie den kürzesten realen Local-MVP-Pfad (2–3 Min. zuerst, später 10 Min.). Keine Code-Änderungen.

## BA 26 — Real Content Live Smoke

**Status:** **BA 26.0** + **BA 26.2–26.8** im Repo **umgesetzt**; **BA 26.1** weiter **planned**. Für Abgleich Code ↔ Dokumentation siehe **BA 26.3R**.

**Ziel (Gesamtbild):**  
Nach **BA 25.6** wird der Flow mit **echten Inhalten und angeschlossenen Provider-Assets** getestet. **Erster Bildpfad:** **Leonardo Live Images** (`run_asset_runner` / `--asset-mode live`, sofern Key und Live-Modus gesetzt). **Video-Clips:** nicht parallel mehrere Anbieter — zuerst **Provider-Spike Runway vs. Google Veo**, dann **ein** ausgewählter Connector. **Sora** wird **nicht** als Primär-Connector priorisiert (Anbieter-Doku: Videos-API deprecated/auslaufend). **Voice:** zunächst Smoke bzw. vorhandene/manuelle Audio-Option; echte Provider-TTS später separat. Output bleibt **lokal** (`final_video.mp4`). **Kein** YouTube-Upload, **kein** Publishing.

**Leitentscheidung:**  
Nach **BA 25.6** werden **keine** weiteren internen Komfort-, Dashboard-, Cost-, Report- oder Quality-BAs eingeschoben, außer **echte Bugfixes**. Nächster inhaltlicher Block: **Real Content Live Smoke** gemäß **BA 26.0** Scope Freeze.

**Ist-Stand im Repository (Code + dokumentierte Smoke-Pfade):**

| Thema | Stand |
|-------|--------|
| **Leonardo Live (Bilder)** | **Ausführbar:** `scripts/run_asset_runner.py` mit `--mode live` nutzt u. a. `LEONARDO_API_KEY` (Pflicht für Live), optional `LEONARDO_API_ENDPOINT`, optional `LEONARDO_MODEL_ID`. Ohne Key: Fallback Placeholder mit Warnungen. Zusätzlich `app/production_connectors/leonardo_live_connector.py` (HTTP mit Guard; Dry-Run möglich). |
| **Runway (Video-Clips)** | **BA 26.2** Smoke-Skript erzeugt lokalen MP4; **BA 26.3** bindet **vorhandene** lokale Clips in Asset-Manifest, Timeline und Render ein (`video_path` u. a.) — **ohne** neuen Runway-Call in der Pipeline. |
| **Google Veo (Video-Clips)** | **BA 26.4 Smoke-Modus:** `dry_run`-Stub + Live blockt mit `veo_provider_not_implemented` (kein HTTP-Client); Key-Env `GOOGLE_VEO_API_KEY` für spätere Anbindung dokumentiert. |
| **Sora** | **Nicht als Primärpfad** geplant (Scope Freeze). |
| **Kling** | `app/production_connectors/kling_connector.py` **Dry-Run only**; nicht Teil der BA-26-Video-Entscheidung. |
| **`run_real_video_build` / BA 25.4** | Verarbeitet **Leonardo-Live-PNGs** bei `asset_mode=live`; Timeline/Render aktuell **Bildpfade** im `asset_manifest.json`. |
| **Render** | `render_final_story_video.py`: Stillimages + optional **Video-Segmente** (lokal, **BA 26.3**) mit ffmpeg (`-stream_loop`/`filter_complex`); weiterhin **basic**/**static** für Bilder. |
| **provider_configs / Guards** | Primär Produktions-/Dashboard-Pfade; lokaler Asset-Runner prüft Leonardo-ENV direkt (`run_asset_runner._live_env_ready`). |
| **Outputs bei Live-Bildern** | `output/generated_assets_<run_id>/scene_XXX.png`, `asset_manifest.json` u. a. mit `generation_mode` `leonardo_live` / gemischt bei `--max-assets`-Cap. |

**Visual Text Policy (BA 26.4b):** Bild- und Video-**Generatoren** liefern **keine finale Lesetypografie** (keine Fake-UI, keine „echten“ Dokumenttexte im Bild). Konkrete Titel, Untertitel, Lower-Thirds und Listenzeilen werden im **Render-/Overlay-Layer** gesetzt. Stimmung, Szene, Motiv, Licht und Komposition gehen an **Leonardo** (cineastische B-Roll/Stills ohne Schrift), **OpenAI Images** (textnahe Schlüsselbilder / Thumbnail-Basis / text_sensitive), **Runway** (Motion aus sauberen Startframes ohne generierte Schrift). Reines Typo-/Label-Paket: Disposition **`render_layer`** plus optionales Basis-Still über `image_provider`.

**Stand Video-Clips:** **BA 26.3** erlaubt **lokal vorliegende** Clips in der Render-Kette. **BA 26.4** ergänzt **kontrollierten** Provider-Smoke (`dry_run` / Live mit Sicherheitsflags, max. 1 echte Szene Default). **BA 26.5** liefert einen **Founder-Run** (URL oder `script.json` + optionales `--asset-dir`) bis **`final_video.mp4`** ohne Provider-Pflicht. **BA 26.6** entfernt aus dem Founder-Render sichtbare Debug-/Szenenlabels (textfreie cinematic Placeholder, Video-Reuse, Default `motion-mode=basic`). **BA 26.7** ergänzt den Founder-Run um **Voice** (`--voice-mode existing|elevenlabs|dummy|openai`); ohne `--voice-mode` bleibt das BA-26.5/26.6-Verhalten unverändert. **BA 26.7b** passt optional die Video-Timeline an die Voice-Länge an (`--fit-video-to-voice`). **BA 26.8** orchestriert den ersten **echten Visual-Durchstich**: Script → Leonardo-Bilder (live) → Runway-Videos (live) → ElevenLabs-Voice → `final_video.mp4` + `visual_summary.json`; Provider-Live nur bei ENV/Keys, ehrliche Blocker/Fallbacks. **BA 26.1** = echte Artikel-URL + **Leonardo** + Render bis `final_video.mp4`.

### BA 26.x — Real Video Build (Ist-Code vs. Plan)

| BA | Kurztitel | Implementiert | Kurzbeschreibung |
|----|-----------|---------------|------------------|
| **26.2** | Runway Image-to-Video Smoke | **ja** | `scripts/runway_image_to_video_smoke.py` → lokaler MP4 (ein Task), `RUNWAY_API_KEY` aus ENV. |
| **26.3** | Local Video Clip Ingest | **ja** | `scripts/run_asset_runner.py` (Felder s. unten), `scene_pack_local_video.py`, `build_timeline_manifest.py`, `render_final_story_video.py`; Tests `tests/test_ba263_runway_clip_asset_ingest.py`. |
| **26.3R** | Reality Check & Plan-Sync | **ja** (Doku) | Kein neues Produkt-Feature: Plan und Runbook an Realität; optionaler manueller Reality-Lauf mit vorhandenem Clip (siehe **Reality-Test Status**). |
| **26.4** | Real Provider Smoke Test Mode | **ja** (siehe **26.4R**) | Orchestrierung Pack→Szenen; **Runway** Live = echter API-Pfad via `run_runway_image_to_video_smoke`. **Veo** = Stub / Blocking. |
| **26.4b** | Visual Provider Routing + No-Text Guard | **ja** | `app/visual_plan/visual_provider_router.py`, `visual_no_text.py`; Prompt-/Pack-Pfade (Export, Scene Assets, Script-Adapter, Runway-Smoke, Leonardo-Stil-Preset); additive Model-Felder (`overlay_intent`, Routing). |
| **26.4R** | Audit & Next-Step | **ja** (Doku) | Prüfung: BA 26.4 ist **nicht** „nur Stub“ für Runway, aber **nicht** voll Live für Veo; Anbindung an BA 26.3 nur manuell per Pfad. |
| **26.5** | URL-to-final-MP4 Founder Run (vorhandene Assets) | **ja** | [`scripts/run_url_to_final_mp4.py`](scripts/run_url_to_final_mp4.py): `--url` oder `--script-json`, `--asset-dir` (rekursiv `.mp4`/…/Bilder), Placeholder-Asset-Runner, Timeline, Render → `final_video.mp4` + `run_summary.json`; **kein** Pflicht-Live-Provider. Tests `tests/test_ba265_url_to_final_mp4.py`. |
| **26.6** | Visual Founder Upgrade | **ja** | Founder-`final_video.mp4` ohne sichtbare „SCENE 001"-Labels: textfreie cinematic Placeholder + Video-Reuse über Szenen + Default `motion-mode=basic`. Kein neuer Provider-Call. Detail unten. |
| **26.7** | ElevenLabs Voice Founder Integration | **ja** | Founder-`final_video.mp4` mit Ton: `--voice-mode existing\|elevenlabs\|dummy\|openai`; `--voice-mode none` (Default) = altes Verhalten; ENV-getriebene Secrets, keine neuen Verträge. Detail unten. |
| **26.7b** | Fit Video Duration to Voice | **ja** | Optional `--fit-video-to-voice` + `--voice-fit-padding-seconds` (Default 0,75): nach Voice-Erzeugung Szenen-Dauern/Timeline an Voice-Länge anpassen; `run_summary` mit `fitted_video_duration_seconds` u. a.; keine neue Voice-Integration. |
| **26.8** | Real Visual Assets Founder Smoke | **ja** | [`scripts/run_real_visual_founder_smoke.py`](scripts/run_real_visual_founder_smoke.py): Script → Leonardo-Bilder (live) + Runway-Clips (live) → ElevenLabs Voice → `final_video.mp4` + `visual_summary.json`. Provider-Live nur bei ENV/Keys; saubere Blocker und Fallbacks. Tests `tests/test_ba268_real_visual_founder_smoke.py`. |

**BA 26.3 — unterstützte Beat-/Pack-Felder für lokale Clips:** `video_path`, `local_video_path`, `clip_path`, `runway_clip_path`, `asset_video_path` (relativ zum Ordner der `scene_asset_pack.json` oder absolut); Datei muss existieren, reguläre Datei, Endung `.mp4` / `.mov` / `.webm`, kein Symlink (wo prüfbar). Ungültig → Warnung, Fallback Placeholder/Leonardo wie bisher.

**BA 26.3 — Tests / Render mit MP4:** Unit-/Integrationspfad in `test_ba263`: Manifest/Timeline/Mock-ffmpeg; bei vorhandenem **ffmpeg** zusätzlich `test_render_creates_mp4_from_video_timeline` mit synthetischem Mini-MP4. **Kein** Pflicht-Check eines fest eingecheckten Runway-Binärclips im Repo (Artefakte liegen typ. unter `output/`).

**Reality-Test Status (BA 26.3R, manuell im Workspace):** Unter `output/runway_smoke_runway_smoke_002/runway_clip.mp4` lag ein gültiger Clip (~862 KB). Kette **Asset Runner** → **Timeline** → **Render** (`--motion-mode static`) mit `scene_asset_pack.json`, das per `runway_clip_path` auf diesen Clip zeigt, lieferte u. a. `asset_manifest` mit `asset_type` `video` und `video_path` `scene_001.mp4` (Kopie im `generated_assets_*`‑Ordner), `timeline_manifest` mit `media_type` `video`, und `video_created: true` für `output/ba263r_reality_check/ba263r_clean.mp4` (Dauer gemäß Timeline ~6 s, ohne Audio → erwartete Warnung `audio_missing_silent_render`). Liegt **kein** lokaler Clip vor, entfällt dieser Schritt; **BA 26.3** bleibt im Code implementiert, der Reality-Lauf wird dann nicht ausgeführt.

**BA 26.4R — Real Provider Smoke: Ist-Status (Audit, kein Code-Change)**

| Aspekt | Befund |
|--------|--------|
| **Gesamteinschätzung** | **Live-fähig für Runway** (echter HTTP über BA 26.2); **Veo nur Dry-Run/Stub**, Live immer `veo_provider_not_implemented`. CLI-Default = **Dry-Run** → **kein** Provider-Call ohne `--live`. |
| **Module / CLI** | `app/production_connectors/real_provider_smoke.py` (`run_real_provider_smoke`), `scripts/run_real_provider_smoke.py`. |
| **Provider-Auswahl** | `--selected-provider runway \| veo` (Pflicht). |
| **ENV** | Runway: `RUNWAY_API_KEY`. Veo (nur für spätere Nutzung dokumentiert): `GOOGLE_VEO_API_KEY` — Live nutzt sie **nicht** (Block vor HTTP). |
| **Live-Runway-Gates** | `dry_run=false` (CLI: `--live`), `real_provider_enabled=true` (`--real-provider-enabled`), Key gesetzt, `max_real_scenes` nicht überschritten, pro Szene `scene_{i:03d}.png` unter `--assets-directory`, kein gültiger lokaler Clip im Beat **oder** `--force-provider`. |
| **Dry-Run** | Runway: strukturierte `dry_run_request_summary` (URL, Body-Felder mit Platzhalter statt Base64). Veo: statischer TBD-Stub. **Kein** Netzwerk. |
| **Output (CLI)** | `output/real_provider_smoke_<run_id>/real_provider_smoke_result.json` (+ stdout JSON). |
| **Output (Runway Live)** | Zusätzlich Artefakte von `run_runway_image_to_video_smoke`: typ. `…/real_provider_smoke_<run_id>/runway_smoke_<run_id_scNNN>/runway_clip.mp4` und `runway_smoke_result.json` (Kontrakt BA 26.2). |
| **Blocking / Warnings (Auszug)** | `invalid_run_id`, `invalid_selected_provider`; pro Szene u. a. `real_provider_not_enabled`, `runway_api_key_missing` / `veo_api_key_missing`, `max_real_scenes_reached`, `veo_provider_not_implemented`, `runway_scene_image_missing`, `runway_call_exception`; Warnung `local_clip_takes_precedence_skip_provider` wenn BA-26.3-Pfad Vorrang hat. |
| **Tests** | `tests/test_ba264_real_provider_smoke.py`: Dry-Payload, Gates, fehlender Key, Cap, `force_provider`, lokale Priorität — **Live-Runway bewusst mit `runway_run_fn`-Mock**, kein optionaler CI-Live-Test gegen die echte API. |
| **Anbindung BA 26.3** | **Kein** automatischer Schritt „26.4 → Manifest“. Ein erfolgreicher Live-Lauf liefert eine **lokale MP4-Datei**; für die Render-Pipeline trägt der Operator den Pfad in `scene_asset_pack` ein (`runway_clip_path` / `video_path` o. ä.) oder kopiert die Datei — identisch zum manuellen BA-26.3R-Pfad. |

**BA 26.5 — Umsetzung (Option A umgesetzt):** [`scripts/run_url_to_final_mp4.py`](scripts/run_url_to_final_mp4.py) verdrahtet **URL** (`extract_text_from_url` + `build_script_response_from_extracted_text`) oder **`script.json`** → `script.json` / `scene_plan.json` / `scene_asset_pack.json` → `run_asset_runner` (**placeholder**, kein Leonardo-Pflicht) → `build_timeline_manifest` → `render_final_story_video` → **`final_video.mp4`**, dazu **`run_summary.json`** und **`render_result.json`**. Vorhandene Clips/Bilder aus **`--asset-dir`** (rekursive Suche) werden Szenen **der Reihe nach** als `runway_clip_path` bzw. nach dem Asset-Runner als zusätzliche Bilddatei ins Manifest gemappt; ohne Video im Ordner: Warnung `no_existing_video_asset_found_using_fallback` und Placeholder-Pfad. URL ohne extrahierbaren Text: **blocking** `url_extraction_empty_use_script_json`. **BA 26.4** bleibt **optional** (z. B. Runway-Clip erzeugen → Ordner als `--asset-dir` oder MP4 in denselben Ordner legen).

**BA 26.5 — Reality-Lauf (manuell, ohne neuen Provider-Call):** Mit der Mini-Fixture `fixtures/real_video_build_mini/generate_script_response.json` und dem BA‑26.2-Clip `output/runway_smoke_runway_smoke_002/runway_clip.mp4` als `--asset-dir` liefert `scripts/run_url_to_final_mp4.py` (Script-JSON-Modus, `--max-scenes 3 --duration-seconds 30 --motion-mode static`) ein lokales `final_video.mp4` (~30 s) unter `output/ba265_founder_smoke/` mit `run_summary.json` (`ok: true`, `used_video_assets_count: 1`) und den erwartbaren Warnungen `existing_asset_used` / `audio_missing_silent_render`. Liegt **kein** Clip im `--asset-dir`, blockt nichts: Warnung `no_existing_video_asset_found_using_fallback` (Placeholder-Render).

**Was möglich ist:** Vorhandene lokale Clips (z. B. BA-26.2-Output) in die gleiche Render-Kette wie Placeholder-Bilder einbinden; gemischte Bild-/Video-Timelines mit ffmpeg.

**BA 26.6 — Visual Founder Upgrade (umgesetzt):** [`scripts/run_url_to_final_mp4.py`](scripts/run_url_to_final_mp4.py) überschreibt nach `run_asset_runner` alle Bild-Szenen-PNGs durch eine **textfreie cinematic Placeholder-Variante** (`_draw_cinematic_placeholder_png`, deterministisch identisch über alle Szenen — keine sichtbaren `SCENE NNN` / `Chapter X · Beat Y` / `BROLL` / `DRAFT PLACEHOLDER`-Texte aus BA 20.2b mehr im Founder-Render). Liegt **weniger** Videos in `--asset-dir` als Szenen vor, wird das **letzte vorhandene Video** für die restlichen Szenen wiederverwendet (Reuse-Loop, ffmpeg `-stream_loop`); Warnung `ba266_video_reuse_for_remaining_scenes`. CLI-Default `--motion-mode` wandert von `static` auf **`basic`** (Ken-Burns / xfade), damit reine Bild-Szenen nicht starr stehen. Asset-Runner / Render / `scene_asset_pack`-Vertrag bleiben unverändert (das textbeschriftete BA-20.2b-Placeholder wird nur **nach** dem Asset-Runner überschrieben, nicht ersetzt). Tests: `tests/test_ba266_visual_founder_upgrade.py`.

**BA 26.6 — Reality-Lauf:** Mit derselben Mini-Fixture und demselben BA‑26.2-Clip (`output/runway_smoke_runway_smoke_002/runway_clip.mp4`) liefert `scripts/run_url_to_final_mp4.py --motion-mode basic` ein lokales `final_video.mp4` (~30 s, ~5,5 MB) unter `output/ba266_visual_founder_smoke/` mit `used_video_assets_count: 3` und drei **bytegleichen** textfreien Placeholder-PNGs (~19 KB) im `generated_assets_*`-Ordner. Erwartete Warnungen: `ba266_video_reuse_for_remaining_scenes`, `existing_asset_used`, `ba266_cinematic_placeholder_applied:3`, `audio_missing_silent_render`.

**BA 26.7 — Umsetzung (ElevenLabs Voice Founder Integration):** [`scripts/run_url_to_final_mp4.py`](scripts/run_url_to_final_mp4.py) sammelt aus den geplanten Szenen einen **labelfreien** Voiceover-Text (Hook + Kapitel-Narration, **ohne** „Szene 1" / „Chapter 1" / IDs / JSON), schreibt ihn als `voiceover_text.txt` in den Output-Ordner und übergibt ihn — je nach `--voice-mode` — an einen Voice-Synthesizer:

- **`none`** (Default) — altes Verhalten unverändert; `audio_missing_silent_render` weiterhin möglich.
- **`existing`** — `--voice-file` (`.mp3`/`.wav`/`.m4a`) wird validiert und direkt als `audio_path` an die Timeline übergeben.
- **`elevenlabs`** — wiederverwendet die vorhandene `synthesize_elevenlabs_mp3()` aus [`scripts/build_full_voiceover.py`](scripts/build_full_voiceover.py); ENV `ELEVENLABS_API_KEY`, optional `ELEVENLABS_VOICE_ID` / `ELEVENLABS_MODEL_ID`. Per CLI können `--elevenlabs-voice-id` / `--elevenlabs-model` die ENV überschreiben (Werte werden **nie** gelogged).
- **`dummy`** — schreibt ein stilles MP3 via ffmpeg `anullsrc` (Smoke-Pfad ohne API-Kosten, klare Warnung `dummy_voice_used_not_real_tts`).
- **`openai`** — optionaler Pfad über die vorhandene `synthesize_openai_mp3()`; nicht Hauptpfad.

Audio-Pfad wandert **transparent** durch `build_timeline_manifest(audio_path=…)` → `render_final_story_video` → `final_video.mp4`. Bei `voice_used: true` enthält das Video einen Audio-Stream; `audio_missing_silent_render` verschwindet aus den Warnungen (es kann statt­dessen `audio_shorter_than_timeline_padded_or_continued` auftauchen, wenn die Audio-Dauer kürzer als das Video ist — wird vom bestehenden Render robust gehandhabt). Fehlt API-Key/Voice-ID, blockt der Pfad sauber mit z. B. `elevenlabs_missing_api_key` — **kein** Crash, **kein** Secret-Leak. `run_summary.json` enthält die neuen Felder `voice_used`, `voice_mode`, `voice_text_path`, `voice_file_path`, `voice_duration_seconds`, `audio_stream_expected`, `voice_warnings`, `voice_blocking_reasons`. Tests: `tests/test_ba267_elevenlabs_voice_founder_integration.py`.

**BA 26.7 — Reality-Lauf (lokal, ohne ElevenLabs-Live, ENV nicht gesetzt):**

- `output/ba267_dummy_voice_smoke/final_video.mp4` (~5,5 MB, Audio-Stream **vorhanden**) — `voice_mode: dummy`, `voice_used: true`, Warning `dummy_voice_used_not_real_tts`.
- `output/ba267_existing_voice_smoke/final_video.mp4` (~5,5 MB, Audio-Stream **vorhanden**) — `voice_mode: existing`, `voice_used: true` aus einer demonstrativen lokalen MP3-Datei.
- `output/ba267_voice_founder_smoke/` (`voice_mode: elevenlabs`) — sauber blockiert mit `voice_blocking_reasons: ["elevenlabs_missing_api_key"]`, `audio_stream_expected: false`; final_video.mp4 wird trotzdem erzeugt (silent), keine Secrets im Output.

**BA 26.7 — Live-Smoke bestätigt (ElevenLabs + Fit, Operator-Lauf):** Unter **`output/baum_voice_custom_fit_5/`** liegt ein erfolgreicher Founder-Run mit **`voice_mode: elevenlabs`**, **`voice_used: true`**, leeren **`voice_blocking_reasons`**, **`audio_stream_expected: true`**, **`fit_video_to_voice: true`**. **`run_summary.json`** (ohne Secrets): `ok: true`, **`voice_duration_seconds`** ≈ **15,23** (ffprobe Voice), **`fitted_video_duration_seconds`** **16**, **`original_requested_duration_seconds`** **30**; **`voice_warnings`:** leer. **`final_video.mp4`** und **`voiceover.mp3`** vorhanden und nicht leer; **ffprobe:** Audio-Stream im MP4, Video-Dauer ≈ **16,0 s** (statt ~30 s ohne Fit). Erwartete **nicht-sensitive** Warnings: u. a. `ba266_*`, `existing_asset_used`, `ba267_video_fitted_to_voice:…target_total=16s…`. **Bekannte frühere Blocker (ohne Key-Werte):** `elevenlabs_missing_api_key`, HTTP **401** oder Key **ohne** passende **Text-to-Speech-Berechtigung** bei ElevenLabs. **Lösung:** gültiger Account/API-Zugang mit **TTS-Berechtigung** plus **korrekte Voice-ID** (per ENV oder `--elevenlabs-voice-id`); keine Schlüssel oder IDs im Repo oder in Logs dokumentieren.

**BA 26.7b — Fit Video Duration to Voice (`--fit-video-to-voice`, done):** Wenn nach der Voice-Erzeugung eine nutzbare `voice_duration_seconds` vorliegt, verteilt der Founder-Run die Szenen-Dauern so, dass Σ(Szenen) ≈ **Voice + Padding** (ganze Sekunden, Untergrenze `max(3, n_scenes×2, n_scenes×min_per_scene)`). Padding per **`--voice-fit-padding-seconds`** (Default **0,75**). Patch erfolgt **nach** Voice (weil die Dauer erst dann zuverlässig ist), **vor** `build_timeline_manifest` — [`scripts/run_url_to_final_mp4.py`](scripts/run_url_to_final_mp4.py): `_apply_fit_to_voice_durations` aktualisiert `asset_manifest.json` sowie konsistent `scene_plan.json` / `scene_asset_pack.json`; `timeline_manifest.json` spiegelt die gefitteten `duration_seconds`. **`run_summary.json`:** `fit_video_to_voice`, `voice_fit_padding_seconds`, `fitted_video_duration_seconds`, `original_requested_duration_seconds`. Ohne Voice oder ohne messbare Dauer: **`fit_video_to_voice_requested_but_no_voice_duration`**, kein Crash; übliches Verhalten ohne Timeline-Verkürzung. Render: leichte Toleranz für „Audio kürzer als Timeline“ ([`scripts/render_final_story_video.py`](scripts/render_final_story_video.py), Slop ≈ **1,05 s**), damit kurzes Padding nicht dauernd `audio_shorter_than_timeline_padded_or_continued` auslöst; bei großem Mismatch (z. B. langes Video, kurze Voice ohne Fit) bleibt die Warnung.

**Reality-Smoke (BA 26.7b):** `output/ba267b_fit_voice_smoke/final_video.mp4` — z. B. `--script-json output/ba266_visual_founder_smoke/script.json`, `--asset-dir output/runway_smoke_runway_smoke_002`, `--max-scenes 3`, `--duration-seconds 30`, `--voice-mode elevenlabs` (wenn ENV) oder `--voice-mode dummy`, plus **`--fit-video-to-voice`**. Erwartung: `fitted_video_duration_seconds` gesetzt, Timeline-Szenen summieren zur Zieldauer, keine lange stumme Reststrecke wie bei ungefittetem 30‑s‑Video mit ~16 s Voice.

Tests: `tests/test_ba267b_fit_video_to_voice.py`, weiterhin Fit-/Voice-Helfer in `tests/test_ba267_elevenlabs_voice_founder_integration.py`.

**BA 26.8 — Real Visual Assets Founder Smoke (umgesetzt):** [`scripts/run_real_visual_founder_smoke.py`](scripts/run_real_visual_founder_smoke.py) orchestriert den ersten **echten visuellen Durchstich**:

1. **Script** → `scene_plan.json` / `scene_asset_pack.json` (Wiederverwendung der BA-26.5-Logik)
2. **Leonardo-Bilder** (live) — `run_asset_runner` mit `--mode live` und `LEONARDO_API_KEY`; pro Szene `scene_NNN.png`; ohne Key: sauberer Blocker `leonardo_missing_api_key`, kein Fake
3. **Runway-Videos** (live) — `run_runway_image_to_video_smoke` pro Szene (max. `--max-runway-scenes`, Default 3); Input = Leonardo-Bild; ohne Key: Blocker `runway_missing_api_key`
4. **Merged Asset-Dir** — Priorität: Runway-Video > Leonardo-Bild > Fallback-Clip > cinematic Placeholder; kein sichtbarer Draft-Text
5. **Voice** — bestehender BA-26.7-Pfad (`--voice-mode elevenlabs`); `--fit-video-to-voice`
6. **Render** — `run_ba265_url_to_final` mit dem merged Asset-Dir → `final_video.mp4`
7. **`visual_summary.json`** — `used_leonardo_images_count`, `used_runway_videos_count`, `fallback_assets_used`, `scenes`, `warnings`, `blocking_reasons`, `provider_env_detected` (ohne Secret-Werte), `output_paths`

CLI-Beispiel (PowerShell):
```
python scripts/run_real_visual_founder_smoke.py `
  --script-json output/ba266_visual_founder_smoke/script.json `
  --out-dir output/ba268_real_visual_founder_smoke `
  --max-scenes 5 --duration-seconds 60 `
  --use-leonardo --use-runway --max-runway-scenes 3 `
  --voice-mode elevenlabs --fit-video-to-voice
```

ENV-Variablen (ohne Werte): `LEONARDO_API_KEY`, `RUNWAY_API_KEY`, `ELEVENLABS_API_KEY`, optional `LEONARDO_API_ENDPOINT`, `LEONARDO_MODEL_ID`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_MODEL_ID`.

Tests: `tests/test_ba268_real_visual_founder_smoke.py` (8 Tests: visual_summary-Erzeugung, Provider-Blocker ohne ENV, Fallback-Markierung, Priorität Video>Bild>Fallback, BA-26.5-Baseline, missing script, Leonardo-only, disable flags).

**Was (noch) nicht möglich ist:** Paralleler Multi-Provider-Betrieb; Veo-Live; durchgängiger 10‑Minuten-Longform-Smoke; automatisches Re-Render bei partiellen Provider-Fehlern.

**Nächster logischer Schritt:** **BA 26.9** (geplant): Longform / Längen-Stabilität (3–5 Min), oder **BA 27.0** (Founder-Button / Dashboard-Flow) — Reihenfolge nach Priorität.

### BA 26.0 — Live Smoke Scope Freeze

**Status:** **done**

**Ziel:**  
Den ersten echten Live-Test klar begrenzen: **echte Artikel-URL**, **lokale** Video-Erzeugung, **Leonardo Live-Bilder**, **später ein ausgewählter** Video-Provider (nach Spike), **kein** Upload.

**Festgelegter Scope:**

- **Quelle:** echte Artikel-URL  
- **Dauer:** zuerst **2–3 Minuten**  
- **Bilder:** **Leonardo Live Images**, sofern `LEONARDO_API_KEY` gesetzt und Live-Modus aktiv ist  
- **Videos:** noch **nicht** angebunden; **Provider-Spike Runway vs. Google Veo** (nur **ein** Provider wird danach umgesetzt)  
- **Sora:** **nicht** als Primärpfad  
- **Voice:** zunächst **Smoke** oder vorhandene/manuelle Audio-Option; echte Voice **später separat**  
- **Output:** lokales **`final_video.mp4`**  
- **Kein** Publishing / **kein** YouTube-Upload  

**Provider-Entscheidung:**

| Provider | Rolle | Status | Entscheidung |
|----------|------|--------|--------------|
| Leonardo | Live Images | vorhanden/anschließbar | erster Bildpfad |
| Runway | Video Clips | Kandidat | gegen Veo prüfen |
| Google Veo | Video Clips | Kandidat | gegen Runway prüfen |
| Sora | Video Clips | nicht primär | nicht als Pipeline-Connector priorisieren |

**Neue BA-26-Reihenfolge:**

| BA | Titel | Status | Ziel |
|----|-------|--------|------|
| BA 26.0 | Live Smoke Scope Freeze | **done** | Scope festlegen: echte Artikel-URL, Leonardo-Bilder, Video-Provider-Spike, lokal, kein Upload. |
| BA 26.1 | Real Article URL + Leonardo Image Smoke | planned | Echte Artikel-URL mit Leonardo Live-Bildern bis lokales `final_video.mp4` testen. |
| BA 26.2 | Runway Image-to-Video Smoke | **done** | `scripts/runway_image_to_video_smoke.py`: optional mit `RUNWAY_API_KEY` ein kurzer lokaler MP4 aus Bild+Prompt; **keine** Pipeline-Integration, **kein** Upload. |
| BA 26.3 | Runway Clip Asset Ingest (lokal) | **done** | Lokale Clips per `scene_asset_pack`-Feldern (`video_path`, `runway_clip_path`, …) → `asset_manifest` / `timeline_manifest` → `render_final_story_video.py`; kein neuer Provider-Call; Fallback Bild/Placeholder. |
| BA 26.3R | Reality Check & Pipeline Plan Sync | **done** | Abgleich BA-26.x mit Code/Tests; dokumentierter optionaler Reality-Lauf mit lokalem Clip; siehe Abschnitt **BA 26.x — Real Video Build**. |
| BA 26.4 | Real Provider Smoke Test Mode | **done** | Wie **BA 26.4R**: Runway Live über BA 26.2 möglich; Default Dry-Run; Veo Stub-only. |
| BA 26.4R | Real Provider Smoke Audit & Next-Step | **done** (Doku) | Audit + Entscheidungshilfe **BA 26.5**; siehe Abschnitt **BA 26.4R** unter **BA 26.x — Real Video Build**. |
| BA 26.5 | OpenAI Images Provider Integration V1 | **done** | `openai_images`-Disposition wird zu echtem Provider-Pfad (dry-run default, Live nur mit Flag/ENV). Asset Runner nutzt `visual_prompt_effective` + Guard, schreibt `openai_image_result`/`provider_used`/`provider_status` ins `asset_manifest.json`. Tests: `tests/test_ba265_openai_images_adapter.py`, Erweiterung `tests/test_run_asset_runner.py`. |
| BA 26.6 | Visual Founder Upgrade | **done** | Textfreie cinematic Placeholder im Founder-Render, Video-Reuse über Szenen, Default `motion-mode=basic`; kein Render-Refactor, kein neuer Provider; Tests `tests/test_ba266_visual_founder_upgrade.py`. |
| BA 26.7 | ElevenLabs Voice Founder Integration | **done** | `--voice-mode none\|existing\|elevenlabs\|dummy\|openai` für [`scripts/run_url_to_final_mp4.py`](scripts/run_url_to_final_mp4.py); Wiederverwendung `synthesize_elevenlabs_mp3` / `synthesize_openai_mp3`; ENV-Secrets, keine Vertragsänderung; Tests `tests/test_ba267_elevenlabs_voice_founder_integration.py`. |
| BA 26.7b | Fit Video Duration to Voice | **done** | Optional `--fit-video-to-voice`, `--voice-fit-padding-seconds` (Default 0,75), `--fit-min-seconds-per-scene`; `run_summary`-Felder `fitted_video_duration_seconds` u. a.; Tests `tests/test_ba267b_fit_video_to_voice.py`. |
| BA 26.8 | Length-Stability / Longform Smoke (5–10 Min) | planned | Dauer-Stabilität: 5- bis 10-Minuten lokales `final_video.mp4` als ein Folge-Schritt (BA 26.6/26.7/26.7b vorausgesetzt). |

**Nicht-Ziele (Scope Freeze / gesamte BA 26):**

- Kein YouTube-Upload  
- Kein Publishing  
- Kein Scheduling  
- Kein Dashboard-Redesign  
- **Kein** paralleler Einbau **mehrerer** Video-Provider  
- **Kein** Sora-Primärconnector  
- Kein Auto-Publishing  
- Kein neuer Quality-Layer / Approval- / Cost- / SaaS-Schwerpunkt vor dem Live-Smoke-Fokus  

**Definition of Done BA 26.0:**

- Scope ist dokumentiert.  
- Provider-Richtung ist dokumentiert (Leonardo zuerst; Video **Runway vs. Veo**, ein Provider; **Sora** nicht primär).  
- **BA 26.1–26.7** sind als Reihenfolge festgelegt.  
- **Keine** Code-Änderungen.  

**Definition of Done für BA 26 (Gesamtabnahme, nach Umsetzung von 26.1ff.):** Eine echte Quelle verarbeitet; **Leonardo Live** im Smoke-Pfad genutzt oder dokumentiert blockiert; **BA 26.5** liefert einen Founder-Pfad bis lokales `final_video.mp4` (optional vorhandene Clips); **BA 26.6** liefert Founder-Render ohne sichtbare Debug-/Szenenlabels; **BA 26.7** liefert Founder-Render **mit echter Voice** (ElevenLabs bei vorhandener ENV, sonst sauberes Blocking + dummy/existing als technischer Smoke); **BA 26.7b** erlaubt optional (`--fit-video-to-voice`) die Ausrichtung der Video-Timeline an die Voice-Länge; **26.8** für Längen-Stabilität.

### BA 9.10 — Prompt Planning System V1 (**done**)

**Ziel:** Reproduzierbares **Story-Planning** statt isolierter Einzelprompts — Backend-first, modular, erweiterbar um weitere JSON-Templates.

**Core Flow (Umsetzung):** Topic Input → **Topic Classifier** (`topic_classifier.py`) → **Narrative Selector** (`narrative_selector.py`) → **Hook Generator** (`hook_generator.py`, delegiert **`generate_hook_v1`** aus BA 9.2) → **Chapter Planner** (`chapter_planner.py`) → **Scene Prompt Builder** (`scene_builder.py`) → Felder **Voice** / **Thumbnail** aus Template-JSON; Orchestrierung **`pipeline.py`**, Schema **`schema.py`**, Loader **`loader.py`**.

**Kontrakte:** Response-Modell **`ProductionPromptPlan`** (u. a. `video_template` für Downstream-Alignment mit `story_engine`); **kein** neuer Pflichtpfad für `/generate-script` oder `/youtube/generate-script`.

**Nächste Ausbaustufen (optional):** Zusätzliche Templates unter `app/templates/prompt_planning/`; LLM-gestützte Varianten nur als Schicht **hinter** dem deterministischen Kern.

### BA 9.11 — Prompt Plan Quality Check V1 (**done**)

**Zweck:** Ein erzeugter **`ProductionPromptPlan`** soll **bewertbar** sein, bevor Downstream (Export, Produktion) startet — ohne LLM, nur strukturierte Heuristiken.

**Dateien:** **`app/prompt_engine/quality_check.py`** (`evaluate_prompt_plan_quality`); Schema **`PromptPlanQualityResult`** in **`app/prompt_engine/schema.py`**; Einbindung in **`app/prompt_engine/pipeline.py`** (Feld **`quality_result`** nach Planbau).

**API-Verhalten:** **`POST /story-engine/prompt-plan`** liefert dasselbe JSON wie zuvor **plus** verschachteltes **`quality_result`** (additive Felder). Clients, die das Feld ignorieren, bleiben kompatibel. Blocker (z. B. leerer Hook, leere Kapitel) → **`status: fail`**; nachrangige Lücken (z. B. unter Mindestkapitelzahl 5, leeres `voice_style`) → **`warning`**; Einträge mit Präfix **`inherited_plan_warning:`** spiegeln Plan-Warnungen aus BA 9.10/Hook-Engine.

**Anschluss:** **BA 9.12** (Narrative Scoring) liefert die erzählerische Bewertung; **BA 9.13** übernimmt das **Performance-Learning-Datenmodell** und KPI-Vorbereitung (keine YouTube-API in V1).

### BA 9.12 — Narrative Scoring V1 (**done**)

**Zweck:** **BA 9.11** beantwortet: *„Kann produziert werden?“* (strukturelle Reife). **BA 9.12** beantwortet: *„Ist die Story klick- und watch-würdig?“* — **regelbasiert**, nachvollziehbar, ohne OpenAI-Calls.

**Unterschied zu BA 9.11:** Keine Blocker/Warnungen zur Pflichtfeldern-Lückenlogik, sondern **fünf Narrativ-Dimensionen** mit Teilscores und **`strong` / `moderate` / `weak`** ab Gesamtscore (≥80 / 50–79 / &lt;50).

**Bewertungsdimensionen:** `hook_curiosity_score`, `emotional_pull_score`, `escalation_score`, `chapter_progression_score`, `thumbnail_potential_score` — jeweils Keyword-/Struktur-Heuristiken auf Hook, Kapiteltexte und Thumbnail-Winkel; optional leichte Kopplung an **`hook_score`** (BA 9.2) bei Curiosity.

**Dateien / API:** **`app/prompt_engine/narrative_scoring.py`**, Schema **`NarrativeScoreResult`** / **`NarrativeSubscores`** in **`schema.py`**; Pipeline setzt **`narrative_score_result`** gemeinsam mit **`quality_result`**; **`POST /story-engine/prompt-plan`** liefert beide Felder additiv.

**Anschluss:** **BA 9.13** übernimmt Persistenz-Vorbereitung und KPI-Anbindung (siehe unten).

### BA 9.13 — Performance Learning Loop V1 (**done**)

**Zweck:** Ein **messbares Gedächtnis** für Template-, Hook- und Story-Signale vorbereiten: Prompt-Plan-Metadaten und spätere **echte Performance-KPIs** (CTR, Watchtime, RPM, Revenue, Kosten) in einem gemeinsamen **`PerformanceRecord`**-Schema — **ohne YouTube-API** und **ohne Firestore-Write** in V1 (bestehendes Watchlist-Repo wird nicht erweitert, bis ein eigenes Persistenz-Deliverable folgt).

**Verbindung BA 9.10–9.12:** Aus einem fertigen **`ProductionPromptPlan`** (inkl. **`quality_result`**, **`narrative_score_result`**) erzeugt **`build_performance_record_from_prompt_plan`** einen Entwurf mit **`template_type`**, **`video_template`**, **`hook_*`**, **`quality_*`**, **`narrative_*`** und Zeitstempeln. **`evaluate_performance_snapshot`** liefert **`pending_data`**, solange keine KPIs gesetzt sind; bei Views + CTR + Watch/Retention **`ready`** mit grobem **`learning_score`** (0–100). **`summarize_template_performance`** gruppiert nach **`template_type`**.

**Optionale API:** Gleicher Endpunkt **`POST /story-engine/prompt-plan`** mit **`include_performance_record: true`** — additive Response, keine neuen Routen.

**Spätere Felder:** `youtube_video_id`, `impressions`, `views`, `ctr`, `average_view_duration`, `retention_percent`, `watch_time_minutes`, `rpm`, `estimated_revenue`, `production_cost_estimate`, `profit_estimate` — alle optional im Modell.

**Langfristiges Ziel:** Templates **datenbasiert** verbessern, sobald Produktions- und Plattformdaten eingespeist werden (nächste Ausbaustufen: Firestore-Collection **`performance_records`** oder Anbindung an bestehende Job-Dokumente — **keine** große Migration in V1).

### BA 9.14 — Prompt Plan Review Gate V1 (**done**)

**Zweck:** Aus den Signalen von **9.11–9.13** eine **einzige operative Entscheidung** ableiten: **`go`** (weiter produzieren), **`revise`** (nachbessern), **`stop`** (nicht produktionsfähig). Kein LLM, keine Firestore-Writes.

**Unterschied zu 9.11/9.12:** Quality und Narrative liefern **einzelne Bewertungsdimensionen**; das Review Gate **priorisiert** (z. B. **stop** bei fail/blocking/leerem Hook/fehlenden Kapiteln/Szenen oder Kombination **narrative weak** mit **quality ≠ pass**) und bündelt **reasons** / **required_actions** für Operateure.

**Decision Matrix (V1):** **`stop`** bei Quality-fail, **`blocking_issues`**, leerem Hook, 0 Kapiteln/Szenen, oder **weak + Quality nicht pass**; **`revise`** bei Quality-warning, alleinstehendem **weak** bei Quality-pass, Narrativ-Score &lt; 50, Warnungsbudget überschritten; sonst **`go`** bei **pass** und Narrativ **strong/moderate**. **`confidence`** wird aus Abzügen berechnet und auf Bereiche **stop ≤ 40**, **revise 40–79**, **go 80–100** begrenzt. Vorhandenes **`performance_record`** mit KPI **`pending_data`** ist nur **Hinweis**, kein Stop.

**Dateien:** **`app/prompt_engine/review_gate.py`** (`evaluate_prompt_plan_review_gate`), Schema **`PromptPlanReviewGateResult`**, Einbindung in **`pipeline.py`** nach Quality/Narrative/optional **`performance_record`**.

**Anschluss:** **BA 9.15** liefert strukturierte Reparaturvorschläge; **BA 9.16** eine deterministische Repair-Vorschau (siehe unten).

### BA 9.15 — Prompt Repair Suggestions V1 (**done**)

**Zweck:** **BA 9.14** sagt, ob der Plan weiter darf (**`go` / `revise` / `stop`**). **BA 9.15** übersetzt Probleme in **konkrete, priorisierte To-dos** — die Pipeline bleibt kritisch, wird aber **operativ hilfreich** (nicht nur Ampel, sondern „wo die Schraube locker ist“).

**Input-Signale:** **`review_gate_result`** (bei **`go`** → **`not_needed`**, leere Liste); bei **`revise`** / **`stop`** u. a. **`quality_result.blocking_issues`** und Warnungslast, **`narrative_score_result.weaknesses`** und niedrige Teilscores (Curiosity, Eskalation, Emotion, Thumbnail-Potenzial), strukturelle Lücken (**Hook**, **Kapitel** ≥ 5 Produktionsziel, **Szenen** 1:1 zu Kapiteln, **voice_style**, **thumbnail_angle**), **`review_gate_result.required_actions`**, optional **`performance_record`** mit Snapshot **`pending_data`** (nur **low**-Priority-Hinweis auf spätere KPIs: CTR, Watchtime, RPM).

**Kategorien:** `hook`, `chapters`, `scenes`, `voice`, `thumbnail`, `narrative`, `quality`, `performance` — jeweils mit **`high` / `medium` / `low`**.

**Unterschied zum Review Gate:** Das Gate **entscheidet** (Ampel + Confidence); Repair Suggestions **benennen** priorisierte Maßnahmen und Kurzvorschläge im gleichen Request — **ohne** Änderung von **`GenerateScriptResponse`** oder neuen externen Abhängigkeiten.

**Dateien:** **`app/prompt_engine/repair_suggestions.py`**, Schema in **`app/prompt_engine/schema.py`**, Einbindung in **`app/prompt_engine/pipeline.py`** unmittelbar nach **`review_gate_result`**; **`POST /story-engine/prompt-plan`** liefert additiv **`repair_suggestions_result`**.

**Anschluss:** **BA 9.16** (siehe unten).

### BA 9.16 — Repair Preview / Auto-Revision V1 (**done**)

**Zweck:** **BA 9.15** benennt, **was** zu reparieren ist; **BA 9.16** liefert eine **deterministische Vorschau**, wie ein Plan nach einfachen strukturellen Nachbesserungen aussehen könnte — **ohne** den Originalplan zu überschreiben und **ohne** automatische Produktions-Freigabe („der Chef drückt noch selbst“).

**Kein Auto-Overwrite:** Der zurückgegebene **`ProductionPromptPlan`** (Live-Plan) bleibt unverändert; nur **`repair_preview_result.preview_plan`** ist die **Kopie** mit Heuristiken (Hook-Platzhaltertext, Kapitel auf ≥ 5 Standardbeats, Szenen 1:1, Voice/Thumbnail aus Template-Regeln). **Narrativ `weak`:** keine vollständige Story-Neuschreibung; Hinweis in **`remaining_issues`** / **`warnings`**.

**Re-Evaluation:** Auf der Preview werden **`quality_result`**, **`narrative_score_result`**, **`review_gate_result`** und **`repair_suggestions_result`** neu berechnet; **`preview_plan.repair_preview_result`** ist immer **`None`**, um Rekursion und Doppel-Vorschau zu vermeiden.

**Unterschied zu BA 9.15:** 9.15 = **Checkliste / To-dos**; 9.16 = **konkreter Entwurf** plus **`applied_repairs`**-Telemetrie.

**Dateien:** **`app/prompt_engine/repair_preview.py`**, Schema **`PromptRepairPreviewResult`**, Pipeline nach **`repair_suggestions_result`**, **`POST /story-engine/prompt-plan`** additiv.

**Anschluss:** **BA 9.17** — Human Approval Layer (siehe unten).

### BA 9.17 — Human Approval Layer V1 (**done**)

**Zweck:** **BA 9.14** liefert die **technische** Ampel; **BA 9.17** bereitet die **menschliche** Freigabe vor — klarer Status, empfohlene Aktion, Pflicht-Freigabe-Flag und **Redaktions-Checkliste**, ohne den Chefredakteur zu ersetzen.

**Statuswerte:** **`pending_review`** (u. a. technisch **`go`** oder fehlendes Gate → manuelle Prüfung), **`needs_revision`** (**`revise`**), **`rejected`** (**`stop`**), sowie Schema-Reservat **`approved`** für spätere Persistenz-Runden. **`recommended_action`:** `approve` / `review` / `revise` / `reject`.

**Warum V1 ohne Firestore/Auth:** Nur **API-Output** als Entscheidungshilfe; **`approved_by`** / **`approved_at`** bleiben **`None`**, bis eine spätere Persistenz-Stufe (z. B. nach **BA 9.22** oder eigenem Persistenz-Deliverable) greift — kein Schreiben in Firestore, kein Login, kein Frontend-Zwang.

**Unterschied zu Review Gate:** Gate = automatisierte technische Kriterien; Human Approval = **explizite** Vorbereitung auf menschliche Endfreigabe (Checkliste bei **`go`**, gebündelte **`reasons`** bei **`revise`** inkl. Repair-Summary, **`rejected_reason`** bei **`stop`**).

**Dateien:** **`app/prompt_engine/human_approval.py`**, Schema **`HumanApprovalState`**, Pipeline nach **`repair_preview_result`**.

**Anschluss:** **BA 9.18** — Production Handoff (siehe unten).

### BA 9.18 — Production Handoff V1 (**done**)

**Zweck:** Aus einem vollständigen **`ProductionPromptPlan`** ein **kontrolliertes Übergabepaket** für eine spätere Produktionspipeline bauen — strukturierte **`package`**-Felder, Ampel **`handoff_status`**, **`production_ready`** und Klartext-**`summary`** — **ohne** Render-Jobs, Provider-Calls oder „roten Knopf“.

**`handoff_status`:** **`ready`** (Paket für Übergabe vorgesehen), **`blocked`** (**`rejected`** / Stop-Pfad), **`needs_review`** (**`pending_review`** oder fehlende Human-Approval-Schicht), **`needs_revision`**.

**Konservative V1-Regel:** **`pending_review`** bedeutet technisch oft **`go`**, aber **`production_ready=False`** — echte Übergabe erst nach persistierter oder explizit gesetzter **`approved`**-Freigabe (**`production_ready=True`**). Fehlendes **`human_approval_state`** → **`needs_review`** + Warning.

**Unterschied zu Human Approval (9.17):** 9.17 formuliert **Redaktionspflicht** und Empfehlung; 9.18 sagt, **was** als Paket an Produktion denkbar ist und **welche Blocker** die Übergabe stoppen.

**Dateien:** **`app/prompt_engine/production_handoff.py`**, Schema **`ProductionHandoffPackage`** / **`ProductionHandoffResult`**, Pipeline nach **`human_approval_state`**.

**Anschluss:** **BA 9.19** — Export Contract (siehe unten).

### BA 9.19 — Production Handoff Export Contract V1 (**done**)

**Zweck:** Aus internem **`ProductionPromptPlan`** und **`production_handoff_result`** einen **stabilen, maschinenlesbaren Export-Vertrag** erzeugen — für Connectoren, spätere Produktionssysteme oder Batch-Verarbeitung — **ohne** Render, Provider und Firestore.

**Export-Vertrag:** **`ProductionExportContractResult`** mit fester **`export_contract_version`** (`9.19-v1` für Parser), **`handoff_package_id`** (deterministisch; mit **`performance_record.production_job_id`** wenn gesetzt, sonst Hash aus Template/Hook/Struktur), **`export_ready`** / **`export_status`** (spiegelt Handoff), **`summary`**, **`export_payload`** (Hook, Kapitel, Szenen, Voice, Thumbnail, eingebettete Quality/Narrative/Gate/Human-Approval/Handoff-Objekte), **`warnings`**, **`blocking_reasons`**, **`checked_sources`**. Keine API-Keys, keine Binärdaten, keine erzwungenen Firestore-IDs.

**Versionierung:** Downstream prüft **`export_contract_version`** und kann Felder strikt parsen; Änderungen am Contract → neue Version (`9.19-v2`, …).

**Unterschied zu BA 9.18:** 9.18 = **operative Übergabeentscheidung** und kompaktes **`package`**; 9.19 = **vollständiger, versionierter Export-Container** für externe Systeme.

**Downstream-Nutzung:** JSON aus **`production_export_contract_result`** serialisieren, validieren, an Queue/Connector übergeben — **`GenerateScriptResponse`** bleibt unberührt.

**Dateien:** **`app/prompt_engine/production_export_contract.py`**, Schema **`ProductionExportPayload`** / **`ProductionExportContractResult`**, Pipeline nach **`production_handoff_result`**.

**Anschluss:** **BA 9.20–9.22** — Production Packaging Suite (siehe unten).

### BA 9.20 — Connector Packaging / Provider Mapping V1 (**done**)

**Zweck:** Den Export-Vertrag (**9.19**) in **provider-spezifische, JSON-serialisierbare Payloads** übersetzen — weiterhin **ohne** HTTP-Calls zu Leonardo, Kling, ElevenLabs usw.

**Providerrollen:** **`image`** (Leonardo, `style_profile` ← `template_type`, Prompts ← `scene_prompts`), **`video`** (Kling, Motion-Prompts + Kapitel-Progression), **`voice`** (OpenAI/ElevenLabs **Stub**, `voice_style` + Kapitel-Blöcke), **`thumbnail`** (Hook + `thumbnail_angle`), **`render`** (Timeline-Skeleton aus Kapitel-/Szenen-Reihenfolge).

**Status:** Export-Contract **`blocked`** oder fehlend → alle Pakete **`blocked`**; fehlende Pflichtdaten (z. B. leere Szenen) → **`incomplete`**, Gesamt oft **`partial`**; nur bei lokaler Vollständigkeit **und** **`export_ready`** → **`packaging_status: ready`**.

**Dateien:** **`app/prompt_engine/provider_packaging.py`**, Schema **`ProviderPackage`** / **`ProviderPackagingResult`**, Pipeline nach **`production_export_contract_result`**.

### BA 9.21 — Multi-Provider Export Bundle V1 (**done**)

**Zweck:** Alle Provider-Pakete in **ein** maschinenlesbares Objekt bündeln — **`bundle_version`** `9.21-v1`, **`bundle_id`** (deterministischer Hash), **`providers`** mit fünf benannten Slots.

**Bundle-Logik:** Spiegelt **`ProviderPackagingResult.packaging_status`** als **`bundle_status`**; sammelt Warnungen aus den Einzelpaketen; **`export_summary`** in Klartext für Operateure.

**Unterschied zu 9.19:** 9.19 = normativer Gesamt-Export des Plans; 9.21 = **Connector-orientiertes** Sammelpaket je Provider-Rolle.

**Dateien:** **`app/prompt_engine/provider_export_bundle.py`**, Schema **`ProviderExportProviders`** / **`ProviderExportBundleResult`**, Pipeline nach **`provider_packaging_result`**.

### BA 9.22 — Production Package Validation V1 (**done**)

**Zweck:** Prüfen, ob das Bundle **produktionsnah sicher** ist: Kernpakete (**alle fünf** Provider-Slots **`ready`**), Bundle nicht **`blocked`**, Kapitel/Szenen-Zähler konsistent, Hook/Voice/Thumbnail ohne kritische Lücken.

**Validierung:** **`validation_status`** `pass` / `warning` / `fail`; **`production_safety`** `safe` / `review` / `unsafe`; **`missing_components`** listet fehlende oder inkonsistente Teile; **`recommendations`** für nächste Schritte. **Ergänzung (BA 9.23+):** Sind alle fünf Provider-Slots **`ready`**, Kapitel/Szenen konsistent, aber das Bundle nur **`partial`** weil **`export_ready`** noch nicht gesetzt ist (typisch: Human **`pending_review`**), liefert die Validierung **`warning`** / **`production_safety: review`** statt **`fail`** — damit die operative Readiness-Ampel (**BA 9.25**) zwischen „hart blockiert“ und „Review-Pfad“ unterscheiden kann.

**Dateien:** **`app/prompt_engine/package_validation.py`**, Schema **`PackageValidationResult`**, Pipeline nach **`provider_export_bundle_result`**.

### BA 9.23 — Production Timeline Builder V1 (**done**)

**Zweck:** Aus Hook und Kapitel/Szenen (1:1) eine **operative Timeline** ableiten — geschätzte **Sekunden pro Szene**, Rolle (**hook** / **setup** / **build** / **escalation** / **climax** / **outro**), **`provider_targets`** (Leonardo/Kling als Planungsanker). Beantwortet: *Wie läuft das Video zeitlich?*

**Produktionsdauer V1:** deterministische Mittelwerte innerhalb der Bandbreiten (Hook 8–15s, Standard 20–45s, Climax 30–60s, Outro 10–20s). **Kategorie:** **short** &lt; 90 s Gesamt, **medium** 90–480 s, **long** &gt; 480 s.

**Einbindung:** Pipeline unmittelbar nach **`package_validation_result`** → Feld **`production_timeline_result`** auf **`POST /story-engine/prompt-plan`**. Export-Contract **blocked** / fehlend → Timeline **`blocked`**. Kapitel/Szenen-Mismatch → **`partial`** + Warnungen.

**Anschluss:** **BA 9.24** nutzt Timeline-Längen für Kosten pro Minute; **`GenerateScriptResponse`** unverändert.

### BA 9.24 — Cost Projection V2 (**done**)

**Zweck:** Grobe **Kostenprojektion in EUR** aus Planungsgrößen (Szenen/Kapitel/Timeline), ohne echte Provider-Antworten. Beantwortet: *Was kostet das ungefähr?*

**Heuristik V1:** Leonardo ≈ pro Timeline-Szene, Kling ≈ pro Szenen-Prompt, Voice ≈ pro Kapitel, Thumbnail pauschal (entfällt ohne **`thumbnail_angle`**), Render pauschal. Ohne nutzbare Timeline → **`insufficient_data`**.

**Einbindung:** Nach **`production_timeline_result`** → **`cost_projection_result`**.

**Anschluss:** **BA 9.25** wertet Kosteningenieurspfad zusammen mit Export, Validation und Timeline für die finale Ampel aus.

### BA 9.25 — Final Production Readiness Gate V1 (**done**)

**Zweck:** Ein **Gesamturteil** vor einem hypothetischen Produktionsstart (ohne Job-Enqueue): **`ready_for_production`**, **`ready_for_review`** oder **`not_ready`**, plus Score, Blocker, Review-Flags und Stärken. Beantwortet: *Ist das Gesamtpaket wirklich bereit?*

**Freigabelogik V1:** Harte Blocker bei fehlgeschlagenem Package-Validation (**fail**), blockiertem Export/Bundle, fehlender/blockierter Timeline, **`insufficient_data`** bei Kosten, **`rejected`** / **`needs_revision`** bei Human-Approval. **`ready_for_production`** nur bei grünem Bundle/Validation, Timeline **`ready`**, Kosten **`estimated`**, Human **`approved`** und konsistent hohem Score — in der Default-Pipeline bleibt Human typischerweise **`pending_review`** → Ergebnis **`ready_for_review`**.

**Einbindung:** Letzter Schritt der Prompt-Plan-Pipeline → **`final_readiness_gate_result`**.

### BA 9.26 — Template Performance Comparison V1 (**done**)

**Zweck:** Aus einer Liste von **`PerformanceRecord`** (BA 9.13) je **`template_type`** Mittelwerte für Qualität, Narrativ und optionalen **Learning-Score** bilden und Templates vergleichen. Antwort auf: *Was performt am besten?*

**Logik V1:** Gruppierung, kombinierter **`overall_template_score`** (ohne KPIs: Qualität/Narrativ 50/50; mit Learning-Anteilen: 35/35/30), **`strengths`** / **`weaknesses`** pro Eintrag. Ohne Records → **`comparison_status: insufficient_data`**.

**Unterschied zu 9.13:** **`summarize_template_performance`** liefert flache Summaries; **9.26** liefert **Vergleichs**objekt inkl. **`best_template_type`** und **`insights`**.

**Anschluss:** **BA 9.27** nutzt dieselben Records optional für Empfehlungen.

### BA 9.27 — Auto Template Recommendation V1 (**done**)

**Zweck:** **`recommend_best_template`** — Topic-Keywords (**`classify_topic`**), optional **historische** Record-Summaries, optional **Narrative-Fit** (Archetyp-ID in Template-JSON). Antwort: *Welches Template sollen wir wählen?*

**API:** Feld **`template_recommendation_result`** auf **`POST /story-engine/prompt-plan`**.

### BA 9.28 — Provider Strategy Optimizer V1 (**done**)

**Zweck:** Heuristische **`cost_priority`** (low_cost / balanced / premium) und konsistente **Stub-Provider-Namen** aus **`cost_projection_result`**, Timeline-Länge, Packaging-/Bundle-Status. Antwort: *Welche Providerstrategie ist sinnvoll?* — **keine** echten Connector-Calls.

### BA 9.29 — Production OS Dashboard Summary V1 (**done**)

**Zweck:** Ein **JSON-Dashboard-Layer** für Founder/Operator (ohne Frontend): Gesundheits- und Readiness-Scores, geschätzte Kosten, empfohlenes Template, Provider-Strategie-Zeile, Top-Risiken/-Stärken, **`executive_summary`**.

**Unterschied zu BA 9.25:** **9.25** = formale **Readiness-Ampel** mit Blockern; **9.29** = **aggregierte Cockpit-Sicht** inkl. Kosten- und Empfehlungsstrings für Reporting.

### BA 9.30 — Story-to-Production Master Orchestrator V1 (**done**)

**Zweck:** Eine **Master-Zusammenfassung** von Topic/Plan über Produktion/Provider bis **`launch_recommendation`** (proceed / revise / hold), abgeleitet von **`final_readiness_gate_result`**. Antwort: *Sollten wir dieses Projekt wirklich starten?* — Weiterhin **kein** Produktionsstart, kein Queue-Write.

**Intelligence Layer:** Daten (Records, Kosten, Timeline) → Entscheidungshilfen (9.26–9.28) → Sichten (9.29–9.30); **keine LLM-/Firestore-/API-Pflicht**.

**Anschluss:** **BA 10.0** nimmt das Export-Bundle und materialisiert die erste **Connector-fähige** Ausführungs-Schicht (Dry-Run); siehe unten.

### BA 10.0 — Production Connector Layer V1 (**done**)

**Zweck:** Brücke von **BA 9.20–9.21 Packaging** zur späteren **Live-Ausführung**: einheitlicher **Adapter-Contract** (`validate_payload` → `build_request` → `dry_run` → `normalize_response`), **zentrale Registry**, **Dry-Run-Suite** über alle fünf Bundle-Slots — **ohne** HTTP-Calls, **ohne** Secrets, **ohne** Firestore.

**Unterschied zu BA 9.x:** **9.20–9.21** liefern strukturierte **Payloads** im Bundle; **10.0** definiert **wie** ein Connector diese Payloads technisch ansprechen würde und normiert Request/Response-Stubs. **9.22–9.25** bewerten Produktions-/Ops-Reife; **10.0** bewusst **Ausführungs-Vorbereitung**, keine zweite Readiness-Ampel.

**Sicherheitsmodell:** Bundle **`blocked`** → Suite **`blocked`**; fehlendes Bundle → **`blocked`** ohne Slot-Ergebnisse; ungültige Payloads → **`invalid_payload`** je Connector; Default immer **Dry-Run**.

**Connector-Architektur:** `app/production_connectors/base.py` (**`BaseProductionConnector`**), Stubs **`leonardo_connector`**, **`kling_connector`**, **`voice_connector`**, **`thumbnail_connector`**, **`render_connector`**, **`registry.py`**, **`dry_run_executor.py`**, **`schema.py`**.

**Integration:** Pipeline nach **`package_validation_result`** → **`production_connector_suite_result`** (inkl. angereicherter **`suite_version`**), **`connector_auth_contracts_result`**, **`provider_execution_queue_result`**; nachgelagerte BA-9.23+ Schritte nutzen den Plan **mit** diesen Feldern.

**Anschluss:** **BA 10.1–10.3** erweitern die Suite um Auth-Matrix und Queue; **BA 10.4–10.10** (siehe unten) liefern **Execution Safety & Run Core**; **Connector BA 11.0–11.5** (siehe unten) die erste **kontrollierte Live-Provider-Aktivierung** (optional HTTP). **Dashboard BA 11.x** (Founder UI) ist **eine andere** Nummernkreis-Linie.

### BA 10.1 — Live Connector Auth Contract V1 (**done**)

**Zweck:** Pro Connector **sichtbar machen, welche Auth später nötig wäre** (`LEONARDO_API_KEY`, `KLING_API_KEY`, `VOICE_API_KEY`, …) — nur **Namen**, keine Werte, **kein** `os.environ`-Read in V1. Thumbnail/Render: **`auth_not_required`** / **`none`**.

**Sicherheitsmodell:** Kein Secret-Logging; Warnhinweis, dass V1 keine echte Konfigurationsprüfung durchführt.

### BA 10.2 — Provider Execution Queue V1 (**done**)

**Zweck:** **Deterministische Job-Reihenfolge** für spätere Worker: Thumbnail zuerst (`dependency_order` 0), **Image** und **Voice** in derselben Welle (10), **Video** (20), **Render** zuletzt (30). Bundle **`blocked`** → alle Jobs **`blocked`**; incomplete Slots → Job **`invalid`**, Queue **`partial`**.

**Unterschied zu 10.0:** **10.0** validiert Payloads im Dry-Run; **10.2** modelliert **Ausführungsgraph** und repliziert Payloads in **`ExecutionQueueJob`**.

### BA 10.3 — Asset Return Normalization V1 (**done**)

**Zweck:** **Einheitliches Rückgabe-Schema** (`asset_url`, `local_path`, `metadata`, `normalization_status`) für künftige Provider-Responses — aktuell **rein heuristisch** aus Dict-Keys, ohne Netzwerk.

**Unterschied zu 9.x:** Kein Eingriff in Skript-Verträge; nur Utility für spätere Live-Returns.

### BA 10.4 — Live Execution Guard V1 (**done**)

**Zweck:** Vor jedem hypothetischen **Live**-Schritt ein **Gate-Ergebnis** (`live_ready` / `dry_run_only` / `blocked` / `policy_review`): Human Approval, Final Readiness, Export-Contract, Package-Validation, Auth-Contracts, Execution Queue, Cost Projection, Kill-Switch-Default. **Regel:** Default **`dry_run_only`**; **`live_ready`** nur bei explizit grünen, konsistenten Bedingungen — praktisch bleibt V1 durch **Kill Switch an** typischerweise bei **`dry_run_only`** / **`live_execution_allowed: false`**.

**Modul:** `app/production_connectors/live_execution_guard.py` — **`evaluate_live_execution_guard(plan)`**.

### BA 10.5 — Controlled API Activation V1 (**done**)

**Zweck:** **`activation_mode`** (`dry_run` / `restricted_live` / `disabled`) und **`provider_activation_matrix`** (Leonardo, Kling, Voice, Thumbnail, Render) — **theoretisch**, ohne Keys, ohne HTTP. **V1-Standard:** Modus **`dry_run`** (auch wenn der Guard **`blocked`** meldet: keine Live-Aktivierung, Blocker in **`warnings`**).

**Modul:** `app/production_connectors/api_activation_control.py` — **`build_api_activation_control(plan)`**.

### BA 10.6 — Execution Policy / Kill Switch V1 (**done**)

**Zweck:** **`global_execution_mode`** (`dry_run_only` / `guarded_live` / `emergency_stop`), **`kill_switch_active`** (Default **an**), **`max_estimated_cost_eur`**, **`max_jobs_per_run`**, **`policy_flags`**, **`violations`**. Fehlende oder widersprüchliche Policy → **`dry_run_only`** / **`emergency_stop`** bei harten Verstößen.

**Hinweis zur Nummerierung:** Diese **Connector-BA 10.6** = Policy-Layer; sie ist **nicht** dasselbe wie **„BA 10.6 Founder Dashboard“** weiter unten im Dokument (ältere Dashboard-Schiene).

**Modul:** `app/production_connectors/execution_policy.py` — **`build_execution_policy(plan)`**.

### BA 10.7 — Connector Result Store Schema V1 (**done**)

**Zweck:** **`ProviderExecutionRecord`** und **`ProductionRunRecord`** als **reines Schema** (Request/Response-Snapshots, Modus, Status, Warnungen) — **kein** Firestore, **kein** DB-Write.

**Modul:** `app/production_connectors/result_store_schema.py`.

### BA 10.8 — Provider Job Runner Mock V1 (**done**)

**Zweck:** Queue-Jobs **simuliert** abarbeiten (`queued` → `simulated_success` / `skipped` / `blocked`); optionale **`ProviderExecutionRecord`**-Einträge — **keine** Provider-HTTP-Calls.

**Modul:** `app/production_connectors/job_runner_mock.py` — **`simulate_provider_job_run(plan)`**.

### BA 10.9 — Asset Status Tracker V1 (**done**)

**Zweck:** Aus Mock-Runner-Ergebnis **`total_expected_assets`**, **`generated_assets`**, **`pending_assets`**, **`failed_assets`**, **`asset_matrix`** (Typen image / video / audio / thumbnail / render), **`tracker_status`**.

**Modul:** `app/production_connectors/asset_status_tracker.py` — **`build_asset_status_tracker(run_result)`**.

### BA 10.10 — Production Run Summary V1 (**done**)

**Zweck:** Kompakte **Run-Sicht**: **`run_readiness`**, **`execution_safety`**, **`projected_cost`**, **`projected_jobs`**, **`provider_summary`**, **`asset_summary`**, **`launch_recommendation`** (`hold` / `dry_run_execute` / `guarded_live_candidate`), **`founder_summary`**.

**Modul:** `app/production_connectors/production_run_summary.py` — **`build_production_run_summary(plan)`**.

**Integration (Pipeline):** Nach **`plan_readiness`** (Final Readiness Gate) → **`apply_run_core_suite`** (`run_core_bundle.py`): Guard → API-Aktivierung → Policy → Job-Runner-Mock → Asset-Tracker → Run-Summary; Felder additiv auf **`ProductionPromptPlan`**.

**Unterschied zu BA 10.0–10.3:** **10.0–10.3** = die Maschine **versteht** Payloads, Auth-Stubs, Queue und Normalisierung; **10.4–10.10** = die Maschine **kontrolliert** Ausführungspfade, Kosten-/Job-Limits und aggregierte Launch-Empfehlung — weiterhin **ohne** echten Produktionsstart.

### Connector BA 11.0–11.5 — Live Provider Activation Suite V1 (**done**)

**Abgrenzung:** Diese **Connector-BA 11.0–11.5** sind **nicht** identisch mit **„Dashboard BA 11.x“** weiter unten (**Founder Dashboard**). Hier geht es um **serverseitige** Prompt-Plan-Erweiterungen unter **`app/production_connectors/`** und **`POST /story-engine/prompt-plan`**.

**Leitsatz:** **BA 10** = die Maschine ist **sicher**; **BA 11** = unter Aufsicht **vorsichtig echte Provider** (optional HTTP), Standard weiterhin **Dry-Run**.

### BA 11.0 — Live Provider Safety Contract V1 (**done**)

**Zweck:** Vor Live-HTTP ein zusätzliches Gate **`live_provider_mode`** (`dry_run_only` / `guarded_live_ready` / `provider_restricted` / `blocked`): Execution Policy, Kill-Switch, API-Aktivierung, Auth-Contracts (Schema), Human Approval, Final Readiness, Provider-Mindestanforderungen, Flag **`allow_live_provider_execution`** auf **`PromptPlanRequest`** / **`ProductionPromptPlan`**.

**Modul:** `live_provider_safety.py` — **`evaluate_live_provider_safety(plan)`**.

### BA 11.1 — Secret / ENV Runtime Check V1 (**done**)

**Zweck:** **Presence-only** für **`LEONARDO_API_KEY`**, **`VOICE_API_KEY`** (optional **`VOICE_API_ENDPOINT`**) via **`os.getenv`** — **keine** Werte in Logs.

**Modul:** `runtime_secret_check.py` — **`build_runtime_secret_check(plan)`**.

### BA 11.2 — Leonardo Live Connector V1 (**done**)

**Zweck:** Optional **`urllib`**-HTTP zu **`LEONARDO_API_ENDPOINT`** nur wenn Safety-Bundle + Secret + Aktivierung; sonst **Dry-Run** über **`LeonardoProductionConnector`**; Response über **BA 10.3** **`normalize_provider_asset_result`**.

**Modul:** `leonardo_live_connector.py` — **`execute_leonardo_live(request, runtime_guard)`**.

### BA 11.3 — Voice Live Connector V1 (**done**)

**Zweck:** Analog **Voice** mit **`VOICE_API_ENDPOINT`** / **`VOICE_API_KEY`**, Fallback Dry-Run.

**Modul:** `voice_live_connector.py` — **`execute_voice_live(request, runtime_guard)`**.

### BA 11.4 — Asset Persist / Download Contract V1 (**done**)

**Zweck:** **`metadata_manifest`**, **`downloadable_assets`**, lokale Zielpfadvorschläge — **keine** Cloud-Pflicht, **kein** automatischer Write.

**Modul:** `asset_persistence.py` — **`build_asset_persistence_contract(plan)`**.

### BA 11.5 — Provider Error Recovery V1 (**done**)

**Zweck:** Aggregierte **`recovery_status`** / **`error_classification`** (auth / timeout / payload / provider / unknown) aus Leonardo-/Voice-Live-Ergebnissen.

**Modul:** `error_recovery.py` — **`build_provider_error_recovery(plan)`**.

**Integration:** Nach **`apply_run_core_suite`** → **`apply_live_provider_suite`** (`live_provider_suite.py`): Safety → Runtime-Secrets → **`LiveRuntimeGuardBundle`** → Leonardo/Voice → Persistenz → Recovery.

**Unterschied zu BA 10.x:** **10.x** simuliert und sperrt standardmäßig; **11.0–11.5** erlauben **kontrolliert** echte HTTP-Versuche **nur** bei explizitem Flag und grünem Safety-Pfad.

**Anschluss:** **BA 12.0–12.6 Full Production Asset Assembly** — Zusammenführung, finale Timeline, Render-Instructions und Human Review über die Persistenz-/Manifest-Schicht.

### Connector BA 12.0–12.6 — Full Production Asset Assembly Suite V1 (**done**)

**Abgrenzung:** **BA 12.x** baut aus BA-10/11-Ergebnissen ein **renderfähiges Produktionspaket**. Es gibt weiterhin **kein Auto-Publishing**, **keinen YouTube-Upload**, **kein Frontend-Erfordernis** und **keinen kommerziellen Final-Render**. Die Schicht liegt in **`app/production_assembly/`** und erweitert **`POST /story-engine/prompt-plan`** additiv.

**Leitsatz:** **BA 11** = die Maschine kann Assets erzeugen; **BA 12** = die Maschine kann daraus ein echtes Produktionspaket bauen.

### BA 12.0 — Master Asset Manifest V1 (**done**)

**Zweck:** Zentrale **Asset-Liste** aus Leonardo-/Voice-Ergebnissen, Persistenz-Kontrakt und Mock-Runner: **`ManifestAsset`** mit Provider, Typ, Source-Status, URLs/Pfaden, optional Szene/Kapitel und Metadaten. Status **`complete`**, **`partial`**, **`blocked`**.

**Modul:** `master_asset_manifest.py` — **`build_master_asset_manifest(plan)`**.

### BA 12.1 — Multi-Asset Assembly V1 (**done**)

**Zweck:** Gruppiert Manifest-Assets in **image**, **video**, **voice/audio**, **thumbnail**, **render** und berechnet **`coverage_score`**. Beantwortet: *Welche Assetgruppen sind vorhanden?*

**Modul:** `multi_asset_assembly.py` — **`build_multi_asset_assembly(plan)`**.

### BA 12.2 — Timeline Finalizer V1 (**done**)

**Zweck:** Führt **BA-9-Timeline** und Asset-Manifest zusammen: finale Szenen mit **`start_time`**, **`end_time`**, **`linked_assets`**, **`narration_asset`**, **`render_priority`**. Fehlende Links → **`partial`**.

**Modul:** `timeline_finalizer.py` — **`build_final_timeline(plan)`**.

### BA 12.3 — Voice / Scene Alignment V1 (**done**)

**Zweck:** Prüft, ob jede finale Szene eine Voice-/Narration-Verknüpfung besitzt und ob Dauerfenster auffällig kurz/lang sind. Liefert fehlende Voice-Szenen, Pacing-Warnungen und Empfehlungen.

**Modul:** `voice_scene_alignment.py` — **`build_voice_scene_alignment(plan)`**.

### BA 12.4 — Render Instruction Package V1 (**done**)

**Zweck:** Bereitet ein späteres Render-System vor: **`render_targets`**, **`scene_render_map`**, **`voice_track_map`**, **`thumbnail_target`** — ohne Renderstart.

**Modul:** `render_instruction_package.py` — **`build_render_instruction_package(plan)`**.

### BA 12.5 — Downloadable Production Bundle V1 (**done**)

**Zweck:** Erzeugt eine exportierbare Paketstruktur mit deterministischem **`bundle_id`**, **`downloadable_manifest`**, Komponentenliste und lokalen Exportziel-Vorschlägen — ohne tatsächliches Zip/Cloud-Write.

**Modul:** `downloadable_bundle.py` — **`build_downloadable_production_bundle(plan)`**.

### BA 12.6 — Human Final Review Package V1 (**done**)

**Zweck:** Finales Review-Paket vor Render-Freigabe: Checkliste, Risiken, Stärken, Summary und **`release_recommendation`** (`approve_for_render` / `revise_before_render` / `hold`). Prüft Asset-Vollständigkeit, Timeline, Voice-Alignment, Render-Package, Cost und Safety.

**Modul:** `human_final_review.py` — **`build_human_final_review_package(plan)`**.

**Integration:** Nach **`apply_live_provider_suite`** → **`apply_production_assembly_suite`** (`assembly_suite.py`): Manifest → Multi-Asset Assembly → Final Timeline → Voice Alignment → Render Instructions → Download Bundle → Human Final Review. Danach laufen die bestehenden Intelligence-/Dashboard-/Master-Orchestration-Schritte weiter.

**Unterschied zu BA 11.x:** **11.x** erzeugt oder simuliert Provider-Assets unter Safety-Gates; **12.x** organisiert diese Assets zu einer Produktionsbasis mit Timeline, Render-Anweisungen und Review-Paket.

**Anschluss:** **BA 13.0–13.6 Publishing Preparation** — Veröffentlichungs-Vorbereitung, Metadaten-QA und Upload-Readiness, weiterhin getrennt von echtem Auto-Publishing.

### BA 13.0–13.6 — Publishing Preparation Suite V1 (**done**)

**Abgrenzung:** **BA 13.x** bereitet aus dem renderfähigen BA-12-Produktionspaket ein **veröffentlichungsfähiges Medienpaket** vor. Es gibt weiterhin **keinen echten Upload**, **keine OAuth-/YouTube-Live-Integration**, **kein Auto-Publishing**, **kein Frontend-Erfordernis** und **keinen Scheduler-Deploy**. Die Schicht liegt in **`app/publishing/`** und erweitert **`POST /story-engine/prompt-plan`** additiv.

**Leitsatz:** **BA 12** = die Maschine kann ein Produktionspaket bauen; **BA 13** = die Maschine kann daraus ein veröffentlichungsfähiges Medienpaket vorbereiten.

### BA 13.0 — Metadata Master Package V1 (**done**)

**Zweck:** Zentraler Metadata-SoT für Plattform-Publishing: **`platform_target`** (Default YouTube), **`canonical_title`**, **`canonical_description`**, **`canonical_tags`**, Kategorie, Audience Flags und Compliance-Warnings.

**Modul:** `app/publishing/metadata_master_package.py` — **`build_metadata_master_package(plan)`**.

### BA 13.1 — Title / Description / Tag Optimizer V1 (**done**)

**Zweck:** Heuristische Publishing-Optimierung ohne LLM-Pflicht: Titelvarianten, Description-Blöcke, Tag-Cluster, **`seo_score`**, **`click_potential_score`**. Hybrid aus Hook, Narrativ und Such-/YouTube-Kontext.

**Modul:** `app/publishing/metadata_optimizer.py` — **`build_metadata_optimizer(plan)`**.

### BA 13.2 — Thumbnail Variant Pack V1 (**done**)

**Zweck:** Mehrere Thumbnail-Angles (**curiosity**, **urgency**, **authority**, **emotional**) inklusive empfohlenem Primary Variant und Visual Hooks — **keine** Bildgenerierung.

**Modul:** `app/publishing/thumbnail_variant_pack.py` — **`build_thumbnail_variant_pack(plan)`**.

### BA 13.3 — Upload Checklist V1 (**done**)

**Zweck:** Upload-Readiness ohne Upload prüfen: Metadata, Thumbnail, Download Bundle, Human Final Review, Policy/Compliance, Copyright-/Risk-Hinweise. Blocker bleiben strukturiert sichtbar.

**Modul:** `app/publishing/upload_checklist.py` — **`build_upload_checklist(plan)`**.

### BA 13.4 — Schedule Plan V1 (**done**)

**Zweck:** Heuristischer Veröffentlichungsplan: **`suggested_publish_mode`** (`immediate` / `scheduled` / `hold`), empfohlene Publish-Windows, Zeitzonen- und Strategienotizen — **keine** Live Analytics und kein Scheduler.

**Modul:** `app/publishing/schedule_plan.py` — **`build_schedule_plan(plan)`**.

### BA 13.5 — Publishing Readiness Gate V1 (**done**)

**Zweck:** Publishing-Gate mit **`publishing_status`** (`ready_to_publish` / `ready_for_review` / `not_ready`), Score, Blockern, Warnungen, Stärken und Release-Empfehlung (`publish` / `review` / `hold`). Human-Final-Review mit **`needs_revision`** bleibt bewusst **Review**, nicht Publish.

**Modul:** `app/publishing/publishing_readiness_gate.py` — **`evaluate_publishing_readiness(plan)`**.

### BA 13.6 — Founder Publishing Summary V1 (**done**)

**Zweck:** Founder-/Operator-Zusammenfassung: Content Summary, Marketability, SEO, Publishing-Risiko, Release Strategy und Final Founder Note.

**Modul:** `app/publishing/founder_publishing_summary.py` — **`build_founder_publishing_summary(plan)`**.

**Integration:** Nach **`apply_production_assembly_suite`** → **`apply_publishing_preparation_suite`** (`publishing_suite.py`): Metadata Master → Optimizer → Thumbnail Variants → Upload Checklist → Schedule Plan → Publishing Readiness Gate → Founder Publishing Summary. Danach laufen die bestehenden Intelligence-/Dashboard-/Master-Orchestration-Schritte weiter.

**Unterschied zu BA 12.x:** **12.x** macht das Paket renderfähig; **13.x** macht es publish-ready: Metadaten, SEO/CTR-Schicht, Upload-Checklist, Schedule-Plan, Publishing-Gate und Founder-Summary — weiterhin ohne externen Upload.

**Anschluss:** **BA 14.0–14.7 Performance Feedback Loop** — nach Veröffentlichung oder manueller Ausspielung können Performance-Signale in Template-, Metadata- und Publishing-Optimierung zurückfließen.

### BA 14.0–14.7 — Performance Feedback Loop Suite V1 (**done**)

**Abgrenzung:** **BA 14.x** macht das veröffentlichungsfähige Medienpaket **learn-ready**. V1 nutzt manuelle KPI-Eingabe, CSV-/API-Stub-Contracts und normalisierte Performance-Signale. Es gibt **keine verpflichtende Live-YouTube-API**, **keine Auto-Monetization**, **kein Frontend-Erfordernis** und keine automatischen Business-Entscheidungen. Die Schicht liegt in **`app/performance_feedback/`** und erweitert **`POST /story-engine/prompt-plan`** additiv.

**Leitsatz:** **BA 13** = die Maschine kann veröffentlichen; **BA 14** = die Maschine kann lernen, was nach Veröffentlichung wirklich funktioniert.

### BA 14.0 — KPI Ingest Contract V1 (**done**)

**Zweck:** Importvertrag für Kernmetriken **views**, **impressions**, **ctr**, **avg_view_duration**, **watch_time**, **subscribers_gained**, **revenue_optional**. Quellen: **manual**, **csv**, **youtube_api_stub**, **unknown** — ohne Live-Fetch-Pflicht.

**Modul:** `app/performance_feedback/kpi_ingest_contract.py` — **`build_kpi_ingest_contract(plan, external_metrics=None)`**.

### BA 14.1 — YouTube KPI Normalization V1 (**done**)

**Zweck:** Einheitlicher KPI-SoT: normalisierte CTR, Retention, RPM und Growth; leitet CTR/Retention heuristisch ab, wenn Rohdaten ausreichen.

**Modul:** `app/performance_feedback/kpi_normalization.py` — **`normalize_kpi_metrics(raw_metrics)`**.

### BA 14.2 — Hook Performance Analyzer V1 (**done**)

**Zweck:** Hook-Score und CTR zusammenführen: Effektivitäts-Score, Alignment, Stärken, Schwächen und Empfehlungen für Hook-/Packaging-Tests.

**Modul:** `app/performance_feedback/hook_performance.py` — **`analyze_hook_performance(plan, normalized_metrics)`**.

### BA 14.3 — Template Performance Evolution V1 (**done**)

**Zweck:** Template-/Narrativ-Outcomes aus echten oder importierten KPIs bewerten: Real-World-Score, Skalierbarkeit, Best Use Cases, Avoid Cases und Optimierungsnotizen.

**Modul:** `app/performance_feedback/template_evolution.py` — **`build_template_evolution(plan, metrics)`**.

### BA 14.4 — Cost vs Revenue Analyzer V1 (**done**)

**Zweck:** Produktionskosten aus BA 9.24/Run-Plan mit optionalem Revenue vergleichen: ROI, Break-even-Status, Monetization Notes. **Keine** Auto-Monetization.

**Modul:** `app/performance_feedback/cost_revenue_analysis.py` — **`build_cost_revenue_analysis(plan, metrics)`**.

### BA 14.5 — Auto Recommendation Upgrade V1 (**done**)

**Zweck:** Performance-Signale in Empfehlungen übersetzen: Template, Hook-Strategie, Provider-Anpassung, Publishing-Anpassung und Confidence.

**Modul:** `app/performance_feedback/auto_recommendation_upgrade.py` — **`build_auto_recommendation_upgrade(plan)`**.

### BA 14.6 — Founder Growth Intelligence V1 (**done**)

**Zweck:** Founder-Level Wachstumsanalyse: Growth Summary, Scaling Opportunities, Major Risks, Content Strategy Shift und konkrete Founder Actions.

**Modul:** `app/performance_feedback/founder_growth_intelligence.py` — **`build_founder_growth_intelligence(plan)`**.

### BA 14.7 — Master Feedback Orchestrator V1 (**done**)

**Zweck:** Eine einzige Wachstumszusammenfassung: Story → Production → Publishing → Performance → Wachstum. Liefert Market-Fit-Zusammenfassungen, Scaling Score, Strategic Direction und Final Growth Note.

**Modul:** `app/performance_feedback/master_feedback_orchestrator.py` — **`build_master_feedback_orchestrator(plan)`**.

**Integration:** Nach **`apply_publishing_preparation_suite`** → **`apply_performance_feedback_suite`** (`feedback_suite.py`): KPI Ingest → Normalisierung → Hook Performance → Template Evolution → Cost/Revenue → Recommendation Upgrade → Founder Growth Intelligence → Master Feedback Orchestrator. Danach laufen die bestehenden Intelligence-/Dashboard-/Master-Orchestration-Schritte weiter.

**Unterschied zu BA 13.x:** **13.x** bereitet Veröffentlichung vor; **14.x** wertet nach manueller oder späterer externer Ausspielung Performance-Signale aus und macht daraus Lern- und Wachstumsempfehlungen.

**Anschluss:** **Manual URL Story Execution V1** (URL-Eingang → Extraktion → Rewrite → Asset-Prompts → Demo-Hinweis, Feld **`manual_url_story_execution_result`**) plus **BA 15.0–15.9 First Production Acceleration Suite** — lokale Wiederholbarkeit aus realen Assets: Demo-Video, Download-/Registry-/Stitching-Schicht, Founder-Snapshot und Prototyp-Presets, ohne Upload- oder Frontend-Pflicht.

### Manual URL Story Execution Engine V1 — operative Bausteine **15.0–15.4** (**done**)

**Nummerierungs-Hinweis:** Die folgenden Bausteine **15.0–15.4** benennen den **manuellen Kernpfad „URL rein → Geschichte/Szenen raus → Demo-Kommando“**. Sie sind **nicht** identisch mit den **BA 15.0–15.9 Production Acceleration**-Feldern (`demo_video_automation_result`, `asset_downloader_result`, …). Beide Spuren sind additiv auf **`POST /story-engine/prompt-plan`**.

**Modul:** **`app/manual_url_story/`** — **`run_manual_url_rewrite_phase`** / **`finalize_manual_url_story_execution_result`**; Anbindung in **`build_production_prompt_plan`** (`pipeline.py`).

**Regeln:** kein Topic Discovery, kein Watch-Ausbau, kein Firestore-/YouTube-/Full-SaaS-Zwang; gemeinsamer Textpfad mit **`build_script_response_from_extracted_text`** (wie **`POST /generate-script`**).

**Leitsatz:** URL rein — bessere Geschichte raus — echte Szenen-Prompts raus — nächster Ausführungsschritt: lokales Demo-Video wie BA 15.0.

### Founder Production Mode / Proof of Production (Kanon V1)

**Zweck:** Festhalten des **einen** Minimalpfads „**produce one real asset end-to-end**“ — ohne SaaS-Overbuild, ohne Multi-User-Architektur.

**Durchgehend vorhanden:** Über **`POST /story-engine/prompt-plan`** mit **`manual_source_url`** (optional **`manual_url_rewrite_mode`**, **`template_override`**) orchestriert **`build_production_prompt_plan`** (`app/prompt_engine/pipeline.py`) in einem Lauf: Manual-URL-Story (Extraktion/Rewrite/Quality Gate) → Topic/Klassifikation → **Hook** → Kapitel → **Szenen-Prompts** → Export/Handoff/**Provider-Bundle** → Connector-Dry-Run/Live-Gates → **BA 17.0 Viral Upgrade (advisory)** → **BA 18.0 Multi-Scene Expansion (plan-only)** → **Production Assembly (BA 12)** → **Publishing Preparation (BA 13)** → Performance Feedback (BA 14) → **Production Acceleration (BA 15)** → Monetization Scale (BA 16) — jeweils additiv als Felder auf **`ProductionPromptPlan`**. **Danach lokal (Skripte, kein API-Zwang):** **BA 18.1** CLI-Sicht (`run_url_to_demo.py`), **BA 18.2** Export-Pack (`export_scene_asset_pack.py`), **BA 19.0** Asset Runner Placeholder (`run_asset_runner.py`), **BA 19.1** Timeline (`build_timeline_manifest.py`), **BA 19.2** ffmpeg-MP4 (`render_final_story_video.py`) — siehe Master Bauplan Founder Local Production Machine.

**Lücke / bewusste Trennung:** **`POST /generate-script`** und **`POST /youtube/generate-script`** liefern nur den festen **`GenerateScriptResponse`** und **keinen** vollen Prompt-Plan, **kein** Publishing-Pack und **keine** Acceleration-Felder. Proof-of-Production für „alles aus einem Guss“ = Prompt-Plan-Spine; Skript-Endpoints bleiben Schnellpfad / Vertrags-API.

**BA 13.x (Publishing):** Vorbereitung zum Veröffentlichen (**Metadaten**, Thumbnail-Varianten, Checklisten, Schedule-Heuristik, **`publishing_readiness_gate_result`**, **`founder_publishing_summary_result`**) — **ohne** echten Upload/OAuth.

**BA 15.x (Production Acceleration):** Lokale Wiederholbarkeit nach Smoke-Erfolgen (**`demo_video_automation_result`**, Downloader, Voice Registry, Stitcher, Subtitles, **`founder_local_dashboard_result`**, Batch/Cost/Presets) — **ohne** Firestore-/Frontend-Zwang.

**Paralleler Ops-Pfad (nicht identisch):** **`GOLD_PRODUCTION_STANDARD.md`** — Referenz über Watchlist/Firestore **`production_jobs`** und gestaffelte **`POST /production/jobs/...`**-Schritte; Schwerpunkt Betrieb mit persistiertem Skript, nicht der rein lokale URL→PromptPlan-Einstieg.

**First Real Demo Run (minimal):** (1) **`POST /story-engine/prompt-plan`** mit gültiger **`manual_source_url`**; (2) Response-Felder **`downloadable_production_bundle_result`**, **`founder_publishing_summary_result`**, **`demo_video_automation_result`** / **`manual_url_story_execution_result`** auslesen; (3) optional **`python scripts/run_url_to_demo.py "<URL>"`** für verdichteten CLI-JSON-Überblick; (4) **`python scripts/build_first_demo_video.py`** sobald Bild- und Audio-Artefakte vorliegen; (5) Publishing-Felder für manuelle Plattform-Eingabe nutzen.

**Ops:** Read-only **`GET /founder/production-proof/summary`** — statische Verweise auf Endpunkte/Skripte/Doku (keine Secrets).

#### Founder Demo V1 (Local Proof Complete) — Meilenstein

**Status:** Lokaler **Founder Production Proof** durchgespielt und als Demo-V1-Meilenstein festgehalten — **operativ**, nicht als Produkt-Ausbau.

**Was konkret bestätigt wurde:** **`manual_source_url`** auf **`POST /story-engine/prompt-plan`**; vollständiger **Prompt-Plan** inkl. nachgelagerter Suites; bei schwachem Template-Match **Zero-Keyword-Fallback** → **`documentary`** / **`generic`** (siehe `documentary.json` + `topic_classifier`); **Voice-Smoke** als **lokale Datei**; **ffmpeg**-basiertes **lokales Render**; **ein Standbild + eine Audio-Datei → `first_demo_video.mp4`** (z. B. **`python scripts/build_first_demo_video.py`** / `app/production_assembly/first_demo_video.py`).

**Abgrenzung (bewusst):** Das ist **kein** SaaS, **kein** Auto-Publish, **kein** Multi-User-System und **keine** Mandanten-Architektur — **Founder-first**, **lokal**, **Proof** vor weiterer Automatisierung.

**Nicht-Ziel:** Keine Architektur-Rewrites und kein „Empire“-Backend; nächste Schritte bleiben **manuell** (Plattform-Upload, KPI, Freigaben) oder spätere **optionale** Anbindungen.

#### 15.0 — Manual URL Intake V1 (**done**)

**Zweck:** Optional **`manual_source_url`** auf **`PromptPlanRequest`**; sichere Anzeige (**Host/Pfad**, keine Query) in **`manual_url_story_execution_result.intake`**.

#### 15.1 — Source Extraction Layer V1 (**done**)

**Zweck:** **`extract_text_from_url`** (Trafilatura / YouTube-Pfad wie **`app/utils.py`**); Status und Warnungen in **`extraction`**.

#### 15.2 — Narrative Rewrite Engine V1 (**done**)

**Zweck:** Strukturiertes Skript aus extrahiertem Text; **`chapter_outline`**, **`hook`** und **`source_summary`-Naher Feed** für Hook/Szenen werden aus dem Rewrite gespeist, wenn Extraktion erfolgreich war.

#### 15.3 — Asset Prompt Builder V1 (**done**)

**Zweck:** Bestehende **`build_scene_prompts`** auf URL-Kapitel × gewähltem Template; **`asset_prompt_build.scene_prompt_count`**.

#### 15.4 — Demo Video Execution V1 (**done**)

**Zweck:** Reproduzierbares **`command_hint`** für **`scripts/build_first_demo_video.py`** sobald Narrativ und Szenen-Prompts bereitstehen (Bild kommt wie gehabt aus Manifest/Live-Smoke); konsistent mit **BA 15.0 Demo Video Automation**.

### BA 15.5–15.7 — URL To Demo Acceleration Layer V1 (**done**, manueller URL-Track)

**Unterschied zu 15.0–15.4:** Die Basis-Spur liefert Intake → Extraktion → Rewrite → Szenen-Prompts → Demo-Hinweis (**`manual_url_story_execution_result`**). **15.5–15.7** verdichten das zu **schneller operativer Demo-Orchestrierung**: ein CLI-Einstieg, standardisierte Rewrite-Presets und ein **heuristisches Quality Gate** — ohne Auto-Publishing, ohne Firestore, ohne Frontend.

**Nummerierungs-Hinweis:** Dieselben Nummern **15.5–15.7** existieren **parallel** auch als **Production Acceleration** (Thumbnail Extract / Founder Dashboard / Batch Runner). Hier bezeichnet **15.5–15.7** ausschließlich den **URL→Demo-Beschleuniger** (`manual_url_demo_execution_result`, `manual_url_quality_gate_result`, **`scripts/run_url_to_demo.py`**).

**Full Flow:** Manual URL → Extraktion → Rewrite → **URL Quality Gate** → **Rewrite Mode** (optional) → PromptPlan / Asset-Prompts → **Demo-Kommando-Hooks** (Leonardo-Smoke, Voice-Smoke, First-Demo-Video).

#### 15.5 — One-Command URL to Demo Execution V1 (**done**)

**Zweck:** **`python scripts/run_url_to_demo.py "<URL>"`** — JSON mit **`rewritten_story`**, **`prompt_plan_summary`**, **`leonardo_asset_hook`**, **`voice_asset_hook`**, **`first_demo_video_command`**, **`local_output_summary`**, **`local_run_id`**. Feld **`manual_url_demo_execution_result`** auf **`POST /story-engine/prompt-plan`**.

#### 15.6 — Rewrite Preset Modes V1 (**done**)

**Zweck:** **`manual_url_rewrite_mode`**: `documentary` \| `emotional` \| `mystery` \| `viral`. **`template_override`** bleibt strikt prioritär. Ohne Override: Preset mappt auf **Video-Rewrite-Template** und **Prompt-Planning-Template** (z. B. mystery → `mystery_history` / `mystery_explainer`); Hook-Engine nutzt den Modus für Tonalität (**`generate_hook_v1`**).

#### 15.7 — URL Quality Gate V1 (**done**)

**Zweck:** **`UrlQualityGateResult`** (**`manual_url_quality_gate_result`**): `strong` \| `moderate` \| `weak` \| `blocked`, Scores (Hook-Potenzial, Narrativdichte, emotionaler Gewicht), **`recommended_mode`**, Warnungen, Blocking-Gründe. **Schwache** URLs bleiben rewritebar; **blocked** nur bei klar unzureichender Extraktion / Länge — rein heuristisch, keine externe API.

### BA 15.8–15.9 — Batch URL Engine + Watch Approval Layer V1 (**done**, manueller URL-Track)

**Unterschied zu 15.5–15.7:** Dort ging es um **einen** URL→Demo-Pfad inkl. PromptPlan-Feldern. **15.8–15.9** sind eine **eigenständige operative Schicht** (keine Aufblähung von **`ProductionPromptPlan`**): **Multi-URL-Priorisierung** und **Watch-Radar mit Founder-Approval** — maximal Reuse der bestehenden Manual-URL-Engine bzw. des **URL Quality Gates**.

**Batch statt Single:** Mehrere kuratierte URLs pro Lauf; Ausgabe je URL + **`ranked_urls`**, **`top_candidates`**, **`blocked_urls`**.

**Radar statt Vollauto:** Lokale JSON-Config (**`items`** / **`sources`** mit **`urls`**); **kein** Watch-Autofetch, **kein** Provider-Auto-Run, **kein** Publish.

**Founder-first Approval:** **`approval_queue`** (approve/review) vs **`rejected_items`** (skip u. a. Duplikat/Blocked); Relevanz aus Gate-Scores + Hook-Potenzial; **Duplicate Guard light** (normalisierte URL ohne Query).

#### 15.8 — Batch URL Engine V1 (**done**)

**Modul:** **`app/manual_url_story/batch_engine.py`** — **`run_batch_url_demo`** ruft nur **`run_manual_url_rewrite_phase`** pro URL (gleiche Rewrite-Logik wie Single-URL, keine zweite Implementierung).

**CLI:** **`python scripts/run_batch_url_demo.py urls.txt`** oder **`--json-file`** (`["…"]` oder `{"urls":[…]}`).

**Output-Modell:** **`BatchUrlRunResult`** (`items`, `ranked_urls`, `top_candidates`, `blocked_urls`) in **`app/manual_url_story/schema.py`**.

#### 15.9 — Watch Approval Layer V1 (**done**)

**Modul:** **`app/manual_url_story/watch_approval.py`** — **`run_watch_approval_scan`** nutzt **Extraktion + `build_url_quality_gate_result`** ohne vollen Rewrite (token-effizienter Radar-Modus).

**CLI:** **`python scripts/run_watch_approval.py config.json`**.

**Output-Modell:** **`WatchApprovalResult`** (`detected_items`, `approval_queue`, `rejected_items`) in **`app/manual_url_story/schema.py`**.

**Anschluss:** **BA 16 Monetization & Scale OS** — strategische Nutzung priorisierter Inputs und wiederholbarer Demo-Pfade (**Cash-/ROI-Denken** auf bestehender Produktionsbasis), ohne operative Monetarisierungsautomatik.

### BA 15.0–15.9 — First Production Acceleration Suite V1 (**done**)

**Abgrenzung:** **BA 15.x** beschleunigt die lokale Demo-Produktion nach den ersten echten Leonardo-/ElevenLabs-Smoke-Erfolgen. Es gibt weiterhin **keinen YouTube-Upload**, **keinen Firestore-Zwang**, **keine Frontend-Pflicht**, **keine Breaking Changes** und keinen Ersatz für die Makro-**Phase 9** (Packaging) oder **Phase 10** (Publishing). Die Schicht liegt in **`app/production_acceleration/`** und erweitert **`POST /story-engine/prompt-plan`** additiv.

**Leitsatz:** **BA 14** = die Maschine lernt aus Performance-Signalen; **BA 15** = die Maschine produziert lokal wiederholbar aus echten Assets.

### BA 15.0 — Demo Video Automation V1 (**done**)

**Zweck:** Strukturierter Build-Plan für **`scripts/build_first_demo_video.py`** und **`output/first_demo_video.mp4`** aus einem Bild plus **`output/voice_smoke_test_output.mp3`**. Feld **`demo_video_automation_result`**.

### BA 15.1 — Asset Downloader V1 (**done**)

**Zweck:** Manifest-Assets in lokale Download-Ziele und lokale Pfade aufteilen, ohne Pflicht-Download im Prompt-Plan. Feld **`asset_downloader_result`**.

### BA 15.2 — Voice Registry V1 (**done**)

**Zweck:** Sichere Voice-Registry mit Default-Test-Voice-ID, **`VOICE_ID`**-Präsenz und Verweis auf **`scripts/list_elevenlabs_voices.py`** — keine Secret-Werte. Feld **`voice_registry_result`**.

### BA 15.3 — Scene Stitcher V1 (**done**)

**Zweck:** Finale Timeline-Szenen in eine einfache lokale Stitching-Map überführen. Feld **`scene_stitcher_result`**.

### BA 15.4 — Subtitle Draft V1 (**done**)

**Zweck:** Erster SRT-kompatibler Entwurf aus Kapitel-/Szenenstruktur, ohne Burn-in und ohne Publishing. Feld **`subtitle_draft_result`**.

### BA 15.5 — Thumbnail Extract V1 (**done**)

**Zweck:** Lokalen ffmpeg-Extraktplan für **`output/first_demo_thumbnail.jpg`** aus **`output/first_demo_video.mp4`** bereitstellen. Feld **`thumbnail_extract_result`**.

### BA 15.6 — Founder Local Dashboard V1 (**done**)

**Zweck:** Lokaler Readiness-Score, bereite/blockierte Komponenten und nächste Aktionen für wiederholbare Demo-Produktion. Feld **`founder_local_dashboard_result`**.

### BA 15.7 — Batch Topic Runner V1 (**done**)

**Zweck:** Minimaler Batch-Plan für wiederholbare Demo-Themen ohne Job-Backend und ohne Scheduler. Feld **`batch_topic_runner_result`**.

### BA 15.8 — Cost Snapshot V1 (**done**)

**Zweck:** Lokaler Kosten-Snapshot aus vorhandener Cost Projection plus realem Demo-Pfad (Image, Voice, ffmpeg), ohne Live-Abrechnung. Feld **`cost_snapshot_result`**.

### BA 15.9 — Viral Prototype Presets V1 (**done**)

**Zweck:** Kleine Preset-Liste für wiederholbare Prototypen (Documentary Proof, Mystery Short, Authority Explainer) aus Template-/Hook-Kontext. Feld **`viral_prototype_presets_result`**.

**Integration:** Nach **`apply_performance_feedback_suite`** → **`apply_production_acceleration_suite`** (`acceleration_suite.py`): Demo Video Automation → Asset Downloader → Voice Registry → Scene Stitcher → Subtitle Draft → Thumbnail Extract → Founder Local Dashboard → Batch Topic Runner → Cost Snapshot → Viral Prototype Presets. Danach laufen Template-Comparison, Recommendation, Provider Strategy, Production OS Dashboard und Master Orchestration weiter.

**Unterschied zu BA 12–14:** **12.x** organisiert Assets, **13.x** macht publish-ready, **14.x** macht learn-ready; **15.x** macht den lokalen Beweis wiederholbar und operativ schneller — ohne neue Plattform- oder Datenbankpflicht.

**Anschluss:** **Cash Optimization Layer (CO 16.0–16.4)** plus **BA 16.0–16.9 Monetization & Scale Operating System** — strategische Vorbereitung von Umsatz, Portfolio, Multi-Platform und Skalierung aus der wiederholbaren lokalen Produktion.

### BA 16.0–16.4 — Cash Optimization Layer V1 (**done**, Cash-Track / Founder Profit Filter)

**Nummerierungs-Hinweis:** Diese **16.0–16.4** bezeichnen **`app/cash_optimization/`** (Profit-Priorität, RPM-Schätzung, Produktionskosten-Snapshot, Viral-Hook-Heuristik, Winner-Cluster). Sie sind **nicht** identisch mit **`app/monetization_scale/` BA 16.0–16.4** (**`revenue_model_result`**, **`channel_portfolio_result`**, **`multi_platform_strategy_result`**, **`opportunity_scanning_result`**, **`founder_kpi_result`**).

**Kern:** **Heuristik first** — keine Viral-Hellseherei, kein ML, keine externe API. Nutzt **URL Quality Gate**, Textblob (Titel/Rewrite/Modus) und bestehende Batch-/Watch-Pfade.

**Integration:** **`cash_optimization_layer_result`** auf **`POST /story-engine/prompt-plan`** bei **`manual_source_url`**; **`BatchUrlItemResult.cash_layer`** + **`profit_ranked_urls`**; **`WatchItemVerdict.cash_layer`** und nach **ROI sortierte `approval_queue`**.

#### CO 16.0 — Candidate ROI Score V1 (**done**)

**Zweck:** **`CandidateRoiScoreResult`**: aggregierter **`candidate_roi_score`**, Teilscores (Hook-Power, Narrativ, Nische, Produktions-Effizienz), **`confidence_level`**, **`recommended_priority`**, **`warnings`**.

#### CO 16.1 — Estimated RPM Category V1 (**done**)

**Zweck:** Keyword-/Nischen-Raster **`high` / `medium` / `low`** mit **`estimated_rpm_confidence`** und **`niche_reasoning`**.

#### CO 16.2 — Production Cost Snapshot V1 (**done**)

**Zweck:** **`production_cost_tier`** (`lean` / `standard` / `heavy`), Szenen-Schätzung, Fact-Check-Risiko, visuelle Schwierigkeit.

#### CO 16.3 — Viral Hook Score V1 (**done**)

**Zweck:** Dimensionen shock/secrecy/controversy/transformation/money/danger/exclusivity → **`viral_hook_score`**, **`dominant_hook_type`**, **`hook_risk_warning`**.

#### CO 16.4 — Winner Repeat Detector V1 (**done**)

**Zweck:** Cluster wie hidden_truth, scandal, survival → **`winner_cluster`**, **`repeatability_score`**, **`format_scaling_potential`**.

### BA 16.5–16.9 — Real KPI Feedback Loop V1 (**done**, Cash-Feedback-Track)

**Nummerierungs-Hinweis:** Diese **16.5–16.9** liegen in **`app/cash_feedback/`** (echte Post-Publish-Metriken, Kalibrierung gegen **`CashOptimizationLayerResult`**). Sie sind **nicht** identisch mit **`monetization_scale` BA 16.5–16.9** (**`scale_blueprint_result`** … **`monetization_scale_summary_result`**).

**Unterschied zu CO 16.0–16.4:** Dort **Heuristik vor Publish**; hier **Realität nach Publish** — manuelle JSON-KPI, Winner/Loser-Klassifikation, Prognose-vs.-Ist, Founder-Decision, Summary. **Kein** Firestore, **kein** Frontend, **kein** YouTube-API-Import in V1.

#### CF 16.5 — Real KPI Capture V1 (**done**)

**Modul:** **`app/cash_feedback/loop.py`** — **`capture_real_kpi`**, **`RealKpiCaptureResult`**. **CLI:** **`python scripts/record_video_kpi.py metrics.json`** optional **`--cash-layer-json`**.

#### CF 16.6 — Winner / Loser Classification V1 (**done**)

**Output:** **`PerformanceClassificationResult`** (`winner` \| `promising` \| `neutral` \| `loser`), Confidence, Stärken/Schwächen, **`repeat_recommendation`**.

#### CF 16.7 — Prediction vs Reality Compare V1 (**done**)

**Output:** **`PredictionRealityResult`** — **`prediction_accuracy`**, over-/underestimated Signals, **`calibration_notes`** (benötigt optional gespeichertes **`cash_optimization_layer_result`**).

#### CF 16.8 — Repeat / Kill Recommendation V1 (**done**)

**Output:** **`FounderPerformanceDecisionResult`** — `repeat_format` \| `modify_hook` \| `change_niche` \| `kill_topic` \| `test_again`.

#### CF 16.9 — KPI Feedback Summary V1 (**done**)

**Output:** **`KpiFeedbackSummaryResult`** + gebündelt **`RealKpiFeedbackLoopResult`**.

**Öffentlicher Einstieg:** **`run_real_kpi_feedback_loop(metrics_dict, cash_layer=…)`** — **kein** Pflicht-Hook in **`build_production_prompt_plan`**.

**Anschluss (später):** optionaler automatischer YouTube-KPI-Import — bewusst **nicht** in V1.

### BA 16.0–16.9 — Monetization & Scale Operating System V1 (**done**)

**Abgrenzung:** **BA 16.x** macht aus dem Produktionssystem eine strategische Medienunternehmens-Vorstufe. Es gibt weiterhin **keinen Upload**, **keine Pflicht-Analytics**, **keine Auto-Monetarisierung**, **keine Business-Automation**, **keinen Firestore-Zwang** und keine Änderung an **`GenerateScriptResponse`**. Die Schicht liegt in **`app/monetization_scale/`** und erweitert **`POST /story-engine/prompt-plan`** additiv.

**Leitsatz:** **BA 15** = lokale Produktion wird wiederholbar; **BA 16** = aus wiederholbarer Produktion entsteht ein skalierbares Medienunternehmen-Modell.

### BA 16.0 — Revenue Model V1 (**done**)

**Zweck:** Primäre und sekundäre Revenue Streams, Monetization-Readiness und Warnungen aus Produktions- und KPI-Reife ableiten. Feld **`revenue_model_result`**.

### BA 16.1 — Channel Portfolio V1 (**done**)

**Zweck:** Channel-Lanes wie Flagship Documentary, Shorts Discovery und Evergreen Explainer strukturieren. Feld **`channel_portfolio_result`**.

### BA 16.2 — Multi-Platform Strategy V1 (**done**)

**Zweck:** Plattform-Ziele und Repurposing-Plan ohne Upload-Pflicht definieren. Feld **`multi_platform_strategy_result`**.

### BA 16.3 — Opportunity Scanning V1 (**done**)

**Zweck:** Hook-/Narrativ-/Template-Signale zu Opportunity Score und Experimenten verdichten. Feld **`opportunity_scanning_result`**.

### BA 16.4 — Founder KPI V1 (**done**)

**Zweck:** North-Star-Metrik, wöchentliche KPIs und Entscheidungsgrenzen für Founder-Betrieb festlegen. Feld **`founder_kpi_result`**.

### BA 16.5 — Scale Blueprint V1 (**done**)

**Zweck:** Stufen von Proof → Repeatability → Portfolio → Monetization als strategischen Skalierungsplan modellieren. Feld **`scale_blueprint_result`**.

### BA 16.6 — Sponsorship Readiness V1 (**done**)

**Zweck:** Sponsor-Fit-Kategorien und Media-Kit-Anforderungen ohne Outreach oder externe Kontakte vorbereiten. Feld **`sponsorship_readiness_result`**.

### BA 16.7 — Content Investment Plan V1 (**done**)

**Zweck:** Reinvestitionsprioritäten und Budget-Guardrails für wiederholbare Produktion definieren. Feld **`content_investment_plan_result`**.

### BA 16.8 — Scale Risk Register V1 (**done**)

**Zweck:** Skalierungsrisiken wie Qualitätsabfall, Plattformabhängigkeit, Rechte-/Quellenrisiken und Kostenwachstum sichtbar machen. Feld **`scale_risk_register_result`**.

### BA 16.9 — Monetization & Scale Summary V1 (**done**)

**Zweck:** Founder-Level Summary mit Company Stage, Readiness Score, strategischem Fokus und nächsten Aktionen. Feld **`monetization_scale_summary_result`**.

**Integration:** Nach **`apply_production_acceleration_suite`** → **`apply_monetization_scale_suite`** (`scale_suite.py`): Revenue → Channel Portfolio → Multi-Platform → Opportunity Scanning → Founder KPI → Scale Blueprint → Sponsorship Readiness → Content Investment → Risk Register → Monetization Scale Summary. Danach laufen Template-Comparison, Recommendation, Provider Strategy, Production OS Dashboard und Master Orchestration weiter.

**Unterschied zu BA 15.x:** **15.x** beweist wiederholbare Produktion; **16.x** bereitet Wachstums-, Umsatz- und Unternehmensentscheidungen vor — strategisch, additiv und ohne operative Monetarisierungsaktionen.

### BA 17.0 — Viral Upgrade Layer V1 (**done**, Founder-only, Lean)

**Zweck:** Vor Production Assets eine **leichte** Schicht CTR/Retention-Verpackung (nur **Vorschläge**), ohne Faktenstruktur des Rewrites zu überschreiben.

**Modul:** **`app/viral_upgrade/`** — **`build_viral_upgrade_layer(plan)`**; Ergebnis **`ViralUpgradeLayerResult`** auf **`ProductionPromptPlan.viral_upgrade_layer_result`**.

**Integration:** In **`build_production_prompt_plan`** nach Live-Provider-Suite und **vor** **`apply_production_assembly_suite`** — additiv, deterministisch, **keine** HTTP-APIs.

**Nicht-Ziele:** kein SaaS, kein Multi-User, kein Auto-Publish, keine Skript-Overwrite, keine LLM-Pflicht.

### BA 18.0 — Multi-Scene Asset Expansion Layer V1 (**done**, plan-only)

**Zweck:** Von **einem Bild** hin zu **vielen Szenen** — Founder kann **20–40** Visual-Prompts für ein **5–10-Minuten-Video** aus einem Story-Plan ableiten, ohne Provider-Pipeline zu verändern.

**Modul:** **`app/scene_expansion/`** — **`build_scene_expansion_layer(plan)`** → **`SceneExpansionResult`** mit Liste **`expanded_scene_assets`** (je Beat: `chapter_index`, `beat_index`, `visual_prompt`, `camera_motion_hint`, `duration_seconds`, `asset_type` ∈ image|broll|establishing|detail, `continuity_note`, `safety_notes`).

**Integration:** In **`build_production_prompt_plan`** direkt **nach** BA 17.0 und **vor** **`apply_production_assembly_suite`** — Feld **`scene_expansion_result`**.

**Nicht-Ziele:** kein SaaS, kein Auto-Publish, keine Leonardo-Automatik, keine Architektur-Umstellung.

### BA 18.1 — Scene Expansion CLI Visibility V1 (**done**)

**Zweck:** Founder sieht im **CLI-JSON** von **`scripts/run_url_to_demo.py`** sofort **Skalierung** (Beat-Anzahl, Preview der ersten Visual-Beats).

**Nicht-Ziele:** keine neuen HTTP-Endpunkte, kein SaaS.

### BA 18.2 — Scene Asset Export Pack V1 (**done**)

**Zweck:** **Produktionsordner** unter **`output/scene_asset_pack_<run_id>/`** — vollständige Beats, Leonardo-Textzeilen, Shotlist, Summary.

**Beweis:** „Ich habe einen echten Produktionsordner.“

---

## Master Bauplan — Founder Local Production Machine V1 (BA 18.1 → BA 19.2)

**Mission:** Von **URL → PromptPlan → Szene** zu **URL → Bilder → Voice → Timeline → echtes MP4** — **Founder-only**, **lokal**, **ein Artikel rein → ein 5–10-Minuten-Video raus**.

**Nummerierungs-Hinweis:** **BA 19.x** ist die **Founder-Video-Render-Linie** (Assets → Timeline → MP4). **BA 17.1+** bleibt der **getrennte** Empire-/SaaS-**Blueprint** — nicht vermischen.

### Nicht-Ziele (für die gesamte Linie 18.1–19.2)

- Kein SaaS, kein Multi-User, kein Auto-Publish, kein Enterprise-System, **kein** Architektur-Neubau der Kern-PromptPlan-Verträge.

### Kanonische Reihenfolge

```
BA 18.1 (CLI-Sicht)  →  BA 18.2 (Export-Pack)  →  BA 19.0 (Asset Runner)  →  BA 19.1 (Timeline)  →  BA 19.2 (Final Render)  →  Founder Production Proof „Video“
```

| BA | Status | Output / Beweis |
|----|--------|------------------|
| **18.1** | **done** | CLI zeigt Beat-Anzahl + Preview |
| **18.2** | **done** | Ordner `scene_asset_pack_*` mit JSON, Prompts, Shot-Plan, Summary |
| **19.0** | **done** | Ordner `generated_assets_*` mit Placeholder-**PNG** (+ Manifest); Live optional (V1 nur Env-Check) |
| **19.1** | **done** | `output/timeline_<run_id>/timeline_manifest.json` (`build_timeline_manifest.py`) |
| **19.2** | **done** | `final_story_video.mp4` — ffmpeg MVP (scale/pad, concat, optional Audio) |
| **19.3** | **planned** (optional) | Polish: Intro/Outro, Lower Thirds, Burn-in-Subs, Thumbnail |

### BA 19.0 — Local Asset Runner V1 (**done**)

**Zweck:** Aus dem **BA-18.2-Export** automatisch **lokale Bilddateien** erzeugen, damit Timeline/Render ohne Leonardo-Credits testbar sind.

**Skript:** **`scripts/run_asset_runner.py`** — **`--scene-asset-pack`**, optional **`--out-root`**, **`--run-id`**, **`--mode placeholder|live`** (Default **placeholder**).

**Nicht-Ziele:** kein SaaS, kein Auto-Publish, **keine** vollständige Leonardo-Integration in V1 (Live nur Env-Check + Warnung).

### BA 19.1 — Timeline Builder V1 (**done**)

**Skript:** **`scripts/build_timeline_manifest.py`** — **`--asset-manifest`**, optional **`--audio-path`**, **`--out-root`**, **`--run-id`**, **`--scene-duration-seconds`** (Default 6).

**Output:** **`output/timeline_<run_id>/timeline_manifest.json`** mit **`run_id`**, **`asset_manifest_path`**, **`assets_directory`**, **`audio_path`**, **`total_scenes`**, **`estimated_duration_seconds`**, **`scenes[]`** (u. a. **`scene_number`**, **`image_path`**, Zeiten, **`transition`:** fade, **`zoom_type`**, **`pan_direction`**, **`chapter_index`**, **`beat_index`**).

**Nicht-Ziele:** kein ffmpeg, kein MP4 in diesem Schritt.

### BA 19.2 — Final Video Render V1 (**done**)

**Skript:** **`scripts/render_final_story_video.py`** — **`--timeline-manifest`**, optional **`--output`** (Default **`output/final_story_video.mp4`**).

**Verhalten:** ffmpeg concat demuxer → scale/pad 1920×1080 → libx264; fehlendes ffmpeg → JSON mit **`ffmpeg_missing`**; fehlendes/ungültiges Audio → stumm + Warnungen; stdout immer JSON-Metadaten.

**Nicht-Ziele:** kein Ken-Burns-MVP (nur statische Szenenlängen), kein Auto-Publish.

### Realitätscheck

- Nach **18.2:** „Ich habe **Produktionsmaterial**.“
- Nach **19.0:** „Ich habe **echte Bilder** (oder kontrollierte Placeholders).“
- Nach **19.1:** „Ich habe eine **Regie-Struktur**.“
- Nach **19.2:** „Ich habe ein **echtes Video**.“

### Strategie (kreditsparend)

1. **Placeholder + lokal** zuerst validieren (Pfade, Manifeste, ffmpeg-Pipeline).  
2. **Dann** optional Leonardo Live mit Safety/Dry-Run (bestehende Connector-Patterns).  
3. **Dann** Feinschliff (19.3), nicht vor dem ersten durchgängigen MP4.

### Komplexität (Richtwert)

- **18.1–18.2:** leicht (umgesetzt).  
- **19.0:** leicht–mittel (Placeholder umgesetzt; Live-Generierung später).  
- **19.1–19.2:** V1 umgesetzt (Timeline JSON + ffmpeg-MVP); Feinschliff Motion/Polish optional **BA 19.3**.

**Endzustand nach BA 19.2:** Keine reine Theorie-Pipeline mehr — **eine lokale Video-Maschine** unter Founder-Kontrolle.

---

## Master Blueprint BA 15.0–17.9 — Production → Monetization → Platform Empire

**Mission:** Aus der Pipeline wird kein bloßes Feature-Bündel, sondern ein schrittweise betreibbares Medienunternehmen-System. Die Reihenfolge bleibt bewusst: erst wiederholbar produzieren, dann Umsatzlogik validieren, dann Produktisierung/SaaS/Exit vorbereiten.

**Leitsatz:** **BA 15** = Maschine produziert. **BA 16** = Maschine verdient. **BA 17.0** = Maschine packt stärker (advisory). **BA 17.1+** = Maschine wird Produkt / Plattform / Exit (Blueprint).

### Strategische Architektur

```mermaid
flowchart LR
  BA15[BA 15 Production Acceleration] --> BA16[BA 16 Monetization & Scale OS]
  BA16 --> BA171[BA 17.1+ Media OS / Empire Blueprint]
  BA15A[Real Assets + Local MP4] --> BA15
  BA16A[Manual KPIs + Revenue Hypotheses] --> BA16
  BA17A[Validated Repeatability + Revenue Signals] --> BA171
```

**Hinweis:** **BA 17.0 Viral Upgrade** läuft **auf dem Prompt-Plan** (Packaging-Heuristik) und ist **kein** SaaS-/Empire-Runtime-Schritt; siehe eigenes Unterkapitel oben.

**Architekturprinzip:** Jede Stufe erzeugt erst ein **Operating Artifact** (Plan, Registry, Score, Blueprint, Checkliste), bevor daraus Runtime, UI, Persistenz oder externe Automatisierung wird. Dadurch bleiben Kosten, Komplexität und Haftungsrisiken kontrolliert.

### Prioritätsreihenfolge

1. **BA 15 stabilisieren:** echte lokale Produktion wiederholbar machen (`image + audio + mp4`, Batch-Plan, Kosten-Snapshot, Thumbnail/Subtitles nur als Hilfsschichten).
2. **BA 16 validieren:** reale oder manuelle KPIs sammeln, Revenue-Hypothesen priorisieren, Channel-Portfolio eng halten, Multi-Platform erst als Export-/Repurposing-Plan.
3. **BA 17.1+ vorbereiten:** erst White-Label/API/Licensing-Contracts dokumentieren, bevor SaaS Dashboard, Marketplace oder Agency Mode gebaut werden.
4. **Nur bei Beweisen skalieren:** keine Plattform-/SaaS-Entwicklung ohne wiederholbare Produktion und erste Revenue-/Demand-Signale.

### Dependency Map

| Ebene | Hängt ab von | Liefert | Gate zur nächsten Ebene |
|-------|--------------|---------|--------------------------|
| **BA 15 Production Acceleration** | Leonardo/Voice Smoke, Demo-Video, BA12 Asset Manifest | Wiederholbare lokale Demo-Produktion | 3 echte MP4s + Kosten-/Asset-Snapshot |
| **BA 16 Monetization & Scale** | BA15 Wiederholbarkeit, BA14 KPI-Schicht, manuelle Performance-Daten | Revenue-Modell, Portfolio, Founder KPIs, Scale Blueprint | 1 validierter Revenue-Test oder klarer Demand-Indikator |
| **BA 17.1+ Media OS / SaaS / Platform Empire** | BA16 Revenue-/Demand-Signale, stabile Produktionskosten, klare Zielgruppe | Produktisierungs-, White-Label-, API-, Licensing- und Exit-Blueprint | zahlender Pilot / wiederholbarer Agency-Workflow / belegter White-Label-Bedarf |

### Welche BA zuerst real bauen

- **BA 15.0 Demo Video Automation:** weiter realisieren und härten, weil es den Beweis „echte Assets → echtes Video“ materialisiert.
- **BA 15.1 Asset Downloader:** als lokale Asset-Verlässlichkeit priorisieren; keine Cloud-Pflicht.
- **BA 15.7 Batch Topic Runner:** zuerst klein halten: 3 Themen, lokale Artefakte, keine Scheduler-Automation.
- **BA 15.8 Cost-per-video Snapshot:** bei jedem Demo-Run mitschreiben, damit BA16 nicht auf Gefühl skaliert.
- **BA 16.4 Founder KPI Command Center:** früh operationalisieren, aber zunächst manuell und read-only.
- **BA 16.0 Revenue Forecast Engine:** als konservative Heuristik bauen, nicht als Finanzversprechen.

### Welche BA nur vorbereiten

- **BA 16.3 Content Opportunity Scanner:** vorerst regelbasiert und manuell speisbar; kein Trend-Scraping-Zwang.
- **BA 16.4 Affiliate Insert Layer:** zuerst Placement-Contract und Compliance-Check, keine echten Affiliate-Links in Runtime.
- **BA 16.5 Sponsor Placement Framework:** Media-Kit-Anforderungen und Sponsor-Kategorien, kein Outreach-Automat.
- **BA 16.6 Multi-Platform Export:** Export-Presets vorbereiten, kein Auto-Upload.
- **BA 16.7 Trend Response Mode:** nur Playbook und Priorisierungslogik, keine Live-Trend-Abhängigkeit.
- **BA 17.0–17.9 komplett:** zunächst Blueprint/Contracts/Readiness, keine SaaS-/Marketplace-/Agency-Runtime ohne Demand-Beweis.

### BA 17.0–17.9 — Media OS / SaaS / Platform Empire Blueprint (**planned**)

**Abgrenzung:** BA 17 ist **nicht** die nächste Runtime-Suite. BA 17 beschreibt Produktisierung und Unternehmensoptionen nur als strategische Architektur, bis BA15/16 reale Wiederholbarkeit und Monetarisierungssignale liefern.

#### BA 17.0 — White-Label Pipeline (**planned**)

Mandantenfähige Branding-/Template-/Output-Contracts vorbereiten. **Nicht bauen:** Tenant-DB, Billing, Auth oder UI, bevor ein zahlender White-Label-Pilot existiert.

#### BA 17.1 — SaaS Dashboard (**planned**)

Produkt-Oberfläche als Zielbild: Run-Status, Artefakte, Kosten, KPI, Export. **Nicht bauen:** neues Frontend-Framework oder Multi-User-System ohne validated demand.

#### BA 17.2 — API Productization (**planned**)

Stabile externe API-Flächen definieren: `create_run`, `get_assets`, `get_video`, `get_report`. **Nicht bauen:** Public API Keys, Rate Limits oder Billing vor Pilot.

#### BA 17.3 — Licensing Layer (**planned**)

Lizenzpakete für Templates, Workflows, Presets und Medienpakete modellieren. **Nicht bauen:** Vertragsautomation oder Legal-Tech.

#### BA 17.4 — Agency Mode (**planned**)

Client-/Projekt-/Deliverable-Struktur für Done-for-you-Produktion vorbereiten. **Nicht bauen:** CRM, Invoicing oder Mitarbeiter-Workflow vor manuellem Agency-Pilot.

#### BA 17.5 — Marketplace Layer (**planned**)

Spätere Bausteine für Templates, Voice Packs, Thumbnail Packs, Channel Kits. **Nicht bauen:** Marketplace-Listing, Payments oder Seller-Onboarding.

#### BA 17.6 — Investor Readiness (**planned**)

Metriken und Narrative für Investoren: Unit Economics, Run-Rate, Retention, Produktionskosten, Moat. **Nicht bauen:** Pitch-Automation ohne echte KPIs.

#### BA 17.7 — Founder Replacement System (**planned**)

Runbooks, Decision Logs und Delegationspfade, damit operative Aufgaben nicht am Founder hängen. **Nicht bauen:** Autopilot ohne menschliche Review-Gates.

#### BA 17.8 — Acquisition Funnel (**planned**)

Lead- und Demo-Funnel für SaaS/Agency/White-Label-Angebote. **Nicht bauen:** Cold Outreach Automation oder Lead Scraping ohne Compliance.

#### BA 17.9 — Exit Blueprint (**planned**)

Optionen für Verkauf, Lizenzierung, Spin-out oder Mediennetzwerk. **Nicht bauen:** Bewertungs- oder Deal-Automation ohne Umsatzdaten.

### Token-Effizienz-Hinweise

- Künftige Prompts sollen **Difference-only** sein: `Use PPOS_FULL_SUITE. Delta: BA 15.7 harden batch runner with 3 local topics.`
- Nutze **Makro + Delta + Out of scope** statt Wiederholung aller Regeln.
- Verweise auf kanonische Artefakte: `PIPELINE_PLAN.md`, `docs/PROMPT_OPERATING_SYSTEM.md`, `docs/TOKEN_EFFICIENCY_GUIDE.md`.
- Pro Folgeauftrag nur eine Ebene anfassen: **Production**, **Monetization** oder **Platform**, nicht alle drei gleichzeitig implementieren.
- Für BA17 zuerst `MODULE_TEMPLATE.md` pro realem Modul nutzen, bevor Code entsteht.

### Risikoanalyse

| Risiko | Warum kritisch | Gegenmaßnahme |
|--------|----------------|---------------|
| **Overengineering** | SaaS-/Marketplace-/Agency-Features können Produktivität blockieren, bevor Produktion stabil ist. | BA17 nur Blueprint bis BA15 drei echte Videos und BA16 erste KPI-/Revenue-Signale liefert. |
| **Monetarisierung zu früh** | Revenue-Forecasts ohne echte Retention/CTR/Views erzeugen Scheingenauigkeit. | BA16-Forecasts als Hypothesen markieren; Founder KPI Command Center zuerst manuell. |
| **SaaS zu früh** | Auth, Billing, Tenanting und Support erzeugen Komplexität ohne validierten Markt. | Erst White-Label-/Agency-Pilot manuell verkaufen; dann API/SaaS schrittweise extrahieren. |
| **Feature-Spam** | Zu viele Module verwässern den Kern: echte Assets → echtes Video → echte Nachfrage. | Founder Execution Order als Gate verwenden; pro Sprint maximal ein echter Produktionsengpass. |
| **Rechts-/Brand-Risiko** | News, True Crime, Sponsorship und Licensing brauchen saubere Quellen-/Compliance-Logik. | Human Review, Quellenhinweise, Sponsorship Readiness und Risk Register vor Monetarisierung. |

### Founder Execution Order

#### NOW

- Drei echte lokale Demo-Videos aus Leonardo-Bild + ElevenLabs-Voice + ffmpeg bauen.
- Pro Video speichern: Kosten, Dauer, Thema, Hook, Thumbnail-Frame, Warnungen.
- Manual KPI Sheet vorbereiten: Views, CTR, Retention, Watch Time, qualitative Kommentare.
- BA15 stabilisieren: Asset Download, MP4 Build, Batch Topic Runner, Cost Snapshot.

#### NEXT

- BA16 realer machen: Founder KPI Command Center, Revenue Forecast Engine, Channel Portfolio und Multi-Platform Export mit echten Ergebnissen füttern.
- Einen Revenue-Test wählen: Affiliate-Hinweis, Sponsor-Dummy-Package oder Newsletter-CTA, aber jeweils mit Review-Gate.
- Opportunity Scanner nur mit manuell bestätigten Signalen nutzen.
- Team-/VA-Handoff als Checkliste und Runbook vorbereiten, nicht als Automatisierung.

#### LATER

- BA17 nur dann in Code ziehen, wenn mindestens ein klarer Produktisierungspfad validiert ist: zahlender Agency-Kunde, White-Label-Pilot, API-Interessent oder wiederholbares Medienformat mit KPI-Traktion.
- SaaS Dashboard erst nach manuellem Founder-/Operator-Workflow bauen.
- Marketplace, Investor Readiness und Exit Blueprint bleiben Dokument-/Contract-Schichten, bis Umsatzdaten vorliegen.

### BA 10.x — Prompt-to-Production (Export-Paket)

**Abgrenzung:** **BA 10.0–10.3** = **Connector-/Queue-/Auth-Vorbereitung** in der **Prompt-Plan-Pipeline** (`POST /story-engine/prompt-plan`). Die **Export-Package-UI-Linie** (lokaler Export **`POST /story-engine/export-package`**, Quality, Stub-Formatter) bleibt ein **eigenes** Themenfeld unter **`app/story_engine/`** — **nicht** Makro-**Phase 10** (Publishing). **BA 10.6+** = Founder-Dashboard (HTML). **Numerische Überschneidung:** die ältere Sprechweise „10.1–10.3 Export-Core“ im Dokument bezieht sich **nicht** auf die **neuen** BA-10.1–10.3 Connector-Prep-Einträge in der Tabelle oben.

**BA 10.6 — Founder Dashboard UI V1** (**implemented / ready for deploy**): **`GET /founder/dashboard`** — read-only internes Cockpit als **`HTMLResponse`** (eingebettetes CSS/JS); **`GET /founder/dashboard/config`** — JSON-Konfig/Meta zu den angebundenen Pfaden. V1: **keine Auth**, **keine Firestore-Writes**, **keine externen Provider-Calls**; ruft bestehende Story-Engine-Endpunkte **nur clientseitig** per **`fetch`** auf. Tests: **`tests/test_phase10_founder_dashboard.py`**.

**BA 10.7 — Founder Dashboard Upgrade** (**implemented / ready for deploy**): **additive** Erweiterung derselben **`GET /founder/dashboard`**-Seite (`app/founder_dashboard/html.py`): Copy-to-Clipboard und Downloads (JSON/CSV/TXT) pro Panel, **`<details>`**-Sektionen (Export, Preview, Readiness, Optimize, CTR, Batch Compare, Prompt Lab, Formats), **Prompt-Quality-Farbbadge** (Preview-Score), **Batch Template Compare** (alle IDs aus **`GET /story-engine/template-selector`**, nacheinander Preview + Readiness, Vergleichstabelle inkl. aggregiertem Readiness-Score), **Prompt Lab** (Side-by-side Leonardo/OpenAI/Kling). Weiterhin **kein** Build-Tool, **keine** Auth/Firestore/externe Provider; **keine** neuen Story-Engine-Verträge. Config-Version **`10.7-v1`**; Tests weiterhin **`tests/test_phase10_founder_dashboard.py`**.

### BA 11.x — Founder Dashboard: Source Intake & Full-Pipeline (Dashboard-first)

**Abgrenzung:** **BA 11.x** betrifft ausschließlich **`GET /founder/dashboard`** / **`app/founder_dashboard/html.py`**. Es gibt **keine** Makro-Roadmap-**Phase 11** in diesem Dokument; **BA 11.x** ist **nicht** **BA 9.x** (Story-Engine-Kern) und **nicht** **Phase 9** (Packaging) / **Phase 10** (Publishing). Der feste JSON-Vertrag **`GenerateScriptResponse`** (Sechs-Felder-Output der Skript-Endpoints) bleibt **unverändert**; neue **serverseitige** Pflichtlogik für „reinen Rohtext ohne URL“ ist **nicht** Teil von V1 — Rohtext wird im Dashboard nur **clientseitig** in Kapitel segmentiert, mit klarer **Warning** im Warning-Center.

**BA 11.0 — Source Intake Layer** (**implemented / dashboard-first V1**): Eingaben **YouTube-URL**, **News-/Artikel-URL**, **Rohtext**, **Topic (optional)**; Aktion **„Auto Body aus Quelle“** füllt Titel, Topic, Zusammenfassung und Kapitel-JSON im bestehenden Input-Panel aus den Antworten von **`POST /youtube/generate-script`** bzw. **`POST /generate-script`** oder aus dem lokalen Pseudo-Skriptobjekt (Rohtext-Pfad). **Tests:** **`tests/test_phase10_founder_dashboard.py`** (Strings/IDs/JS-Helfer).

**BA 11.1 — Run Full Pipeline** (**implemented / dashboard-first V1**): **One-Click-Orchestrierung** ausschließlich über bestehende Endpunkte (**`fetch`** im Browser): Intake-Generate → **`POST /story-engine/export-package`** → Preview → Readiness → Optimize → Thumbnail-CTR → **Founder Summary** (Client-Refresh der Interpretations-Widgets) → **Production Bundle** (mehrere Downloads wie bisher); **Timeline** mit Zuständen pro Schritt (inkl. Fehlerstufe); bei Fehler **Abbruch** und markierter Schritt; nach erfolgreichem Lauf **Session Snapshot** in **`localStorage`** (gleiche Struktur wie manuelles „Save Session Snapshot“). **Tests:** wie bei 11.0.

**BA 11.2 — Operator Clarity Layer** (**implemented / dashboard-first V1**): **`GET /founder/dashboard`** — **Executive Scorecard** (Go/Hold/Stop + Buchstabennoten aus bestehenden Heuristiken), **Rewrite Recommendation Engine** (NBA + Top-Warnungen mit Repair-Shortcut), **One-Click Repair** (scrollt und triggert bestehende Action-Buttons), **Founder / Operator / Raw**-Ansicht (Operator: Human Layer aus, kompaktere JSON-Panels), **Opportunity Radar** (Balken 0–100 %), **Kill Switch** (Checkbox blockiert **`fetchJson`** / **`withActionButton`**-Tasks — rein clientseitig, kein Server-State). **Keine** Änderung an **`GenerateScriptResponse`** oder Story-Engine-Verträgen. **Tests:** **`tests/test_phase10_founder_dashboard.py`**.

---

### BA 9.3–9.9 Story Engine Maturity Track (Reihenfolge)

Nach abgeschlossener **Hook Engine (9.2)** folgt die Story-Achse in dieser Reihenfolge — jeweils **ohne** Bruch des Sechs-Felder-Vertrags von **`POST /generate-script`** / **`POST /youtube/generate-script`**. Die Stufen **9.6–9.9** setzen auf **9.5b** (und den Vorläufern **9.5a Observability**, **9.4 Rhythm**, **9.3 Workflow**) auf und vertiefen Reifegrad und Optimierung **innerhalb derselben BA-9.x-Linie**.

```mermaid
flowchart LR
  done92[BA_9_2_HookEngine]
  b93[BA_9_3_WorkflowStrict]
  b94[BA_9_4_SceneRhythm]
  b95c[BA_9_5a_Observability]
  b95b[BA_9_5b_StoryPack]
  b96[BA_9_6_Experimentation]
  b97[BA_9_7_AdaptiveTemplate]
  b98[BA_9_8_StoryIntelligence]
  b99[BA_9_9_OpsMaturity]
  done92 --> b93 --> b94 --> b95c --> b95b --> b96 --> b97 --> b98 --> b99
```

| Stufe | Schwerpunkt |
|-------|-------------|
| **9.3** | Betrieb und Qualitätsschienen: Strict optional, Review-**Automatisierung**, Nebenkanal, Versionierung. |
| **9.4** | Inhaltlicher Rhythmus / Pacing auf Basis Blueprints und optional Hook-Meta. |
| **9.5a** | Observability: Metriken, Kurzüberblick, Audit-Anbindung — **nur Aggregation**, keine Secrets. |
| **9.5b** | Story-Pack: ein exportierbares Bündel für Downstream — **nach** 9.5a und idealerweise mit 9.4-Kontext. |
| **9.6** | Experimentation: A/B und Registry, Metadaten, Vorbereitung Refinement, Performance-Vergleich. |
| **9.7** | Adaptive Templates: Drift, Refinement-Inputs, Health, Scoring. |
| **9.8** | Intelligence: Feedback, Empfehlung, Cross-Template-Analyse unter Governance. |
| **9.9** | Operations Maturity: Governance, Story-OS-Zielbild, Control-Panel-Reife, Kernmodul „fertig“ in BA 9.x. |

Detailspezifikation **9.3** siehe unten; **9.4**, **9.5a**, **9.5b**, **9.6–9.9** jeweils eigene Unterabschnitte vor „Abhängigkeiten und Risiken“.

#### Erweiterte kanonische Übersicht (Unterstufen)

Die folgende Grafik verdichtet dieselbe **Reihenfolge** wie die Tabelle und das kompakte Diagramm oben (inkl. **9.5a vor 9.5b**). **Nebenkanal-Artefakte** umfassen **u. a.** die im Diagramm genannten Collections **`review_results`** / **`script_jobs`** sowie weitere Export- und Produktionspfade (siehe **BA 9.3.3**).

```mermaid
flowchart LR

A[BA 9.2<br>Hook Engine V1] --> B[BA 9.3<br>Strict + Review-Automatisierung]
B --> C[BA 9.4<br>Scene Rhythm]
C --> D[BA 9.5a<br>Story Observability]
D --> E[BA 9.5b<br>Story-Pack / Beat-Sheet]
E --> F[BA 9.6<br>Experimentation Layer]
F --> G[BA 9.7<br>Adaptive Template Optimization]
G --> H[BA 9.8<br>Story Intelligence Layer]
H --> I[BA 9.9<br>Story Engine Operations Maturity]

B --> B1[Strict Template Mode]
B --> B2[Review-Automatisierung]
B --> B3[Nebenkanal-Artefakte<br>review_results / script_jobs]
B --> B4[Template-Versionierung]

C --> C1[Pacing / Rhythmus-Meta]
C --> C2[Beat-Dichte prüfen]
C --> C3[Reveal-/Twist-Timing]
C --> C4[Rhythm Validation]

D --> D1[Hook Metrics]
D --> D2[Review Metrics]
D --> D3[Template Health Sichtbarkeit]
D --> D4[Founder Control Panel Story Health]

E --> E1[Standardisierte Beat-Sheets]
E --> E2[Template-spezifische Story Packs]
E --> E3[Wiederverwendbare Story-Strukturen]

F --> F1[A/B Hook Registry]
F --> F2[Experiment Metadata]
F --> F3[Variant Comparison]
F --> F4[Refinement Readiness]

G --> G1[Template Drift Detection]
G --> G2[Performance-based Template Scoring]
G --> G3[Adaptive Refinement Inputs]

H --> H1[Feedback Loop]
H --> H2[Template Recommendation Logic]
H --> H3[Cross-template Analysis]

I --> I1[Canonical Story OS]
I --> I2[Governance abgeschlossen]
I --> I3[Story Engine operativ reif]
```

---

### BA 9.0 — Basismotor (Referenz: umgesetzt)

**Ziel:** Einheitliche Schnittstelle **`video_template`** für Artikel- und YouTube-Skripte, mit nachvollziehbaren Auswirkungen auf Prompts und Downstream-Defaults — **ohne** neue Pflichtfelder in der Skript-Response.

**Bereits geliefert (Ist-Zustand, nicht erneut planen):**

- Definition der Template-IDs und Normalisierung; deutscher Prompt-Baukasten; abgeleitete Profile für Szene/Stimme wo vorgesehen.
- Conformance als **reine Hinweise** in `warnings` (kein harter Abbruch der Pipeline).
- Persistenz und Metadaten entlang Watchlist/Job/Production-Pfad; Dev-Fixtures angepasst.

**Akzeptanz (Referenz):** `GenerateScriptResponse` unverändert; `compileall` + bestehende Tests grün; kein zirkulärer Import zwischen Conformance und Skript-Utils.

---

### BA 9.1 — Template-Reife, Blueprints, Operabilität (**done**)

**Ziel:** Aus „technisch vorhandenen Templates“ wird ein **redaktionell und operativ nutzbarer Katalog**: Redakteur:innen und Automatisierung wissen pro Template, **was** in Hook, Kapitelzahl und Tonalität **erwartet** wird — und das Backend liefert **Transparenz** (Endpunkt oder eingebettete Meta), ohne Geheimnisse oder `.env` preiszugeben.

#### Inhalt und Fachlogik (BA 9.1)

1. **Kapitel- und Hook-Blueprints (pro `video_template`)**  
   - Ableitung aus Dauer (`duration_minutes`) und Template: **Zielband** für Kapitelanzahl, Mindestlänge Hook (Wörter/Sätze als Heuristik), empfohlene **Kapitel-Titel-Muster** (z. B. Frageform vs. Aussage bei `mystery_explainer`).  
   - Umsetzung primär in `app/story_engine/` (Daten + Funktionen), konsumiert von Prompt-Zusätzen und von `conformance_warnings_for_template` (erweitert).

2. **Prompt-Baukasten 9.1**  
   - Strukturierte Zusammensetzung: *Rollenzeile* + *Formatvorgabe* + *Blueprint* + *Quellenregeln* (bestehende AGENTS-Regeln unverändert einbetten).  
   - Ziel: weniger Drift zwischen LLM- und Fallback-Pfad; Änderungen an einem Template zentral editierbar.

3. **Warning-Konvention (lesbar für Menschen und Logs)**  
   - Einheitliches Präfix oder Tag im Freitext, z. B. `[template_conformance:chapter_count] …` / `[template_conformance:hook_length] …` — weiterhin **nur** `List[str]` in `warnings`, kein JSON-Subvertrag in der Response.  
   - Optional: kurze interne Hilfsfunktion, die Präfixe setzt (ein Ort für konsistente Formulierung).

4. **Review-Integration (optional, rückwärtskompatibel)**  
   - Optional `video_template` auf **`ReviewScriptRequest`**, falls sinnvoll: template-spezifische **Empfehlungen** oder **Zusatz-Warnungen** (z. B. Sensibilisierung bei `true_crime`), ohne Pflichtfelder in **`ReviewScriptResponse`** zu erfinden — nur optional neue Felder nach MODULE_TEMPLATE und README, oder nur angereicherte `warnings`/`recommendations`.

5. **Watchlist / Kanal-Defaults**  
   - Dokumentieren und ggf. verifizieren: Override-Reihenfolge (Job vs. Kanal vs. Request); ein Testfall „Kanal mit Template X erzeugt persistiertes Skript mit Metadatum X“.

#### Technik und API (BA 9.1)

| Thema | Vorschlag | Vertrag |
|--------|-----------|---------|
| **Template-Katalog lesbar** | `GET /story-engine/templates` (**umgesetzt**) | 200 + `templates[]` mit `id`, `label`, `description`, `duration_examples`, … — **keine** vollständigen Prompt-Rohlinge |
| **Generate** | optional `video_template` im Body | Response-Felder unverändert |
| **Review** | optional `video_template` auf **`ReviewScriptRequest`** (**umgesetzt**) | **`ReviewScriptResponse`** unverändert; template-spezifische **`recommendations`** / Normalisierungs-**`warnings`** |
| **Firestore** | nur bei Bedarf Zusatzfelder (z. B. `story_engine_version` auf Dokumenten) — erst nach Bedarf MODULE_TEMPLATE | Migration/Defaults dokumentieren |

#### Tests und Akzeptanz (BA 9.1)

- Neue oder erweiterte Tests (z. B. `tests/test_ba91_story_engine.py`): Blueprint-Matrix (pro Template × zwei Dauern), Konformität der Warning-Präfixe, Katalog-Endpoint (Schema, Status). Watchlist: `tests/test_watchlist_run_job.py` prüft **`video_template`** bis **`generated_scripts`**. Review: `tests/test_review_script.py` (**`video_template`**).  
- Regression: `tests/test_ba90_story_engine.py` grün; vollständige Suite laut AGENTS.  
- **Nicht-Ziele 9.1:** Pflicht-JSON neben dem Sechs-Felder-Skript; automatische Eskalation zu HTTP-Fehlern nur wegen Template; LLM-Review-Pflicht.

---

### BA 9.2 — Hook Engine V1 / Opening-Line (**done**)

**Ziel:** Systematische **erste ~15–30 Sekunden** je **`video_template`**: starker Einstieg für Retention — **ohne** den Sechs-Felder-**`GenerateScriptResponse`** zu erweitern.

**Umsetzung:**

- Module [`app/story_engine/hook_library.py`](app/story_engine/hook_library.py) (Hook-Typen, Muster), [`app/story_engine/hook_engine.py`](app/story_engine/hook_engine.py) (regelbasierte Auswahl, Score 1–10, **kein LLM** in V1).
- **`POST /story-engine/generate-hook`** — Request: `video_template`, `topic`, `title`, `source_summary`; Response: `hook_text`, `hook_type`, `hook_score`, `rationale`, `template_match`, `warnings`.
- **`generated_scripts`:** optionale Felder `hook_type`, `hook_score`, `opening_style` (Meta aus Hook-Engine-Lauf beim Watchlist-Job-Run, zusätzlich zum bestehenden `hook`-Feld).
- **Review:** Heuristik „Hook passt zu Template?“ in [`app/review/originality.py`](app/review/originality.py); optional `hook_text` / `hook_type` auf **`ReviewScriptRequest`**.

**Nicht-Ziel V1:** LLM-Hook-Refinement; A/B-Varianten (später).

---

### BA 9.3 — Strenge Conformance, Nebenkanal, Review-Automatisierung, Versionierung (**done**)

**Ziel:** Template-Engine wird **workflowfähig**: Teams können „mit Template X nur veröffentlichen, wenn …“ abbilden — **ohne** den öffentlichen Generate-Vertrag zu sprengen. Schwere oder strukturierte Daten landen in **Nebenkanälen** (Production, Export, Connector, optionale Collections).

#### 9.3.1 Strikter Modus (Policy festlegen)

- **Request-Flag** (Vorschlag): z. B. `template_strict: bool` oder `template_conformance_level: "off" | "warn" | "strict"` auf Generate-Requests (und ggf. Kanal-Default).  
- **Strict** bedeutet **konzeptionell**: schwere Verstöße gegen Template-Blueprint erzeugen **explizite, auffindbare** `warnings` und optional einen **numerischen oder enumartigen „Gate“-Status** nur in **persistierten** Objekten oder Export — nicht als neues Pflichtfeld in `GenerateScriptResponse`.  
- **HTTP:** Weiterhin kein 500 durch LLM; gemäß AGENTS Fehler abfangen. Ob Strict bei „hartem“ Fehlschlag 422 verlangt — **Produktentscheid** im MODULE_TEMPLATE; Default eher „200 + warnings + ggf. `template_strict_failed` in Export“.

#### 9.3.2 Review-Automatisierung (Workflow)

- Konfigurierbar (Kanal oder global): nach erfolgreichem **`generated_scripts`**-Write **optional** `review-script` intern aufrufen oder Job-Substatus setzen „review_pending“.  
- Ergebnis an **`script_jobs`** / **`review_results`** anbinden gemäß bestehendem Phase-4-/Watchlist-Muster — **kein** automatisches Veröffentlichen.

#### 9.3.3 Nebenkanal-Artefakte („zweites Format“)

- Strukturierte Zusatzdaten: z. B. `story_structure` (Kapitel-Rollen, Timestamps-Idee, CTA-Platzierung) nur in **`production_jobs`**, **`render_manifests`**, Connector-JSON oder neuer Collection — **nicht** in den sechs Pflichtfeldern der Live-Generate-Response.  
- Export-Version im Connector erhöhen oder `metadata.story_engine` Block dokumentieren.

#### 9.3.4 Template-Versionierung

- **`video_template`** bleibt ID; zusätzlich **`template_definition_version`** (int oder semver-String) in Persistenz und Export, damit alte Jobs reproduzierbar bleiben, wenn sich Blueprints ändern.

#### 9.3.5 Tests & Akzeptanz BA 9.3

- Tests für Strict-Warnpfade, Hook-Sequenz (mock), Nebenkanal-JSON Schema (snapshot oder Feldpräsenz).  
- Expliziter Regressionstest: Roh-Generate-Response-Keys unverändert.

---

### BA 9.4 — Scene Rhythm Engine (**done**)

**Ziel:** Aus **`duration_minutes`**, **`video_template`** und dem **Kapitel-/Skriptinhalt** empfohlene **Taktführung** ableiten (Beat-Längen-Hinweise, Übergänge, CTA-Platzierung als **Text/Meta**) — **nicht** als Pflichtfeld in der Live-**`GenerateScriptResponse`**.

#### Inhalt und Technik (Skizze)

- Neues Modul z. B. [`app/story_engine/rhythm_engine.py`](app/story_engine/rhythm_engine.py) (deterministisch in V1).
- Optionaler öffentlicher Nebenkanal z. B. **`POST /story-engine/rhythm-hint`** oder ausschließlich intern über Production/Export — siehe [MODULE_TEMPLATE.md](MODULE_TEMPLATE.md) vor größerem Scope.
- **Persistenz:** bevorzugt **`production_jobs`**, **`render_manifests`**, Connector-JSON — nicht die sechs Generate-Felder.

#### Nicht-Ziele (9.4 V1)

- Keine Pflicht-JSON-Erweiterung von `/generate-script`.
- Kein Ersatz für [`scene_plans`](app/watchlist/scene_plan.py); Rhythmus-Hinweise **ergänzen** die bestehende Produktionskette.

#### Tests und Akzeptanz (9.4)

- Matrix: Template × Dauer × minimaler Kapitel-Input; stabile Strings oder strukturierte Meta-Blöcke.
- Regenerate-/Export-Snapshots nur bei vereinbartem Schema.

---

### BA 9.5a — Observability für Story-Modul (**done**, Control Panel Slice)

**Ziel:** **Story-Relevantes** (Templates, Hook-Meta, später Rhythm-Hinweise, Strict-/Gate-Signale) im **Founder-Betrieb** auf einen Blick — **read-only**, ohne neue Secrets.

- Erweiterung z. B. [`app/watchlist/control_panel.py`](app/watchlist/control_panel.py) und/oder schlanker Endpoint unter **`/production/control-panel`** oder **`/story-engine`** (nur Aggregation).
- Anknüpfung an bestehende **Audits** [`pipeline_audit_scan.py`](app/watchlist/pipeline_audit_scan.py), soweit Story-Meta ohne Overengineering abbildbar.

#### Tests (9.5a)

- Smoke mit Mocks / leeren Collections; keine Live-Firestore-Pflicht in CI.

---

### BA 9.5b — Story-Pack / Beat-Sheet (**done**, Connector + Download-Paket)

**Ziel:** Ein **gebündeltes Nebenkanal-Artefakt** für Downstream: u. a. **`video_template`**, Hook-Engine-Meta (wo vorhanden), **Rhythm-Metadaten** (nach 9.4), Verweise auf **`scene_plans`**/Kapitel — **ein** Block im Connector bzw. Export-Download.

- **Vertrag:** `GenerateScriptResponse` unverändert; Pack nur in Export / Manifest / `production_jobs`.
- Optional: Anbindung an Gold-Pfad [`tests/test_ba88_full_production_run.py`](tests/test_ba88_full_production_run.py), wenn Schema stabil ist.

#### Tests (9.5b)

- Feldpräsenz / JSON-Schema-Snapshot; Regression Generate-Keys.

---

### BA 9.6 — Experimentation Layer (**done**, Registry + Persistenzfelder)

**Ziel:** Systematisches **Ausprobieren und Vergleichen** von Hook-Varianten und Experimenten — ohne den Live-**`/generate-script`**-Vertrag zu erweitern.

- **A/B Hook Testing** (Zuordnung zu Jobs/Kontext; Auswertung über Metriken, nicht über Pflichtfelder in Generate).
- **Hook Variant Registry** (Versionierte/namhafte Varianten, referenzierbar aus Persistenz/Export).
- **Experiment Metadata** (Experiment-ID, Hypothese, Zeitraum — nur dort, wo MODULE_TEMPLATE/Schema es festlegt).
- **Optional: LLM Refinement Preparation** (Schnittstellen/Flags/Pipeline-Hooks für spätere LLM-Nachbearbeitung von Hooks — **ohne** Pflicht-LLM in V1).
- **Hook Performance Comparison** (Aggregation aus Observability 9.5a + eigenen Experiment-Telemetrien).

#### Nicht-Ziele (9.6)

- Kein neues Pflichtfeld in **`GenerateScriptResponse`**; kein automatisches Überschreiben produktiver Hooks ohne redaktionellen/policy Rahmen.
- Keine Vermischung mit **Phase 9/10** (Packaging/Publishing bleiben getrennt).

#### Tests (9.6)

- Deterministische Zuordnung von Varianten/Experiment-IDs; Smoke auf leeren Fixtures; Schema-/Snapshot-Tests für Nebenkanal-JSON.

---

### BA 9.7 — Adaptive Template Optimization (**done**)

**Modulsteckbrief:** [docs/modules/ba97_adaptive_template_optimization.md](docs/modules/ba97_adaptive_template_optimization.md). § [Nächste Priorität](#nächste-priorität-ausrichtung) bleibt als historische Produktfokussierung; Umsetzung abgeschlossen.

**Umsetzung:** Drift-/Score-/Refinement-Logik **`app/story_engine/template_drift.py`**, **`template_health_score.py`**, **`refinement_signals.py`**, **`template_optimization_aggregate.py`**. Aggregation im Control Panel und **`StoryEngineTemplateHealthHttpResponse`** via **`GET /story-engine/template-health`** (Service **`get_story_engine_template_health_service`**). Persistenz nur lesend aus **`generated_scripts`** (Stichprobe).

**Ziel:** Templates **gesund und aktuell** halten: Drift sichtbar machen und Inputs für gezielte Nachschärfung liefern.

- **Template Drift Detection** (Abweichung Istvorlagen vs. Blueprint/Conformance-Historie).
- **Auto-Refinement Inputs** (Vorschläge/Signale für Redaktion oder spätere Automatisierung — **kein** stilles Rewrite produktiver Blueprints ohne Freigabe).
- **Template Health Evolution** (Zeitreihen oder Status je Template-ID).
- **Performance-based Template Scoring** (Kopplung an Metriken aus 9.5a/9.6/9.8-Kontext).

#### Nicht-Ziele (9.7)

- Kein Bruch des Sechs-Felder-Skript-Vertrags; keine Umbenennung bestehender **Phase**-Nummern.

#### Tests (9.7)

- **`tests/test_ba97_template_optimization.py`**; Regression Control Panel **`tests/test_ba84_control_panel.py`**; Generate-Keys unverändert (`tests/test_ba9396_story_maturity.py`).

---

### BA 9.8 — Story Intelligence Layer (**done**)

**Modulüberblick:** [docs/modules/ba98_story_intelligence_layer.md](docs/modules/ba98_story_intelligence_layer.md). Technisch **`story_intelligence_layer.py`**; Ausgaben nur Hinweislisten ohne Schreibzugriff auf Produktions-Skripte.

**Ziel:** **Auswertung und Empfehlung** über Hook-, Review- und Story-Metriken hinweg — unter klarer **Governance** („Self-Learning Readiness“, nicht blindes Selbstlernen).

- **Feedback Loop** aus Hook / Review / Story Metrics (read-only Aggregation + dokumentierte Empfehlungsregeln).
- **Self-Learning Readiness** (Voraussetzungen, Audits, Feature-Flags — before any closed-loop automation).
- **Template Recommendation Logic** (z. B. „für Kontext X eher Template Y“ als Hinweis/Nebenkanal).
- **Cross-template Performance Analysis** (Vergleiche nur mit Datenschutz-/Quota-Grenzen wie heute).

#### Nicht-Ziele (9.8)

- Keine stillen Produktionsänderungen ohne Logging/Audit; kein **BA 10** als Ersatznummer — alles bleibt **BA 9.x** bis 9.9.

#### Tests (9.8)

- **`tests/test_ba98_story_intelligence.py`**; gemeinsamer READ-Pfad **`GET /story-engine/template-health`**.

---

### BA 9.9 — Story Engine Operations Maturity (**done**)

**Abschlussdoku:** [docs/STORY_ENGINE_OS.md](docs/STORY_ENGINE_OS.md); Operativer Kurzblick **[OPERATOR_RUNBOOK.md](OPERATOR_RUNBOOK.md)**; Kontext Deploy **[docs/runbooks/cloud_run_deploy_runbook.md](docs/runbooks/cloud_run_deploy_runbook.md)**. Detail-Steckbrief [docs/modules/ba99_story_engine_operations_maturity.md](docs/modules/ba99_story_engine_operations_maturity.md).

**Ziel:** Das Story-Modul ist **betrieblich und dokumentarisch** als **Kernfähigkeit abgeschlossen** — weiterhin innerhalb **BA 9.x**, ohne **Phase 9** (Packaging) oder **Phase 10** (Publishing) zu ersetzen oder zu verschmelzen.

- **Vollständige Story Governance** (Rollen, Freigaben, documented runbooks im Sinne von AGENTS/PIPELINE).
- **Canonical Story OS** als **Zielbild** / Begriff für das integrierte Zusammenspiel: Templates, Hooks, Rhythm, Packs, Experimentation, Intelligence.
- **Story Control Panel Reifegrad** (Ausbau von Observability 9.5a zu operativ nutzbarer „Einzelanlaufstelle“ für Story-relevante KPIs).
- **Story System als abgeschlossenes Kernmodul** in der **BA-9.x**-Roadmap — nächste große Produktlinien **nicht** durch Hochzählen zu „BA 10 Story“ ohne separates Planungs-Deliverable.

#### Nicht-Ziele (9.9)

- Kein Ersatz für Video-Schnitt (**Phase 9**) oder Upload-Workflow (**Phase 10**); kein neues Pflichtfeld in **`GenerateScriptResponse`**.

#### Tests (9.9)

- Smoke auf Control-Panel-/Aggregations-Verträgen; Dokumentations-Regression (Verweise BA vs. Phase konsistent).

---

### Abhängigkeiten und Risiken (gesamt BA 9.x)

| Risiko | Mitigation |
|--------|------------|
| Verwechslung BA 9.x vs. Phase 9 / Phase 10 | Plan, README, AGENTS und ISSUES_LOG: **BA** = modulare Bauphase; **Phase** = Makro-Roadmap; **BA 9.x ≠ Phase 9/10**. |
| Zu viele Felder in Generate-Body | Neue Ideen zuerst Export/Production; MODULE_TEMPLATE vor neuen Collections. |
| LLM ignoriert Blueprints | Striktere Prompts + Fallback + Conformance; kein „erfundenes“ Kapitel zum Auffüllen. |
| Review-**Automatisierung** erhöhen Latenz/Kosten | Triggern nur async/Job-Flag; Dry-Run in Runbook dokumentieren. |

---

## Workflow: Plan ↔ Umsetzung ↔ Fehler

1. **Vor größeren Änderungen** dieses Dokument und die betroffene Phase prüfen.  
2. **Neues Modul**: [MODULE_TEMPLATE.md](MODULE_TEMPLATE.md) ausfüllen und in der Phase verlinken.  
3. **Nach Incidents oder wiederkehrenden Bugs**: [ISSUES_LOG.md](ISSUES_LOG.md) aktualisieren (Datum, Ursache, Fix, Commit-Referenz).  
4. **Commits**: nur mit Tests/Checks laut [AGENTS.md](AGENTS.md) und Statusabgleich hier.

Letzte inhaltliche Überarbeitung dieser Plan-Datei: **2026-04-30** — **Phase 7 V1** (Bausteine **7.2–7.5**, **7.7–7.8**, ohne optionales **7.6**) in Endpunktliste und Phasenblock verankert: u. a. **`POST …/voice/synthesize`** → **`production_files`** (Metadaten), **`voice_production_file_refs`** / **`voice_artefakte`**, Audit‑ und **`production_costs`‑Warnpfade**, Ops‑Docs; Regression **`tests/test_phase7_73_voice_synthesize_commit.py`**; Stub **Makro‑Phase 8** in **`docs/phases/phase8_image_sceneplan_bauplan.md`**. Zuvor u. a. **2026-05-04**: Phase‑7.2‑Preview‑Slice (`tests/test_phase7_72_voice_provider_contract.py`).
