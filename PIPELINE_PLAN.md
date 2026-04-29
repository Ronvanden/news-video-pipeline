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
| Review / Originalität | Noch nicht implementiert |
| Persistenz Jobs / Watchlist / Voice / Bild / Render / Publish | Geplant |

Details zu Deploy und Tests: [README.md](README.md), [DEPLOYMENT.md](DEPLOYMENT.md).  
Agenten- und Qualitätsregeln: [AGENTS.md](AGENTS.md).

---

## Phasenübersicht

| # | Phase | Status |
|---|--------|--------|
| 1 | Skriptmotor | **done** |
| 2 | YouTube Channel Discovery | **done** |
| 3 | YouTube Transcript-to-Script | **done** |
| 4 | Script Review / Originality Check | **next** |
| 5 | Watchlist / Channel Monitoring | **planned** |
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
| **Status** | **next** (Planung für V1 abgestimmt; Implementierung folgt gesondertem Bauauftrag) |
| **Ziel** | Zusätzliche Prüfstufe vor Voiceover/Bild/Video: Nähe zum Quelltext, lange ähnliche Passagen, grobe Struktur-/Einordnungs-Signale — **hybrid** (lokale Heuristiken + optionaler LLM-Teil für qualitative Empfehlungen). **`GenerateScriptResponse` von `/generate-script` und `/youtube/generate-script` bleibt unverändert**; Review als eigener Endpoint und Vertrag. |
| **Endpoints (geplant)** | `POST /review-script` — Request: u. a. `source_url`, `source_type`, `source_text`, `generated_script` (inhaltlich = `full_script` aus Generate), `target_language`; Response: u. a. `risk_level`, `originality_score`, `similarity_flags`, `issues`, `recommendations`, `warnings` (Detail siehe Projektplanung / MODULE_TEMPLATE). |
| **Relevante Dateien (geplant)** | Neu: `app/review/` (`__init__.py`, `originality.py`, ggf. `llm_review.py`, `service.py`); neu: `app/routes/review.py`; Anbindung in `app/main.py`; Modelle in `app/models.py`; Doku `README.md` nach Implementierung. |
| **Akzeptanzkriterien (V1-Zielbild)** | 200 oder validierter Client-/Fehlerpfad ohne unerwartete 500; kein Secret-/.env-Zugriff im Review-Modul; `risk_level` nachvollziehbar aus Heuristik (+ ggf. LLM nur als Zusatzsignal); bei identischem `source_text` und `generated_script` → `high`; eigenständiges Skript → `low` oder `medium` möglich; konkrete `recommendations`; `python -m compileall app` grün; Tests mindestens für identisch / stark ähnlich / eigenständig + YouTube-Strenge + fehlender Kurz-`source_text`. |
| **Bekannte Grenzen** | Keine Rechtsberatung, keine Freigabe zum Veröffentlichen; keine dauerhafte Speicherung von `source_text` ohne spätere Produktentscheidung; Heuristiken können false positive/negative liefern — menschliche Redaktion bleibt maßgeblich. |
| **Nächster Schritt** | [MODULE_TEMPLATE.md](MODULE_TEMPLATE.md) für „Script Review API“ ausfüllen; Implementierungs-Bauauftrag: Modelle, `app/review/*`, Route registrieren, Tests, README-Abschnitt. |

---

### Phase 5 — Watchlist / Channel Monitoring

| | |
|--|--|
| **Status** | **planned** |
| **Ziel** | Kanäle/Themen überwachen, neue Kandidaten-Videos erkennen, ggf. Benachrichtigung oder Queue — aufbauend auf RSS/Discovery. |
| **Endpoints** | *geplant* |
| **Relevante Dateien** | v. a. `app/youtube/*`; ggf. Scheduler/Cron extern zu Cloud Run |
| **Akzeptanzkriterien** | Kein Dauer-Polling ohne Konzept zu Rate-Limits; Speicherung sensibler Daten nur nach Datenschutz-Folgenabschätzung. |
| **Bekannte Grenzen** | YouTube-RSS allein liefert keine Echtzeit-Garantie; Handles weiterhin fragil. |
| **Nächster Schritt** | Nach Phase 4 oder parallel mit klar getrenntem Scope entscheiden. |

---

### Phase 6 — Script Job Speicherung

| | |
|--|--|
| **Status** | **planned** |
| **Ziel** | Jobs/Versionen persistieren (Datenbank oder Object Storage), Status (queued, done, failed), Re-Runs. |
| **Endpoints** | *geplant* |
| **Relevante Dateien** | *neu* — z. B. `app/jobs/`, Konfiguration in `app/config.py` |
| **Akzeptanzkriterien** | Keine Secrets im Repo; Migration/Schema dokumentiert; idempotente Job-Erstellung wo sinnvoll. |
| **Bekannte Grenzen** | Cloud Run ist zustandslos ohne externe DB. |
| **Nächster Schritt** | Technologie wählen (z. B. Firestore, Postgres); MODULE_TEMPLATE. |

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

Letzte inhaltliche Überarbeitung dieser Plan-Datei: bei Bedarf bei jeder Phasenänderung das Datum im Git-Commit dokumentieren.
