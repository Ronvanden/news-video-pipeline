# Real Image Provider Smoke (Leonardo / OpenAI Image)

Manuelle Mini-Smokes für **echte** Bild-Assets. Keine Provider-Calls in CI.

## Provider-Auswahl (Runtime)

| Env | Wirkung |
|-----|--------|
| `IMAGE_PROVIDER` nicht gesetzt oder `leonardo` | Leonardo Live (wie bisher; `LEONARDO_API_KEY`). |
| `IMAGE_PROVIDER=openai_image` | OpenAI Image Live über `POST /v1/images/generations` (`OPENAI_API_KEY`). |
| `IMAGE_PROVIDER=gemini_image` | Gemini / Nano Banana Image Live über Gemini REST `generateContent` (`GEMINI_API_KEY` oder `GOOGLE_API_KEY`). |
| `OPENAI_IMAGE_MODEL` | Live-Smokes: **`gpt-image-2`** bevorzugt (nach Organization Verification, **BA 32.71b**); **`gpt-image-1`** nur Diagnose/Einengung. Reihenfolge: Env → `settings.openai_image_model` → Adapter-Default **`gpt-image-2`** (BA 32.69). |
| `GEMINI_IMAGE_MODEL` | Optional; Default: `gemini-2.5-flash-image` (ohne Wert in Doku setzen). |
| `GEMINI_IMAGE_TRANSPORT` | Optional; `rest` (Default) oder `sdk` (Google Gen AI SDK). |

Routing `routed_visual_provider=openai_images` in der Szene bleibt dem **BA 26.5**-Pfad (`openai_images_*` im Manifest) vorbehalten; der Default-Pfad **BA 32.40** nutzt `openai_image_live` / `provider_used=openai_image`.
Der Default-Pfad **BA 32.41** nutzt `gemini_image_live` / `provider_used=gemini_image`.

## Raw Text Input (BA 32.42) — empfohlen für Provider-Smokes

Wenn du **Provider** (Gemini/OpenAI/Leonardo/ElevenLabs) testen willst, nutze bevorzugt **`raw_text`** im
`POST /founder/dashboard/video/generate`, damit der Smoke **nicht** an URL-Extraktion scheitert.

- **`raw_text`** umgeht URL-Extraktion und erzeugt trotzdem `script.json`, `scene_plan.json`, `scene_asset_pack.json`.
- URL-Smokes testen zusätzlich die Extraction — sinnvoll, aber für Provider-Diagnose oft ein unnötiger Blocker.

## YouTube-Source-Flow (BA 32.58) — nicht mit Raw-Text-Smoke verwechseln

`source_youtube_url` (oder Alias `youtube_url`) zieht ein **YouTube-Transkript** als **Recherche-/Quellenmaterial** und erzeugt daraus ein **neues, eigenständiges Skript** (kein 1:1-Reupload, keine wörtliche Abschrift). Für **reine Provider-Tests** (Bild/TTS) bleibt **`raw_text`** oder **`script_text`** die stabilere Wahl.

Details und manueller Smoke: [youtube_source_to_video_smoke.md](youtube_source_to_video_smoke.md).

Erster dokumentierter End-to-End-Referenzlauf (YouTube-Quelle → neues Skript → Gemini/Nano-Banana-Bilder → ElevenLabs → Fit-to-Voice → MP4): **BA 32.59** im selben Runbook.

## OpenAI Image Mini-Smoke (manuell)

1. `OPENAI_API_KEY` in der Shell setzen (keine `.env` aus dem Repo lesen; Werte nicht loggen).
2. `IMAGE_PROVIDER=openai_image` setzen.
3. **`OPENAI_IMAGE_MODEL`**: für Live-Smokes **`gpt-image-2`** bevorzugen (nach Organization Verification der übliche Preferred Path). Bei **403** zuerst **Organization Verification** und Modellzugriff prüfen, danach Smoke mit **`gpt-image-2`** wiederholen; **`gpt-image-1`** nur zum **Einengen** (Modell vs. Key), kein automatischer Modellwechsel im Code.
4. Video-Pipeline wie `real_leonardo_live_smoke.md` starten, mit `allow_live_assets=true`, `max_live_assets=1`, kleiner Szenenzahl.
5. Erwartung: `generation_mode` im Manifest-Eintrag **`openai_image_live`**, `asset_quality_gate.status` **`production_ready`**, wenn Datei existiert und kein Placeholder-Modus im Modus-String steht.

### OpenAI Image Diagnose (BA 32.69) — HTTP ohne Response-Body

Live-Aufrufe nutzen **`POST /v1/images/generations`** (`openai_image_transport:images_api`). Typische Meta-Warnungen:

- `openai_image_model:<model>`, `openai_image_provider:openai_image`, `openai_image_transport:images_api`, optional `openai_image_size:<size>`

HTTP-Status (keine Bodies, keine Header in Warnungen):

| Situation | Warn-Codes (Auszug) |
|-----------|---------------------|
| 400 | `openai_image_http_400` + `openai_image_generation_failed:http_400` |
| 401 | `openai_image_http_401` + … |
| **403** | **`openai_image_http_403`** + **`openai_image_model_access_denied:<model>`** + `openai_image_generation_failed:http_403` |
| 429 | `openai_image_http_429` + … |
| 5xx | `openai_image_http_5xx` + … |
| Sonst | `openai_image_http_error:<status>` |

**Bei 403:** Zuerst **Organization Verification** im OpenAI-Dashboard sowie **Projekt / Billing / Berechtigungen** und **Modellzugriff** für **`gpt-image-2`** prüfen; danach erneuten Smoke mit **`gpt-image-2`**. Optional **`gpt-image-1`** nur zur **Diagnose** (Einengung Modell vs. Key), ohne automatischen Fallback im Code.

**Ohne Key:** `openai_image_key_missing_fallback_placeholder` und Placeholder-Assets wie bisher.

## BA 32.70 — OpenAI Image Real Smoke V1 (ein API-Call, ohne volle Pipeline)

Minimaler **Live**-Check nur gegen **`POST /v1/images/generations`** — kein Dashboard, kein Langlauf, **kein automatischer Modell-Fallback**.

### Script (empfohlen für schnelle Diagnose)

Voraussetzungen in der **Shell** (keine `.env` aus dem Repo lesen; Keys nicht loggen):

| Variable | Hinweis |
|----------|---------|
| `OPENAI_API_KEY` | **Pflicht** für Live |
| `OPENAI_IMAGE_MODEL` | Optional; Default-Reihenfolge wie BA 32.69 (`gpt-image-2` nach Env/Settings/Adapter) |
| `IMAGE_PROVIDER` | Für dieses Script **nicht** nötig (direkter Connector-Call) |

```text
python scripts/run_openai_image_smoke.py --confirm-live-openai-image --run-id my_oai_img_smoke
```

Optional: Modell explizit (`OPENAI_IMAGE_MODEL` wird vom Adapter ebenfalls gelesen):

```text
set OPENAI_IMAGE_MODEL=gpt-image-2
python scripts/run_openai_image_smoke.py --confirm-live-openai-image --run-id my_oai_img_smoke --model gpt-image-2
```

Bei **403:** wie oben **Verification** prüfen, dann Smoke mit **`gpt-image-2`** wiederholen. **`gpt-image-1`** nur bei Bedarf zum Einengen — **kein** automatischer Wechsel im Code.

**Sicherheit:** Ohne `--confirm-live-openai-image` bricht das Script mit Exit **3** ab (`confirm_live_openai_image_required`). Es werden **keine** API-Response-Bodies und **keine** Secrets ausgegeben; Ausgabe ist strukturiert (`ok`, `model`, `provider`, `size`, `warnings`, `output_path`, …). Ergebnis zusätzlich unter `output/openai_image_smoke_<run-id>/openai_image_smoke_result.json`.

**Akzeptanz kurz:**

