# BA 9.7 — Adaptive Template Optimization

Steckbrief nach [MODULE_TEMPLATE.md](../../MODULE_TEMPLATE.md). **Status: umgesetzt** (siehe Code `template_optimization_aggregate.py`).

**Kanone:** [PIPELINE_PLAN.md](../../PIPELINE_PLAN.md) (Abschnitt **BA 9.7**) und § **Nächste Priorität (Ausrichtung)**.

---

## Modulname

**BA 9.7 Adaptive Template Optimization** (Story Engine)

---

## Ziel

Template-Blueprint und produzierte Skripte **über die Zeit konsistent halten**: Drift sichtbar machen, **nachvollziehbare** Verbesserungs- und Refinement-Signale liefern, ohne produktives Verhalten ohne Freigabe zu überschreiben.

---

## Scope (Vorschlag erste Lieferung)

- **Template-Drift-Indikatoren** aus bestehenden Signalen (**`generated_scripts.template_conformance_level`**, **`template_definition_version`**, Blueprint-/Policy-Metadaten, **`warnings`-Präfixe**, optional **`story_structure`** / Rhythm-Hinweise) — Aggregation oder Read-API, **deterministisch** testbar.
- **„Template Health Snapshot“** lesbar für Ops (z. B. Erweiterung **`GET /production/control-panel/summary`** um ein kompaktes `template_health`-Feld oder neuer **`GET /story-engine/template-health`**) — konkrete Wahl erst bei Implementierung, **ohne Bruch bestehender Verträge**.
- **Performance-/Qualitäts-Scores** nur aus **bereits gespeicherten** Metriken (9.5a/9.6, Review, Hooks) — **keine neuen Secrets**, keine zusätzliche externe Attribution.

---

## Nicht-Ziele

- **`GenerateScriptResponse`** (die sechs Pflichtfelder) **nicht** erweitern oder umbrechen.
- Blueprints (**`story_engine`**, Template-Definitions) **nicht still** automatisch überschreiben; Auto-Refinement nur als **Vorschläge**/Flags/`warnings`.
- Keine Verschmelzung mit **Phase 9** (Packaging / MP4) oder **Phase 10** (Publishing); **BA 9.x** bleibt eigenständige Achse.

---

## Dateien

| Pfad | Rolle |
|------|--------|
| `app/story_engine/` | neue oder erweiterte Engine (z. B. `template_drift.py`, `template_health.py`) |
| `app/watchlist/control_panel.py` | optional Aggregation |
| `app/routes/story_engine.py` | optional neuer GET |
| `app/models.py` | Response-Models für neue/summarische Endpoints (bestehende Kernverträge unverändert) |
| `tests/test_ba97_*.py` | automatische Tests Drift-/Score-Fixtures |

---

## Endpoints

| Methode | Pfad | Request | Response | Vertrag stabil? |
|---------|------|---------|----------|-----------------|
| *TBD* | *optional* `GET /story-engine/template-health` oder Erweiterung Control-Panel | Query-Parameter minimal | strukturierte Drift-/Health-Zusammenfassung | ja (neuer Vertrag dokumentieren) |

**`POST /generate-script`** und **`POST /youtube/generate-script`**: keine Pflichtfelderänderungen.

---

## Datenmodell

- Lesend aus **`generated_scripts`**, optional **`experiment_registry`**, bestehenden Review-/Hook-Feldern.  
- **Neue Persistenz nur** wenn [PIPELINE_PLAN.md](../../PIPELINE_PLAN.md) und dieses Dokument einen Bedarf dokumentieren (z. B. optional **`template_health_snapshots`** o. ä. — noch **nicht beschlossen**).

---

## Akzeptanzkriterien

- [ ] HTTP 200 + valides JSON auf allen neuen Routen bei gültigen Eingaben; **keine 500** bei erwartbarem Datenfehlen/leerem Firestore-Stichprobensatz mit defensiver Antwort/`warnings`.
- [ ] **`python -m compileall app`** grün.
- [ ] Deterministische Unit-Tests mit Fixtures (gleiche Inputs → gleiche Drift-/Score-Ausgabe).
- [ ] Keine Änderung des festen **`GenerateScriptResponse`**-Schemas der Skript-Endpunkte.

---

## Tests

| Test | Art | Befehl / Ablauf |
|------|-----|----------------|
| Neue Unit-Suite BA 9.7 | automatisch | `python -m unittest discover -s tests -p 'test_ba97*.py'` |
| Regression Story Engine | automatisch | `python -m unittest tests.test_ba9396_story_maturity` |
| Smoke API | manuell | `GET /health`; ggf. neuer Story- oder Control-Panel-Endpoint |

---

## Deployment

- Voraussichtlich **keine neuen Secrets**; falls zeitbezogene Aggregation: nur Standard- **`ENABLE_*`** / bereits vorhandene Firestore-Anbindung.  
- Größenordnung Payload: Aggregation auf **begrenzte Stichproben** (analog bestehendem Control Panel).

---

## Risiken

| Risiko | Mitigation |
|--------|------------|
| Falsche Drift-Alarms bei wenigen Daten | Mindest-Stichprobgrößen, **`warnings`** statt Hard-Fail |
| Scope-Creep „Auto-Learning“ | klar gegen **BA 9.8** abgrenzen; hier nur Signals/Health |
| Latenz-Control-Panel | optionale neue Route statt immer teurer Aggregation |

---

## Abnahme

| Rolle | Name / Datum | OK |
|-------|----------------|-----|
| Technisch | | |
| Redaktion / Produkt | | |

---

## Verknüpfung Pipeline-Plan

**BA / Phase:** **BA 9.7** (Story Engine — **nicht** Phase 9/10).

**Status nach Merge:** `PIPELINE_PLAN.md`: **BA 9.7** von **planned** → **done** (sobald Akzeptanzkriterien erfüllt); ggf. **§ Nächste Priorität** um nächstes Arbeitspaket (**BA 9.8**) ergänzen.
