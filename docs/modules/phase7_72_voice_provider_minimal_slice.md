# Modulname

**Phase 7.2 — Voice Provider Contract + Minimal Vertical Slice** (TTS-Adapter + eine schmale End-to-End-Nadel **lesend** aus `voice_plans`, **ohne** dauerhafte Audio-Persistenz in Firestore — Speichern folgt **Baustein 7.3**).

---

## Ziel

Einen **herstellerunabhängigen TTS-Vertrag** festlegen und **mindestens eine echte Adapter-Implementierung** (priorisiert: **OpenAI Speech API**) bereitstellen, plus einen **öffentlichen Produktions-Endpoint**, der einen **persistierten** `VoicePlan` einliest, **deterministisch** wenige Abschnitte synthetisiert und die Antwort als **konfigurierbare Vorschau** (Metadaten + optional begrenzte Audiodaten) zurückgibt — **ohne** Bruch von `GenerateScriptResponse` und **ohne HTTP 500** bei erwartbarem Provider-/Key-Fehler.

---

## Scope

| Lieferobjekt | Beschreibung |
|--------------|---------------|
| **Provider-Vertrag** | Abstrakte Schnittstelle (Python `typing.Protocol` oder ABC) **`VoiceSynthProvider`**: Eingaben (Sprache/Text/Modell/Stimmen-ID soweit unterstützt), Ausgang (**`bytes`**, MIME-Type, geschätzte Dauer, strukturierte `warnings`). Unterstützung für **chunkweise** Aufrufe (ein `VoiceBlock` pro Request im MVP ausreichend). |
| **OpenAI-TTS Adapter** | Konkrete Implementierung gegen die **öffentlich dokumentierte** OpenAI **`/audio/speech`**-API oder vergleichbares Produkt-Endpunkt-Schema; verwendet bestehendes **`OPENAI_API_KEY`** / `Settings.openai_api_key` (wie LLM bereits). |
| **`dry_run`** / No-Network | Request-Flag oder Config: **kein** externer HTTP-Call → Antwort nur mit strukturellen Hinweisen (zur Nutzung in Tests und Sanity-Checks). |
| **Minimal Vertical Slice Route** | **Neuer** FastAPI-Endpunkt (siehe unten): liest **`voice_plan`** für `production_job_id` über bestehendes Repository-Service-Muster; führt Provider für **`max_blocks` ≥ 1** (Default 1) aus; **persistiert keine Audiodatei** auf `production_files` / kein GCS in **7.2** (das ist **Baustein 7.3**). |
| **Antwort-Vertrag** | Neuer Pydantic-Response (**eigenes Modell**, nicht GenerateScriptResponse): Felder wie `chunks[]`, `warnings[]`, pro Chunk `scene_number`, `byte_length`, `content_type`; optional **`audio_base64`** nur wenn **`ENABLE_VOICE_SYNTH_PREVIEW_BODY`** (oder gleichwertig in `Settings`) aktiv und **`max_preview_bytes`** überschreitet nicht dokumentiertes Limit (**z. B. ≤ 262144**), sonst Nur-Metadaten-Modus. |

---

## Nicht-Ziele

- Persistenz oder Versionierung fertiger Mediendateien auf **`production_files`** / **`execution_jobs`**-Dispatch (**7.3**).
- FFmpeg, Concat mehrerer Chunks zu einer Datei, Lautnormalisierung.
- Zweiter Kommerzanbieter (ElevenLabs, Google Cloud TTS), SSML-Produktionsworkflow (**7.6** / später).
- Änderungen an **`POST /generate-script`**, **`POST /youtube/generate-script`**, oder **`VoicePlan`**-Speicherfeldstruktur (Felder können **read-only** genutzt werden; keine Schema-Brüche ohne separates RFC).
- Public **unauthentischer** Zugriff ohne spätere IAP/Scheduler-Diskussion (Cloud Run bleibt wie heute; keine neue Auth-Matrix in **7.2** außer Verweis auf zukünftige Absicherung).

---

## Dateien

