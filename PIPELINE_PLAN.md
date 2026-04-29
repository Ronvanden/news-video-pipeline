# Pipeline-Plan — News- und YouTube-to-Video

Ziel dieses Dokuments ist eine **kontrollierte Weiterentwicklung**: Phasen, Status, Akzeptanzkriterien, Tests und dokumentierter Fehler-Rücklauf (siehe [ISSUES_LOG.md](ISSUES_LOG.md)).  
Neue fachliche Bausteine werden idealerweise zuerst mit [MODULE_TEMPLATE.md](MODULE_TEMPLATE.md) skizziert.

---

## Gesamtziel

Eine **zuverlässige, modulare Pipeline** von **Quellen** (Nachrichten-URLs, YouTube) zu **strukturierten, redaktionell nutzbaren Skripten** für längere Videoformate — mit **optionaler LLM-Nutzung**, **stabilem Fallback ohne API-Key**, **festem JSON-Vertrag** für Skript-Endpoints und klarer **Warn- und Fehlerlogik**. Spätere Phasen erweitern um Prüfung, Monitoring, Persistenz, Medienproduktion und Veröffentlichungsvorbereitung — ohne die bestehenden API-Verträge ungeplant zu brechen.

---

## Aktueller Stand (Kurz)

| Bereich | Stand |
|--------|--------|
| FastAPI, Health | Lokal und Cloud Run MVP v1 nutzbar |
| Skript aus Artikel-URL | `POST /generate-script` — Extraktion, LLM optional, Fallback |
| YouTube Transkript → Skript | `POST /youtube/generate-script` — gleicher Response-Vertrag wie Generate |
| Kanal-Discovery | `POST /youtube/latest-videos` — RSS, Scoring, ohne Data API |
| Review / Originalität | `POST /review-script` — V1 heuristisch (Phase 4 **done**) |
| Persistenz Jobs / Watchlist / Voice / Bild / Render / Publish | Geplant (Watchlist/Phase 5: siehe Abschnitt Phase 5 — Firestore-Plan, noch nicht implementiert) |

Details zu Deploy und Tests: [README.md](README.md), [DEPLOYMENT.md](DEPLOYMENT.md).  
Agenten- und Qualitätsregeln: [AGENTS.md](AGENTS.md).

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
| 7 | Voiceover | **planned** |
| 8 | Bild- / Szenenplan | **planned** |
| 9 | Video Packaging | **planned** |
| 10 | Veröffentlichungsvorbereitung | **planned** |

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
| **Status** | **next** (nächste geplante Implementierung — Umsetzung noch offen, siehe Detailplan unten) |
| **Ziel (Kurz)** | YouTube-Kanäle dauerhaft speichern, regelmäßig oder manuell prüfen, neue Videos erkennen, Kandidaten bewerten, Script-Jobs vorbereiten und Status führen — aufbauend auf bestehender RSS-/Discovery-Logik (`POST /youtube/latest-videos`). |
| **Relevante Dateien (geplant)** | `app/youtube/*` (Wiederverwendung `get_latest_channel_videos` u. a.), `app/routes/youtube.py`, `app/utils.py`, `app/review/*`; neu u. a. `app/watchlist/`, `app/routes/watchlist.py` |
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
| **review_results** | Ergebnisse analog **`POST /review-script`** (`risk_level`, `originality_score`, Flags, Issues, Recommendations, `warnings`). |

#### Geplante Endpoints (Phase 5 V1)

| Methode | Pfad | Zweck |
|---------|------|--------|
| `POST` | `/watchlist/channels` | Kanal in Watchlist anlegen |
| `GET` | `/watchlist/channels` | Watchlist auflisten |
| `POST` | `/watchlist/channels/{channel_id}/check` | Einen Kanal manuell prüfen |
| `POST` | `/watchlist/run-check` | Alle aktiven Kanäle prüfen (mit Drossel/Cap nach Implementierung) |
| `GET` | `/watchlist/jobs` | Script-Jobs auflisten |
| `POST` | `/watchlist/jobs/{job_id}/run` | Einen Script-Job manuell ausführen (Skript persistieren; optional Review wie konfiguriert) |

(Response-Verträge der Watchlist-Endpunkte sind neu; bestehende Endpoints **`/generate-script`**, **`/youtube/*`**, **`/review-script`** bleiben unverändert.)

#### V1-Entscheidungen (Pflichtlage Plan)

| Thema | Entscheid |
|-------|-----------|
| Neue Videos → Ausführung | Nach Check entstehen **nur `pending` Script-Jobs** — **keine** automatische Ausführung aller Jobs in V1. |
| Job-Ausführung | **Manuell** über **`POST /watchlist/jobs/{job_id}/run`** (Kosten-/Kontrollgründe, weniger Blind-LLM-Last). |
| Veröffentlichung | **Kein Auto-Publish** |
| Produktion | **Keine Voiceover-/Video-Produktion** in Phase 5 |

