# News to Video Pipeline

## 1. Projektziel

Dieses MVP liefert eine lokale FastAPI-Anwendung, die aus einer Nachrichten-URL oder einem YouTube-Link ein strukturiertes YouTube-Skript erzeugt. Fokus liegt auf einer sicheren, modularen Pipeline mit optionaler LLM-Unterstützung und stabiler Fallback-Logik.

**Planung:** Phasen, Status und Akzeptanzkriterien für die gesamte Pipeline stehen in [PIPELINE_PLAN.md](PIPELINE_PLAN.md). Gelöste und dokumentierte Vorfälle: [ISSUES_LOG.md](ISSUES_LOG.md). Vorlage für neue Module: [MODULE_TEMPLATE.md](MODULE_TEMPLATE.md).

## 2. Aktueller MVP-Status

- FastAPI-App läuft lokal.
- **Cloud MVP v1:** Bereitstellung auf **Google Cloud Run** mit öffentlicher Service-URL, `GET /health` und `POST /generate-script` online nutzbar. Details, Deploy-Befehl, Secret Manager und Test-`curl`: [DEPLOYMENT.md](DEPLOYMENT.md).
- Endpoint `POST /generate-script` ist funktionsfähig.
- Endpoint `POST /youtube/generate-script` (V1): YouTube-Video-URL → Transkript → eigenständiges deutschsprachiges Skript (ohne YouTube Data API-Key).
- Endpoint `POST /youtube/latest-videos` (V1): YouTube-Kanal prüfen und neueste Videos per RSS abrufen (ohne YouTube Data API-Key).
- `GET /health` liefert den Service-Status.
- OpenAI ist optional und wird über Umgebungsvariablen (lokal z. B. `.env`) aktiviert.
- Der LLM-Modus nutzt strikt geparste JSON-Ausgabe; bei zu kurzem erstem LLM-Output kann ein **zweiter Expansion-Pass** das Skript Richtung Ziel-Länge erweitern (siehe `app/utils.py`, Warnungen in `warnings`).
- Ein stabiler Fallback bleibt aktiv, wenn OpenAI fehlt oder fehlschlägt.
- `AGENTS.md` enthält verbindliche Agent-Regeln.

## 3. Features

- Strukturierte Skripterzeugung: Titel, Hook, Kapitel, Full Script
- Strikte JSON-Antwort mit fixer Vertragsform
- Text- und Artikel-Extraktion aus URLs
- Dauerbasierte Wort- und Kapitelplanung
- Optionaler OpenAI-LLM-Modus
- Lokaler Fallback-Modus ohne API-Schlüssel
- UTF-8-Response-Handling
- Klare Warnungen bei Unsicherheit oder unzureichendem Inhalt
- YouTube Video-to-Script V1: Transkript aus Video-URL → strukturiertes Skript (`POST /youtube/generate-script`)
- YouTube-Kanal-Discovery V1: neueste Videos strukturiert mit Heuristik (`score`, `reason`, `summary` aus Metadaten)
- **Phase 4 V1:** `POST /review-script` — heuristische Originalitäts- und Nähe-zur-Quelle-Prüfung (keine Rechtsberatung, kein Auto-Publish)
- **Phase 5 V1 Schritt 1–4:** `POST /watchlist/channels`, `GET /watchlist/channels`, **`POST /watchlist/channels/{channel_id}/check`**, **`GET /watchlist/jobs`**, **`POST /watchlist/jobs/{job_id}/run`** — Kanäle und **`processed_videos`** in Firestore; bei **`auto_generate_script=true`** prüft der Kanal-Check vor **`pending`**-Jobs einen **Transcript-Preflight** (gleiche Abruflogik wie **`POST /youtube/generate-script`**); **`pending`** entstehen nur bei verfügbarem Transkript; Speicherung in **`generated_scripts`**.
- **Phase 5.5–5.7 (Automation-Layer):** **`POST /watchlist/channels/{channel_id}/recheck-video/{video_id}`** (ein Video erneut prüfen, mit Warnung bei einzelner `processed_videos`-Entfernung), **`POST /watchlist/jobs/run-pending`** (pending Jobs im Batch ausführen, Limit Default 3, Max 10), **`POST /watchlist/automation/run-cycle`** (scheduler-tauglicher Zyklus: aktive Kanäle prüfen, danach pending Jobs; Body `channel_limit` / `job_limit`; schreibt bei Erfolg **`last_run_cycle_at`** in Firestore **`watchlist_meta/automation`**) und optional **`POST /watchlist/jobs/{job_id}/review`** (nutzt dieselbe Heuristik wie **`POST /review-script`**, ohne ScriptJob-Status zu ändern). **Kein** Cloud-Scheduler-Deploy in diesem Schritt — nur HTTP-Schnittstellen. Details: [PIPELINE_PLAN.md](PIPELINE_PLAN.md).
- **Phase 5.8–6.6 (Control Tower & Production Jobs):** … Ausführlich: [PIPELINE_PLAN.md](PIPELINE_PLAN.md).
- **BA 6.8–7.0 (Voice Layer, Render Manifest, Connector Export):** neue Firestore-Collections **`voice_plans`**, **`render_manifests`**; Endpoints **`POST/GET /production/jobs/{id}/voice-plan`**, **`POST/GET …/render-manifest`**, **`GET …/export`** — nur strukturierte Daten und JSON, **kein** echtes TTS, kein Video-Render, keine Provider-API-Aufrufe. Details und Tests: [PIPELINE_PLAN.md](PIPELINE_PLAN.md), `tests/test_ba68_6970_production_voice_render_export.py`.
- **BA 6.6.1 (nur lokale/integration Tests):** `POST /dev/fixtures/completed-script-job` — optional mit `ENABLE_TEST_FIXTURES=true` in `.env`; legt ohne YouTube-Anruf einen **completed** `script_jobs`-Eintrag, **`generated_scripts`** mit Kapiteln und optional **`production_jobs`** an (IDs immer Präfix `dev_fixture_`). **In Produktion deaktiviert lassen.**

