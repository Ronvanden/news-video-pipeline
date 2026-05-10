# Real Leonardo Live Smoke

Kontrollierter **manueller** Smoke-Lauf: genau **ein** echtes Bildasset über Leonardo (kostenpflichtig). Kein automatisierter Provider-Test in CI — nur für lokale oder staging Runtime mit bewusst gesetzter Konfiguration.

**Querverweis (anderer Bildprovider):** Multi‑Scene‑Smoke mit **Gemini/Nano Banana**, ElevenLabs und **Fit‑to‑Voice** — siehe [`real_image_provider_smoke.md`](real_image_provider_smoke.md), u. a. **BA 32.52** (3 Szenen), **BA 32.54** (5 Szenen) und **BA 32.57** (8‑Minuten‑Langlauf, Referenzlauf dokumentiert).

## Voraussetzungen

- `LEONARDO_API_KEY` ist in der **Runtime** gesetzt (Werte niemals committen, loggen oder in Tickets pasten).
- Founder Dashboard: Provider-Readiness zeigt **Live Assets = Bereit**, oder du prüfst die Umgebung manuell.
- Keine Secrets aus dieser Datei oder aus Logs rekonstruieren.

## Ziel

Ein Lauf erzeugt mindestens **ein** Asset mit `generation_mode: leonardo_live` und referenziert eine **existierende** Bilddatei im Asset-Manifest.

## Sichere Minimal-Parameter

Über `POST /founder/dashboard/video/generate` (oder gleichwertige Aufrufkette wie das Dashboard):

| Parameter | Wert |
|-----------|------|
| `allow_live_assets` | `true` |
| `confirm_provider_costs` | `true` |
| `max_live_assets` | `1` |
| `max_scenes` | `1` |
| `voice_mode` | `none` (oder `dummy`, wenn Voice gewünscht) |
| `motion_mode` | `static` (optional; Dashboard sendet derzeit oft `basic` — für rein statisches Rendering API mit `static` nutzen) |
| `max_motion_clips` | `0` (optional, weniger Motion-Metadaten) |

Im Dashboard: **Max. Szenen** und **Max. Live-Assets** auf **1** setzen; **Max. Motion-Clips** auf **0**; Voice **Keine Voice** wählen; **Echte Assets erzeugen** und **Mögliche Provider-Kosten bestätigen** aktivieren. Siehe auch die eingeklappte Sektion **Real Leonardo Live Smoke** im Founder Dashboard.

### UI vs. Runbook (Governance)

- **Keine neuen Bedienelemente** nur für Smoke-Vorbereitung: Solange das Dashboard bereits passende Felder hat, reichen **Hinweise** und dieses Runbook.
- Aktuell im Founder Dashboard vorhanden: u. a. **Max. Szenen**, **Max. Live-Assets**, **Max. Motion-Clips**, Voice-Modus, Live-Assets- und Kosten-Checkboxen.
- **Nicht** als separates Control vorgesehen: **`motion_mode`** — der Smoke mit `motion_mode=static` erfolgt über die **API** (`POST /founder/dashboard/video/generate` mit JSON), nicht über ein zusätzliches Dashboard-Feld.

## Erwartetes Ergebnis (Antwort / OPEN_ME)

- `asset_artifact.real_asset_file_count >= 1`
- `asset_artifact.placeholder_asset_count == 0` — bei teilweisem Fallback ggf. `mixed_assets` statt `production_ready`
- `asset_artifact.generation_modes` enthält einen Eintrag für **`leonardo_live`**
- `asset_artifact.asset_quality_gate.status` idealerweise **`production_ready`**, sonst **`mixed_assets`** wenn noch Placeholder-Szenen im Manifest sind
- In `warnings` **kein** `leonardo_env_missing_fallback_placeholder`

## Fehlerbilder (readiness_audit / warnings)

| Signal | Bedeutung / nächster Schritt |
|--------|------------------------------|
| `live_asset_provider_not_configured` (Blocker in `readiness_audit`) | Key fehlt oder Runtime sieht ihn nicht — Deployment/Shell prüfen. |
| `leonardo_live_beat_failed_fallback_placeholder:*` oder ähnliche Leonardo-Warnungen | Provider/API, Limits, Netzwerk oder Prompt-Pipeline prüfen (ohne Keys zu loggen). |
| `placeholder_only` am Asset-Gate | Live-Runner hat kein echtes Asset geliefert — Konfiguration und Warnungen des Asset-Runners prüfen. |