- Erfolg: `ok=true`, PNG unter dem Smoke-Ordner, Warnungen u. a. `openai_image_transport:images_api`.
- 403: Warnungen enthalten `openai_image_http_403` und `openai_image_model_access_denied:<model>`.
- Fehlender Key: `openai_image_key_missing_fallback_placeholder`, kein Key-Material in der Ausgabe.

### Abgrenzung BA 32.70 vs. BA 32.71

- **BA 32.70** isoliert: ein API-Call (`run_openai_image_smoke.py`) — **Provider** prüfen.
- **BA 32.71**: **Asset Runner + Manifest** (`run_openai_image_pipeline_smoke.py`) — **Produktionspfad** prüfen.

**Tests (CI):** `python -m pytest tests/test_ba370_openai_image_smoke.py` — nur Mocks.

## BA 32.71 — OpenAI Image Pipeline Mini-Smoke (Asset Runner, 1–2 Szenen)

**BA 32.71b — Preferred Path:** **`gpt-image-2`** ist der bevorzugte Live-Smoke nach erfolgreicher **Organization Verification**. **`gpt-image-1`** bleibt **Diagnose-/Fallback-Testmodell** zum Einengen, nicht der Dauer-Favorit — **kein** automatischer Modell-Fallback im Code.

**403 mit `gpt-image-2`:** **Organization Verification** und Modell-/Projektzugriff prüfen; nach Freigabe Smoke mit **`gpt-image-2`** erneut fahren.

Voraussetzungen:

| Variable | Hinweis |
|----------|---------|
| `OPENAI_API_KEY` | Pflicht |
| `OPENAI_IMAGE_MODEL` | Bevorzugt **`gpt-image-2`** (Live-Smoke); ohne Env nutzt das Pipeline-Script denselben Default wie die Smoke-CLI |
| `IMAGE_PROVIDER` | Setzt das Script temporär auf **`openai_image`** (wird nach dem Lauf zurückgesetzt) |

```text
python scripts/run_openai_image_pipeline_smoke.py --confirm-live-openai-image --run-id ba3271_smoke --max-scenes 1 --model gpt-image-2
```

- **`--max-scenes`**: Default **1**, maximal **2** (hart begrenzt).
- **`--scene-asset-pack`**: optional; sonst eingebautes Mini-Pack mit 1–2 Beats.
- Ohne **`--confirm-live-openai-image`**: Exit **3**, **keine** API-Calls.
- Ergebnis: `output/openai_image_pipeline_smoke_<run-id>/openai_image_pipeline_smoke_result.json` plus **`generated_assets_<run-id>/`** mit PNGs und **`asset_manifest.json`**.
- Ausgabe-JSON (Auszug): `ok`, `provider`, `model`, `size`, `run_id`, `max_scenes`, `generated_count`, `failed_count`, `output_dir`, `asset_paths`, `warnings`, `smoke_version` — **keine** Response-Bodies, **keine** Secrets.

**Voller Video-Dashboard-Pfad** (optional): weiterhin „OpenAI Image Mini-Smoke (manuell)“ oben mit `IMAGE_PROVIDER=openai_image`, `allow_live_assets`, wenige Szenen.

**Tests (CI):** `python -m pytest tests/test_ba371_openai_image_pipeline_smoke.py` — nur Mocks.

## BA 32.71c — Mini Video Smoke (1 PNG → kurzes MP4)

**Ziel:** Minimaler **End-to-End-Videotest** vor größeren Visual-/Thumbnail-Bausteinen: ein Bild (ideal **`gpt-image-2`** über den bestehenden Pipeline-Pfad) wird mit der **bestehenden** Kette **`asset_manifest.json` → `build_timeline_manifest.write_timeline_manifest` → `render_final_story_video`** zu einem **kleinen MP4** gerendert (**eine Szene**, kein Thumbnail-Feature, kein Multi-Szenen-Baukasten).

### Pfad (kurz)

| Schritt | Komponente |
|--------|------------|
| Bild | Entweder **`run_openai_image_pipeline_smoke`**-Logik intern (1 Szene) oder vorhandenes PNG via **`--image-path`** |
| Timeline | `scripts/build_timeline_manifest.py` (geladen vom Orchestrator) |
| Video | `scripts/render_final_story_video.py`, Default **`--motion-mode static`** |

### CLI (manuell, kostenpflichtig wenn generiert wird)

Pflicht: **`--confirm-live-openai-image`** (bewusste Smoke-Freigabe).

**A) Bild von OpenAI erzeugen lassen + MP4 (1 API-Bild):**

```text
python scripts/run_openai_image_mini_video_smoke.py --confirm-live-openai-image --run-id ba371c_live --model gpt-image-2 --duration-seconds 12
```

**B) Bereits vorhandenes PNG nur durch den Render-Pfad jagen (kein Bild-API-Call):**

```text
python scripts/run_openai_image_mini_video_smoke.py --confirm-live-openai-image --run-id ba371c_from_png --image-path path\to\scene_001.png --duration-seconds 12
```

- Ausgabe-Verzeichnis: `output/openai_image_mini_video_smoke_<run-id>/`
- Video: `mini_video.mp4`
- Ergebnis-JSON (auch auf stdout): `openai_image_mini_video_smoke_result.json` mit u. a. `ok`, `run_id`, `model`, `image_path`, `video_path`, `duration_seconds`, `bytes_written`, `warnings`, `smoke_version`
- **Keine** API-Response-Bodies, **keine** Secrets; bei Fehlern bleiben die bekannten OpenAI-Diagnose-Warnungen (z. B. **403**-Codes aus BA 32.69) in **`warnings`** sichtbar.
- **ffmpeg** muss verfügbar sein (wie bei jedem `render_final_story_video`-Lauf).
- **Budget:** eine Szene / ein Bild — Kosten bewusst niedrig halten.

**Tests (CI):** `python -m pytest tests/test_ba371c_openai_image_mini_video_smoke.py` — nur Mocks.

## BA 32.73 — Visual Reference Layer V1 (1 Master Reference Image)

Ziel: pro Video einen **visuellen Referenzanker** erzeugen (Art-Direction-Anker), der später für
Thumbnail-Kandidaten, Szenenbilder und Video-Provider (Runway/Kling/Seedance) nutzbar ist.

Abgrenzung (Kurz):

- **Einzel-Smoke (BA 32.70)** = Provider-Test (ein API-Call)
- **Pipeline-Smoke (BA 32.71)** = Asset-Pfad-Test (Manifest/Runner)
- **Mini-Video-Smoke (BA 32.71c)** = Bild → MP4 (lokal)
- **Visual Reference Smoke (BA 32.73)** = **1 Master Reference Image + strukturierter Visual Brief** pro Video

Eigenschaften V1:

- Genau **1** Bild (`master_reference.png`)
- **`gpt-image-2`** bevorzugter Pfad (kein automatischer Modell-Fallback)
- Prompt ist 16:9/YouTube-orientiert (auch wenn Output quadratisch ist), ohne Text-im-Bild zu erzwingen
- Keine Secrets, keine API-Bodies in der Ausgabe

### CLI (Live, kostenpflichtig)

Voraussetzungen in der **Shell** (keine `.env` aus dem Repo lesen; Keys nicht loggen):

| Variable | Hinweis |
|----------|---------|
| `OPENAI_API_KEY` | Pflicht |
| `OPENAI_IMAGE_MODEL` | Optional; Default-Reihenfolge wie BA 32.69 (`gpt-image-2` bevorzugt) |

```text
python scripts/run_visual_reference_smoke.py --confirm-live-openai-image --run-id my_vr_smoke --title "…" --summary "…" --model gpt-image-2
```

Ohne `--confirm-live-openai-image` bricht das Script mit Exit **3** ab (`confirm_live_openai_image_required`).

Output:

