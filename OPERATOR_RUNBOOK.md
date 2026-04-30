# Operator Runbook (BA 8.9)

Kurzleitfaden für Founder/Betrieb — **ohne Secrets**, **ohne `.env`-Inhalt**. Logik und Endpunkte siehe `README.md` und `PIPELINE_PLAN.md`.

---

## Daily Check

- `GET /health` — Dienst lebt.
- `GET /watchlist/dashboard` — Kanäle/Jobs/Skripte-Zähler und letzte Metazeitstempel.
- `GET /production/control-panel/summary` — Audits, Eskalationen, Recovery-Stichprobe, Kostensätze.

## Dry Run

- `POST /production/automation/run-daily-cycle` mit `"dry_run": true` — keine Firestore-Schreibvorgänge; prüft Zykluslogik.
- `POST /providers/configs/seed-defaults` ohne `apply_writes=true` — nur Vorschau der Standard-Provider-Slots (BA 8.6).

## Monitoring

- `GET /production/monitoring/summary` — offene Audit-Schweregrade, Recovery-Hinweise.
- `GET /watchlist/errors/summary` — Stichprobe `error_code` / `skip_reason` bei Script-Jobs und `processed_videos`.

## Audit

- `POST /production/audit/run` — `pipeline_audits` auffrischen (Gap-/Stuck-Erkennung).
- `GET /production/audit` — Liste filtern nach `status` / `severity`.

## Recovery

- `POST /production/jobs/{id}/recovery/retry` mit Body `step` (`scene_plan`, `scene_assets`, `voice_plan`, `render_manifest`, `execution`, `costs`, `files`, `full_rebuild`) — **nicht** verwechseln mit Legacy `POST /production/jobs/{id}/retry` (nur Status-Anhebung).

## Transcript Missing

- Symptom: `skip_reason` / `input_quality_status` = `transcript_missing` (Legacy oft `transcript_not_available`).
- Aktion: kein blindes Re-Run ohne neue Quelle; Video ggf. manuell bewerten oder überspringen; Hooks siehe `app/watchlist/input_quality_guard.py` (`fallback_hooks`).

## Provider Failure

- `GET /providers/status` — kombiniert Stub-Liste aller registrierten Namen mit `validate_provider_runtime_health` (enabled ohne `dry_run`, Budgetüberschreitung, `status=error`).
- Konfiguration nur über `POST /providers/configs/{name}/upsert` — **keine API-Keys** in Firestore.

## Cost Spike

- `GET /production/jobs/{id}/costs` — `over_budget_flag`, `cost_variance`, `estimated_profitability_hint` (grob, BA 8.7).
- Bei wiederholten Spikes: Szenenanzahl, `duration_minutes` am Script-Job und tatsächliche Anbieterpreise außerhalb der Heuristik prüfen.

## Failed Script

- `GET /watchlist/jobs` — Jobs mit `failed` und `error_code` / `input_quality_status`.
- `POST /watchlist/jobs/{job_id}/retry` — zurück auf `pending`, wenn Inhalt/Ingestion bereinigt wurde.

## Stuck Job

- `POST /production/status/normalize/run` — Eskalationen/`pipeline_escalations`, Stuck-Heuristiken.
- `GET /production/status/escalations` — letzte Einträge.

## Escalation Interpretation

- Schwere und Kategorie aus `pipeline_escalations`; `retry_reason` und Backoff aus Normalizer (BA 8.3). Kein automatisches Publishing.

## Golden Run Check

- Manuell oder per Fixture: ein Produktionsjob durch den Pfad in `GOLD_PRODUCTION_STANDARD.md`; Regression: `tests/test_ba88_full_production_run.py`.

---

## Nützliche Smoke-Tests (lokal)

```bash
python -m compileall app
python -m unittest discover tests
```
