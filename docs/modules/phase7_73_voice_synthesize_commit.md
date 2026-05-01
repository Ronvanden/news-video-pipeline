# Phase 7.3 — Voice Synthesize Commit (Firestore `production_files`)

**Kanone:** [docs/phases/phase7_voice_bauplan.md](../phases/phase7_voice_bauplan.md) Baustein 7.3  
**Nachfolger Preview:** Phase 7.2 — [phase7_72_voice_provider_minimal_slice.md](phase7_72_voice_provider_minimal_slice.md)

## Ziel

Persistente **Voice-Synthese** aus bestehendem `voice_plan`: Aufruf des TTS-Adapters (**OpenAI** über `VoiceSynthProvider`), Aktualisierung der Firestore‑Collection **`production_files`** für `file_type="voice"` **ohne Binärblobs** in Dokumenten (nur Metadaten, u. a. `synthesis_byte_length`, `status`).

## Endpoint

| Methode | Pfad | Body |
|---------|------|------|
| `POST` | `/production/jobs/{production_job_id}/voice/synthesize` | `VoiceSynthCommitRequest`: `dry_run`, `max_blocks` (1–50), `overwrite`, optional `voice` |

## Datenmodell

- **`ProductionFileRecord`**: optionales Feld **`synthesis_byte_length`** (≥ 0) für dokumentierte Offline‑Synthesegröße; **kein** Base64/File-Payload im Doc.
- **Document-ID:** bestehendes Muster **`_production_file_doc_id`** → `pfile_{pid_safe}_voice_{scene:04d}` (wie `plan_production_files_service`).

## Idempotenz

- **`overwrite=false`:** Zeile mit `status=ready` und `synthesis_byte_length>0` → **Skip** (Warning `[voice_commit:skipped_ready]`).
- **`overwrite=true`:** erneuter Provider‑Aufruf, Metadaten überschreiben.
- **Fehlende Zeile:** anlegen (**upsert**) mit plausiblem `storage_path` (`voice/{pid}/scene_XXX.mp3`), `provider_name` nach erfolgreicher Synthese **`openai`** (konkret implementierter MVP‑Provider).

## DoD / Gates

- `compileall`, `pytest`; `GenerateScriptResponse` unverändert.