| Pfad | Rolle |
|------|-------|
| `app/voice/__init__.py` | Neu: Paket (oder alternativ **`app/watchlist/voice_providers/`** — im PR eine Variante festlegen und hier nicht splitten). |
| `app/voice/contracts.py` | Neu: **`VoiceSynthRequest`/`VoiceSynthChunkResult`/`VoiceSynthProvider`** (Namen variabel, Semantik aus diesem Steckbrief). |
| `app/voice/openai_tts.py` | Neu: OpenAI-HTTP-Client (z. B. `httpx` wie im restlichen Stack, falls vorhanden). |
| `app/config.py` | Erweitern: optionale Flags **`openai_tts_model`**, **`voice_synth_preview_max_bytes`**, **`enable_voice_synth_preview_body`** (Namen final im PR; **keine** Defaults die Secrets loggen). |
| `app/models.py` oder `app/watchlist/models.py` | **Neue** Request/Response-Modelle **`VoiceSynthPreviewRequest`/`VoiceSynthPreviewResponse`** (Konvention: Produkt-Nähe ⇒ tendenziell `watchlist/models` bei anderen Production-Routen). |
| `app/watchlist/service.py` | Neue Service-Funktion **`synthesize_voice_plan_preview`** (oder äquivalent): Orchestrierung Repo + Provider + Fehlerkartierung. |
| `app/routes/production.py` | Registrierung **`POST …/voice/synthesize-preview`** (exakter Pfadsuffix im PR konsistent zur `PIPELINE_PLAN`-Endpunktliste). |
| `tests/test_phase7_72_voice_provider_contract.py` | Neu: Protocol/Adapter Mock-Tests, Route-Integration mit gesamtem Repo-Mock (**kein Live-HTTP** ohne expliziten Mark **`@pytest.mark.integration`** — optional später). |

---

## Endpoints

| Methode | Pfad | Request | Response | Vertrag stabil? |
|---------|------|---------|----------|-----------------|
| `POST` | `/production/jobs/{production_job_id}/voice/synthesize-preview` *(finaler Pfad im PR zwecks Konsistenz mit Router-Prefix prüfen — Basis `production` wie bestehend)* | Body: **`VoiceSynthPreviewRequest`**: z. B. `dry_run: bool=false`, `max_blocks: int=1` (clamp 1–5), optional `voice: str \| None` (OpenAI‑Stimmnname — **nie** Secret) | **`VoiceSynthPreviewResponse`**: `chunks[]`, `warnings[]`; optional eingeschränkt `audio_base64` siehe Scope | **neu**, stabil sobald dokumentiert — nach Merge in [PIPELINE_PLAN.md](../../PIPELINE_PLAN.md) und README-Kurzverweis erwägenswert |

**`GenerateScriptResponse`:** bleibt **unverändert** — keine neuen Pflichtfelder dort.

HTTP-Semantik (Ziel):

| Situation | Ziel-HTTP |
|-----------|-----------|
| Job / `voice_plan` fehlt | **404**, Response mit **`warnings`** (keine leere Liste ohne Grund) |
| Firestore nicht erreichbar | **503**, wie bestehende Production-Patterns (`VoicePlanGenerateResponse`-Stil erwägenswert) |
| Provider/Key fehlt oder Provider 401/429 | **200** mit **`warnings`** + leeren Chunk-Byte-Längen **oder** **502** nur wenn bereits etabliertes Pattern — **Default laut AGENTS: kein blindes 500**; im PR an existierende `review`/`generate` Fehlertöne anlehnen |

---

## Datenmodell

| Artefakt | Nutzung in 7.2 |
|----------|----------------|
| **`VoicePlan` / `VoiceBlock`** | **Read-only** Quelle für `voice_text`, `scene_number`, optional `tts_provider_hint` (Logik: **Hinweis ist nicht bindend** für MVP-Adapter solange nur OpenAI implementiert; Warnung ausgeben wenn Hint ≠ `openai` und `generic`). |
| **Neue Pydantic-Modelle** | Nur für **synthesize-preview** Request/Response und interne Provider-DTOs. |
| **Firestore** | Nur **Lesen** `voice_plans` / ggf. Validierung `production_jobs` existiert — **kein** Schreiben von Audio. |
| **Secrets** | `OPENAI_API_KEY` (bereits); bei gesondertem TTS-Key später optionales `OPENAI_TTS_API_KEY` — **nur** benennen in `.env.example` wenn eingeführt, **keine** Werte. |

---

## Akzeptanzkriterien

