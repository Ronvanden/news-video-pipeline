# Cloud MVP v1 — Google Cloud Run

Stand: **MVP v1** (produktionsnaher Online-Betrieb mit optionaler OpenAI-Anbindung über Secret Manager).

## Service-URL (v1)

- **Basis-URL:** `https://news-to-video-pipeline-161409593172.europe-west3.run.app`
- **Health:** `GET /health`
- **Skript:** `POST /generate-script`

Die URL ist die öffentliche Cloud-Run-Service-Adresse; sie enthält **keine** Secrets.

## Aktueller v1-Status (Referenz-Test)

Mit einem konkreten Artikel und `duration_minutes=10` wurde u. a. Folgendes beobachtet:

| Feld | Wert (Beispiel) |
|------|-----------------|
| Test-URL | `https://www.tagesschau.de/ausland/europa/eu-facebook-instagram-100.html` |
| `duration_minutes` | 10 |
| Zielwortzahl (Plan) | 1400 (10 × 140 Wörter/Minute) |
| Ist-Wortzahl `full_script` | ca. 1300 |
| Modus | LLM (OpenAI aktiv) |
| Warnings (Auszug) | `Generated using LLM mode`, `LLM script expanded toward target length` |

`POST /generate-script` ist online funktionsfähig; der feste JSON-Antwortvertrag bleibt unverändert (`title`, `hook`, `chapters`, `full_script`, `sources`, `warnings`).

## Deploy (Beispielbefehl)

Voraussetzungen: `gcloud` konfiguriert, Projekt gewählt, Artifact Registry / Berechtigungen für Cloud Run und Secret Manager.

```bash
gcloud run deploy news-to-video-pipeline \
  --source . \
  --region europe-west3 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_MODEL=gpt-4o-mini,FIRESTORE_DATABASE=watchlist \
  --set-secrets OPENAI_API_KEY=OPENAI_API_KEY:latest
```

**Hinweise:**

- `OPENAI_MODEL` ist optional; ohne Setzen gilt der Default aus `app/config.py`.
- **`FIRESTORE_DATABASE`** muss zur **Named-Database-ID** in GCP passen (Standard in diesem Projekt: **`watchlist`**, nicht `(default)`).
- `--set-secrets` verbindet eine **Umgebungsvariable** mit einem **Secret-Manager-Eintrag** (siehe unten). Ersetze bei Bedarf Secret-Name und Version (`:latest` oder feste Version).
- Keine API-Schlüssel oder anderen Geheimnisse in Befehlen, Images oder Git ablegen.

## Secret Manager (Google Cloud)

1. Secret in **Secret Manager** anlegen (z. B. Name analog zur Variable `OPENAI_API_KEY` — der **Wert** verbleibt nur in GCP).
2. Dem **Cloud-Run-Dienstkonto** Zugriff auf dieses Secret gewähren (z. B. Rolle „Secret Manager Secret Accessor“ auf die betroffene Secret-Resource).
3. Beim Deploy `--set-secrets OPENAI_API_KEY=<SECRET_NAME>:<VERSION>` setzen, sodass die Laufzeit-Variable `OPENAI_API_KEY` aus dem Secret befüllt wird.

Ohne gesetztes Secret bzw. ohne Key läuft die Anwendung im dokumentierten **Fallback-Modus** (kein LLM).

## Firestore (Phase 5 Watchlist)

Für **Watchlist** (`POST/GET /watchlist/channels`, `POST /watchlist/channels/{channel_id}/check`) ist **Google Firestore** (Native Mode) im **gleichen GCP-Projekt** wie Cloud Run zu aktivieren.

- **Collections:** u. a. **`watch_channels`** (Kanal-Dokumente, Document-ID = YouTube-`channel_id`) und **`processed_videos`** (bekannte/übersprungene Videos, Document-ID = **`video_id`** — wird vom manuellen Check angelegt).
- **Named Database:** In der Konsole eine Firestore-Datenbank mit ID **`watchlist`** anlegen (oder `FIRESTORE_DATABASE` auf dieselbe ID setzen). Der Client nutzt `firestore.Client(database=…)` gemäß Konfiguration (`app/config.py`).
- **IAM:** Dem **Cloud-Run-Dienstkonto** Rolle **`roles/datastore.user`** (Zugriff auf Firestore/Datastore) zuweisen.
- **Lokal:** Projekt setzen (z. B. Umgebungsvariable `GOOGLE_CLOUD_PROJECT` auf die Projekt-ID); **Application Default Credentials** via `gcloud auth application-default login` (keine Service-Account-JSON-Dateien im Repository).
- Alternativ **Firestore-Emulator** für Entwicklung/Test (siehe Google-Dokumentation).

Keine Firestore- oder GCP-**Secret-Werte** in dieser Datei ablegen.

## Online-Test mit curl

**Health:**

```bash
curl -s "https://news-to-video-pipeline-161409593172.europe-west3.run.app/health"
```

**Skript (Beispiel wie Referenz-Test):**

```bash
curl -s -X POST "https://news-to-video-pipeline-161409593172.europe-west3.run.app/generate-script" \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"https://www.tagesschau.de/ausland/europa/eu-facebook-instagram-100.html\",\"target_language\":\"de\",\"duration_minutes\":10}"
```

Unter Windows/PowerShell kann `curl` ein Alias sein; ggf. `curl.exe` verwenden oder den Body wie in der README mit einem JSON-fähigen Client senden.

## Bekannte Grenzen (v1)

- **Qualität und Länge** des Skripts hängen stark vom **extrahierten Artikelmaterial** und vom gewählten **LLM** ab.
- Zielwortzahlen sind Planungsgrößen; die Pipeline kann bei knappem Quelltext oder Modellgrenzen **unter** der Zielspanne bleiben — das wird über `warnings` transparent gemacht (z. B. Expansion-Hinweise, Fallback).
- LLM-Ausgaben sind redaktionell und fachlich zu prüfen; die Pipeline erfindet bewusst keine Fakten im Fallback und weist auf Unsicherheiten hin.

## Weiterführend

- Lokale Entwicklung und API-Vertrag: [README.md](README.md)
- Agent- und Qualitätsregeln: [AGENTS.md](AGENTS.md)