## 4. Projektstruktur

```
app/
├── __init__.py
├── main.py           # FastAPI app setup
├── config.py         # Settings und Umgebungsvariablen
├── models.py         # Pydantic Request-/Response-Modelle
├── utils.py          # Extraktion, Generierung, LLM und Fallback
├── review/           # Phase 4: Originalitäts-Heuristiken + Review-Service
├── watchlist/        # Phase 5: Watchlist (Firestore, Jobs, generated_scripts)
├── youtube/          # Kanal-Auflösung, RSS, Scoring (ohne Data API)
└── routes/
    ├── __init__.py
    ├── generate.py   # /generate-script Endpoint
    ├── youtube.py    # /youtube/generate-script, /youtube/latest-videos
    ├── review.py     # /review-script
    ├── watchlist.py  # Watchlist-CRUD, Kanal-Check, Jobs, POST …/jobs/{id}/run (Phase 5)
    ├── production.py # /production/jobs (+ scene-plan … scene-assets … voice-plan … render-manifest … export BA 6.6–7.0)
    └── dev_fixtures.py # BA 6.6.1: POST /dev/fixtures/* nur bei ENABLE_TEST_FIXTURES

Dockerfile
README.md
DEPLOYMENT.md      # Cloud Run MVP v1: URL, Deploy, Secret Manager, Tests
requirements.txt
.env.example
AGENTS.md
```

## 5. Voraussetzungen

- Python 3.9 oder neuer
- Internetzugang für URL-Fetching und optionale OpenAI-Anfragen
- Optional: Docker für Container- oder Cloud-Run-Nutzung

## 6. Installation lokal

1. Repository klonen
2. Python-Umgebung erstellen:
   ```bash
   python -m venv .venv
   ```
3. Umgebung aktivieren:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
4. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```

## 7. .env Setup

- Kopiere `.env.example` nach `.env`.
- Setze optional `OPENAI_API_KEY` und `OPENAI_MODEL` für den LLM-Modus.
- `.env` darf niemals in dieses Repository eingecheckt, gelesen oder ausgegeben werden.
- Wenn kein OpenAI-Key vorhanden ist, nutzt die App den lokalen Fallback-Modus.

## 8. Server starten

```bash
uvicorn app.main:app --reload
```

Die API ist dann unter `http://127.0.0.1:8000` erreichbar.

