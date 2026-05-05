# Real Video Build Wiring Map

## Ziel
Vom **echten Script/Story-Pack** zu einem **lokal gespeicherten Video** (Preview + Final‑Package) – ohne Upload/Publishing.

**Scope (BA 25.0):** reine Analyse/Dokumentation. Keine neuen Features, keine Provider‑Calls, keine Secrets.

## Existing Building Blocks

| Schritt | Script | Input | Output | Real/Placeholder | Hinweise |
|---|---|---|---|---|---|
| 1. Script / Story Pack Input | *(extern / API / Export)* | URL, `ProductionPromptPlan.json`, oder `GenerateScriptResponse`/Story‑Pack | **Plan/Pack** für nachfolgende Schritte | real | Aktuell gibt es mehrere mögliche Quellen (API, CLI, Exporte). |
| 2. Scene Asset Pack Export | `scripts/export_scene_asset_pack.py` | `--url` **oder** `--prompt-plan-json` | `output/scene_asset_pack_<run_id>/scene_asset_pack.json` + `leonardo_prompts.txt` + `shot_plan.md` + `founder_summary.txt` | real | Baut/erzwingt Scene Expansion im Plan. `--duration-minutes` wirkt nur auf Plan‑Erzeugung via URL. |
| 3. Asset Runner | `scripts/run_asset_runner.py` | `scene_asset_pack.json` | `output/generated_assets_<run_id>/scene_001.png…` + `asset_manifest.json` | **placeholder default** / optional live | Default `--mode placeholder` erzeugt bewusst PIL‑Placeholder‑PNGs. `--mode live` nutzt Leonardo nur mit `LEONARDO_API_KEY`, sonst Fallback + Warnungen. |
| 4. Timeline Manifest | `scripts/build_timeline_manifest.py` | `--asset-manifest …/asset_manifest.json` + optional `--audio-path` | `output/timeline_<run_id>/timeline_manifest.json` | real | Legt `timeline_manifest.audio_path` **nur** fest, wenn `--audio-path` gesetzt ist. |
| 5. Voiceover / Narration Audio | `scripts/build_full_voiceover.py` | `--url` **oder** `--prompt-plan-json` (+ optional `--full-script-json`/Plan‑Felder) | `output/full_voice_<run_id>/narration_script.txt`, `full_voiceover.mp3`, `voice_manifest.json` | **smoke default** / optional real | Default ist „Smoke“ (stilles MP3 mit geschätzter Dauer). Echt nur mit Keys (ElevenLabs/OpenAI). |
| 6. Clean Video Render | `scripts/render_final_story_video.py` | `--timeline …/timeline_manifest.json` (Bilder liegen via `assets_directory`) + optional Audio (über Timeline) | MP4 (clean) + optional `output/render_<run_id>/render_output_manifest.json` | real (ffmpeg) | Ohne Audio: silent + Warnung. Bei fehlendem ffmpeg: `blocking_reasons` (kein Video). Motion/Transition Layer steckt hier (BA 20.4). |
| 7. Subtitle File | `scripts/build_subtitle_file.py` | `--narration-script …/narration_script.txt` + optional `--timeline-manifest …` + Subtitle‑Optionen | `output/subtitles_<run_id>/subtitles.srt` + `subtitle_manifest.json` | real | Subtitle‑Quelle: `narration` (default) oder `audio` (Transkription via OpenAI nur mit Key, sonst Fallback). |
| 8. Subtitle Burn‑In Preview | `scripts/burn_in_subtitles_preview.py` | `--input-video <clean_video.mp4>` + `--subtitle-manifest …/subtitle_manifest.json` | `output/subtitle_burnin_<run_id>/preview_with_subtitles.mp4` (+ `burnin_output_manifest.json`) | real (ffmpeg) | Für `typewriter` kann ASS‑Renderer genutzt werden; bei „suspected burned input“ blockt es ohne `--force` (BA 20.6c). |
| 9. Final Render Package | `scripts/run_final_render.py` | `output/local_preview_<run_id>/preview_with_subtitles.mp4` + Gates/Approval + Dry‑Run | `output/final_render_<run_id>/final_video.mp4` + `final_render_result.json` + `FINAL_OPEN_ME.md` + `final_render_report.md` | **copy‑v1** | Final Render ist im Local MVP bewusst nur Copy aus Preview (kein neuer Render). Robustheit/Idempotenz: BA 24.6. |