- `output/visual_reference_smoke_<run-id>/master_reference.png`
- `output/visual_reference_smoke_<run-id>/visual_reference_result.json`
- `output/visual_reference_smoke_<run-id>/visual_reference_smoke_result.json`

Kostenhinweis: Es ist **genau 1** OpenAI Images API Call. Nutze kurze Titel/Summaries, um Prompt-Kosten klein zu halten.

## BA 32.74 — Thumbnail Candidates V1 (1–3 Varianten)

Ziel: auf Basis der **Visual Reference Art Direction** (BA 32.73/32.73a) **1 bis max. 3** Thumbnail-Kandidaten
für YouTube erzeugen. Die Kandidaten testen unterschiedliche Winkel, bleiben aber stilistisch konsistent.

- **Visual Reference** = Art-Direction-Anker (Master Reference Image + Visual Brief)
- **Thumbnail Candidates** = Varianten für das Klickbild (ohne CTR-Modell, ohne Upload)

Eigenschaften V1:

- **1–3** Bilder, max. **3**
- Kein Text/keine Typografie im Bild erzwingen (Text später als Overlay)
- Subject Lock (z. B. `adult_man`) wird respektiert
- **`gpt-image-2`** bevorzugter Pfad (kein automatischer Modell-Fallback)
- Keine Secrets, keine API-Bodies in der Ausgabe

### CLI (Live, kostenpflichtig)

```text
python scripts/run_thumbnail_candidates_smoke.py --confirm-live-openai-image --run-id my_thumbs --title "…" --summary "…" --count 3 --model gpt-image-2
```

Ohne `--confirm-live-openai-image` bricht das Script mit Exit **3** ab (`confirm_live_openai_image_required`).

Output:

- `output/thumbnail_candidates_smoke_<run-id>/thumbnail_candidate_thumb_a.png`
- `output/thumbnail_candidates_smoke_<run-id>/thumbnail_candidate_thumb_b.png`
- `output/thumbnail_candidates_smoke_<run-id>/thumbnail_candidate_thumb_c.png`
- `output/thumbnail_candidates_smoke_<run-id>/thumbnail_candidates_result.json`
- `output/thumbnail_candidates_smoke_<run-id>/thumbnail_candidates_smoke_result.json`

Kostenhinweis: Es sind **1–3** OpenAI Images API Calls (abhängig von `--count`). Für Tests bewusst klein halten.

## BA 32.75 — Thumbnail Text Overlay V1 (lokal, kontrollierte Typografie)

Ziel: Thumbnail-Text wird **nicht** vom Bildmodell „ins Bild gerendert“, sondern lokal als Overlay auf ein vorhandenes
PNG/JPG gelegt. Dadurch sind **Lesbarkeit**, **Schreibweise** und **Layout** kontrollierbar.

Prinzip:

- **Bildgenerierung** (BA 32.74) erzeugt Kandidaten ohne Text/Typografie.
- **Text-Overlay** (BA 32.75) rendert Text lokal (Stroke/Outline/Schatten) auf ein bestehendes Bild.

Eigenschaften V1:

- 1 Bild rein → 1 finales Thumbnail raus (`1280x720`)
- keine API-Keys, keine Provider-Calls, keine Kosten
- Text maximal 2 Zeilen, kurze Hook-Phrasen (DE bei `language=de`)

### CLI (lokal)

```text
python scripts/run_thumbnail_overlay_smoke.py --image-path output\\thumbnail_candidates_smoke_<run-id>\\thumbnail_candidate_thumb_a.png --run-id ov_demo --title "Der Mann, der spurlos verschwand"
```

Optionaler Text-Override (2 Zeilen via `|`):

```text
python scripts/run_thumbnail_overlay_smoke.py --image-path path\\to\\thumb.png --run-id ov_demo --title "x" --text "DER MANN|VERSCHWAND"
```

Output:

- `output/thumbnail_overlay_smoke_<run-id>/thumbnail_final.png`
- `output/thumbnail_overlay_smoke_<run-id>/thumbnail_overlay_result.json`

## BA 32.76 — Thumbnail Batch Overlay + Selection V1 (lokal, heuristisch)

Ziel: aus **bestehenden** Thumbnail Candidates (BA 32.74) mehrere fertige Thumbnails erzeugen (Text-Overlay + Style Presets)
und eine **einfache Empfehlung** ausgeben. Die Auswahl ist **heuristisch** (kein CTR-Modell, kein ML).

Prinzip:

- **Thumbnail Candidates** (BA 32.74) erzeugt Bilder (A/B/C).
- **Thumbnail Overlay** (BA 32.75/32.75a) rendert Text lokal (Styles: `impact_youtube`, `urgent_mystery`, …).
- **Batch Overlay + Selection** (BA 32.76) kombiniert kontrolliert wenige Varianten und wählt eine Empfehlung.

Eigenschaften V1:

- keine API-Keys, keine Provider-Calls, keine Kosten
- maximal `--max-outputs` Dateien (Default 6)
- Empfehlung basiert auf Textkürze, Style-Preset und einfacher Angle-Heuristik (Dateiname `thumb_a/b/c`)

### CLI (lokal)

```text
python scripts/run_thumbnail_batch_overlay_smoke.py --candidate-dir output\\thumbnail_candidates_smoke_<run-id> --run-id batch_demo --title "Der Mann, der spurlos verschwand" --max-outputs 6
```

Output:

- `output/thumbnail_batch_overlay_smoke_<run-id>/thumbnail_batch_01.png` …
- `output/thumbnail_batch_overlay_smoke_<run-id>/thumbnail_batch_overlay_result.json` (inkl. `recommended_thumbnail`)

## BA 32.77 — Thumbnail Pack Export / Dashboard Preview (nur Lesen/Anzeige)

**BA 32.76** erzeugt die Dateien (`thumbnail_batch_*.png` + `thumbnail_batch_overlay_result.json`). **BA 32.77** macht das Ergebnis im **Founder-/Operator-Flow** sichtbar, **ohne** neue Provider-Calls, **ohne** Upload und **ohne** CTR-Learning.

Verhalten V1:

- Im **Video-Generate-Output-Ordner** (und Unterordnern) wird nach `thumbnail_batch_overlay_result.json` gesucht; der „beste“ Treffer (bevorzugt `ok: true` und höhere `generated_count`) wird normalisiert.
- Die **HTTP-Response** von `POST /founder/dashboard/video/generate` enthält **`thumbnail_pack`** (u. a. `thumbnail_pack_status`, `thumbnail_recommended_path`, `thumbnail_variants`, `thumbnail_pack_result_path`).
- **`OPEN_ME_VIDEO_RESULT.html`** enthält den Abschnitt **Thumbnail Pack (BA 32.77)** mit Status, empfohlener Variante (heuristisch), Tabelle aller Varianten und optionaler **lokaler Bildvorschau** (`file:`-URI), wenn die empfohlene PNG existiert.
- Das **Dashboard** zeigt eine kompakte **Thumbnail-Pack-Zusammenfassung** und **kopierbare Pfade** (empfohlenes Thumbnail, Batch-Report, Pack-Ordner).

Hinweis: Die **Empfehlung** stammt aus der **Heuristik** von BA 32.76 — keine automatische finale Editorial-Auswahl, kein ML.

**Tests (CI):** `python -m pytest tests/test_ba3277_thumbnail_pack_export.py` — keine Provider-Calls.

## BA 32.78 — Thumbnail Pack Auto-Attach (Video Generate, optional)

**BA 32.77** zeigt ein Thumbnail Pack, wenn `thumbnail_batch_overlay_result.json` im Run-Baum liegt. **BA 32.78** kann dieses Pack **optional** im selben **`POST /founder/dashboard/video/generate`** erzeugen — ohne manuelles Kopieren von Reports.

