# Modulname

**Phase 8 — Visual Planning Contract & deterministisches Prompt-Pack (minimaler vertikaler Slice, Bausteine 8.2 + 8.4 vorbereitet, 8.3 persist)**

**Kanone:** [docs/phases/phase8_image_sceneplan_bauplan.md](../phases/phase8_image_sceneplan_bauplan.md)  
**Nicht Teil:** BA 8.0 Audit, Phase 9 Packaging, Phase 10 Publishing — siehe Bauplan Governance.

**Umsetzung Baustein 8.1 (Slice, keine Persistenz):** `POST /story-engine/scene-plan` unter [`app/routes/story_engine.py`](../../app/routes/story_engine.py); Paket [`app/visual_plan/`](../../app/visual_plan/). Persistenz **`visual_plans`** (**8.3**) und Production‑Routen folgen später.

---

## Ziel

Einen **stabilen, binärfreien Visual‑Plan** pro `production_job_id` bereitstellen (Firestore **`visual_plans`**) sowie **deterministisch** aus **`scene_assets`** (optional BA 9‑`story_structure` / `rhythm_hints` vom `generated_script`) ableitbare **Prompt-Pack‑Felder**, **ohne** externe Bildgeneratoren oder Stock‑APIs.

---

## Scope

- Python‑Package **`app/visual_plan/`** (Naming im PR konsistent haltbar auch als `app/visual/` wenn einheitlicher Import gewünscht): **Contracts**, **deterministische Builder‑Funktionen**, keine Netzwerk‑Calls.
- **Firestore** neue Collection **`visual_plans`**; Doc‑ID = **`production_job_id`** (wie `voice_plans`).
- **HTTP**: `POST /production/jobs/{production_job_id}/visual-plan/generate`, `GET /production/jobs/{production_job_id}/visual-plan` — analog bestehendem Voice‑Plan‑Pfad unter [production routes](../../app/routes/production.py).
- **Ausgaben** mit **`warnings`**, konsistent **`[visual_*]`**‑Präfixe (wie Voice‑Pattern mit `[voice_*]`).
- **`GenerateScriptResponse`**: **unverändert** ([AGENTS.md](../../AGENTS.md)).

---

## Nicht‑Ziele

- Keine Bild‑ oder Stock‑**API‑Integration** und keine Bild‑ oder Presigned‑**Binärdaten** in diesem Slice.
- Keine Änderung an **`POST /generate-script`** / **`POST /youtube/generate-script`**.
- Keine Aufweichung Phase‑10‑Upload‑Grenzen; kein FFmpeg/Render.
- **`production_files`‑Image‑Zeilen mit Status `ready`** — optional **zeitversetzt** (Baustein 8.5); nur wenn PR‑Größe es zulässt, sonst **separates PR**.

---

## Dateien

| Pfad | Rolle |
|------|--------|
| `app/visual_plan/` *(neu)* | Contracts, Ableitungs‑Builder, Konstanten/`warning_codes` optional |
| `app/watchlist/models.py` *(ändern)* | `VisualPlan`, `VisualSceneBlock`, Request/Responses (`VisualPlanGenerateRequest`, …) |
| `app/watchlist/firestore_repo.py` *(ändern)* | `VISUAL_PLANS_COLLECTION`, `get_visual_plan`, `upsert_visual_plan` |
| `app/watchlist/service.py` *(ändern)* | `generate_visual_plan`, `get_visual_plan_for_production_job`, ggf. idempotentes Verhalten wie `generate_voice_plan` |
| `app/routes/production.py` *(ändern)* | Registrierung der zwei neuen Routen |
| `tests/test_phase8_81_visual_plan_minimal.py` *(neu)* | Unit/API‑Mocks ohne externes Netz |
| optional später | `PIPELINE_PLAN.md` Endpoint‑Liste bei Merge der Routen aktualisieren |

---

## Endpoints

| Methode | Pfad | Request | Response | Vertrag stabil? |
|---------|------|---------|----------|-----------------|
| `POST` | `/production/jobs/{production_job_id}/visual-plan/generate` | `VisualPlanGenerateRequest` *(optional wie Voice: leere Defaults akzeptiert; z. B. `dry_run` nur wenn implementiert)* | `VisualPlanGenerateResponse`: `visual_plan`, `warnings` | ja (nach dokumentierter erste Version — Minor‑Felder additive only) |
| `GET` | `/production/jobs/{production_job_id}/visual-plan` | — | `VisualPlanGetResponse`: `visual_plan`, `warnings` | ja |

**Fehlersemantik:** fehlende Voraussetzungen (**kein Production Job**, **keine `scene_assets`**) ⇒ **404** mit erklärter **`warnings`** erste Zeile, **503** wenn Firestore laut Repo nicht erreichbar (Bestehendes Pattern).

---

## Datenmodell (Vorschlag für diesen Slice)

**`VisualSceneBlock`** (nested)