- [ ] `python -m compileall app` grün.  
- [ ] `python -m pytest` grün; **neue** Tests in `tests/test_phase7_72_*.py` decken ab: **Mock-Provider** (Happy Path), **fehlender Key** (kein Crash, erwartete `warnings`/Status), **dry_run** (kein HTTP Call), **fehlendes `voice_plan`** (404 + Struktur).  
- [ ] `GET /health` unverändert **200**.  
- [ ] `POST …/voice/synthesize-preview`: **nie** unbearbeiteter 500er bei Timeout/4xx wenn vermeidbar; Fehler nach **warnings**/`detail`-Pattern dokumentiert im PR.  
- [ ] **Keine** Logs mit API-Keys oder Voll-Payload proprietärer API.  
- [ ] Dokumentierte Obergrenze für optional `audio_base64` eingehalten; Default-Antwort **metadata-only** ohne großen Body.  

---

## Tests

| Test | Art | Befehl / Ablauf |
|------|-----|----------------|
| Adapter Request-Bau | automatisch | `pytest tests/test_phase7_72_voice_provider_contract.py -k adapter` *(exakte Namenswahl im PR)* |
| Route + Service + Mock HTTPS | automatisch | `pytest tests/test_phase7_72_voice_provider_contract.py` |
| Smoke lokal | manuell | `POST …/voice/synthesize-preview` mit `dry_run=true` nach Anlegen Fixtures / vorhandenen Job |
| Optional Live Smoke | manuell | Mit gültigem **`OPENAI_API_KEY`**, kleinem **`max_blocks`**, ohne Base64 wenn nicht nötig |

**Minimum laut Projektregeln:** `compileall`; API-Änderung ⇒ `/health` + neue Route Smoke.

---

## Deployment

| Variable / Secret | Zweck |
|-------------------|--------|
| `OPENAI_API_KEY` | Bereits vorhanden — TTS reused **solange** produktrechtlich gleiche OpenAI-Rechnungslogik erwünscht; sonst später separater Secret-Name. |
| Neue optionale **`OPENAI_TTS_VOICE`** oder Modell-Spalte in `settings` | Default-Stimmenname (**kein** Secret); in Cloud Run Env setzbar wie `OPENAI_MODEL`. |
| `enable_voice_synth_preview_body` (o. Ä.) | Steuert, ob Binärdaten in JSON überhaupt je zurückgegeben werden (**Default empfohlen: false** Prod). |

Image-Größe: `httpx` / `urllib` i. d. R. schon transitive Abhängigkeit — neue Lock-Zeilen vermeiden wo möglich.

---

## Risiken

| Risiko | Mitigation |
|--------|------------|
| Höhere OpenAI-Kosten durch Vorschau-Calls | `max_blocks`, Rate-Defaults, `dry_run`, optional Feature-Flag. |
| Große Responses / Cloud Run Timeout | Klein halten (**1 Block**, begrenzte Textlänge, Metadata-Only-Default). |
| Rechtliche TTS/Stimmnutzung | Produkt dokumentiert Provider-ToS nutzen — keine Marken-/Stimmen-Claims durch Pipeline. |
| Doppelnutzung `OPENAI_API_KEY` für Chat + TTS | Akzeptiert im MVP — später getrennte Keys/Budget-Alerts (**7.5** Kostenschätzung). |

---

## Abnahme

| Rolle | Name / Datum | OK |
|-------|----------------|-----|
| Technisch | | |
| Redaktion / Produkt | | |

---

## Verknüpfung Pipeline-Plan

**Phase:** [Phase 7 — Voiceover](../../PIPELINE_PLAN.md#phase-7--voiceover) (**Makro**); dieser Steckbrief = **Baustein 7.2** aus [docs/phases/phase7_voice_bauplan.md](../phases/phase7_voice_bauplan.md).

**Status nach Merge:** In `PIPELINE_PLAN.md` Endpunktliste (Phase‑5-Produktionstabelle) neue Zeile **`POST …/voice/synthesize-preview`** ergänzen; Phase‑7‑Status optional von **`planned`** auf **`in progress`** setzen sobald erste Zeile Implementierung gemerged ist.

---

## Implementierungs-Hinweise (Konvention Repo)

1. **`VoiceSynthProvider`** bleibt **schmal** — komplexeres Chunk-Merging/Chaining kommt erst **7.3+**.  
2. OpenAI-spezifische Parameter (Stimmenliste) **einmalig** dokumentieren unter README oder diesem Modul, verlinken.  
3. Parallel beginnend **Baustein 7.3**: beim Implementieren keine Kreuz-PR-Mischung ohne Absprache — **7.2** merged als isolierte Nadel vorher bevorzugt.
