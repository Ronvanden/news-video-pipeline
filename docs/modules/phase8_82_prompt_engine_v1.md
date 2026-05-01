# Modulname

**Phase 8.2 — Prompt Engine V1** (Story-Engine-Nebenkanal, keine Makro-BA-8.x-Verwechslung)

---

## Ziel

Deterministische **Prompt-Expansion** und **Provider-Stubs** auf Basis des Phase-8.1-Scene-Blueprints (`POST /story-engine/scene-plan`), inkl. **Continuity Lock** und **Safety-/Negative-Merge** — ohne Bildgenerierung, ohne Persistenz, ohne Änderung von `GenerateScriptResponse`.

---

## Scope

- Modul [`app/visual_plan/prompt_engine.py`](../../app/visual_plan/prompt_engine.py) mit `build_scene_prompts_v1`.
- Pydantic-Modelle in [`app/models.py`](../../app/models.py): `ScenePromptsRequest` (erbt `StorySceneBlueprintRequest`), `SceneExpandedPrompt`, `ScenePromptsResponse`.
- HTTP: `POST /story-engine/scene-prompts` in [`app/routes/story_engine.py`](../../app/routes/story_engine.py).
- Policy: `SAFETY_NEGATIVE_SEGMENTS_V1`, `VISUAL_PROMPT_ENGINE_POLICY_V1` in [`app/visual_plan/policy.py`](../../app/visual_plan/policy.py).
- Warn-Codes in [`app/visual_plan/warning_codes.py`](../../app/visual_plan/warning_codes.py).

---

## Nicht-Ziele

- Keine Leonardo/OpenAI/Kling-API-Calls, keine Presigned-URLs, keine Blobs.
- Keine Firestore-/Production-Persistenz (folgt z. B. 8.3/8.4 / `visual_plans`).
- Keine Änderung an `POST /generate-script` / `POST /youtube/generate-script`.
- Kein Deploy-Pflichtgate.

---

## Dateien

| Pfad | Rolle |
|------|-------|
| [`app/visual_plan/prompt_engine.py`](../../app/visual_plan/prompt_engine.py) | Expansion, Provider-Stubs, Continuity, Negative-Merge |
| [`app/visual_plan/policy.py`](../../app/visual_plan/policy.py) | Safety-Segmente, Prompt-Engine-Policy-String |
| [`app/visual_plan/warning_codes.py`](../../app/visual_plan/warning_codes.py) | `[visual_prompt:…]` |
| [`app/models.py`](../../app/models.py) | Request/Response |
| [`app/routes/story_engine.py`](../../app/routes/story_engine.py) | Route |
| [`tests/test_phase8_82_prompt_engine.py`](../../tests/test_phase8_82_prompt_engine.py) | Tests |

---

## Endpoints

| Methode | Pfad | Request | Response | Vertrag stabil? |
|---------|------|---------|----------|-----------------|
| `POST` | `/story-engine/scene-prompts` | `ScenePromptsRequest` (wie 8.1 + `provider_profile`, `continuity_lock`) | `ScenePromptsResponse` | ja (additive Felder nur mit Doku-Bump) |

`GenerateScriptResponse` unberührt.

---

## Datenmodell

- **`ScenePromptsRequest`:** `StorySceneBlueprintRequest` + `provider_profile: leonardo | openai | kling` + `continuity_lock: bool`.
- **`ScenePromptsResponse`:** `policy_profile` (8.2), `prompt_engine_version`, Echo `provider_profile`, `continuity_anchor`, `blueprint_status` aus 8.1, `scenes[]` mit `positive_expanded`, `negative_prompt`, `continuity_token`, `warnings`.

---

## Akzeptanzkriterien

- [x] Gleiche Eingabe ⇒ byte-stabiler `ScenePromptsResponse` (Unit-Test).
- [x] Provider-Profile unterscheiden Positiv- und Negativ-Anteile deterministisch.
- [x] Continuity Lock nur wenn `continuity_lock=true`; Szene 2+ erhält `Continuity_lock:`-Suffix.
- [x] Safety-Segmente aus `SAFETY_NEGATIVE_SEGMENTS_V1` im `negative_prompt` je Szene.
- [x] `python -m compileall app` und `pytest` grün.

---

## Tests

| Test | Art | Befehl / Ablauf |
|------|-----|-----------------|
| Prompt Engine + Route | automatisch | `pytest tests/test_phase8_82_prompt_engine.py -q` |

Minimum: `python -m compileall app`; nach Router-Änderung `GET /health` optional.

---

## Deployment

Keine neuen Secrets oder Env-Pflichtfelder für diesen Slice.

---

## Risiken

| Risiko | Mitigation |
|--------|------------|
| „Provider_stub“ im Klartext suggeriert echten Adapter | Warnung `[visual_prompt:provider_profile_placeholder_v1]`; Doku Nicht-Ziele |
| Überlange Prompts | 8.1-Truncation im Blueprint bleibt maßgeblich |

---

## Abnahme

| Rolle | Name / Datum | OK |
|-------|----------------|-----|
| Technisch | | |
| Redaktion / Produkt | | |

---

## Verknüpfung Pipeline-Plan

**Phase:** Makro **Phase 8 — Bild- / Szenenplan** in [PIPELINE_PLAN.md](../../PIPELINE_PLAN.md).

**Status nach Merge:** Phase-8-Abschnitt in `PIPELINE_PLAN.md` zeigt 8.1 + 8.2 unter Story-Engine.

---

## DoD

- 8.2 Prompt Engine live unter `/story-engine/scene-prompts`; Governance: [phase8_image_sceneplan_bauplan.md](../phases/phase8_image_sceneplan_bauplan.md), Steckbrief 8.1 [phase8_81_visual_contract_minimal_slice.md](phase8_81_visual_contract_minimal_slice.md).