## 9. API-Endpunkte

### GET /health

- Prüft, ob die App erreichbar ist.
- Antwort: `{"status":"healthy"}`

### POST /generate-script

- Generiert das Skript aus einer URL.
- Request-Body:
  ```json
  {
    "url": "https://example.com/article",
    "target_language": "de",
    "duration_minutes": 10
  }
  ```

### POST /youtube/generate-script

**Zweck:** Aus einer **YouTube-Video-URL** das **Transkript** (Untertitel) laden und daraus ein **eigenständiges, deutschsprachiges Story-Skript** erzeugen — im gleichen festen Antwortformat wie `POST /generate-script` (`GenerateScriptResponse`).

**Request-Body:**

```json
{
  "video_url": "string",
  "target_language": "de",
  "duration_minutes": 10
}
```

**Response:** `GenerateScriptResponse` (Vertrag unverändert):

```json
{
  "title": "",
  "hook": "",
  "chapters": [],
  "full_script": "",
  "sources": [],
  "warnings": []
}
```

**Unterstützte URL-Formate** (Auszug):

- `youtube.com/watch?v=…` (z. B. `https://www.youtube.com/watch?v=…`)
- `youtu.be/…`
- Pfade mit `/shorts/`
- Pfade mit `/embed/`
- Pfade mit `/live/`

**Transkript fehlt:** Die API antwortet mit **HTTP 200** und einem **leeren bzw. minimalen Vertrag**; in `warnings` erscheint u. a.:

`Transcript not available for this video.`

**Hinweise:**

- **Kein YouTube Data API Key** nötig (öffentliche Untertitel, z. B. über `youtube-transcript-api`).
- **Keine automatische Veröffentlichung** und keine Speicherung des Outputs in diesem Endpoint.

### POST /youtube/latest-videos

**Zweck:** Einen YouTube-Kanal prüfen und die **neuesten Videos** strukturiert zurückgeben (Metadaten aus dem Kanal-Feed, keine automatische Veröffentlichung, kein Scheduler).

**Request-Body:**

```json
{
  "channel_url": "string",
  "max_results": 5
}
```

`max_results` ist optional (Standard `5`), erlaubt sind Werte von **1 bis 50**.

**Response:**

```json
{
  "channel": "",
  "videos": [
    {
      "title": "",
      "url": "",
      "video_id": "",
      "published_at": "",
      "summary": "",
      "score": 0,
      "reason": ""
    }
  ],
  "warnings": []
}
```

**Hinweise:**

- **V1** nutzt das **öffentliche YouTube-RSS** (`feeds/videos.xml?channel_id=…`) und **keinen YouTube Data API-Key**.
- URLs der Form **`https://www.youtube.com/channel/UC…`** sind **zuverlässiger** als **`@handle`**-Links: Letztere erfordern ggf. eine lesbare Kanal-HTML-Seite; bei Cookie-/Einwilligungsseiten oder Bot-Schutz kann die Auflösung fehlschlagen — Details stehen in `warnings`.
- **Keine Transcript-Extraktion** in V1; `summary` leitet sich nur aus Feed-Metadaten (z. B. Titel) ab, nicht aus Untertiteln oder Audio.

### POST /review-script

**Zweck:** Nach der Skript-Generierung eine **technische/redaktionelle Risikoeinschätzung** liefern: wie nah liegt das Skript am übergebenen Quelltext (Wort-/Satzüberlappung, lange gemeinsame Folgen)? Das ist **keine Rechtsberatung**, **keine Freigabe** zur Veröffentlichung und **kein** Ersatz für menschliche Redaktion. Es erfolgt **keine** automatische Veröffentlichung und **keine** Speicherung des Quelltexts durch diesen Endpoint.

**Request-Body:**

```json
{
  "source_url": "",
  "source_type": "youtube_transcript",
  "source_text": "",
  "generated_script": "",
  "target_language": "de",
  "prior_warnings": []
}
```