## File Handoff Map (konkrete Pfadkette)

> **Wichtig:** Heute ist die Kette nicht „one command“ durchverkabelt. Die Artefakte existieren, aber einige Hand‑offs (Audio→Timeline, Script→Pack) sind noch manuell/teilweise redundant.

- **Input Script / Story‑Pack**
  - Quelle A: `POST /generate-script` (Text‑Script, kein Video‑Pack)
  - Quelle B: `ProductionPromptPlan.json` (Prompt‑Plan Export)
  - Quelle C: Story‑Engine Export/Pack (falls vorhanden)
- **Scene Asset Pack**
  - `output/scene_asset_pack_<run_id>/scene_asset_pack.json`
- **Asset Manifest**
  - `output/generated_assets_<run_id>/asset_manifest.json`
- **Timeline Manifest**
  - `output/timeline_<run_id>/timeline_manifest.json`
- **Voiceover**
  - `output/full_voice_<run_id>/full_voiceover.mp3`
  - `output/full_voice_<run_id>/narration_script.txt`
- **Clean Video**
  - Output aus `render_final_story_video.py` (Pfad/Name abhängig von CLI‑Args; häufig via `--output-video …/clean_video.mp4` im Preview‑Flow)
- **Subtitles**
  - `output/subtitles_<run_id>/subtitle_manifest.json`
  - `output/subtitles_<run_id>/subtitles.srt`
  - optional: `*.ass` (Typewriter Burn‑in Renderer)
- **Preview With Subtitles**
  - `output/subtitle_burnin_<run_id>/preview_with_subtitles.mp4` *(oder im Preview‑Flow nach `output/local_preview_<run_id>/preview_with_subtitles.mp4` kopiert/kolokiert)*
- **Final Package**
  - `output/final_render_<run_id>/final_video.mp4` *(Copy‑V1 aus Preview)*

## Current Placeholder Points

- **Placeholder Images**: `run_asset_runner.py` default `--mode placeholder` (PIL‑PNGs).
- **Smoke Audio**: `build_full_voiceover.py` default „smoke“ (stille MP3 mit Dauer‑Heuristik).
- **Final Render Copy‑V1**: `run_final_render.py` kopiert `preview_with_subtitles.mp4` → `final_video.mp4`.
- **Provider Live Modes optional**:
  - Leonardo live nur mit Key (sonst Fallback Placeholder).
  - OpenAI/ElevenLabs TTS nur mit Key (sonst Smoke).
  - Audio‑Transkription (OpenAI) nur mit Key (sonst Narration‑Fallback).

## Missing Wiring (konkrete Lücken)

- **Script/Story‑Pack → `scene_asset_pack.json`**
  - `export_scene_asset_pack.py` erwartet URL oder `ProductionPromptPlan.json`. Für `GenerateScriptResponse`/Story‑Pack fehlt ein direkter Adapter.
- **Voiceover → Timeline (`audio_path`)**
  - `build_timeline_manifest.py` setzt `audio_path` nur über `--audio-path`. Der Voiceover‑Output wird heute nicht automatisch eingespeist.
- **Run‑ID Propagation**
  - Es gibt mehrere Run‑IDs pro Teil‑Script (`scene_asset_pack_<rid>`, `generated_assets_<rid>`, `timeline_<rid>`, `full_voice_<rid>`…). Es fehlt eine durchgehende „eine run_id“ Konvention + Weitergabe.
- **Unified Output Package**
  - Local Preview hat ein Paket `output/local_preview_<run_id>/…`, Final Render hat `output/final_render_<run_id>/…`. Für „Real Build“ fehlt ein durchgehendes „Build‑Package“ mit allen Zwischenartefakten (oder stabile Verweise).
- **One‑Command Orchestrator**
  - `run_local_preview_pipeline.py` ist bereits ein Orchestrator – aber er startet **nicht** die vorgelagerten Schritte (Script→Pack→Assets→Timeline→Voiceover) automatisch.

## Shortest Real Local MVP Path (heute, ohne neue Features)

Ziel: erst **2–3 Minuten** stabil, dann Richtung **10 Minuten** skalieren.