## Tests / CI (keine echten Provider-Calls)

- Automatisierte Tests dürfen **keine** echten Leonardo- oder anderen kostenpflichtigen Provider-Requests auslösen.
- Wo Readiness oder Keys relevant sind: nur **Env-Presence** per `unittest.mock.patch` / `monkeypatch` / `patch.dict(os.environ, …)` simulieren — **keine** Key-Werte loggen oder in Assertions wiedergeben.
- Echter Bild-Lauf bleibt **manuell** (lokal/staging), siehe nächster Abschnitt.

## BA 32.26 — Manual Real Leonardo Live Smoke (Referenz)

Erster kontrollierter Echtlauf mit u. a.:

- `allow_live_assets=true`
- `confirm_provider_costs=true`
- `max_live_assets=1`
- `max_scenes=1`
- `voice_mode=none`
- `motion_mode=static` (nur sinnvoll über API, siehe oben)

**Knallhart prüfen:**

1. Hat Leonardo wirklich ein Asset geliefert (Datei unter dem Manifest-Pfad vorhanden)?
2. Steht im `asset_manifest.json` bzw. in den Einträgen **`generation_mode=leonardo_live`**?
3. Ist `asset_quality_gate.status` **`production_ready`** oder **`mixed_assets`** (wenn noch Placeholder-Szenen)?
4. Sind **Placeholder-/Env-Fallback-Warnungen** weg (insb. kein `leonardo_env_missing_fallback_placeholder`)?

## BA 32.34 – Erster erfolgreicher Leonardo Live Mini-Smoke

Der erste kontrollierte manuelle Mini-Smoke mit Leonardo Live Asset war erfolgreich. Die Pipeline erzeugte ein echtes Leonardo-Asset, erkannte das Asset Manifest als `production_ready`, nutzte keinen Render-Placeholder und schrieb ein finales MP4.

### Referenzlauf (ohne Secrets, ohne Key-Werte)

| Feld | Wert |
|------|------|
| `run_id` | `video_gen_10m_1778179303883` |
| Ausgabe (relativ zum Repo-Root) | `output/video_generate/video_gen_10m_1778179303883/` |
| `final_video.mp4` | vorhanden, **99 198** Bytes |
| `asset_manifest.json` | unter `generated_assets_<run_id>/asset_manifest.json` (siehe Ausgabeordner) |
| `requested_live_assets` | `true` |
| `asset_runner_mode` | `live` |
| `real_asset_file_count` | `1` |
| `placeholder_asset_count` | `0` |
| `generation_modes.leonardo_live` | `1` |
| `asset_quality_gate.status` | `production_ready` |
| `asset_strict_ready` | `true` |
| `asset_loose_ready` | `true` |
| `render_used_placeholders` | `false` |
| `requested_voice_mode` | `none` |
| `effective_voice_mode` | `none` |
| `silent_render_expected` | `true` |
| `silent_render_reason` | `voice_mode_none` |

**Hinweis zu Warnungen in diesem Lauf**

- `audio_missing_silent_render` — **erwartbar**, weil `voice_mode=none` bewusst gewählt wurde (BA 32.31 / 32.32).
- `live_motion_not_available` kann in `readiness_audit.provider_blockers` vorkommen — **kein Blocker** für diesen Smoke, wenn Motion nicht angefordert wurde.
- **Keine** `ba266_cinematic_placeholder_applied`-Warning (Live-Assets werden nicht mehr durch den cinematic-Placeholder-Layer überschrieben; BA 32.30).
- **Keine** `leonardo_env_missing_fallback_placeholder`-Warning — Runtime hat den Asset-Provider als nutzbar erkannt.

Weitere dokumentierte Meldungen (Inhalt/LLM, kein Leonardo-Blocker): u. a. kurzer Extrakt, Zielwortzahl vs. Ist-Wortzahl, `Generated using LLM mode`, kürzere LLM-Ausgabe als Ziel.

### Was dieser Lauf beweist