- **Steuerung:** Request-Felder `generate_thumbnail_pack` (bool), `thumbnail_candidate_count` (1–3), `thumbnail_max_outputs` (1–6), optional `thumbnail_model`, `thumbnail_size`, `thumbnail_style_presets`, Text-Overrides.
- **Kosten / Gate:** Wie Live-Assets gilt: **`confirm_provider_costs: true`** ist Pflicht, wenn `generate_thumbnail_pack` aktiv ist (zusätzliche **OpenAI Image**-Calls für Kandidaten).
- **Ablauf:** Nur wenn der **Video-Lauf** (`ok`) erfolgreich war: Kandidaten (`run_thumbnail_candidates_v1`) → Batch-Overlay (`run_thumbnail_batch_overlay_v1`) unter **`output/video_generate/<run_id>/thumbnail_pack/`** inkl. `thumbnail_batch_overlay_result.json`. Anschließend lädt die Response das Pack wie BA 32.77; **OPEN_ME** wird nach dem Lauf mit dem finalen Payload geschrieben.
- **Fehler:** Scheitert der Thumbnail-Schritt, bleibt das Video-Ergebnis bestehen; **Warnings** mit Präfix `ba3278_`, **`thumbnail_pack_status`** z. B. `warning` / `failed`. **Kein** automatischer Modell-Fallback.
- **Dev-Key:** `dev_openai_api_key` (BA 32.72b) wirkt auch für die Kandidaten-Generierung (transient, nie im JSON/OPEN_ME).
- **Mini-Preset „OpenAI gpt-image-2“:** Schaltet **kein** Thumbnail Pack selbst ein; setzt bei Bedarf **1 Kandidat / 2 Overlays** als konservative Vorgabe, wenn du das Pack manuell aktivierst.

**Empfehlung für Minikosten:** `thumbnail_candidate_count: 1`, `thumbnail_max_outputs: 2`.

**Tests (CI):** `python -m pytest tests/test_ba3278_thumbnail_pack_auto_attach.py` — gemockte Kandidaten, keine echten API-Calls.

## BA 32.79 — Production Bundle / Final Output Pack V1

Nach einem **Video-Generate-Lauf** legt die Pipeline unter **`output/video_generate/<run_id>/production_bundle/`** einen **lokalen Paketordner** an: bestehende Artefakte werden **kopiert** (keine neuen Provider-Calls, kein erneutes Rendering, kein Upload, keine Secrets im Manifest).

Typische Dateien im Bundle:

- `final_video.mp4`
- `recommended_thumbnail.png` (wenn `thumbnail_pack.thumbnail_recommended_path` zeigt auf eine existierende Datei)
- `script.json`, `scene_asset_pack.json`, `asset_manifest.json`
- `thumbnail_batch_overlay_result.json` (wenn im Run-Baum vorhanden / aus Thumbnail-Pack-Pfad)
- `OPEN_ME_VIDEO_RESULT.html` (nach dem ersten OPEN_ME-Schreiben finalisiert; die Response-**`production_bundle`**-Metadaten enthalten die vollständige Kopie)

**Manifest:** `production_bundle_manifest.json` (Version **`ba32_79_v1`**, Status **`ready` | `partial` | `missing`**, Liste `bundled_files` mit `exists` / `bytes_written`).

**API / UI:** Response-Feld **`production_bundle`**; **OPEN_ME**-Abschnitt **Production Bundle (BA 32.79)**; Dashboard-Block mit kopierbaren Pfaden.

**Tests (CI):** `python -m pytest tests/test_ba3279_production_bundle.py`.

## BA 32.72 — Smoke-Stufen und Founder Video Generate (Dashboard-Integration)

| Stufe | Zweck | Typisches Kommando / Endpoint |
|-------|--------|-------------------------------|
| **Einzel-Smoke (BA 32.70)** | Nur **Provider/API** (`POST /v1/images/generations`) | `python scripts/run_openai_image_smoke.py --confirm-live-openai-image …` |
| **Pipeline-Smoke (BA 32.71)** | **Asset Runner + Manifest** auf dem Produktionspfad | `python scripts/run_openai_image_pipeline_smoke.py …` |
| **Founder-Generate-Smoke (BA 32.72)** | **Dashboard** → `POST /founder/dashboard/video/generate` → `run_ba265_url_to_final` → `run_local_asset_runner` | HTTP-JSON mit `allow_live_assets=true`, optional `image_provider` / `openai_image_*` |

### Erster echter Dashboard-Mini-Test (`gpt-image-2`, max. 1 Szene)

1. **`OPENAI_API_KEY`** in der **Server**-Runtime (keine `.env` aus dem Repo lesen; nicht loggen).
2. Optional **`IMAGE_PROVIDER=openai_image`** auf dem Server **oder** im Request **`image_provider`: `"openai_image"`** (nur wirksam mit **`allow_live_assets=true`**).
3. **`POST /founder/dashboard/video/generate`** mit u. a. **`confirm_provider_costs`: true**, **`allow_live_assets`: true**, **`max_scenes`: 1**, **`max_live_assets`: 1**, empfohlen **`raw_text`** statt URL für stabile Smokes; optional **`openai_image_model`: `"gpt-image-2"`**, **`openai_image_size`**, **`openai_image_timeout_seconds`** (≥ 15).
4. **Ergebnis:** Response enthält **`image_asset_audit`** (effektiver Provider, angeforderte OpenAI-Optionen, Zähler, Manifest-Pfad) und **`run_summary.json`** kann **`asset_runner_audit`** enthalten; **`OPEN_ME_VIDEO_RESULT.html`** zeigt den Abschnitt **Image Asset Audit (BA 32.72)**.
5. **403:** Warnungen müssen **`openai_image_http_403`** und **`openai_image_model_access_denied:<model>`** enthalten (Diagnosecodes BA 32.69 unverändert; keine Response-Body-Logs).
6. **Budget:** Jede Live-Generierung ist kostenpflichtig — Mini-Smoke bewusst auf **eine Szene / ein Live-Asset** begrenzen.

**Tests (CI):** `python -m pytest tests/test_ba372_founder_openai_image_generate.py` — keine echten API-Calls.

**Voller Video-Dashboard-Pfad** zu OpenAI Image: siehe diesen Abschnitt; die ältere Kurzreferenz unter BA 32.71 wird damit für Dashboard-spezifische Parameter ergänzt (`image_provider`, `openai_image_model`, …).

## Leonardo

Unverändert siehe [real_leonardo_live_smoke.md](real_leonardo_live_smoke.md).

## Gemini / Nano Banana Image Mini-Smoke (manuell)

1. `GEMINI_API_KEY` **oder** `GOOGLE_API_KEY` in der Shell setzen (keine `.env` aus dem Repo lesen; Werte nicht loggen).
2. `IMAGE_PROVIDER=gemini_image` setzen.
3. Video-Pipeline wie `real_leonardo_live_smoke.md` starten, mit `allow_live_assets=true`, `max_live_assets=1`, kleiner Szenenzahl.
4. Erwartung: `generation_mode` im Manifest-Eintrag **`gemini_image_live`**, `asset_quality_gate.status` **`production_ready`**, wenn Datei existiert und kein Placeholder-Modus im Modus-String steht.

### Gemini Rate-Limit (HTTP 429) — Diagnose & Verhalten

- Der Connector gibt jetzt präzise HTTP-Codes aus: `gemini_image_http_429` + `gemini_image_http_error:429`.
- Bei **429 / 5xx / Timeout** werden **bis zu 2 Retries** mit kurzem Backoff gemacht:
  - `gemini_image_retry_1_after:gemini_image_http_429`
  - `gemini_image_retry_2_after:gemini_image_http_429`
- Bei **400/401/403** gibt es **kein Retry** (direkt diagnostizieren: Key/Permissions/Request).
- Wenn 429 dauerhaft: Smoke später erneut laufen lassen (Cooldown), `max_live_assets=1`, `max_scenes=1`, und möglichst keine parallelen Runs.