- `source_type`: `youtube_transcript` | `news_article` | `unknown` — bei YouTube wird **strenger** bewertet und eine zusätzliche `warning` gesetzt.
- `generated_script` entspricht inhaltlich dem `full_script` aus `POST /generate-script` bzw. `/youtube/generate-script`.
- Mindestens eines von `source_text` und `generated_script` muss nicht leer sein; sind **beide** leer, antwortet die API mit **422**.
- Ist `generated_script` leer, liefert der Service **200** mit `risk_level: high` und klarer `warning` (kein harter Fehler).

**Response:**

```json
{
  "risk_level": "low",
  "originality_score": 85,
  "similarity_flags": [],
  "issues": [],
  "recommendations": [],
  "warnings": []
}
```

**Score-Konvention:** `originality_score` von **0** bis **100**. **100** = sehr eigenständig, **0** = sehr nah an der Quelle / hohes Risiko im Sinne der Heuristik.

**`risk_level`:** grobe Stufe (`low` / `medium` / `high`) aus den Heuristiken — nachvollziehbar über `similarity_flags`, `issues` und `warnings`, aber **nicht** als juristische Bewertung interpretieren.

**V1-Hinweise:**

- Es läuft eine **rein lokale Heuristik** (kein LLM-Review in V1). In `warnings` steht u. a.: *LLM qualitative review is not enabled in V1; heuristic review only.* Qualitative LLM-Second-Opinion ist für **V1.1** vorgesehen, falls gewünscht.
- Heuristiken können **False Positives** und **False Negatives** erzeugen (z. B. Zitate, Eigennamen, kurze Quellen).

**Beispiel (lokal):**

```bash
curl -s -X POST "http://127.0.0.1:8000/review-script" ^
  -H "Content-Type: application/json" ^
  -d "{\"source_type\":\"news_article\",\"source_text\":\"Kurzer Artikeltext hier.\",\"generated_script\":\"Eigenes Skript mit Einordnung und Fazit.\",\"prior_warnings\":[]}"
```

(PowerShell: Anführungszeichen ggf. anpassen oder JSON aus Datei mit `-d @body.json` übergeben.)

**Tests (Smoke):** Im Repo unter `tests/test_review_script.py` (u. a. identischer Text → `high`, kurze Quelle → `Source text is short…`, YouTube → strengere `warning`). Zusätzlich: `python -m compileall app` und `python -m unittest tests.test_review_script`.

### Watchlist — Phase 5 V1 (Schritte 1–4)

Watchlist speichert überwachte YouTube-Kanäle in **Google Firestore** (Collection **`watch_channels`**, Document-ID = YouTube-`channel_id`). Neue bzw. bereits bekannte Videos pro Kanal werden in **`processed_videos`** gehalten (Document-ID = **`video_id`**, global eindeutig), damit beim nächsten Check **keine** Doppel-Kandidaten mehr auftauchen. **Ohne** erfolgreiche Auflösung einer **Channel-ID (UC…)** wird beim Anlegen nichts persistiert (Handles können an Consent-/Bot-Seiten scheitern — `warnings` wie bei `POST /youtube/latest-videos`).

**Voraussetzungen:**

- Firestore im GCP-Projekt (Native Mode), **Named Database** mit ID **`watchlist`** (oder passende ID in der Konsole anlegen). Die App verwendet standardmäßig die Umgebungsvariable **`FIRESTORE_DATABASE=watchlist`** (siehe `app/config.py`; überschreibbar, Standard ist `watchlist`).
- **Application Default Credentials** lokal (z. B. `gcloud auth application-default login`) bzw. auf Cloud Run über das Dienst-Service-Account; siehe [DEPLOYMENT.md](DEPLOYMENT.md).

**Schritt 1 – CRUD**

**Request (POST Anlegen):** `WatchlistChannelCreateRequest` — Felder u. a. `channel_url`, `check_interval` (`manual` | `hourly` | `daily` | `weekly`), `max_results` (1–50), **`auto_generate_script`**, `auto_review_script`, `target_language`, `duration_minutes` (1–60), `min_score` (0–100), `ignore_shorts`, `notes`.

