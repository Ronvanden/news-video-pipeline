## Modulname

Story Structure Sidechannel (**BA 9.3.3**)

---

## Ziel

Strukturierte, **deterministische** Metadaten (Kapitelrollen, Pacing-/CTA-Hinweise, Template-/Gate-Meta) **neben** dem festen `/generate-script`-Antwort-Vertrag bereitstellen — für Persistenz (`generated_scripts.story_structure`), Export (`story_pack`) und spätere Produktionsschritte.

---

## Scope

- `app/story_engine/story_structure.py` → `build_story_structure_v1` (schema_version `"1"`).
- Anbindung in Watchlist **`run_script_job`** nach erfolgreichem Hook-Lauf gemeinsam mit **Rhythm (9.4)** und **Conformance-Gate**.
- Connector/Download **`story_pack`**-Block konsolidiert gleiche Daten.

---

## Nicht-Ziele

- Kein neues Pflichtfeld in **`GenerateScriptResponse`**.
- Kein Ersatz für `scene_plans` / Schnittautomatik (**Phase 9**).
- Keine automatische Veröffentlichung oder Hooks, die ohne Policy produktiven Text überschreiben.

---

## Dateien

| Pfad | Rolle |
|------|-------|
| `app/story_engine/story_structure.py` | Nebenkanal-Builder |
| `app/watchlist/service.py` | Persistenz nach Job-Run |
| `app/watchlist/connector_export.py` | `build_story_pack_dict` |
| `app/watchlist/export_download.py` | `provider_templates["story_pack"]` |

---

## Endpoints

| Methode | Pfad | Request | Response | Vertrag stabil? |
|---------|------|---------|----------|----------------|
| POST | `/story-engine/rhythm-hint` | `RhythmHintRequest` | `RhythmHintResponse` | ja (Story-Nebenkanal) |

---

## Datenmodell

Firestore-Dokument `generated_scripts` (Erweiterung, rückwärtskompatibel):

- `story_structure`: `Dict` mit `schema_version`, `chapter_roles`, `cta_placement_hint`, `meta.template_definition_version`, `meta.template_conformance_gate`, optional `rhythm`-Unterbaum (wenn 9.4 aktiv).

Export: `story_pack`-Objekt analog `build_story_pack_dict`.

---

## Akzeptanzkriterien

- [ ] Persistenz schreibt `story_structure` bei Watchlist Job-Completion (wenn Pfad aktiv).
- [ ] `GenerateScriptResponse` bleibt sechs Kernfelder ohne Schema-Bruch.
- [ ] Rhythm-/Story-Pack-Felder nur Nebenkanal; Transparenz über `warnings` wo nötig (bestehende Projektregeln).

---

## Tests

| Test | automatisch |
|------|-------------|
| `tests/test_ba9396_story_maturity.py` | `python -m unittest tests.test_ba9396_story_maturity` |

Minimum: `python -m compileall app`.

---

## Deployment

Keine zusätzlichen Secrets. Firestore-Schreibfelder sind abwärtskompatibel (fehlende Keys → Defaults beim Lesen über Pydantic).

---

## Risiken

Übermäßig große `story_structure`-Dictionaries — Begrenzen (Kapitel-Caps bereits im Builder). Firestore Dokumentgrößen beobachten.