**Minimal‑Pfad (lokal, akzeptiert Placeholder/Smoke):**

1) `export_scene_asset_pack.py` mit realer URL oder vorhandenem `ProductionPromptPlan.json`  
2) `run_asset_runner.py` im Placeholder‑Mode  
3) `build_full_voiceover.py` im Smoke‑Mode *(oder echte Audio‑Datei bereitstellen)*  
4) `build_timeline_manifest.py --audio-path <full_voiceover.mp3>`  
5) `render_final_story_video.py` → clean MP4  
6) `build_subtitle_file.py` aus `narration_script.txt` (+ optional Timeline)  
7) `burn_in_subtitles_preview.py` → `preview_with_subtitles.mp4`  
8) (optional) `run_local_preview_pipeline.py` nutzen, **wenn** man dessen Inputs (Timeline + Narration) bereits hat, um Preview‑Paket‑Kolokation + Reports zu bekommen  
9) `run_final_render.py` (Copy‑V1) → `final_video.mp4` Paket

**Warum nicht sofort 10 Minuten?**
- 10 Minuten heißt mehr Beats/Szenen, längere Audio‑Dauer, höhere ffmpeg‑Laufzeit, mehr Artefakte. Stabilität gewinnt, wenn erst 2–3 Minuten sauber verkabelt sind.

## BA 25.x Proposed Plan

| BA | Titel | Status | Ziel |
|---|---|---|---|
| BA 25.1 | Real Video Build Orchestrator CLI | **done** | Verbindet vorhandene Scripts zu **einem** Run (kein Provider‑Zwang; Placeholder/Smoke erlaubt). |
| BA 25.2 | Script/Story-Pack Input Adapter | **done** | Adapter nimmt `GenerateScriptResponse` **oder** Story‑Pack‑JSON und erzeugt ein Orchestrator‑kompatibles `scene_asset_pack.json` (lokal, ohne URL‑Input). |
| BA 25.3 | URL-to-Script Bridge | **done** | Lokale CLI nimmt Artikel-/YouTube-URL und schreibt eine `GenerateScriptResponse`‑kompatible JSON; kein Render, kein Orchestrator‑Lauf. |
| BA 25.4 | Real Local Preview Run | **done** | Lokale CLI verdrahtet `generate_script_response.json` → BA 25.2 Adapter → BA 25.1 Orchestrator und schreibt ein Aggregat unter `output/real_local_preview_<run_id>/`. |
| BA 25.5 | URL-to-Final-Video Smoke | **done** | End‑to‑End lokal: URL → `preview_with_subtitles.mp4` → `final_video.mp4` (ohne Publishing). |
| BA 25.6 | URL-to-Final-Video Smoke Hardening | **done** | Stabiler Result-Contract, Auto-Approve-Transparenz, `--no-auto-approve`, strukturierte `failure_stage`, Idempotenz-Anzeige (`skipped_existing`), Operator-`URL_TO_FINAL_VIDEO_OPEN_ME.md`. **Local URL-to-Final-Video MVP: completed.** |

**Nach BA 25.6:** Der Local URL-to-Final-Video MVP ist abgeschlossen. **BA 26 — Real Content Live Smoke** (siehe [PIPELINE_PLAN.md](../../PIPELINE_PLAN.md), **BA 26.0 Scope Freeze**, Status **done**): zuerst **Leonardo Live** für echte Bilder, **echte Artikel-URL**, Ausgabe **lokal** (`final_video.mp4`). **Video-Clips:** separater Entscheid — **Spike Runway vs. Google Veo**, danach **nur ein** Video-Provider-Connector (nicht parallel). **Sora** nicht als Primärpfad. **Kein** Upload/Publishing/YouTube.

### BA 26 — Live Provider Smoke (geplant) / Ist-Stand