### Gemini „Invalid Response“ (HTTP 200, aber kein Bild) — BA 32.50

- **`gemini_image_response_invalid`**: Gemini hat geantwortet (typisch HTTP 200), aber es liegen **keine verwertbaren Bildbytes** vor (kein `inlineData` / leere Daten / kein Bild-Part).
- Zusätzliche **Detailcodes** (ohne Response-Body): z. B. `gemini_image_no_inline_data`, `gemini_image_no_image_part`, `gemini_image_empty_image_bytes`.
- **Einmaliger Retry pro Szene**: bei diesem Fehlerbild wird **genau ein zweiter Versuch** gemacht; Warnung: `gemini_image_retry_1_after:gemini_image_response_invalid`.
- Schlägt der Retry fehl: wie bisher **Placeholder** und `generation_mode=gemini_image_fallback_placeholder`, u. a. `gemini_image_generation_failed:invalid_response_exhausted`.
- **Kein Ersatz für 401/403**: Auth-/Permission-Fehler werden nicht über diesen Pfad retried (weiterhin nur 429/5xx-Transport-Retries nach BA 32.43).
- Wenn nach Retry weiterhin Placeholder: Smoke später wiederholen oder **Prompt/Szene** prüfen (inhaltlich, nicht vollständige Prompts loggen).

### Gemini Transport: REST vs. SDK

- Default ist **REST**: `GEMINI_IMAGE_TRANSPORT=rest` oder nicht gesetzt.
- Optional **SDK**: `GEMINI_IMAGE_TRANSPORT=sdk`
  - Wenn das SDK nicht installiert ist, fällt der Connector kontrolliert zurück: `gemini_image_sdk_unavailable_fallback_rest` + `gemini_image_transport:rest`.
  - SDK ändert **nicht** die Quota/Rate-Limit-Situation (429 bleibt möglich), kann aber Response-Parsing robuster machen.

## BA 32.44 – Erster erfolgreicher Gemini/Nano Banana + ElevenLabs Mini-Smoke

Der erste kontrollierte Mini-Smoke mit **Gemini/Nano Banana** als Bildprovider und **ElevenLabs** als Voiceprovider war erfolgreich. Die Pipeline erzeugte ein echtes Gemini-Bildasset, erkannte das Asset Manifest als `production_ready`, erzeugte eine echte ElevenLabs-MP3 und schrieb ein finales MP4.

### Referenzlauf (ohne Secrets)

| Feld | Wert |
|------|------|
| `run_id` | `video_gen_10m_1778248430908` |
| `image_provider` | `gemini_image` |
| `gemini_model` | `gemini-2.5-flash-image` |
| `gemini_transport` | `rest` |
| `generation_mode` | `gemini_image_live` |
| `asset_manifest_file_count` | `1` |
| `real_asset_file_count` | `1` |
| `placeholder_asset_count` | `0` |
| `asset_quality_gate.status` | `production_ready` |
| `asset_strict_ready` | `true` |
| `asset_loose_ready` | `true` |
| `voice_provider` | `ElevenLabs` |
| `requested_voice_mode` | `elevenlabs` |
| `effective_voice_mode` | `elevenlabs` |
| `voice_ready` | `true` |
| `voice_file_path` | `voiceover.mp3` |
| `voice_duration_seconds` | `14.675011` |
| `voice_is_dummy` | `false` |
| `render_used_placeholders` | `false` |
| `silent_render_expected` | `false` |
| `provider_blockers` | nur `live_motion_not_available` |
| `final_video.mp4` | vorhanden |

### Warnings (Einordnung)

- `gemini_image_model:gemini-2.5-flash-image`, `gemini_image_provider:gemini_image`, `gemini_image_transport:rest` — erwartbare Diagnose-Metadaten.
- `audio_shorter_than_timeline_padded_or_continued` — **kein** Bild-/Voice-Failure, sondern Timing-/Timeline-Hinweis.
- `live_motion_not_available` — **kein Blocker** für diesen Smoke, weil Motion nicht angefordert wurde.

### Was dieser Lauf beweist

- `GEMINI_API_KEY` / Google-Projekt/Billing/Quota war funktionsfähig (ohne Key-Werte zu dokumentieren).
- `IMAGE_PROVIDER=gemini_image` erreicht den Gemini-Provider und erzeugt ein echtes Bildasset.
- `asset_manifest.json` enthält `generation_mode=gemini_image_live`.
- `asset_quality_gate` erkennt `production_ready` (echte Datei, kein Placeholder).
- ElevenLabs erzeugt eine echte `voiceover.mp3` (`voice_ready=true`, kein Dummy/Fallback).
- `final_video.mp4` wird erzeugt.
- Render-Layer nutzt **keine** Placeholders (`render_used_placeholders=false`).

### Was dieser Lauf noch nicht beweist

- Keine Multi-Scene-Produktion (`max_scenes=1` / `max_live_assets=1`-Charakter).
- Kein Langform-Video (10-Minuten Produktionsumfang).
- Keine Motion-/Runway-Clips (bewusst out of scope; `motion_mode=static`).
- Keine finale YouTube-Qualität / Branding / Upload/Publishing.
- Kein Kostenvergleich zwischen Gemini/OpenAI/Leonardo.

### Neuer bevorzugter Mini-Produktionspfad (Smoke)

- **Image**: Gemini/Nano Banana (`IMAGE_PROVIDER=gemini_image`)
- **Voice**: ElevenLabs
- **Motion**: später optional (nicht Teil dieses Mini-Smokes)
- **Fallbacks**: Placeholder / Leonardo / OpenAI Image je nach Verfügbarkeit und Stabilität

### Nächster sinnvoller Schritt: BA 32.45 – Multi-Scene Gemini + ElevenLabs Smoke

Ziel:

- `max_scenes=3`
- `max_live_assets=3` (oder kontrolliert `2`)
- mehrere Gemini-Bilder + eine ElevenLabs-Voice
- prüfen, ob Timeline/Render mit mehreren echten Assets stabil bleibt
- weiterhin `motion_mode=static`

## BA 32.45 – Erster erfolgreicher Multi-Scene Gemini/Nano Banana + ElevenLabs Smoke

Der erste kontrollierte **Multi-Scene-Smoke** mit **Gemini/Nano Banana** als Bildprovider und **ElevenLabs** als Voiceprovider war erfolgreich. Die Pipeline erzeugte **zwei echte Gemini-Bildassets**, erkannte das Asset Manifest als `production_ready`, erzeugte eine echte ElevenLabs-MP3 und schrieb ein finales MP4.

### Referenzlauf (ohne Secrets)

| Feld | Wert |
|------|------|
| `run_id` | `video_gen_10m_1778249033109` |
| `image_provider` | `gemini_image` |
| `gemini_model` | `gemini-2.5-flash-image` |
| `gemini_transport` | `rest` |
| `generation_mode` | `gemini_image_live` |
| `asset_manifest_file_count` | `2` |
| `real_asset_file_count` | `2` |
| `placeholder_asset_file_count` | `0` |
| `asset_quality_gate.status` | `production_ready` |
| `asset_strict_ready` | `true` |
| `asset_loose_ready` | `true` |
| `requested_voice_mode` | `elevenlabs` |
| `effective_voice_mode` | `elevenlabs` |
| `voice_ready` | `true` |
| `voice_duration_seconds` | `28.932063` |
| `voice_is_dummy` | `false` |
| `render_used_placeholders` | `false` |
| `silent_render_expected` | `false` |
| `provider_blockers` | nur `live_motion_not_available` |
| `final_video.mp4` | vorhanden |

### Warnings (Einordnung)

- `gemini_image_model:gemini-2.5-flash-image`, `gemini_image_provider:gemini_image`, `gemini_image_transport:rest` — erwartbare Diagnose-Metadaten (für jede Bildszene möglich).
- `audio_shorter_than_timeline_padded_or_continued` — **kein** Provider-Failure, sondern Timing-/Timeline-Hinweis.
- `live_motion_not_available` — **kein Blocker**, da Motion nicht angefordert wurde.