- `LEONARDO_API_KEY` wurde von der **Runtime** erkannt (ohne dass hier ein Wert dokumentiert wird).
- Mit `allow_live_assets=true` und Kostenbestätigung erreicht der Lauf den **Asset Runner** im Live-Modus.
- Ein **Leonardo Live Asset** wird erzeugt und liegt als Datei vor.
- `asset_manifest.json` enthält **`generation_mode=leonardo_live`** (bzw. den entsprechenden Manifest-Eintrag).
- **`asset_quality_gate`** erkennt **`production_ready`** (ein echtes Asset, kein Placeholder-Eintrag nach Zähl-Logik).
- **`_apply_cinematic_placeholders`** überschreibt Live-Assets nicht mehr (kein `ba266_*` in diesem Lauf).
- **`final_video.mp4`** wird erzeugt und ist lesbar (Größe siehe Tabelle).

### Was dieser Lauf noch nicht beweist

- **Keine echte Voice** — `voice_mode=none`, daher kein Nachweis für TTS/ElevenLabs/OpenAI in derselben Kette.
- **Kein Motion-/Runway-Test** — Runway-Integration und Live-Motion-Clips sind out of scope.
- **Kein 10-Minuten-Produktionsvideo** — Mini-Smoke mit begrenzter Szenen-/Dauer-Logik.
- **Keine Multi-Szenen-Produktion** — bewusst `max_scenes=1` / `max_live_assets=1`.
- **Keine finale YouTube-Qualität** — Qualitäts- und Schnitt-Claims sind nicht Ziel dieses Smokes.
- Nur **Mini-Smoke mit einem** Live-Asset als erster belastbarer End-to-End-Nachweis (Asset → Manifest → Render).

### Nächster sinnvoller Schritt: BA 32.35 – Real Voice Mini Smoke

**Ziel**

- Erste **echte Voice-Datei** erzeugen (`voice_artifact.voice_ready=true`).
- `final_video.mp4` **mit Audio** prüfen.
- Weiterhin konservativ: **`max_scenes=1`**, **`max_live_assets=1`**.
- Leonardo Live Asset **wiederverwenden** (gleicher Run/Pfad) oder **erneut erzeugen**, je nach Workflow — ohne Scope-Kreep (keine neue Motion-Architektur).

### BA 32.37 — Leonardo 5xx / Kombi-Smoke: sichere Diagnose & Mini-Payload

- **HTTP-Diagnose** (nach BA 32.36): weiterhin Codes wie `leonardo_http_5xx`, `leonardo_http_error:500`, `leonardo_retry_*` — keine Response-Bodies.
- **Zusätzlich** sichere Prompt-Metadaten in Warnungen: u. a. `leonardo_prompt_chars:*`, `leonardo_dimensions:512x512`, `leonardo_payload_profile:standard|mini_smoke_safe`, `leonardo_model_id:*`, `leonardo_model_label:*`, `leonardo_model_class:*` — **kein vollständiger Prompt**, keine API-Keys.
- Bei **`max_live_assets=1`**: Profil **`mini_smoke_safe`** (kürzeres Prompt-Limit, Repo-Standard-Modell ohne ENV-`LEONARDO_MODEL_ID`-Override für diesen Lauf).
- **`asset_manifest.json`**: bei Live mit Meta optional `leonardo_safe_request_meta_v1` (nur strukturierte Zahlen/Profile — kein Freitext-Prompt).

### BA 32.38 — Modell-/Payload-Validierung (Mini-Smoke)

- **Repo-Standard-Modell** für Live-Asset-Runner bei `max_live_assets=1`: `modelId` = `b24e16ff-06e3-43eb-8d33-4416c2d75876` (in der Leonardo OpenAPI-Dokumentation als **Default** für `createGeneration` ausgewiesen — öffentliche UUID, kein Secret).
- **Profil-Name in Diagnose:** `leonardo_payload_profile:mini_smoke_safe` (Alias `mini_smoke` im Builder für Abwärtskompatibilität).
- **POST-Body (Mini):** ausschließlich `prompt`, `modelId`, `width`, `height`, `num_images` — keine `presetStyle`, `alchemy`, `negative_prompt` o. ä. im Request-Body (serverseitige Defaults greifen laut API).
- **Zusätzliche sichere Codes:** `leonardo_model_id:<uuid>`, `leonardo_model_label:openapi_schema_default` (wenn die UUID dem Repo-Default entspricht) bzw. `custom_model_id` bei ENV-Override — Weiterhin **keine** Response-Bodies, keine Keys, keine vollständigen Prompts in Warnungen.