- **Leonardo Live (erster Bildpfad):** `scripts/run_asset_runner.py` (`--mode live`, u. a. `LEONARDO_API_KEY`, optional Endpoint/Model-ID). Durchreichen via **`--asset-mode live`** (BA 25.1 / BA 25.4 / URL-to-Final-Smoke).
- **Video-Provider:** **BA 26.2** (`scripts/runway_image_to_video_smoke.py`) erzeugt **einen** lokalen Runway-Testclip (bei `RUNWAY_API_KEY`) — **ohne** Timeline-/Render-Integration. **Google Veo** bleibt Kandidat; Vergleich/Connector-Wahl in **BA 26.3** — **nicht** beide Video-Provider parallel einbauen.
- **Sora:** **nicht** als Primär-Connector priorisiert (Scope Freeze).
- **Kling:** `app/production_connectors/kling_connector.py` nur **Dry-Run**; nicht Teil der BA-26-Video-Wahl.
- **Render:** `render_final_story_video.py` = **Stillimages** + optional ffmpeg-**basic** — echte Provider-Clips erst nach **BA 26.4** (Ingest) / **26.5** (Smoke mit Clips).
- **Lücke:** Video-Gen-API + Ingest/Timeline für Clips; bis dahin **BA 26.1** = Artikel-URL + **Leonardo** + bestehender Still-Render bis `final_video.mp4`.

## BA 25.5 — URL-to-Final-Video Smoke (**done**)

### One-Command Runner (lokal)

```bash
python scripts/run_ba_25_5_url_to_final_video_smoke.py \
  --url "https://example.com/article" \
  --run-id real_mini_001 \
  --out-dir output \
  --duration-minutes 3 \
  --asset-mode placeholder \
  --voice-mode smoke \
  --motion-mode static \
  --subtitle-style typewriter \
  --print-json
```

### Output (additiv)

- `output/url_to_final_video_<run_id>/url_to_final_video_result.json` (BA 25.5/25.6 Result-Index, Schema `ba_25_6_url_to_final_video_result_v1`)
- `output/url_to_final_video_<run_id>/URL_TO_FINAL_VIDEO_OPEN_ME.md` (Operator-Hinweis, u. a. Auto-Approve)
- `output/url_script_<run_id>/generate_script_response.json` (BA 25.3)
- `output/real_local_preview_<run_id>/real_local_preview_result.json` (BA 25.4 Aggregat)
- `output/subtitle_burnin_<run_id>/preview_with_subtitles.mp4` (Preview-Video aus Real-Build)
- `output/local_preview_<run_id>/...` (Smoke-only Adapter-Paket für BA 24.x Gates)
- `output/final_render_<run_id>/final_video.mp4` (BA 24.3 Final Render Copy‑V1)

## BA 25.6 — URL-to-Final-Video Smoke Hardening (**done**)

### Offizieller MVP-Smoke-Befehl

```bash
python scripts/run_ba_25_5_url_to_final_video_smoke.py \
  --url "https://example.com" \
  --run-id mein_smoke \
  --out-dir output \
  --print-json
```

### Auto-Approve (Default)

- Standard: Der Runner schreibt ein **Smoke/Dev**-`human_approval.json` (`auto_approved`, `smoke_dev_flow`), damit BA 24.3 die Gates passieren und `final_video.mp4` erzeugt wird.
- Result: `auto_approved: true`, Warnung `ba25_6_auto_approved_for_smoke_dev_only`, `metadata.approval_note` erklärt den Dev-Kontext.

### `--no-auto-approve`

- Es wird **kein** `human_approval.json` geschrieben; **kein** Aufruf von Final Render.
- Result: `status: blocked`, `failure_stage: human_approval_gate`, `blocking_reasons` enthält `human_approval_required_before_final_render`, `final_video_path` leer.

### Output-Ordner und finales Video

- Sammelordner: `output/url_to_final_video_<run_id>/`
- Finales Video: `output/final_render_<run_id>/final_video.mp4`
- Idempotenz: Wenn `final_video.mp4` bereits **>0 Byte** existiert, meldet BA 24.3 `skipped_existing` (im Result als `status` durchgereicht); mit `--force` neu kopieren.

### Bekannte Grenzen (unverändert)

- Placeholder-Bilder / Smoke-Audio im Default; kein Publishing, kein Upload, keine neuen Provider-Pflichten in diesem MVP.

### Reality-Smoke (manuell)

- Erwartung bei gültiger URL und lokalem Tooling: `ok: true`, `status: completed` oder `skipped_existing`, `final_video_path` gesetzt, Datei **>0 Byte**.
- Für maschinenlesbares JSON ggf. Logs umleiten (`stderr`), falls die Python-Logging-Konfiguration Meldungen vor das JSON schreibt.

