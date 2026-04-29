# News to Video Pipeline

## 1. Projektziel

Dieses MVP liefert eine lokale FastAPI-Anwendung, die aus einer Nachrichten-URL oder einem YouTube-Link ein strukturiertes YouTube-Skript erzeugt. Fokus liegt auf einer sicheren, modularen Pipeline mit optionaler LLM-Unterstützung und stabiler Fallback-Logik.

## 2. Aktueller MVP-Status

- FastAPI-App läuft lokal.
- Endpoint `POST /generate-script` ist funktionsfähig.
- `GET /health` liefert den Service-Status.
- OpenAI ist optional und wird über Umgebungsvariablen (lokal z. B. `.env`) aktiviert.
- Der LLM-Modus nutzt strikt geparste JSON-Ausgabe.
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

## 4. Projektstruktur

```
app/
├── __init__.py
├── main.py           # FastAPI app setup
├── config.py         # Settings und Umgebungsvariablen
├── models.py         # Pydantic Request-/Response-Modelle
├── utils.py          # Extraktion, Generierung, LLM und Fallback
└── routes/
    ├── __init__.py
    └── generate.py   # /generate-script Endpoint

Dockerfile
README.md
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

## 12. Beispiel-Response

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

## 13. LLM-Modus vs. Fallback-Modus

- LLM-Modus: Aktiv, wenn `OPENAI_API_KEY` gesetzt ist und OpenAI erfolgreich antwortet.
- Antwort wird strikt als JSON geparst.
- Fallback-Modus: Aktiv, wenn kein API-Key vorliegt oder OpenAI fehlschlägt.
- Fallback liefert weiterhin valide Struktur, ohne neue Fakten zu erfinden.

## 14. Warnings erklärt

- `warnings` enthält Hinweise zu unsicherer Quelle, ungenügendem Inhalt oder Fallback-Einsatz.
- Warnings machen transparent, wenn der Output nicht die gewünschte Länge oder Qualität erreichen kann.

## 15. Lokale Tests

- App kompilieren:
  ```bash
  python -m compileall app
  ```
- Endpoint-Tests per `curl` oder Postman durchführen.
- Prüfe `GET /health` und mindestens einen `POST /generate-script` Request.

## 16. Docker / Cloud Run

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

## 17. Sicherheit / Secret Handling

- `.env` darf niemals in Git landen.
- Geheimnisse bleiben lokal und werden nicht im README dokumentiert.
- Nur `OPENAI_API_KEY` optional in `.env` konfigurieren.

## 18. Agent-Regeln / AGENTS.md Hinweis

- `AGENTS.md` enthält verbindliche Regeln für Agent-Verhalten und redaktionelle Qualität.
- Änderungen am Workflow oder an der Scriptqualität sollten dort dokumentiert werden.

## 19. Bekannte Grenzen

- Kein 100% verlässliches LLM für Faktenprüfung.
- Qualitätsgrenzen hängen von URL-Extraktion und Artikeltext ab.
- Manche Inhalte können kurz bleiben, wenn die Quelle nur wenig Text liefert.

## 20. Nächste Schritte

- Weitere Quellen-Extraktion und Artikelerkennung hinzufügen.
- Erweiterte Kapitel- und Timing-Logik implementieren.
- Tests für API-Responses und Fallback-Pfade ausbauen.
- Dokumentation und Agent-Regeln regelmäßig aktualisieren.
