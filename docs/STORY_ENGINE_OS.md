# Canonical Story OS (BA 9.9 — Zielbild)

Ein **„Story OS“** in diesem Repo bezeichnet das **integrale Zusammenspiel** der Bausteine **`app/story_engine/`**, Watchlist-Persistenz (`generated_scripts`, `review_results`, `script_jobs`), Export (`story_pack`, Connector-Downloads) und read-only Observation (**Founder Control Panel**). Es ist eine **konzeptionelle Oberfläche** für Redaktions-Workflows — **kein** Produkt mit eigenem Datenbank-Vertrag neben **`GenerateScriptResponse`**.

## Was dazu gehört

- **Templates und Blueprints** (`video_template`, Conformance-[`warnings`].
- **Hook Engine**, **Rhythm-Hinweise**, **Story-Struktur** (Nebenkanäle, nicht Six-Field-JSON).
- **Experiment-Registry** (`experiment_id`, `hook_variant_id`).
- **BA 9.7** Adaptive Template Optimization (`template_drift.py`, **`GET /story-engine/template-health`** / Control-Panel-Block `story_engine.template_optimization`).
- **BA 9.8** Story Intelligence (`story_intelligence_layer.py`, Feld `story_engine.story_intelligence`).

## Abgrenzung (kanonisch)

| Begriff | Bedeutung |
|---------|-----------|
| **BA 9.x** | Modulare **Story Engine** Releases im Code und in [PIPELINE_PLAN.md](PIPELINE_PLAN.md). |
| **Phase 9** | Makrophase **Packaging / MP4** — nicht hier. |
| **Phase 10** | Makrophase **Publishing** — nicht hier. |

## Operativer Kurzgraph

Siehe **[OPERATOR_RUNBOOK.md](../OPERATOR_RUNBOOK.md)** (Abschnitt *Story Engine (Daily)*). Deploy und Smoke konsolidiert in **[DEPLOYMENT.md](../DEPLOYMENT.md)** und **[docs/runbooks/cloud_run_deploy_runbook.md](runbooks/cloud_run_deploy_runbook.md)**.

## Abschlussstatus

Nach **BA 9.9** gilt die BA-**9.x-Reihe** unter produktbezogenen Änderungen am Plan als **„Kernbaum für Story-Reife geschlossen“** — Erweiterungen kommen ohne **BA 10 Story** ohne ausdrückliches Planungs-Deliverable (siehe [AGENTS.md](../AGENTS.md), Governance).
