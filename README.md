# News to Video Pipeline

## 1. Projektziel

Dieses MVP liefert eine lokale FastAPI-Anwendung, die aus einer Nachrichten-URL oder einem YouTube-Link ein strukturiertes YouTube-Skript erzeugt. Fokus liegt auf einer sicheren, modularen Pipeline mit optionaler LLM-Unterstützung und stabiler Fallback-Logik.

## 2. Aktueller MVP-Status

- FastAPI-App läuft lokal.
- **Cloud MVP v1:** Bereitstellung auf **Google Cloud Run** mit öffentlicher Service-URL, `GET /health` und `POST /generate-script` online nutzbar. Details, Deploy-Befehl, Secret Manager und Test-`curl`: [DEPLOYMENT.md](DEPLOYMENT.md).
- Endpoint `POST /generate-script` ist funktionsfähig.
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
- YouTube-Kanal-Discovery V1: neueste Videos strukturiert mit Heuristik (`score`, `reason`, `summary` aus Metadaten)

## 4. Projektstruktur

```
app/
├── __init__.py
├── main.py           # FastAPI app setup
├── config.py         # Settings und Umgebungsvariablen
├── models.py         # Pydantic Request-/Response-Modelle
├── utils.py          # Extraktion, Generierung, LLM und Fallback
├── youtube/          # Kanal-Auflösung, RSS, Scoring (ohne Data API)
└── routes/
    ├── __init__.py
    ├── generate.py   # /generate-script Endpoint
    └── youtube.py    # /youtube/latest-videos Endpoint

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

## 12. Beispiel: POST /youtube/latest-videos

Lokaler Test (Standard-Port `8000`, siehe Abschnitt „Server starten“). Beispiel mit **Kanal-URL** `https://www.youtube.com/channel/UC…` (robuster als `@handle`). Unter Windows kann `curl` ein PowerShell-Alias sein; ggf. `curl.exe` nutzen oder den Request mit einem anderen HTTP-Client senden.

```bash
curl -X POST http://127.0.0.1:8000/youtube/latest-videos \
  -H "Content-Type: application/json" \
  -d '{"channel_url":"https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw","max_results":5}'
```

**Hinweis:** Für diesen Endpoint sind keine zusätzlichen Secrets nötig; es werden hier keine Geheimnisse dokumentiert.

## 13. Beispiel-Response

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

## 14. LLM-Modus vs. Fallback-Modus

- LLM-Modus: Aktiv, wenn `OPENAI_API_KEY` gesetzt ist und OpenAI erfolgreich antwortet.
- Antwort wird strikt als JSON geparst.
- Fallback-Modus: Aktiv, wenn kein API-Key vorliegt oder OpenAI fehlschlägt.
- Fallback liefert weiterhin valide Struktur, ohne neue Fakten zu erfinden.

## 15. Warnings erklärt

- `warnings` enthält Hinweise zu unsicherer Quelle, ungenügendem Inhalt oder Fallback-Einsatz.
- Warnings machen transparent, wenn der Output nicht die gewünschte Länge oder Qualität erreichen kann.

## 16. Lokale Tests

- App kompilieren:
  ```bash
  python -m compileall app
  ```
- Endpoint-Tests per `curl` oder Postman durchführen.
- Prüfe `GET /health`, mindestens einen `POST /generate-script` Request und bei Bedarf `POST /youtube/latest-videos` (z. B. mit `/channel/UC…`).

## 17. Docker / Cloud Run

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

## 18. Sicherheit / Secret Handling

- `.env` darf niemals in Git landen.
- Geheimnisse bleiben lokal und werden nicht im README dokumentiert.
- Nur `OPENAI_API_KEY` optional in `.env` konfigurieren.

## 19. Agent-Regeln / AGENTS.md Hinweis

- `AGENTS.md` enthält verbindliche Regeln für Agent-Verhalten und redaktionelle Qualität.
- Änderungen am Workflow oder an der Scriptqualität sollten dort dokumentiert werden.

## 20. Bekannte Grenzen

- Kein 100% verlässliches LLM für Faktenprüfung.
- Qualitätsgrenzen hängen von URL-Extraktion und Artikeltext ab.
- Manche Inhalte können kurz bleiben, wenn die Quelle nur wenig Text liefert.

## 21. Nächste Schritte

- Weitere Quellen-Extraktion und Artikelerkennung hinzufügen.
- Erweiterte Kapitel- und Timing-Logik implementieren.
- Tests für API-Responses und Fallback-Pfade ausbauen.
- Dokumentation und Agent-Regeln regelmäßig aktualisieren.