**Responses (Anlegen/Liste):** `CreateWatchlistChannelResponse` bzw. `ListWatchlistChannelsResponse` mit `warnings`. Wenn Firestore nicht erreichbar ist: **503** mit Hinweis in `warnings` (ohne Secrets). Wenn die **Channel-ID nicht auflösbar** ist: **200** mit `channel: null` und erklärenden `warnings`.

**GET** `/watchlist/channels` listet gespeicherte Kanäle (nach `created_at`, neueste zuerst).

**Schritt 2 – manueller Kanal-Check**

**POST** `/watchlist/channels/{channel_id}/check` prüft einen **gespeicherten** Kanal (nur `status=active`): wie `POST /youtube/latest-videos` (RSS, **`max_results`**), **Score**, Shorts-Regel (`ignore_shorts`), **`min_score`**; schreibt **`processed_videos`** (`seen` oder `skipped`). Antwort: **`CheckWatchlistChannelResponse`** mit **`new_videos`**, **`known_videos`**, **`skipped_videos`**, **`created_processed_videos`**, **`created_jobs`**, **`warnings`**.

**Schritt 3 – Script-Jobs (pending vor Run)**

- Ist **`auto_generate_script=true`** und das Feed-Video hat alle Filter (**Shorts**, **`min_score`**) passiert, prüft der Service vor einer **`pending`**-Job-Anlage einen **Transcript-Preflight** (öffentliche Untertitel gleicher Weg wie **`POST /youtube/generate-script`** — keine Speicherung von Roh-Transkripten).
  - **Transkript abrufbar:** **`processed_videos.status`** = **`seen`**, in **`script_jobs`** (**Document-ID** = **`video_id`**) **`pending`**; **`processed_videos.script_job_id`** wird gesetzt; Eintrag unter **`created_jobs`** (u. a. `id`, `video_id`, `video_url`, `status`, `target_language`, `duration_minutes`).
  - **Kein Transkript:** **`processed_videos.status`** = **`skipped`**, **`skip_reason`** = **`transcript_not_available`**; **kein** **`script_jobs`**-Eintrag; Video steht unter **`skipped_videos`**. Aggregate **`warnings`** im Response bei mehreren Treffern, keine unnötig langen Texte pro Video.
  - **Technischer Preflight-Fehler:** keine **`pending`**-Job-Anlage; Video **`skipped`** mit **`skip_reason`** **`transcript_check_failed`** (später keine Blind-Kosten durch später sicher scheitende Runs).
- Mit **`auto_generate_script=false`** entstehen wie zuvor **keine** neuen **`script_jobs`** (Videos können **`seen`** ohne Job sein).
- **Keine automatische Skripterzeugung** im Check; Ausführung und Speicherung eines Skripts erfolgen in **Schritt 4** über **`POST /watchlist/jobs/{job_id}/run`**.
- **`GET /watchlist/jobs`** listet persistierte Jobs (Parameter `limit`, Standard 50; **keine** Ausführung).

**Schritt 4 – Script-Job manuell ausführen (`generated_scripts`)**

- **`POST /watchlist/jobs/{job_id}/run`** führt einen **`pending`**- oder **`failed`**-Job aus (nicht erneut bei **`completed`**, **`running`**, **`skipped`** — siehe HTTP-Status **409** bei Konflikten). **`job_id`** entspricht in V1 der **`video_id`** (wie bei **`GET /watchlist/jobs`**).
- Es wird dieselbe interne Pipeline wie **`POST /youtube/generate-script`** genutzt (**kein** HTTP-Selbstaufruf); bei Erfolg liegt das Skript in **`generated_scripts`** (Document-ID in V1 = **`job_id`**), der Job erhält **`generated_script_id`**, **`processed_videos.status`** kann **`script_generated`** werden.
- **`RunScriptJobResponse`:** `job`, optional **`script`**, **`warnings`**. Fehler sind über **`job.error`** und optional **`job.error_code`** standardisiert (z. B. **`transcript_not_available`**, **`script_generation_empty`**, **`script_generation_failed`**, **`firestore_write_failed`**); menschenlesbare Hinweise stehen in **`warnings`**. Selbst bei Preflight kann ein späterer **`run`** noch **`failed`** werden (Transkript zwischenzeitlich nicht mehr verfügbar). Transkript-/Parse-Probleme führen zu **`failed`** am Job und **keinem** Eintrag in **`generated_scripts`** (kein HTTP **500** für diese erwartbaren Fälle).
- Review für den Job erfolgt erst nach separatem **`POST /watchlist/jobs/{job_id}/review`** (**`review_results`**, wenn **`completed`** und **`generated_script_id`** gesetzt); in Schritt 4 bewusst kein automatisches Review oder Rendering; kein Scheduler.