## BA 25.2 — Script/Story-Pack Input Adapter (**done**)

### Scope

- **Input**: lokales JSON im Stil von `GenerateScriptResponse` (Felder `title`, `hook`, `chapters`, `full_script`, `sources`, `warnings`) oder ein einfacher Story‑Pack (`scenes`/`beats`).
- **Output**: `scene_asset_pack.json`, kompatibel genug für `scripts/run_real_video_build.py --scene-asset-pack ...`.
- **Kein** URL‑Input (BA 25.3), **kein** Provider/LLM/TTS‑Live.

### Wiring

- Adapter-Modul: `app/real_video_build/script_input_adapter.py`
- Optionales CLI: `scripts/adapt_script_to_scene_asset_pack.py`
- Orchestrator bevorzugt **echte Narration-Felder** in Beats (`narration`/`voiceover_text`) und fällt sonst auf `visual_prompt` zurück.

## BA 25.1 — Real Video Build Orchestrator CLI (done)

### CLI

```bash
python scripts/run_real_video_build.py \
  --run-id real_mini_001 \
  --scene-asset-pack fixtures/real_video_build_mini/scene_asset_pack.json \
  --asset-mode placeholder \
  --voice-mode smoke \
  --motion-mode static \
  --subtitle-style typewriter \
  --print-json
```

Pflicht: `--run-id` (regex `^[A-Za-z0-9_-]{1,80}$`), `--scene-asset-pack` (existierende Datei).
Optional: `--out-root` (Default `output`), `--asset-mode` (`placeholder` Default | `live`), `--voice-mode` (nur `smoke` in BA 25.1), `--motion-mode` (`static` Default | `basic`), `--subtitle-style` (Default `typewriter`), `--subtitle-mode` (Default `simple`), `--force`, `--print-json`.

### Inputs

- `scene_asset_pack.json` (BA 18.2 Export oder Fixture)

### Outputs

- `output/real_build_<run_id>/real_video_build_result.json` (Indexpaket mit Pfaden, Status, Steps, Warnings/Blockern)
- `output/real_build_<run_id>/clean_video.mp4`
- Zwischen-Artefakte unter den bestehenden Konventionen:
  - `output/generated_assets_<run_id>/` (Bilder + `asset_manifest.json`)
  - `output/full_voice_<run_id>/` (Smoke MP3 + `narration_script.txt` + `voice_manifest.json`)
  - `output/timeline_<run_id>/timeline_manifest.json` (mit `audio_path`, falls Voiceover ok)
  - `output/subtitles_<run_id>/` (`subtitle_manifest.json` + `subtitles.srt`)
  - `output/subtitle_burnin_<run_id>/preview_with_subtitles.mp4`

### Result-Manifest (V1)

`real_video_build_result.json` hat `schema_version: "real_video_build_result_v1"`, Felder:

- `run_id`, `ok`, `status` (`completed` | `failed` | `blocked`)
- `build_dir`, `scene_asset_pack`, `metadata` (asset_mode, voice_mode, motion_mode, subtitle_style, subtitle_mode, force)
- `steps[]` mit jeweils `name`, `ok`, `output`, `warnings`, `blocking_reasons`, optional `extra`
- `paths` mit den Schlüsseln `scene_asset_pack`, `asset_manifest`, `timeline_manifest`, `voiceover_audio`, `narration_script`, `clean_video`, `subtitle_manifest`, `subtitle_file`, `preview_with_subtitles`, `local_preview_dir`, `final_render_dir`, `final_video`
- `warnings`, `blocking_reasons`, `next_step`, `created_at_epoch`

Exit-Codes:

| Code | Bedeutung |
|------|-----------|
| 0 | `completed` |
| 2 | `blocked` (z. B. invalid run_id, fehlender Pack) |
| 1 | `failed` oder `unexpected_exception` |
| 3 | CLI-Vorvalidierung (run_id ungültig oder Pack-Datei fehlt) |

### Grenzen BA 25.1