### Was dieser Lauf beweist

- Gemini/Nano Banana kann **mehrere echte Bildassets** in einem Run erzeugen.
- `asset_manifest.json` enthält `generation_mode=gemini_image_live` für mehrere Szenen.
- `asset_quality_gate` erkennt `production_ready` (echte Dateien, keine Placeholders).
- ElevenLabs erzeugt eine echte `voiceover.mp3` (kein Dummy/Fallback).
- `final_video.mp4` wird erzeugt.
- Render-Layer nutzt **keine** Placeholders (`render_used_placeholders=false`).
- Der Multi-Scene-Pfad ist technisch funktionsfähig.

### Was dieser Lauf noch nicht beweist

- Kein Langform-Video / keine 10‑Minuten-Produktion.
- Keine Motion-/Runway-Clips.
- Keine finale YouTube-Qualität.
- Kein Kostenvergleich zwischen Gemini/OpenAI/Leonardo.
- Kein Upload/Publishing.
- Timing/Voice-Fit ist noch nicht optimiert (siehe Warning oben).

### Nächster sinnvoller Schritt: BA 32.46 – Timeline / Voice Fit Quality Check

Ziel:

- `audio_shorter_than_timeline_padded_or_continued` untersuchen
- Timeline‑Dauer vs. Voice‑Dauer prüfen
- sichtbar machen, ob Video gepadded/verlängert wurde
- später Fit‑Option verbessern, ohne Provider‑Logik anzufassen

## BA 32.52 – Erster sauberer 3‑Scene Gemini/Nano Banana + ElevenLabs Fit‑to‑Voice Smoke

Der erste kontrollierte 3‑Scene‑Smoke mit **Gemini/Nano Banana** als Bildprovider, **ElevenLabs** als Voiceprovider und **Fit‑to‑Voice** war erfolgreich. Die Pipeline erzeugte **drei echte Gemini‑Bildassets**, erkannte das Asset Manifest als **`production_ready`**, erzeugte eine **echte ElevenLabs‑MP3**, passte die **Timeline an die Voice‑Dauer** an und schrieb ein **finales MP4** ohne Render‑Placeholder.

Dieser Lauf ist der **Referenz‑Produktionsnachweis für drei Szenen** in dieser Kombination: 3/3 Live‑Bilder, 0 Placeholder, echte Voice, finaler Render, Timeline an Voice angepasst, **`timing_gap_status: ok`**. (Stärkerer Mehr‑Szenen‑Nachweis: **BA 32.54**.)

Kontext: **BA 32.51** (automatisches Fit Timeline to Voice für Bildläufe mit echter Voice bei `max_motion_clips=0`).

### Referenzlauf (ohne Secrets, ohne API‑Keys)

| Feld | Wert |
|------|------|
| `run_id` | `video_gen_10m_1778259222293` |
| `image_provider` | `gemini_image` |
| `gemini_model` | `gemini-2.5-flash-image` |
| `gemini_transport` | `rest` |
| `generation_mode` (Manifest‑Top/Muster) | `gemini_image_live` |
| `asset_manifest_file_count` | `3` |
| `real_asset_file_count` | `3` |
| `placeholder_asset_count` | `0` |
| `asset_quality_gate.status` | `production_ready` |
| `asset_strict_ready` | `true` |
| `asset_loose_ready` | `true` |
| `requested_voice_mode` | `elevenlabs` |
| `effective_voice_mode` | `elevenlabs` |
| `voice_ready` | `true` |
| `voice_duration_seconds` | `42.213878` |
| `voice_is_dummy` | `false` |
| `timeline_duration_seconds` | `43.0` |
| `final_video_duration_seconds` | `43.04` |
| `requested_duration_seconds` | `60.0` |
| `timing_gap_abs_seconds` | `0.786122` (≈; aus Run) |
| `timing_gap_status` | `ok` |
| `fit_strategy` | `fit_to_voice` |
| `render_used_placeholders` | `false` |
| `silent_render_expected` | `false` |
| `provider_blockers` | nur `live_motion_not_available` |

**Motion/Runway:** für diesen Smoke **nicht** getestet und **nicht** erforderlich.

### Warnings / Hinweise im Lauf (Einordnung)

- `gemini_image_model:gemini-2.5-flash-image`
- `gemini_image_provider:gemini_image`
- `gemini_image_transport:rest`
- `ba267_video_fitted_to_voice:voice_audio~42.21s_padding=0.75s_target_total=43s_scenes=3`
- `timeline_fit_to_voice_applied`

**Einordnung:**

- **`timeline_fit_to_voice_applied`** ist ein **positiver** Hinweis (Timeline an Voice angepasst), **kein** Fehler.
- **`live_motion_not_available`** ist **kein Blocker**, weil Motion nicht angefordert wurde.
- **Keine** Gemini‑429‑Fehler im Referenzlauf.
- **Keine** Placeholder‑Assets; **keine** Voice‑Fallbacks.
- **`render_used_placeholders=false`**, **`timing_gap_status=ok`**.

### Was dieser Lauf beweist

- Gemini/Nano Banana kann **mehrere echte Bildassets** erzeugen.
- `asset_manifest.json` enthält **`generation_mode=gemini_image_live`** für **drei** Szenen.
- `asset_quality_gate` erkennt **`production_ready`**.
- ElevenLabs erzeugt eine echte **`voiceover.mp3`** (kein Dummy).
- **`final_video.mp4`** wird erzeugt.
- Render‑Layer nutzt **keine** Placeholders.
- **Fit‑to‑Voice** funktioniert für **statische Bildläufe** (inkl. Dashboard‑Kontext BA 32.51).
- **Timing‑Gap** liegt **innerhalb der Toleranz** (`timing_gap_status: ok`).
- Der **3‑Scene‑Pfad** ist technisch **funktionsfähig**.

### Was dieser Lauf noch nicht beweist

- Kein **Langform‑Video** / keine **10‑Minuten‑Produktion**.
- Keine **Motion‑/Runway‑Clips**.
- Keine finale **YouTube‑Qualität** (Branding, Mastering, o. ä.).
- Kein **Kostenvergleich** zwischen Gemini/OpenAI/Leonardo.
- Kein **Upload/Publishing**.
- **5‑Szenen‑Pfad:** mit **BA 32.54** nachgewiesen; **8–10 Szenen:** nächster Schritt **BA 32.55**.

### Neuer bevorzugter Mini‑Produktionspfad (Smoke)

- **Image:** Gemini/Nano Banana (`IMAGE_PROVIDER=gemini_image`)
- **Voice:** ElevenLabs
- **Timing:** Fit‑to‑Voice für static image runs (BA 32.51; `max_motion_clips=0` im Video‑Generate‑Default)
- **Motion:** später optional (Runway)
- **Fallbacks:** Placeholder / Leonardo / OpenAI Image je nach Verfügbarkeit und Konfiguration

## BA 32.54 – Erster erfolgreicher 5‑Scene Gemini/Nano Banana + ElevenLabs Fit‑to‑Voice Smoke

Der erste kontrollierte **5‑Scene‑Smoke** mit **Gemini/Nano Banana** als Bildprovider, **ElevenLabs** als Voiceprovider und **Fit‑to‑Voice** war erfolgreich. Die Pipeline erzeugte **fünf echte Gemini‑Bildassets**, erkannte das Asset Manifest als **`production_ready`**, erzeugte eine **echte ElevenLabs‑MP3**, passte die **Timeline an die Voice‑Dauer** an und schrieb ein **finales MP4** ohne Render‑Placeholder.

Dieser Lauf ist der bisher stärkste **technische Produktionsnachweis** in dieser Kombination: **5/5** Live‑Bilder, 0 Placeholder, echte Voice, finaler Render, Timeline an Voice angepasst, **`timing_gap_status: ok`**.