**Phase 5.8–6.6 — Control Tower & Production Jobs**

- **`GET /watchlist/dashboard`**: Zähler (**`processed_videos_total`**, **`script_jobs`** je Status, **`generated_scripts_total`**) und **`health`**; Firestore **`RunAggregationQuery`**, bei Bedarf Fallback **bis 65 535 Docs** Stream-Zählung pro Abfrage. Kein Pipeline-Lauf.
- **`POST /watchlist/jobs/{job_id}/review`**: **`completed`**, **`generated_script_id`** und Skriptinhalt erforderlich; schreibt **`review_results`**, **`script_jobs.review_result_id`**, optional **`processed_videos.review_result_id`**; Speichern fehlgeschlagen → weiterhin **`200`** mit Warnung (**ScriptJob bleibt unverändert**).
- **`GET /watchlist/errors/summary`**, Retry/Skip, Pause/Resume, **`POST …/create-production-job`**: wie zuvor in Abschnitten 5.8–6.2 dokumentiert (**`production_jobs`**-Stub ohne Rendering).
- **`GET /production/jobs`** (`limit` 1–200), **`GET /production/jobs/{production_job_id}`**, **`POST /production/jobs/{production_job_id}/skip`**, **`POST /production/jobs/{production_job_id}/retry`**: nur Status in Firestore (**kein** Video-Render).
- **`POST /production/jobs/{production_job_id}/scene-plan/generate`**, **`GET /production/jobs/{production_job_id}/scene-plan`**: Szenenplan (**BA 6.6**) in Collection **`scene_plans`** (Doc-ID = **`production_job_id`**); deterministische Aufteilung aus **`generated_scripts`**-Kapiteln bzw. Fallback **`full_script`**; erste Generierung wird persistiert — erneuter Aufruf gibt den bestehenden Plan mit Warnhinweis zurück (idempotent).
- **`POST /production/jobs/{production_job_id}/scene-assets/generate`**, **`GET /production/jobs/{production_job_id}/scene-assets`**: Prompt-Entwürfe pro Szene (**BA 6.7**) in **`scene_assets`** (Doc-ID = **`production_job_id`**), auf Basis eines vorhandenen **`scene_plans`**; optionaler JSON-Body `{"style_profile": "documentary" | "news" | "cinematic" | "faceless_youtube" | "true_crime"}` (Default `documentary`). Keine Anbindung an Leonardo, Kling oder andere Renderer — nur Text-Prompts. Idempotent wie der Szenenplan.
- **`POST /production/jobs/{production_job_id}/voice-plan/generate`**, **`GET /production/jobs/{production_job_id}/voice-plan`**: Voice-Blöcke aus **`voiceover_chunk`** (**BA 6.8**, Collection **`voice_plans`**); optionaler Body `voice_profile`: `documentary` \| `news` \| `dramatic` \| `soft` (**kein** TTS). Idempotent wenn bereits vorhanden.
- **`POST /production/jobs/{production_job_id}/render-manifest/generate`**, **`GET /production/jobs/{production_job_id}/render-manifest`**: Maschinenmanifest (**BA 6.9**, **`render_manifests`**) aus Production-Bausteinen; ohne **`scene_assets`** kein Persist (**404** beim Generate); ohne Voice-Plan **Status** `incomplete` mit Warnungen.
- **`GET /production/jobs/{production_job_id}/export`**: BA 7.0 — JSON mit `generic_manifest`, `elevenlabs_blocks`, `kling_prompts`, `leonardo_prompts`, `thumbnail_prompt`, `capcut_timeline_hint`, `metadata` (lokal aus Firestore/Fallbacks — **ohne** API-Calls).
- **`POST /dev/fixtures/completed-script-job`**: nur für Dev/Test — bei **`ENABLE_TEST_FIXTURES=true`** (`.env`) ohne YouTube einen **`completed`** Job + **`generated_scripts`** (+ optional **`production_jobs`**); Job-IDs mit Präfix **`dev_fixture_`**. Ohne Flag: **403**.