- **Kein** URL-Input (`--url` existiert bewusst nicht).
- **Kein** TTS-Live: `--voice-mode` ist auf `smoke` festgenagelt; jede andere Eingabe wird zu Smoke degradiert mit Warnung `voice_mode_forced_smoke_in_ba_25_1:<requested>`.
- **Kein** Adapter aus `GenerateScriptResponse`/Story-Pack — Narration wird minimal aus den `visual_prompts` der `scene_expansion` abgeleitet (Warnung implizit, dokumentiert hier).
- **Kein** Final Render — `paths.final_render_dir` und `paths.final_video` bleiben leer; Final Render bleibt der bestehende BA 24.x-Flow.
- **Kein** Provider-Call (Leonardo Live nur über `--asset-mode live` und nur wenn `LEONARDO_API_KEY` gesetzt ist; Default ist Placeholder).

### Welche Steps real laufen / wo Fallbacks greifen

| Step | Real | Fallback / Warnung |
|------|------|---------------------|
| Asset Runner | placeholder PNGs (Default) | live nur mit Key → BA 19/20.2 Logik |
| Voiceover Smoke | stilles MP3 via ffmpeg `anullsrc` | ohne ffmpeg: `voiceover_smoke_skipped_ffmpeg_missing` + silent render |
| Timeline | real (audio_path automatisch gesetzt, wenn Voiceover ok) | ohne Voiceover-MP3: Warnung `timeline_audio_path_not_wired` |
| Clean Render | ffmpeg | bei ffmpeg-Fehler: `clean_render_failed` (Pipeline stoppt) |
| Subtitle Build | narration source | narration aus scene_pack (minimal) |
| Burn-in | libass / ASS für typewriter | bei Fehler: `burn_in_failed` |

### Reality Check

```text
output/real_build_real_mini_001/
├── clean_video.mp4
└── real_video_build_result.json   (status=completed, alle Steps ok)
```

`paths.preview_with_subtitles` zeigt nach `output/subtitle_burnin_<run_id>/preview_with_subtitles.mp4` (nicht ins `real_build_<run_id>` kopiert — Indexpaket, kein Container).

### Nächster Schritt: BA 25.2

Adapter, der einen `GenerateScriptResponse` (oder Story-Pack) in einen `ProductionPromptPlan` oder direkt in ein `scene_asset_pack.json` übersetzt, damit echte Story-Inhalte statt minimaler Visual-Prompt-Narration in den Build laufen.

## BA 25.3 — URL-to-Script Bridge (**done**)

### Scope

- **Input**: einzelne URL (Artikel oder YouTube).
- **Output**: lokale Datei `output/url_script_<run_id>/generate_script_response.json`, kompatibel mit dem BA-25.2-Adapter.
- **Kein** Render, **kein** Final Render, **kein** Publishing/Upload.
- **Kein** Orchestrator-Lauf — BA 25.3 stoppt nach dem Script-Output.
- **Keine** neuen Provider-Calls erzwingen (nur die bestehende `app.utils`-Logik).

### CLI

```bash
python scripts/run_url_to_script_bridge.py \
  --url "https://example.com/article" \
  --run-id url_test_001 \
  --target-language de \
  --duration-minutes 10 \
  --source-type auto \
  --out-root output \
  --print-json
```

Pflicht: `--url`, `--run-id` (regex `^[A-Za-z0-9_-]{1,80}$`).
Optional: `--target-language` (Default `de`), `--duration-minutes` (Default `10`), `--source-type` (`auto` | `article` | `youtube`, Default `auto`), `--out-root` (Default `output`), `--print-json`, `--no-open-me`.

### Source-Type-Erkennung

- `auto`: Hosts `youtube.com` / `youtu.be` / `m.youtube.com` / `music.youtube.com` → `youtube`, sonst `article`.
- `article` / `youtube`: erzwingt den jeweiligen Pfad unabhängig vom Host.

### Outputs

- `output/url_script_<run_id>/generate_script_response.json` — enthält die sechs `GenerateScriptResponse`-Pflichtfelder (`title`, `hook`, `chapters`, `full_script`, `sources`, `warnings`) und zusätzliche Bridge-Metadaten (`run_id`, `source_url`, `source_type`, `target_language`, `duration_minutes`, `created_at_epoch`).
- `output/url_script_<run_id>/URL_SCRIPT_OPEN_ME.md` (optional, Default an).