Kontext: **BA 32.51** (Fit Timeline to Voice), Vorgänger‑Nachweis **BA 32.52** (3 Szenen).

### Referenzlauf (ohne Secrets, ohne API‑Keys)

| Feld | Wert |
|------|------|
| `run_id` | `video_gen_10m_1778260095287` |
| `image_provider` | `gemini_image` |
| `gemini_model` | `gemini-2.5-flash-image` |
| `gemini_transport` | `rest` |
| `generation_mode` (Manifest‑Muster) | `gemini_image_live` |
| `real_asset_file_count` | `5` |
| `placeholder_asset_count` | `0` |
| `asset_quality_gate.status` | `production_ready` |
| `asset_strict_ready` / `asset_loose_ready` | `true` / `true` |
| `voice_ready` | `true` |
| `voice_duration_seconds` | `121.672562` |
| `timeline_duration_seconds` | `122.0` |
| `final_video_duration_seconds` | `122.04` |
| `requested_duration_seconds` | `90.0` |
| `timing_gap_abs_seconds` | `0.327438` (≈; aus Run) |
| `timing_gap_status` | `ok` |
| `fit_strategy` | `fit_to_voice` |
| `render_used_placeholders` | `false` |

**Ergänzende Referenzfelder:** `asset_manifest_file_count` `5`; `requested_voice_mode` / `effective_voice_mode` `elevenlabs`; `voice_is_dummy` `false`; `silent_render_expected` `false`; `provider_blockers` nur `live_motion_not_available`.

**Motion/Runway:** für diesen Smoke **nicht** getestet und **nicht** erforderlich.

**Hinweis zu `requested_duration_seconds`:** Ziel im Request war **90** s; die **finale** Fit‑/Timeline‑Dauer liegt bei ca. **122** s, weil die **gemessene Voice** länger ist und **Fit‑to‑Voice** die Timeline **korrekt an die Voice** priorisiert (nicht an die ursprüngliche Request‑Dauer).

### Warnings / Hinweise im Lauf (Einordnung)

- `gemini_image_model:gemini-2.5-flash-image`
- `gemini_image_provider:gemini_image`
- `gemini_image_transport:rest`
- `ba267_video_fitted_to_voice:voice_audio~121.67s_padding=0.75s_target_total=122s_scenes=5`
- `timeline_fit_to_voice_applied`

**Einordnung:**

- **`timeline_fit_to_voice_applied`** ist ein **positiver** Hinweis, **kein** Fehler.
- **`live_motion_not_available`** ist **kein Blocker**, weil Motion nicht angefordert wurde.
- **Keine** Gemini‑429‑Fehler im Referenzlauf.
- **Keine** Placeholder‑Assets; **keine** Voice‑Fallbacks.
- **`render_used_placeholders=false`**, **`timing_gap_status=ok`**.

### Was dieser Lauf beweist

- Gemini/Nano Banana kann **fünf echte Bildassets** erzeugen.
- `asset_manifest.json` enthält **`generation_mode=gemini_image_live`** für **fünf** Szenen.
- `asset_quality_gate` erkennt **`production_ready`**.
- ElevenLabs erzeugt eine echte **`voiceover.mp3`**.
- **`final_video.mp4`** wird erzeugt.
- Render‑Layer nutzt **keine** Placeholders.
- **Fit‑to‑Voice** funktioniert für **fünf statische Bildszenen**.
- **Timing‑Gap** liegt **innerhalb der Toleranz** (`timing_gap_status: ok`).
- Der **5‑Scene‑Pfad** ist technisch **funktionsfähig**.

### Was dieser Lauf noch nicht beweist

- Kein **Langform‑Video** / keine **10‑Minuten‑Produktion**.
- Keine **Motion‑/Runway‑Clips**.
- Keine finale **YouTube‑Qualität**.
- Kein **Kostenvergleich** zwischen Gemini/OpenAI/Leonardo.
- Kein **Upload/Publishing**.
- Keine **8–10‑Szenen‑Stabilität** (nächster Schritt **BA 32.55**).

### Neuer bevorzugter Produktionspfad für kleine Videos

- **Image:** Gemini/Nano Banana (`IMAGE_PROVIDER=gemini_image`)
- **Voice:** ElevenLabs
- **Timing:** Fit‑to‑Voice für static image runs (BA 32.51; `max_motion_clips=0` im Video‑Generate‑Default)
- **Motion:** später optional (Runway)
- **Fallbacks:** Placeholder / Leonardo / OpenAI Image je nach Verfügbarkeit und Konfiguration

### Nächster sinnvoller Schritt: BA 32.55 – 8‑Scene / 3‑Minute Gemini + ElevenLabs Smoke

Ziel:

- `max_scenes=8`
- `max_live_assets=8` oder kontrolliert `6`
- mehrere Gemini‑Bilder
- eine ElevenLabs‑Voice
- Fit‑to‑Voice aktiv
- prüfen, ob Timeline/Render mit **mehr Szenen** stabil bleibt
- weiterhin `motion_mode=static` (oder API‑Äquivalent für statischen Bildlauf)

## BA 32.56 – Automatisierter Live‑Smoke‑Runner (`run_live_video_smoke.py`)

Kontrollierte **VideoPipe‑Smokes** gegen einen **bereits laufenden** FastAPI‑Server (das Script **startet keinen** Server). Requests gehen an `POST /founder/dashboard/video/generate` mit **`raw_text`** (keine URL), damit Provider‑Smokes nicht an Extraktion scheitern.

### Voraussetzungen

- Lokaler Stack läuft (z. B. Uvicorn auf Port **8020**); Default‑Base: `http://127.0.0.1:8020` (überschreibbar mit `--base-url`).
- Echte Provider‑Keys in der **Shell**/Umgebung des Servers (keine `.env` aus dem Repo lesen; keine Keys in Logs oder Reports).
- **`--confirm-provider-costs`** ist **Pflicht** — ohne dieses Flag bricht das Script ab (bewusste Kostenbestätigung).
- Profile **8min** / **12min** und das Meta‑Profil **`all`** mit Langläufern nur mit **`--allow-long-runs`**; ohne dieses Flag werden 8min/12min nicht ausgeführt (bei `all` laufen dann nur **mini** + **3min**).

### CLI‑Beispiele

```text
python scripts/run_live_video_smoke.py --profile mini --confirm-provider-costs
python scripts/run_live_video_smoke.py --profile 3min --confirm-provider-costs
python scripts/run_live_video_smoke.py --profile all --confirm-provider-costs
python scripts/run_live_video_smoke.py --profile all --confirm-provider-costs --allow-long-runs
python scripts/run_live_video_smoke.py --base-url http://127.0.0.1:8020 --profile mini --confirm-provider-costs
```

### Profile (Kurzüberblick)

| Profil | `duration_target_seconds` | `max_scenes` / `max_live_assets` |
|--------|---------------------------|-----------------------------------|
| `mini` | 60 | 3 / 3 |
| `3min` | 180 | 5 / 5 |
| `8min` | 480 | 18 / 18 (nur mit `--allow-long-runs`) |
| `12min` | 720 | 24 / 24 (nur mit `--allow-long-runs`) |
| `all` | — | mini + 3min; mit `--allow-long-runs` zusätzlich 8min + 12min |

Gemeinsam im Request u. a.: `allow_live_assets=true`, `voice_mode=elevenlabs`, `motion_mode=static`, `max_motion_clips=0`.

### Reports

Unter `output/live_smoke_reports/`:

- `live_smoke_<timestamp>_<profile>.json`
- `live_smoke_<timestamp>_<profile>.md`

Auswertung **PASS** / **WARN** / **FAIL** nach den im Script dokumentierten Regeln (u. a. `asset_quality_gate.status`, Placeholder‑Zählung, Voice‑Readiness, Timing‑Gap, lokale `final_video_path`).