- `scene_number`: int ≥ 1
- `intent`: str — kurzer redaktioneller Visual‑Intent (**keine neuen behaupteten Fakten**)
- `subjects_safe`: str — zusammengefasste sichtbare Subjekte nur aus bereits vorhandenen Quell‑Strings („safe“ bedeutet **keine Halluzinations‑Garantie**, nur **Ableitungsdisziplin**)
- `style_tags`: `List[str]` — begrenzte, deterministisch sortierte Liste
- `source_class`: Literal `synthetic_placeholder` \| `stock_placeholder` *(Minimal‑Slice)*
- `risk_flags`: `List[str]` — maschinenlesbare Kennzeichen (z. B. `needs_human_review`)
- `prompt_pack`: Objekt oder flache Teilstrings — **`image_primary`**, optional `negative_hints` nur aus Policy‑Whitelist
- `licensing_notes`: str — **keine** Rechts‑Garantien
- `redaction_warnings`: `List[str]`

**`VisualPlan`**

- `id`, `production_job_id`
- `generated_script_id`: str *(aus `ProductionJob.generated_script_id` wenn gesetzt)*
- `scene_assets_id`: str *(gleich `production_job_id` wenn ID‑Konvention wie Voice vorliegt — im PR entscheiden)*
- `script_job_id`: str *(wie VoicePlan für Traceability)*
- `plan_version`: int ≥ 1
- `policy_profile`: str — z. B. **`visual_policy_v1_20260430`** (Konstante aus 8.1‑Doku)
- `status`: `draft` \| `ready` \| `failed`
- `blocks`: `List[VisualSceneBlock]`
- `warnings`: `List[str]`
- `created_at` / `updated_at`: ISO‑Strings UTC

---

## Akzeptanzkriterien

- [ ] Gleiche Inputs (`scene_assets` + gleiche optionale BA‑9‑Felder vom `generated_scripts`‑Lesepfad) ergeben **deterministischen** **`VisualPlan`** (**byte‑stabiler** Snapshot oder struktureller Vergleich in Tests).
- [ ] `POST …/generate` und `GET …` laden **persistiert**; zweiter **`POST`** verhält sich **idempotent** mit klar dokumentierter **Warning** („bereits vorhanden“ analog Render‑Manifest wenn gewählt — im PR konkret beschreiben).
- [ ] **Keine** Secret‑Ausgaben; **503** ohne Stacktrace‑Leak nach außen wie bestehende Production‑Endpoints.
- [ ] **`python -m compileall app`** und **`pytest`** grün für neue/geänderte Codepfade ([AGENTS.md](../../AGENTS.md)).

---

## Tests

| Test | Art | Befehl / Ablauf |
|------|-----|-----------------|
| Contract/Builder Unit | automatisch | `pytest tests/test_phase8_81_visual_plan_minimal.py -q` |
| Route Smoke (Mock Repo) | automatisch | `TestClient(app)` gegen neue Routen unter gemocktem `FirestoreWatchlistRepository` |
| Regression Voice/Manifest optional | automatisch bei Berührung | Bestehende Suite `pytest tests` ohne neue Schwellen‑Warnungen erhöhen |

Minimum laut Projektregeln zusätzlich: `python -m compileall app`; `GET /health` nach Router‑Änderung.

---

## Deployment

Keine neuen Secrets. Optional spätere ENV nur wenn Stock/Bild‑API angekoppelt (**nicht dieser Slice**) — dann nur **Namensliste** wie in [DEPLOYMENT.md](../../DEPLOYMENT.md), keine Werte.

---

## Risiken

| Risiko | Mitigation |
|--------|------------|
| Überlange **`scene_assets`** → große **`visual_plans`** Dokumente | Prompt‑Felder truncate mit **`[visual_*:truncated]`** Warnung konservativ dokumentieren |
| Redaktions‑/Rechtsüberinterpretation („sicher“ suggeriert) | Sprache **`subjects_safe` → Ableitungsquelle dokumentieren** im Bauplan 8.1; nie „rechtssicher“ formulieren |
| Scope‑Inflation Richtung Generatoren | PR‑Reviews strikt gegen **Nicht‑Ziele** |

---

## Abnahme

| Rolle | Name / Datum | OK |
|-------|----------------|-----|
| Technisch | | |
| Redaktion / Produkt | | |

---

## Verknüpfung Pipeline‑Plan

**Phase:** Makro **Phase 8 — Bild-/Szenenplan** in [PIPELINE_PLAN](../../PIPELINE_PLAN.md).

**Status nach Merge:** wenn Routen gemerged sind, **`PIPELINE_PLAN.md`** Endpunktliste und ggf. **„Relevante Dateien“** für Phase 8 aktualisieren; dieser Steckbrief **linken**.

---

## DoD‑Zusammenfassung Slice

- Contracts + Persistenz (**8.3** Grundlage) und deterministisches Pack (**8.4**) ohne externe Bild‑API (**8.8** dokumentiert Smoke mit `dry_run` falls implementiert).