```bash
curl -s -X POST "http://127.0.0.1:8000/watchlist/jobs/VIDEO_ID_HERE/run"
```

**Noch nicht umgesetzt (geplant):** Cloud-Scheduler-Deploy, Auto-Publish, echtes Voiceover-TTS/-Upload und echtes Video-Rendering inkl. Provider-Integration (Überblick [PIPELINE_PLAN.md](PIPELINE_PLAN.md)).

Beispiel **Kanal anlegen** (Kanal-URL mit `/channel/UC…` empfohlen):

```bash
curl -s -X POST "http://127.0.0.1:8000/watchlist/channels" ^
  -H "Content-Type: application/json" ^
  -d "{\"channel_url\":\"https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw\",\"check_interval\":\"manual\",\"max_results\":5}"
```

Liste:

```bash
curl -s "http://127.0.0.1:8000/watchlist/channels"
```

Manueller **Check**:

```bash
curl -s -X POST "http://127.0.0.1:8000/watchlist/channels/UC_x5XG1OV2P6uZZ5FSM9Ttw/check"
```

**Script-Jobs** (nur Liste, **kein Run**):

```bash
curl -s "http://127.0.0.1:8000/watchlist/jobs"
```

**Tests:** `tests/test_watchlist_models.py`, `tests/test_watchlist_service.py`, `tests/test_watchlist_check_channel.py`, `tests/test_watchlist_run_job.py`, `tests/test_watchlist_automation_phases.py`, **`tests/test_watchlist_control_tower.py`**, `tests/test_ba661_dev_fixtures.py`, `tests/test_ba68_6970_production_voice_render_export.py` (Firestore und RSS bzw. Script-Pipeline **gemockt**; keine Pflicht für Live-Firestore-Verbindung).


## 10. Beispiel: GET /health

```bash
curl http://127.0.0.1:8000/health
```

**Antwort:**
```json
{
  "status": "healthy"
}
```

## 11. Beispiel: POST /generate-script

```bash
curl -X POST http://127.0.0.1:8000/generate-script \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/news","target_language":"de","duration_minutes":10}'
```

## 12. Beispiel: POST /youtube/generate-script

Lokaler Test (Standard-Port `8000`). Verwende eine **Video-URL, für die Untertitel/Transkript bei YouTube verfügbar sind**. Unter Windows kann `curl` ein PowerShell-Alias sein; ggf. `curl.exe` nutzen.

```bash
curl -X POST http://127.0.0.1:8000/youtube/generate-script \
  -H "Content-Type: application/json" \
  -d '{"video_url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ","target_language":"de","duration_minutes":10}'
```

## 13. Beispiel: POST /youtube/latest-videos

Lokaler Test (Standard-Port `8000`, siehe Abschnitt „Server starten“). Beispiel mit **Kanal-URL** `https://www.youtube.com/channel/UC…` (robuster als `@handle`). Unter Windows kann `curl` ein PowerShell-Alias sein; ggf. `curl.exe` nutzen oder den Request mit einem anderen HTTP-Client senden.

```bash
curl -X POST http://127.0.0.1:8000/youtube/latest-videos \
  -H "Content-Type: application/json" \
  -d '{"channel_url":"https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw","max_results":5}'
```

**Hinweis:** Für diesen Endpoint sind keine zusätzlichen Secrets nötig; es werden hier keine Geheimnisse dokumentiert.

## 14. Beispiel-Response

```json
{
  "title": "",
  "hook": "",
  "chapters": [],
  "full_script": "",
  "sources": [],
  "warnings": []
}
```

> Der Antwortvertrag ist fix: `title`, `hook`, `chapters`, `full_script`, `sources`, `warnings`.

## 15. LLM-Modus vs. Fallback-Modus