### Sicherheit

- Script liest **keine** `.env`; Reports **redaktieren** typische Secret‑Muster (z. B. `sk-…`, `AIza…`, Bearer‑Token).
- **Keine** Firestore‑Änderung, **keine** Dashboard‑UI‑Änderung durch dieses Runbook/Script.

### Tests (CI)

`python -m pytest tests/test_ba356_live_smoke_runner.py` — **Mocks** nur, **keine** echten HTTP‑Provider‑Calls.

## BA 32.63 — Runway Motion Clip (Smoke, optional Live)

**Ziel:** Erster **echter oder gemockter** Runway-Clip für **Motion-Slot 1** landet als **`video_path`** im **`asset_manifest.json`** und wird vom bestehenden **Timeline/Render**-Pfad genutzt.

**Voraussetzungen (Live):**

- Umgebungsvariable **`RUNWAY_API_KEY`** (nicht ins Repo; Runbook/Logs ohne Werte).
- Video-Generate-Request mit **`max_motion_clips` ≥ 1** (für ersten Test **`max_motion_clips=1`** empfohlen), **`motion_clip_duration_seconds=10`**, typisch **`motion_clip_every_seconds=60`**.
- Bild-Assets für die betroffene Szene müssen existieren (Runway Image-to-Video nutzt **`image_path`** der Szene).

**Erwartung nach erfolgreichem Live-Lauf:**

- `run_summary.json`: **`motion_slot_plan.planned_count` ≥ 1**, erster Slot **`status: rendered`**, **`motion_clip_artifact.rendered_count`** = 1, **`video_clip_paths`** enthält z. B. `scene_001_motion.mp4`.
- **`asset_manifest.json`**: betroffene Zeile mit **`generation_mode: runway_video_live`**, **`provider_used: runway`**, **`video_path`** gesetzt.
- **`final_video.mp4`**: Szene mit Video-Clip (sofern ffmpeg-Pfad wie bei BA 26.3).

**Ohne Key / bei Fehler:** Warnungen z. B. **`runway_key_missing_motion_skipped`** oder **`runway_video_generation_failed:…`** (kein Response-Body), statische Bild-Render-Kette bleibt nutzbar.

**Tests (CI, keine Live-Calls):** `python -m pytest tests/test_ba363_runway_clip_provider_smoke.py`.

**Chronik:** Erster erfolgreicher **Runway + Gemini + ElevenLabs**-Hybrid über Dashboard/`run_ba265_url_to_final` — siehe **BA 32.65** in [real_video_build_wiring_map.md](real_video_build_wiring_map.md) (`run_id` `video_gen_10m_1778273622251`, Readiness **BA 32.64**).

## BA 32.57 – Erster erfolgreicher 8min Gemini/Nano Banana + ElevenLabs Live Smoke

Der erste **8min**‑Profil‑Live‑Smoke mit **Gemini/Nano Banana** als Bildprovider, **ElevenLabs** als Voiceprovider und **Fit‑to‑Voice** war erfolgreich. Die Pipeline erzeugte **sieben** echte Gemini‑Bildassets, erkannte das Asset Manifest als **`production_ready`**, erzeugte eine echte **ElevenLabs‑MP3**, passte die **Timeline an die Voice‑Dauer** an und schrieb ein **finales MP4** ohne Render‑Placeholder.

**Motion/Runway:** für diesen Smoke **nicht** getestet und **nicht** erforderlich.

### Referenzlauf (ohne Secrets, ohne API‑Keys)

| Feld | Wert |
|------|------|
| profile | `8min` (Runner: `scripts/run_live_video_smoke.py` mit `--confirm-provider-costs` und `--allow-long-runs`) |
| run_id | `video_gen_10m_1778263227563` |
| outcome | **PASS** |
| http_status | `200` |
| image_provider | `gemini_image` |
| model | `gemini-2.5-flash-image` |
| transport | `rest` |
| real_asset_file_count | `7` |
| placeholder_asset_count | `0` |
| asset_quality_gate.status | `production_ready` |
| voice_ready | `true` |
| voice_duration_seconds | `178.654331` |
| requested_duration_seconds | `480.0` |
| final_video_duration_seconds | `179.04` |
| timing_gap_status | `ok` |
| fit_strategy | `fit_to_voice` |
| render_used_placeholders | `false` |
| final_video_size_bytes | `4470979` |

**Ergänzend (ohne Pfade):** `generation_mode` im Manifest‑Muster **`gemini_image_live`**; `asset_manifest_file_count` **`7`**; `asset_strict_ready` **true**; `voice_mode` **elevenlabs**; `voice_file_ready` **true**; `voice_is_dummy` **false**; `timeline_duration_seconds` **`179.0`**; `timing_gap_abs_seconds` **≈ `0.345669`**; `provider_blockers` nur **`live_motion_not_available`**.

### Wichtig einordnen

- **Outcome PASS** bedeutet: alle **Kernkriterien** des Smoke‑Runners sind erfüllt.
- **`requested_duration_seconds`** war **480** s (8min‑Profil), die **finale** Video‑/Timeline‑Dauer liegt bei ca. **179** s, weil **Fit‑to‑Voice** die **echte Voice‑Dauer** priorisiert — das ist **kein Fehler**, sondern **gewünschtes Verhalten** für static image runs mit echter Voice.
- **`live_motion_not_available`** ist **kein Blocker**, weil Motion nicht angefordert wurde.
- **Keine** Placeholder‑Assets; **keine** Voice‑Fallbacks.
- **`render_used_placeholders=false`**, **`timing_gap_status=ok`**.
- **`final_video.mp4`** existiert und ist **> 0 Bytes**.

### Warnings / Hinweise im Lauf

- mehrfach `gemini_image_model:gemini-2.5-flash-image`
- mehrfach `gemini_image_provider:gemini_image`
- mehrfach `gemini_image_transport:rest`
- `ba267_video_fitted_to_voice:voice_audio~178.65s_padding=0.75s_target_total=179s_scenes=7`
- `timeline_fit_to_voice_applied`

**Kurz‑Einordnung:** `timeline_fit_to_voice_applied` ist ein **positiver** Hinweis; **keine** Gemini‑429‑Fehler im Referenzlauf.

### Was dieser Lauf beweist

- Gemini/Nano Banana kann **mehrere echte Bildassets** für einen längeren Smoke erzeugen.
- `asset_manifest.json` enthält **`generation_mode=gemini_image_live`** für **sieben** Szenen.
- `asset_quality_gate` erkennt **`production_ready`**.
- ElevenLabs erzeugt eine echte **`voiceover.mp3`**.
- **`final_video.mp4`** wird erzeugt.
- Render‑Layer nutzt **keine** Placeholders.
- **Fit‑to‑Voice** funktioniert im **8min**‑Profil.
- **Timing‑Gap** liegt **innerhalb der Toleranz** (`timing_gap_status: ok`).
- Der **8min**‑Live‑Smoke‑Pfad ist technisch **funktionsfähig**.

### Was dieser Lauf noch nicht beweist

- Keine **10‑** oder **12‑Minuten‑Produktion**.
- Keine **Motion‑/Runway‑Clips**.
- Keine finale **YouTube‑Qualität**.
- Kein **Upload/Publishing**.
- Kein **vollständiger Kostenvergleich** zwischen Gemini/OpenAI/Leonardo.
- Keine **dauerhafte Produktionsautomatisierung/Scheduler**.

### Nächster sinnvoller Schritt: BA 32.58 – 12min Gemini + ElevenLabs Live Smoke

Ziel:

- `profile=12min` mit **`--confirm-provider-costs`** und **`--allow-long-runs`**
- prüfen, ob **Provider/Quota**, **Timeline**, **Render** bei **12min** stabil bleiben
- weiterhin `motion_mode=static`