#### Leonardo HTTP 500 — Troubleshooting

- **`leonardo_http_5xx`** / **`leonardo_http_error:500`** zusammen mit **`mini_smoke_safe`** bedeutet nicht automatisch falscher API-Key: Zuerst **Modell-Verfügbarkeit**, Kontingente, Leonardo-Incident und **payload_profile + model_id** aus den Warnungen bzw. `leonardo_safe_request_meta_v1` prüfen.
- Wenn weiterhin 500 bei minimalem Body: anderen **per ENV konfigurierten Plattform-Modell-UUID** testen (`LEONARDO_MODEL_ID` — Wert nie loggen/README) oder Leonardo-Support/Status konsultieren; das Repo garantiert keine laufzeitstabile Zuordnung „Default UUID → erfolgreiche Generation“ über alle Accounts/Hinweise.

### BA 32.39 — Verfügbare Plattform-Modelle (Account-Check, manuell)

**Ziel:** Prüfen, welche öffentlichen **Platform Models** die Leonardo-API für den aktuellen API-Key zurückgibt — **ohne** Response-Bodies, Header oder Keys auszugeben.

**Discovery-Script (lokal / Staging, nicht CI):**

```text
python scripts/list_leonardo_models.py
```

- Voraussetzung: `LEONARDO_API_KEY` in der **Shell-Umgebung** gesetzt (keine `.env` aus dem Repo auslesen; der Prozess muss die Variable sehen).
- **stdout:** JSON mit `model_count` und `models[]` — pro Eintrag nur `id`, `name`, `featured`, `nsfw`, `description_char_count`, `has_preview_image` (keine Preview-URLs, keine Roh-Responses).
- **stderr:** bei Fehlern kurze Codes, z. B. `leonardo_models_http_401`, `leonardo_models_http_403`, `leonardo_models_http_5xx`, `leonardo_models_http_error:<code>`, `leonardo_models_url_error:*`, `leonardo_models_response_invalid`, `leonardo_models_api_key_missing`.
- Optional: URL-Override `--url` oder Umgebungsvariable `LEONARDO_PLATFORM_MODELS_URL` (Default: `GET …/api/rest/v1/platformModels` laut Leonardo-Doku).

#### Leonardo `modelId` prüfen

1. Script ausführen und in der JSON-Ausgabe eine **Name/ID-Kombination** wählen, die für Generations passend ist.
2. Für Läufe **ohne** Mini-Smoke-Zwang: in der Runtime **`LEONARDO_MODEL_ID=<gewählte-uuid>`** setzen (Wert **nicht** in Runbooks, Tickets oder Git — nur in der sicheren Secret-Verwaltung / Shell).
3. **Hinweis:** Profil **`mini_smoke_safe`** (`max_live_assets=1` im Asset-Runner) **erzwingt weiterhin** das Repo-**OpenAPI-Default-**`modelId`; ein gesetztes `LEONARDO_MODEL_ID` wirkt dort **nicht**. Zum Testen eines alternativen Modells: z. B. `max_live_assets` > 1 und Profil **standard**, oder separater Einzel-Smoke über die gleiche Generations-Pipeline mit Standard-Profil.
4. Wenn das **dokumentierte Standard-**`modelId` weiter **HTTP 500** liefert, aber ein aus der **Platform-Model-Liste** gewähltes Modell mit **Standard-Profil** funktioniert, liegt die Vermutung nahe, dass Default/Tier/Account-Kombination serverseitig nicht passt — **nicht** automatisch als Key-Problem deuten.

**Diagnose im Video-Lauf (unverändert zu BA 32.38):**

- Ohne `LEONARDO_MODEL_ID`: Warnungen u. a. `leonardo_model_label:openapi_schema_default`.
- Mit gesetztem `LEONARDO_MODEL_ID` (Standard-Profil): `leonardo_model_label:custom_model_id`.

### Verwandte Artefakte

- **BA 32.40 OpenAI Image**: [real_image_provider_smoke.md](real_image_provider_smoke.md) (`IMAGE_PROVIDER=openai_image`).
- Asset-Zähl- und Gate-Logik: Docstring `build_asset_artifact()` in `app/founder_dashboard/ba323_video_generate.py`
- Boundary-Tests ohne Provider: `tests/test_ba320_asset_runner_live_boundary.py`, `tests/test_ba323_asset_artifact_fixtures.py`