- LLM-Modus: Aktiv, wenn `OPENAI_API_KEY` gesetzt ist und OpenAI erfolgreich antwortet.
- Antwort wird strikt als JSON geparst.
- Fallback-Modus: Aktiv, wenn kein API-Key vorliegt oder OpenAI fehlschlägt.
- Fallback liefert weiterhin valide Struktur, ohne neue Fakten zu erfinden.

## 16. Warnings erklärt

- `warnings` enthält Hinweise zu unsicherer Quelle, ungenügendem Inhalt oder Fallback-Einsatz.
- Warnings machen transparent, wenn der Output nicht die gewünschte Länge oder Qualität erreichen kann.

## 17. Lokale Tests

- App kompilieren:
  ```bash
  python -m compileall app
  ```
- Endpoint-Tests per `curl` oder Postman durchführen.
- Prüfe `GET /health`, mindestens einen `POST /generate-script` Request, bei Bedarf `POST /youtube/generate-script` (Video mit verfügbarem Transkript), `POST /youtube/latest-videos` (z. B. mit `/channel/UC…`). Watchlist: `tests/test_watchlist_*` (Firestore optional live testen, siehe [DEPLOYMENT.md](DEPLOYMENT.md)).

## 18. Docker / Cloud Run

**Cloud MVP v1 (URL, Deploy, Secret Manager, Online-Tests):** [DEPLOYMENT.md](DEPLOYMENT.md)

### Lokales Image

```bash
docker build -t news-to-video-api .
docker run --rm -p 8080:8080 news-to-video-api
# Health: curl http://127.0.0.1:8080/health
```

Der Container lauscht auf **0.0.0.0**. Der Port kommt aus der Umgebungsvariable **`PORT`** (Standard **8080**). So ist das Image mit **Google Cloud Run** kompatibel, wo `PORT` zur Laufzeit gesetzt wird.

### Google Cloud Run (Kurzüberblick)

1. **Artifact Registry** (oder Container Registry) vorbereiten und Image bauen/pushen, z. B.:
   ```bash
   docker build -t REGION-docker.pkg.dev/PROJECT/REPO/news-to-video-api:latest .
   docker push REGION-docker.pkg.dev/PROJECT/REPO/news-to-video-api:latest
   ```
2. **Service deployen** mit dem Image; Cloud Run setzt `PORT` automatisch — die App muss diesen Port verwenden (tut sie im Dockerfile).
3. **Secrets / Konfiguration** niemals ins Image backen. OpenAI optional über Laufzeit-Konfiguration:
   - `OPENAI_API_KEY` — nur als Umgebungsvariable oder Secret (z. B. Secret Manager an Cloud Run binden).
   - `OPENAI_MODEL` — optional als Umgebungsvariable (z. B. `gpt-4o-mini`), sonst Default aus `app/config.py`.
4. **Health Check**: Cloud Run prüft per HTTP; `GET /health` liefert `{"status":"healthy"}` mit HTTP 200 — geeignet als Liveness-/Startup-Kontext.

Ohne `OPENAI_API_KEY` läuft die API im dokumentierten Fallback-Modus.

## 19. Sicherheit / Secret Handling

- `.env` darf niemals in Git landen.
- Geheimnisse bleiben lokal und werden nicht im README dokumentiert.
- Nur `OPENAI_API_KEY` optional in `.env` konfigurieren.

## 20. Agent-Regeln / AGENTS.md Hinweis

- `AGENTS.md` enthält verbindliche Regeln für Agent-Verhalten und redaktionelle Qualität.
- Änderungen am Workflow oder an der Scriptqualität sollten dort dokumentiert werden.

## 21. Bekannte Grenzen

- Kein 100% verlässliches LLM für Faktenprüfung.
- Qualitätsgrenzen hängen von URL-Extraktion und Artikeltext ab.
- Manche Inhalte können kurz bleiben, wenn die Quelle nur wenig Text liefert.

## 22. Nächste Schritte

- Weitere Quellen-Extraktion und Artikelerkennung hinzufügen.
- Erweiterte Kapitel- und Timing-Logik implementieren.
- Tests für API-Responses und Fallback-Pfade ausbauen.
- Dokumentation und Agent-Regeln regelmäßig aktualisieren.
