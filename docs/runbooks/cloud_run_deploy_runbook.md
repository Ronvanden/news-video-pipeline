# Runbook — Cloud Run Deploy (`news-to-video-pipeline`)

Dauerhafter Ablauf für Deploys nach **Google Cloud Run**, abgestimmt mit [DEPLOYMENT.md](../../DEPLOYMENT.md) und [AGENTS.md](../../AGENTS.md).

---

## 1. Wann ein Deploy nötig ist

Ein neuer Deploy der Cloud-Run-Revision soll erfolgen, wenn sich etwas ändert, das die **laufende Online-Instanz** betrifft:

- **Backend-Code** unter `app/` (Routes, Business-Logik, Watchlist, Story Engine, Reviews, Konfig-Verbrauch zur Laufzeit).
- **Modelle / Schemas**, die Requests/Responses oder Persistenz-Verhalten im laufenden Dienst beeinflussen (z. B. `app/models.py`, Watchlist-/Production-Models), sofern nicht nur lokale/Test-only Änderungen.
- **Neue oder geänderte HTTP-Endpoints** oder geänderte Semantik bestehender Endpoints.
- **`requirements.txt`** (neue/abweichende Produktions-Abhängigkeiten).
- **Laufzeit-Konfiguration**: geänderte **Umgebungsvariablen**, **Firestore-Datenbank-ID**, **Secrets** (z. B. Secret Manager-Anbindung, OpenAI-Verhalten) — in der Regel zusätzlicher Deploy oder explizites Update der Cloud-Run-Service-Konfiguration.
- **`Dockerfile`**, sofern der Build-/Startpfad für Cloud Run beeinflusst wird.

Im Zweifel: wenn `gcloud run deploy --source .` einen neuen Build auslösen würde und die Änderung in diesem Image landet → Deploy einplanen.

---

## 2. Wann kein Deploy nötig ist

Kein Cloud-Run-Deploy, wenn Änderungen **den laufenden Container und dessen Konfiguration** nicht betreffen:

- **Reine Dokumentation** ohne Einfluss auf Build oder Laufzeit (z. B. Erklärungen nur in `docs/`).
- **`README.md`**, **`PIPELINE_PLAN.md`**, **`ISSUES_LOG.md`** (ohne Begleitung von Code/Konfig, die den Dienst ändert).
- **Cursor-Skills, Rules, Pläne** unter `.cursor/` (sofern kein Produktcode oder Dockerfile mitgeändert wird).
- Änderungen, die nur **lokale Entwicklung, Tests oder CI-Artefakte** betreffen, die **nicht** in das von Cloud Run gebaute Image gelangen.

---

## 3. Pre-Deploy Checks

Vor jedem Deploy im **Repository-Root** ausführen (angeschlossenes `origin/master` / relevanter Release-Branch, sauberer Arbeitsbaum).

```bash
git status
git pull
git log --oneline -1
python -m compileall app
python -m pytest
```

### Hinweise zu den Checks

| Schritt | Erwartung |
|--------|-----------|
| `git status` | Prefer „clean working tree“ für reproduzierbare Deploys; sonst Branch/Commit dokumentieren. |
| `compileall` | Muss ohne Fehler durchlaufen (Projektregel in AGENTS.md). |
| **`pytest`** | Im Repo ist **`pytest`** derzeit nicht in `requirements.txt` gebündelt. Wenn bei euch **`pytest`** installiert ist, deckt der Befehl optional zusätzliche Tests ab. **Kanonischer Testlauf ohne pytest:** wie in AGENTS.md: `python -m unittest discover -s tests -q` |

Zusätzlich sinnvoll vor dem ersten Deploy einer Session:

- **`gcloud`** erreichbar: `gcloud --version`
- Aktives GCP-Projekt: `gcloud config get-value project` (bei Bedarf `gcloud config set project PROJECT_ID`)

---

## Referenz — Deploy-Befehl und Smoke Tests

Der **kanonische** Deploy und die **Smoke-Tests** sind zentral beschrieben in:

- **[DEPLOYMENT.md](../../DEPLOYMENT.md)** — Abschnitt „Deploy (Beispielbefehl)“ (`gcloud run deploy news-to-video-pipeline --source …`) und „Online-Test mit curl“.

Nach erfolgreichem Deploy die dort dokumentierten `curl`-Aufrufe gegen **`GET /health`** und bei Bedarf **`POST /generate-script`** ausführen — keine Secrets in Shell-Logs.

---

## Governancenotiz

Neue Produktphasen oder BA-Änderungen: [PIPELINE_PLAN.md](../../PIPELINE_PLAN.md) und bei Incidents [ISSUES_LOG.md](../../ISSUES_LOG.md); Geheimnisse niemals in Runbook oder Shell-Befehle schreiben (nur Secret-**Namen** wie in DEPLOYMENT.md).