#### Scheduler und Auth (nach V1)

- **Cloud Scheduler:** erst **ab V1.1** vorgesehen (z. B. wiederkehrender Aufruf von `POST /watchlist/run-check`). In V1 wird `check_interval` nur gespeichert/ausgewertet, wo die Implementierung es vorsieht; kein Produktzwang Scheduler in V1.
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

1. Firestore aktivieren — Repository — **Watchlist CRUD** (Kanälelisten).
2. **Manueller Channel Check** — **`processed_videos`** füllen / Duplikatlogik.
3. **Script-Jobs anlegen** bei neuen Videos (Konfigurationsabhängig).
4. **Job manuell ausführen** — **`generated_scripts`** persistieren (intern Logik wie `/youtube/generate-script`).
5. Optional **Review** aus Job heraus — **`review_results`** speichern.
6. **Scheduler** später (V1.1+) mit Absicherung.

---

### Phase 6 — Script Job Speicherung

| | |
|--|--|
| **Status** | **planned** |
| **Hinweis zur Abgrenzung** | Persistenz von Script-Jobs, generierten Skripten und Review-Ergebnissen wird in **Phase 5** (Firestore-Collections `script_jobs`, `generated_scripts`, `review_results` u. a.) bereits **mitgeplant und später umgesetzt**. **Phase 6** bleibt für **Erweiterungen** reserviert: z. B. explizite **Job-Versionierung**, erweiterte **Re-Runs**/Historie, alternative Backends oder orchestrierungsseitige Erweiterungen — ohne Phase-5-V1 doppelt zu definieren. |
| **Ziel** | Über Phase 5 hinaus: erweiterte Job-Lifecycle-/Versionierungskonzepte (Details bei Bedarf MODULE_TEMPLATE). |
| **Endpoints** | *abhängig von Erweiterung* |
| **Relevante Dateien** | Anknüpfung an Phase-5-Watchlist/Job-Speicher; ggf. `app/config.py` |
| **Akzeptanzkriterien** | Keine Secrets im Repo; Migration/Schema dokumentiert; idempotente Job-Erstellung wo sinnvoll. |
| **Bekannte Grenzen** | Cloud Run bleibt zustandslos; persistente Arbeit liegt in Phase 5/externem Store. |
| **Nächster Schritt** | Nach Abschluss der Phase-5-Grundfunktion entscheiden, ob Phase 6 nur dokumentarisch zusammengeführt wird oder eigenes Increment. |

---

### Phase 7 — Voiceover

| | |
|--|--|
| **Status** | **planned** |
| **Ziel** | Aus `full_script` oder Kapiteln Audio erzeugen (TTS-Anbieter oder lokal), Dateiformate und Qualitätsparameter festlegen. |
| **Endpoints** | *geplant* |
| **Relevante Dateien** | *neu* |
| **Akzeptanzkriterien** | API-Keys nur über Secret Manager / `.env` (nicht dokumentiert); Kosten und Laufzeitbudget beachten. |
| **Bekannte Grenzen** | Stimme, Aussprache, Markenrechte Drittanbieter. |
| **Nächster Schritt** | Anbieter evaluieren; Pilot mit kurzem Skript. |

---

### Phase 8 — Bild- / Szenenplan

| | |
|--|--|
| **Status** | **planned** |
| **Ziel** | Szenen aus Kapiteln ableiten (Bildprompts, Stock, generierte Bilder — policyabhängig). |
| **Endpoints** | *geplant* |
| **Relevante Dateien** | *neu* |
| **Akzeptanzkriterien** | Lizenz und Quellenangaben pro Asset nachvollziehbar; keine ungeprüften Rechtsclaims in der Pipeline. |
| **Bekannte Grenzen** | Stock-APIs und Generatoren haben Nutzungsbedingungen. |
| **Nächster Schritt** | Nach Voiceover oder parallel nur mit klarem Schnitt. |

---

### Phase 9 — Video Packaging

| | |
|--|--|
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

## Workflow: Plan ↔ Umsetzung ↔ Fehler

1. **Vor größeren Änderungen** dieses Dokument und die betroffene Phase prüfen.  
2. **Neues Modul**: [MODULE_TEMPLATE.md](MODULE_TEMPLATE.md) ausfüllen und in der Phase verlinken.  
3. **Nach Incidents oder wiederkehrenden Bugs**: [ISSUES_LOG.md](ISSUES_LOG.md) aktualisieren (Datum, Ursache, Fix, Commit-Referenz).  
4. **Commits**: nur mit Tests/Checks laut [AGENTS.md](AGENTS.md) und Statusabgleich hier.

Letzte inhaltliche Überarbeitung dieser Plan-Datei: **2026-04-29** — Detailplan Phase 5 (Watchlist / Channel Monitoring) ergänzt; weiterhin bei inhaltlichen Phasenänderungen das Datum im Git-Commit dokumentieren.
