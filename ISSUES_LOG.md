# Issues-Log

Gelöste und offene **Projektprobleme** (technisch und prozessual). Keine Secrets, keine `.env`-Inhalte.  
Neue Einträge bei wiederkehrenden Fehlern oder nach Post-Mortems ergänzen.

---

## Tabelle

| Datum | Bereich | Problem | Ursache | Fix | Status | Commit/Revision |
|-------|---------|---------|---------|-----|--------|-----------------|
| *n/a* | Config / Pydantic | `BaseSettings` nicht verfügbar bzw. Import-Fehler nach Dependency-Upgrade | In Pydantic v2 liegt `BaseSettings` im Paket `pydantic-settings`, nicht mehr im Kernpaket | `pydantic-settings` als Abhängigkeit; Settings-Klasse von `pydantic_settings` importieren | gelöst | *(siehe Repo-Historie)* |
| *n/a* | NLP / NLTK | LookupError für `punkt_tab` beim Satz-Split | NLTK-Daten/Tokenizer-Erwartung (`punkt` vs. `punkt_tab`) je nach NLTK-Version | Fallback oder kompatibler Download/Tokenizer-Pfad; defensive Initialisierung | gelöst | *(siehe Repo-Historie)* |
| *n/a* | Cloud Run / OpenAI | Authentifizierung bei OpenAI schlägt fehl trotz gesetztem Secret | Führende/nachfolgende **Leerzeichen oder Zeilenumbrüche** im Secret-Manager-Wert | API-Key vor Verwendung **trimmen**; Secret-Wert in GCP ohne Whitespace pflegen | gelöst | *(siehe Repo-Historie)* |
| *n/a* | HTTP / OpenAI Client | `APIConnectionError` oder abgelehnte Verbindung wegen **ungültigem HTTP-Header** | Nicht erlaubte Zeichen in einem Custom-Header (z. B. User-Agent), den die Library mitsendet | Header bereinigen oder entfernen; nur erlaubte Header-Werte setzen | gelöst | *(siehe Repo-Historie)* |
| *n/a* | LLM / Skriptlogik | Kurzer erster LLM-Output wurde **fälschlich als Fehler** gewertet und löste vollständigen Fallback aus | Zu strenge Schwellenlogik zwischen „zu kurz“ und „retry/expand“ | Zweiten **Expansion-Pass** bzw. differenzierte Behandlung; Fallback nur bei echtem Fehlschlag; siehe `app/utils.py` und `warnings` | gelöst | *(siehe Repo-Historie)* |
| *n/a* | Prozess / IDE | Agent (Codex) arbeitete an **falscher oder veralteter Verzeichnisstruktur** | Mehrere Projekt-Roots oder veralteter Chat-Kontext ohne aktuelle `app/`-Layout | Immer Workspace-Root und `AGENTS.md`/`README.md` als Referenz; Phasenplan in [PIPELINE_PLAN.md](PIPELINE_PLAN.md) vor größeren Änderungen lesen | gelöst (prozessual) | — |

| 2026-04-29 | Watchlist / Jobs | Pending **`script_jobs`** wurden auch für Videos ohne abrufbares **Transkript** angelegt; späterer **`run`** schlug erwartbar mit „Transcript not available“ fehl | Transcript-Verfügbarkeit wurde erst beim Job-Run geprüft (RSS liefert keine Caption-Verfügbarkeit) | Transcript-Preflight beim Kanal-Check (**`auto_generate_script=true`**, nach Score/Shorts-Filtern); ohne Transkript **`processed_videos`** **`skipped`** (**`transcript_not_available`**) und **kein** Job; Job-Run mit standardisierten **`error`** / **`error_code`** | fixed after implementation | pending commit |
| 2026-04-29 | Watchlist / Control Tower | Operative Übersicht und Queue-Steuerung fehlten | Geplanter Ausbau Watchlist ohne neue Skript-Verträge | BA **5.8–6.2:** Dashboard, Error-Summary (Stichprobe), Retry/Skip/Pause/Resume, **`production_jobs`**-Stub, Pending-Query + Meta-Zeitstempel; **`ScriptJob.attempt_count`**/**`last_attempt_at`** optional | umgesetzt (Tests grün) | pending commit |
| 2026-04-29 | Watchlist / Dashboard | **`generated_scripts_total`**/**`processed_videos_total`** häufig 0 trotz Daten; falsche Aggregation-Warnhinweise im Control Tower | Firestore **`RunAggregationQuery.get()`** lieferte **`AggregationResult`**-Batches; Auswertung war unvollständig; Fallback fehlte | Batches korrekt parsen (**`AggregationResult`** bzw. alias **`all`** / erster Treffer); begrenzte Stream-Zählung wenn Aggregation **`-1`**; Dashboard-Warning-Text vereinheitlicht | umgesetzt (Tests grün) | pending commit |
| 2026-04-29 | Watchlist / Review | **`POST …/jobs/…/review`** nur HTTP ohne dauerhafte Speicherung | Persistenz erst in BA 6.4 geplant | Collection **`review_results`**, **`script_jobs.review_result_id`**, optional **`processed_videos.review_result_id`**; keine ScriptJob-Failed-Logs bei Persistenz-/Heuristik-Störungen wie spezifiziert | umgesetzt (Tests grün) | pending commit |
| 2026-04-29 | Production / Vorproduktion | **BA 6.6**: Script-to-Szenenplan ohne LLM; neue Collection **`scene_plans`**; Endpoints **`/production/jobs/{id}/scene-plan/generate`** und **`GET …/scene-plan`** — **keine** Änderung an **`generated_scripts`** (**`production_jobs`** schlank) | Produktionsbaum braucht Vorstufe für spätere Bild-/Prompt-Phase (Phase 8) | Deterministische Aufteilung aus Kapiteln / Fallback **`full_script`**, Obergrenze Szenen, Fingerabdruck idempotent | umgesetzt (Tests **`test_ba66_scene_plan`** grün; `unittest discover`/`compileall`) | ohne Commit durch Agent |

---

## Hinweise

- **Datum**: Bei älteren Fixes kann das exakte Datum unbekannt sein — dann `*n/a*` oder ungefähre Iteration notieren.  
- **Commit/Revision**: Konkreten Hash eintragen, sobald der Fix im Git nachvollziehbar ist.  
- **Offene Issues**: Neue Zeilen mit Status `offen` oder `in Arbeit` ergänzen; nach Fix auf `gelöst` setzen und Commit verlinken.