### Exit-Codes

| Code | Bedeutung |
|------|-----------|
| 0 | success — Datei geschrieben |
| 1 | generation failed (z. B. leere Article-Extraktion, leeres YouTube-Transcript) |
| 3 | invalid input (run_id ungültig, URL nicht http(s), source_type nicht erlaubt, duration ≤ 0) |

### Adapter-Bridge

- `scripts/adapt_script_to_scene_asset_pack.py --input output/url_script_<run_id>/generate_script_response.json --output output/scene_asset_pack_<run_id>/scene_asset_pack.json --run-id <run_id>` führt den BA-25.2-Adapter direkt auf der Bridge-Datei aus.
- BA 25.4 baut darauf auf.

### Grenzen BA 25.3

- Kein automatischer Aufruf von `scripts/run_real_video_build.py`, kein Asset Runner, kein Voiceover.
- Kein YouTube-Upload, kein Final Render, kein Dashboard.
- Keine Geheimnisse aus `.env` lesen; bestehende Fallback-Logik aus `app.utils` greift unverändert.

## BA 25.4 — Real Local Preview Run (**done**)

### Scope

- **Input**: lokales `generate_script_response.json` (BA 25.3 Output) **oder** ein einfacher Story-Pack-JSON.
- **Output**: `output/real_local_preview_<run_id>/` mit
  - `scene_asset_pack.json` (BA 25.2 Adapter-Ausgabe)
  - `real_local_preview_result.json` (Aggregat, Schema `real_local_preview_result_v1`)
  - `REAL_LOCAL_PREVIEW_OPEN_ME.md` (Operator-Hilfe)
  - Pfadverweise auf `output/real_build_<run_id>/real_video_build_result.json` und auf `output/subtitle_burnin_<run_id>/preview_with_subtitles.mp4` (Indexpaket-Charakter, kein Container).
- **Vertrag**: `GenerateScriptResponse`, `scene_asset_pack.json` und `real_video_build_result.json` bleiben unverändert (BA-25.x-Governance).

### Wiring

```text
generate_script_response.json
  → app/real_video_build/script_input_adapter.py
      build_scene_asset_pack_from_generate_script_response()  # BA 25.2
  → output/real_local_preview_<run_id>/scene_asset_pack.json
  → scripts/run_real_video_build.py
      run_real_video_build()                                  # BA 25.1
  → output/real_build_<run_id>/real_video_build_result.json
  → output/subtitle_burnin_<run_id>/preview_with_subtitles.mp4
```

### CLI

```bash
python scripts/run_ba_25_4_local_preview.py \
  --script-json output/url_script_<run_id>/generate_script_response.json \
  --run-id real_preview_001 \
  --asset-mode placeholder \
  --voice-mode smoke \
  --motion-mode static \
  --subtitle-style typewriter \
  --print-json
```

Pflicht: `--script-json`, `--run-id` (regex `^[A-Za-z0-9_-]{1,80}$`).
Optional: `--out-root` (Default `output`), `--asset-mode` (`placeholder` | `live`), `--voice-mode` (nur `smoke` in BA 25.4), `--motion-mode` (`static` | `basic`), `--subtitle-style`, `--subtitle-mode`, `--force`, `--print-json`, `--no-open-me`.

### Exit-Codes

| Code | Bedeutung |
|------|-----------|
| 0 | `completed` (Preview-Datei existiert) |
| 1 | `failed` (Orchestrator-Fehler oder Schreibfehler) |
| 2 | `blocked` (z. B. fehlendes ffmpeg, Preview fehlt) |
| 3 | `invalid input` (run_id ungültig, script-json fehlt/ungültig) |

### Grenzen BA 25.4

- **Kein** URL-Input — der gehört zu BA 25.3.
- **Kein** Final Render — bleibt bestehender BA 24.x-Flow (`scripts/run_final_render.py`).
- **Kein** YouTube-Upload, **kein** Scheduling, **kein** Dashboard-Redesign.
- **Kein** TTS-Live-Zwang, **kein** Leonardo-Live-Zwang, **keine** neue Cost Engine.
- BA 25.4 bricht **keinen** bestehenden Vertrag (`GenerateScriptResponse`, `scene_asset_pack.json`, `real_video_build_result.json`).

