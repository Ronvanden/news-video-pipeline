# Real Video Build Wiring Map

## Ziel
Vom **echten Script/Story-Pack** zu einem **lokal gespeicherten Video** (Preview + Final‑Package) – ohne Upload/Publishing.

**Visual Text Policy (BA 26.4b):** Bild-/Video-Generatoren erzeugen **keine finale Lesetypografie**; konkrete Schrift/Labels/Untertitel werden im **Render-/Overlay-Layer** gesetzt. Disposition (Leonardo vs. OpenAI Images vs. Runway vs. render_layer) und No-Text-Guard sind im Code (`app/visual_plan/visual_*.py`) und in [PIPELINE_PLAN.md](../../PIPELINE_PLAN.md) unter **BA 26** dokumentiert.

**BA 26.4c (Transparenz):** In `scene_asset_pack.json`, `asset_manifest.json` und Provider-Smoke-Summaries werden jetzt zusätzlich zum bisherigen `visual_prompt` die Felder `visual_prompt_raw`, `visual_prompt_effective`, `visual_text_guard_applied`, `visual_policy_status`, `visual_policy_warnings` und `provider_routing_reason` ausgegeben. Damit sieht der Operator, was roh war und was tatsächlich provider-sicher ausgeführt wurde.

**BA 26.4d (Dashboard-Fallback):** Die Visual Policy Summary im Founder Dashboard bevorzugt Optimize-Daten, kann aber ohne Optimize bereits aus dem Export Package lesen (`provider_prompts`, optional `scene_prompts.scenes`). Der Block zeigt zusätzlich **„Visual Policy Source: Optimize|Export Package|Story Pack|Not available“**.

**BA 26.4e (Acceptance Smoke):** Vor **BA 26.5** gibt es einen trockenen Acceptance-Smoke-Test (`tests/test_ba264e_provider_routing_acceptance_smoke.py`), der 5 synthetische Assets durch Routing/Partition/Guard/Policy-Report jagt und sicherstellt, dass kein `needs_review` entsteht und alle Provider-Ziele (`leonardo`, `openai_images`, `runway`, `render_layer`) mindestens einmal erreicht werden — **ohne** Live-Calls.

**BA 26.5 (OpenAI Images Provider Integration V1):** `scripts/run_asset_runner.py` kann bei Routing `openai_images` den neuen Adapter `app/production_connectors/openai_images_adapter.py` nutzen. Default bleibt **dry-run** (kostenfrei, placeholder PNG ohne Text); Live nur mit `--openai-images-live` oder `Settings.enable_openai_images_live=true`. Ergebnis wird additiv im `asset_manifest.json` gespiegelt (`provider_used`, `provider_status`, `prompt_used_effective`, `openai_image_result`).

**BA 26.6c (Manual Override):** Operator-Overrides werden V1 **file-basiert** in `asset_manifest.json` gepflegt (kein Dashboard-Write). Helpers: `app/visual_plan/asset_override.py`. CLI: `scripts/patch_asset_manifest_override.py` patcht pro `scene_number` Felder wie `asset_decision_status`, `selected_asset_path`, `manual_provider_override`, `manual_prompt_override`, `replacement_history`, `locked_for_render`.

**BA 26.7c (Provider Quality Compare Smoke):** Heuristischer Compare-Layer ergänzt pro Asset in `asset_manifest.json` Felder wie `provider_candidates`, `recommended_provider`, `provider_quality_reason`, `provider_compare_status`. CLI `scripts/run_provider_quality_compare.py` kann den Compare trocken auf ein Manifest anwenden. Dashboard zeigt (read-only) Compare-Infos, **falls** diese Felder im geladenen JSON vorhanden sind.

**BA 26.8c (Visual Cost Tracking):** Heuristische Kostenschätzung pro Asset (EUR) und aggregiert pro Manifest. CLI `scripts/run_visual_cost_tracking.py` patcht `asset_manifest.json` additiv (`visual_cost_estimate_eur`, `visual_provider_unit_cost`, `visual_cost_warning`, `visual_cost_summary`). Keine Billing-API, nur Schätzung; Warnings enthalten `visual_cost_estimate_only`.

**BA 26.9c (Production Asset Approval Gate):** Gate prüft `asset_manifest.json` auf Produktionsreife (Policy/Guard/Decision/Paths/Overlay) und schreibt additiv `production_asset_approval_result`. CLI `scripts/run_production_asset_approval_gate.py`. Keine Live‑Calls; blockiert z. B. bei `visual_policy_status=="needs_review"`, fehlendem Guard bei non-`render_layer`, fehlendem Asset‑Pfad bei non-`render_layer`, `asset_decision_status in ("rejected","needs_regeneration")`, oder `text_sensitive==true` ohne `overlay_intent`.

**BA 27.0 (Production Pack V1):** File-basierter Builder erzeugt `output/production_pack_<run_id>/` und bündelt Artefakte + Entscheidungen: `production_summary.json` + `README_PRODUCTION_PACK.md` + optional kopierte Assets unter `assets/`. `ready_for_render` wird **ausschließlich** aus dem Approval Gate abgeleitet: nur `approval_status=="approved"` → `ready_for_render=true`, sonst `false`. CLI: `scripts/build_production_pack_v1.py`.

**BA 27.1 (Reference Library V1):** Referenzbilder/Kontinuitätsanker werden als `reference_library.json` gespeichert (keine Provider-Uploads). Assets können additiv `reference_asset_ids` + `continuity_strength` tragen; im Production Pack wird die Library optional kopiert und als `reference_library_summary` in `production_summary.json` gespiegelt.

**BA 27.2 (Continuity Wiring V1):** Continuity-Hints werden (ohne Live-Uploads) aus `reference_asset_ids` + `reference_library.json` in additive Asset-Felder verdrahtet (`continuity_reference_paths`, `continuity_provider_payload_stub`, …). CLI `scripts/run_continuity_prompt_wiring.py` patcht `asset_manifest.json` und schreibt `continuity_wiring_summary`.

**BA 27.3 (Continuity Display V1):** Continuity wird im Dashboard in Prompt Cards als kurze Zeile angezeigt (Status/Reference-Count/Strength/Hint) und im Production Pack README als Count-Summary, ohne Provider-Calls.

**BA 27.4 (Reference Provider Payloads V1):** Provider-kompatible Reference-Payload-Stubs werden additiv in `asset_manifest.json` vorbereitet (`reference_provider_payloads`, `recommended_reference_provider_payload`, `reference_provider_payload_status`). CLI `scripts/run_reference_provider_payloads.py`. Keine Live-Uploads/Calls; Real Provider Smoke kann den Status im dry-run anzeigen.

**BA 27.6 (Reference Payload Export/Pack Wiring):** Reference-Felder werden best-effort entlang operator-naher Artefakte gespiegelt (Pack Summary Mirror, Optimizer Pass-through, Dashboard Fallback), damit die Szene-Zeile im Dashboard stabil sichtbar bleibt — ohne Live-Uploads/Calls.

**Scope (BA 25.0):** reine Analyse/Dokumentation. Keine neuen Features, keine Provider‑Calls, keine Secrets.

## Existing Building Blocks

| Schritt | Script | Input | Output | Real/Placeholder | Hinweise |
|---|---|---|---|---|---|
| 1. Script / Story Pack Input | *(extern / API / Export)* | URL, `ProductionPromptPlan.json`, oder `GenerateScriptResponse`/Story‑Pack | **Plan/Pack** für nachfolgende Schritte | real | Aktuell gibt es mehrere mögliche Quellen (API, CLI, Exporte). |
| 2. Scene Asset Pack Export | `scripts/export_scene_asset_pack.py` | `--url` **oder** `--prompt-plan-json` | `output/scene_asset_pack_<run_id>/scene_asset_pack.json` + `leonardo_prompts.txt` + `shot_plan.md` + `founder_summary.txt` | real | Baut/erzwingt Scene Expansion im Plan. `--duration-minutes` wirkt nur auf Plan‑Erzeugung via URL. |
| 3. Asset Runner | `scripts/run_asset_runner.py` | `scene_asset_pack.json` | `output/generated_assets_<run_id>/scene_001.png…` + optional `scene_XXX.mp4`/`.mov`/`.webm` + `asset_manifest.json` | **placeholder default** / optional live | Default `--mode placeholder` erzeugt bewusst PIL‑Placeholder‑PNGs. `--mode live` nutzt Leonardo nur mit `LEONARDO_API_KEY`, sonst Fallback + Warnungen. **BA 26.3:** Beats können **lokale** Clips referenzieren (`video_path`, `runway_clip_path`, …) — Validierung (Datei, Endung, kein Symlink); Kopie ins `generated_assets_*`‑Ordner; `asset_manifest` mit `asset_type`/`video_path` + optional `image_path` (Fallback). |
| 4. Timeline Manifest | `scripts/build_timeline_manifest.py` | `--asset-manifest …/asset_manifest.json` + optional `--audio-path` | `output/timeline_<run_id>/timeline_manifest.json` | real | Legt `timeline_manifest.audio_path` **nur** fest, wenn `--audio-path` gesetzt ist. **BA 26.3:** Szenen optional `media_type` `video` \| `image`, `video_path`, `image_path` (Fallback); Dauer pro Szene aus `duration_seconds` im Asset, sonst Default‑Argument. |
| 5. Voiceover / Narration Audio | `scripts/build_full_voiceover.py` | `--url` **oder** `--prompt-plan-json` (+ optional `--full-script-json`/Plan‑Felder) | `output/full_voice_<run_id>/narration_script.txt`, `full_voiceover.mp3`, `voice_manifest.json` | **smoke default** / optional real | Default ist „Smoke“ (stilles MP3 mit geschätzter Dauer). Echt nur mit Keys (ElevenLabs/OpenAI). |
| 6. Clean Video Render | `scripts/render_final_story_video.py` | `--timeline …/timeline_manifest.json` (Medien via `assets_directory`) + optional Audio (über Timeline) | MP4 (clean) + optional `output/render_<run_id>/render_output_manifest.json` | real (ffmpeg) | Ohne Audio: silent + Warnung. Bei fehlendem ffmpeg: `blocking_reasons` (kein Video). Motion/Transition Layer (BA 20.4). **BA 26.3:** Timeline‑Einträge mit `video_path` werden per ffmpeg eingespeist (`-stream_loop` + Ziel‑Szenendauer); gemischte Bild/Video‑Ketten über `filter_complex`; bei Fehler Warnung und Retry **nur Bild** (falls `image_path` vorhanden). |
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

### BA 26 — Live Provider Smoke / Ist-Stand

- **Leonardo Live (erster Bildpfad):** `scripts/run_asset_runner.py` (`--mode live`, u. a. `LEONARDO_API_KEY`, optional Endpoint/Model-ID). Durchreichen via **`--asset-mode live`** (BA 25.1 / BA 25.4 / URL-to-Final-Smoke).
- **Video-Provider / lokale Clips:** **BA 26.2** (`scripts/runway_image_to_video_smoke.py`) erzeugt einen lokalen Runway-Testclip (bei `RUNWAY_API_KEY`). **BA 26.3:** Lokale Clips im `scene_asset_pack` bis zum Clean-Render. **BA 26.4:** `scripts/run_real_provider_smoke.py` / `run_real_provider_smoke()` — **dry_run** (Request-Shape, kein HTTP) vs. **--live** nur mit `--real-provider-enabled`, `selected_provider` runway\|veo, ENV-Key, **max-real-scenes** (Default 1); lokaler Clip hat Vorrang außer `--force-provider`. Veo-Live: bewusst nicht implementiert (Blocking). **Nicht** beide Video-Provider parallel produktiv einbauen.
- **Sora:** **nicht** als Primär-Connector priorisiert (Scope Freeze).
- **Kling:** `app/production_connectors/kling_connector.py` nur **Dry-Run**; nicht Teil der BA-26-Video-Wahl.
- **Render:** `render_final_story_video.py` = Stillimages + **lokale** Video-Segmente (**BA 26.3**) + ffmpeg-**basic**/**static**; optionaler Provider-Smoke: **BA 26.4**; **BA 26.5** = ein Befehl bis `final_video.mp4` mit vorhandenen Assets (siehe unten).
- **Lücke:** Automatischer Clip-Fetch vom gewählten Video-Provider; bis dahin Clips manuell/lokal (z. B. Smoke-Output) oder über **BA 26.5** `--asset-dir` einbinden. **BA 26.1** = Artikel-URL + **Leonardo** + Render bis `final_video.mp4`.

### BA 26.x — Repo-Inventar (Kurz, Stand Plan-Sync)

| BA | Artefakte |
|----|-----------|
| **26.2** | `scripts/runway_image_to_video_smoke.py` · `tests/test_ba262_runway_image_to_video_smoke.py` |
| **26.3** | `scripts/run_asset_runner.py` · `app/production_connectors/scene_pack_local_video.py` · `scripts/build_timeline_manifest.py` · `scripts/render_final_story_video.py` · `tests/test_ba263_runway_clip_asset_ingest.py` · Fixture-Hinweis `fixtures/real_video_build_mini/video_asset_scene_pack.json` |
| **26.3R** | Nur Doku/Abgleich in `PIPELINE_PLAN.md` + diesem Runbook; optional manueller Reality-Lauf (siehe unten). |
| **26.4** | `app/production_connectors/real_provider_smoke.py` · `scripts/run_real_provider_smoke.py` · `tests/test_ba264_real_provider_smoke.py` |
| **26.5** | `scripts/run_url_to_final_mp4.py` · `tests/test_ba265_url_to_final_mp4.py` |
| **26.6** | `scripts/run_url_to_final_mp4.py` (`_draw_cinematic_placeholder_png`, `_apply_cinematic_placeholders`, Reuse-Loop in `_assign_media`) · `tests/test_ba266_visual_founder_upgrade.py` |
| **26.7** | `scripts/run_url_to_final_mp4.py` (`_collect_voiceover_text`, `_synthesize_voice`, `_validate_voice_file`, `--voice-mode` CLI) · Wiederverwendung von `scripts/build_full_voiceover.py::synthesize_elevenlabs_mp3` / `synthesize_openai_mp3` / `_write_smoke_mp3_ffmpeg` · `tests/test_ba267_elevenlabs_voice_founder_integration.py` |
| **26.7b** | `scripts/run_url_to_final_mp4.py` (`_apply_fit_to_voice_durations`, `--fit-video-to-voice`, `--voice-fit-padding-seconds`) · `scripts/render_final_story_video.py` (Warn-Schwelle `audio_shorter_than_timeline_padded_or_continued`, Slop ≈ 1,05 s) · `tests/test_ba267b_fit_video_to_voice.py` |
| **26.8** | `scripts/run_real_visual_founder_smoke.py` (Orchestrierung: Leonardo-Live → Runway-Live → ElevenLabs Voice → `final_video.mp4` + `visual_summary.json`) · `tests/test_ba268_real_visual_founder_smoke.py` |

### BA 26.8 — Real Visual Assets Founder Smoke (Leonardo + Runway + Voice → final_video.mp4)

**Ziel:** Erster **echter visueller Durchstich** — Script → Leonardo-Bilder → Runway-Clips → ElevenLabs Voice → `final_video.mp4`. Kein Dashboard, kein Publishing, kein Longform.

**CLI (PowerShell, Repo-Root):**

```powershell
python scripts/run_real_visual_founder_smoke.py `
  --script-json output/ba266_visual_founder_smoke/script.json `
  --out-dir output/ba268_real_visual_founder_smoke `
  --max-scenes 5 --duration-seconds 60 `
  --use-leonardo --use-runway --max-runway-scenes 3 `
  --voice-mode elevenlabs --fit-video-to-voice
```

**Parameter:** `--use-leonardo` (Leonardo-Live statt Placeholder), `--use-runway` (Runway-Clips für max. `--max-runway-scenes` Szenen), `--voice-mode` (elevenlabs / dummy / none), `--fit-video-to-voice`, `--fallback-clip` (optional: vorhandene MP4 als Fallback).

**ENV (ohne Werte):** `LEONARDO_API_KEY`, `RUNWAY_API_KEY`, `ELEVENLABS_API_KEY`, optional `LEONARDO_API_ENDPOINT`, `LEONARDO_MODEL_ID`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_MODEL_ID`.

**Outputs:** `visual_summary.json` (Leonardo/Runway-Counts, Szenen-Details, Blocker, Provider-Status), `run_summary.json`, `final_video.mp4`, `scene_plan.json`, `scene_asset_pack.json`, `visual_assets/merged/` (priorisierter Asset-Dir).

**Asset-Priorität pro Szene:** 1. Runway-Video → 2. Leonardo-Bild → 3. Fallback-Clip → 4. cinematic Placeholder (textfrei).

**Blocker ohne Keys:** `leonardo_missing_api_key`, `runway_missing_api_key` — kein Crash, kein Fake-Erfolg; `visual_summary.json` ehrlich.

### BA 26.5 — URL / script.json → final_video.mp4 (vorhandene Assets, kein Provider-Pflicht)

**Ziel:** Ein durchgängiger **Founder-Run**: Eingabe (Artikel-URL oder lokale `script.json`) + optional ein Ordner mit **bereits vorliegenden** Medien → **`final_video.mp4`** im gewählten Ausgabeordner. **Kein** erzwungener Runway/Veo-/Leonardo-Live-Call; Asset-Runner läuft mit **`--mode placeholder`** (nur Placeholder-Bilder, außer wo ein lokales Video eingebunden wird).

**CLI (PowerShell, Repo-Root):**

```powershell
# Mit URL (wenn Extraktion fehlschlägt: blocking + Hinweis --script-json)
python scripts/run_url_to_final_mp4.py `
  --url "https://example.com/artikel" `
  --out-dir output/ba265_url_to_final `
  --max-scenes 3 `
  --duration-seconds 45 `
  --asset-dir output/runway_smoke_runway_smoke_002

# Mit vorhandener script.json (GenerateScriptResponse-ähnlich)
python scripts/run_url_to_final_mp4.py `
  --script-json path/to/script.json `
  --out-dir output/ba265_url_to_final `
  --max-scenes 3 `
  --duration-seconds 45 `
  --asset-dir path/to/assets
```

**Parameter:** `--motion-mode static|basic` (Default `static`), `--run-id` (optional; sonst Name von `--out-dir`). **`--asset-dir`:** rekursiv nach `.mp4`/`.mov`/`.webm` sowie `.png`/`.jpg`/`.jpeg`; Videos werden Szenen **in Reihenfolge** als `runway_clip_path` gesetzt, danach verbleibende Szenen mit Bildern (nach Asset-Runner: Kopie ins `generated_assets_*`‑Verzeichnis).

**Outputs unter `--out-dir`:** `script.json`, `scene_plan.json`, `scene_asset_pack.json`, `generated_assets_<run_id>/`, `timeline_<run_id>/timeline_manifest.json`, **`final_video.mp4`**, **`render_result.json`**, **`run_summary.json`** (u. a. `ok`, `warnings`, `blocking_reasons`, `used_video_assets_count`). Ohne Audio: erwartbare Render-Warnung `audio_missing_silent_render`.

**Handoff BA 26.4 → 26.5:** Runway-Live oder BA-26.2-Output liefert eine lokale MP4 (z. B. unter `output/runway_smoke_*/runway_clip.mp4`). Ordner oder Datei-Struktur als **`--asset-dir`** angeben; **26.5** übernimmt die Einbindung in Pack/Timeline/Render. Alternativ weiterhin manuell wie in **BA 26.3**.

**Reality-Lauf BA 26.5 (manuell, lokal, ohne neuen Provider-Call):** Mit dem vorhandenen Clip aus BA 26.2 (`output/runway_smoke_runway_smoke_002/runway_clip.mp4`) und der Mini-Fixture `fixtures/real_video_build_mini/generate_script_response.json` liefert

```powershell
python scripts/run_url_to_final_mp4.py `
  --script-json fixtures/real_video_build_mini/generate_script_response.json `
  --out-dir output/ba265_founder_smoke `
  --max-scenes 3 --duration-seconds 30 `
  --asset-dir output/runway_smoke_runway_smoke_002 `
  --run-id ba265_founder_smoke --motion-mode static
```

ein `final_video.mp4` (~30 s) unter `output/ba265_founder_smoke/`, `run_summary.json` mit `ok: true`, `used_video_assets_count: 1`, sowie die erwartbaren Warnungen `existing_asset_used` und `audio_missing_silent_render`. Ohne `--asset-dir` oder ohne Video im Ordner: `no_existing_video_asset_found_using_fallback` (kein Crash).

**Tests unter Windows / PowerShell:** PowerShell expandiert Glob-Muster wie `tests\test_ba26*.py` **nicht** automatisch. Tests entweder explizit mit Dateipfad starten oder via `-k` filtern:

```powershell
python -m pytest tests/test_ba267_elevenlabs_voice_founder_integration.py -q
python -m pytest tests/test_ba267b_fit_video_to_voice.py -q
python -m pytest tests/test_ba266_visual_founder_upgrade.py -q
python -m pytest tests/test_ba265_url_to_final_mp4.py -q
python -m pytest tests -k ba267 -q
python -m pytest tests -k ba266 -q
python -m pytest tests -k ba265 -q
python -m pytest tests -k ba264 -q
python -m pytest tests -k ba263 -q
```

### BA 26.6 — Visual Founder Upgrade

**Ziel:** Founder-`final_video.mp4` aus BA 26.5 wirkt nicht mehr wie ein Test-Render mit `SCENE 001`-Karten, sondern wie ein einfacher visueller Rohschnitt — **ohne** neuen Provider-Call, **ohne** Render-Refactor.

**Was BA 26.6 ändert (nur in [`scripts/run_url_to_final_mp4.py`](../../scripts/run_url_to_final_mp4.py)):**

- **Textfreie cinematic Placeholder** (`_draw_cinematic_placeholder_png` / `_apply_cinematic_placeholders`): Nach `run_asset_runner` werden alle Szenen-PNGs (außer expliziten Image-Overrides aus `--asset-dir`) durch ein **deterministisch identisches** 960×540-Bild ersetzt — weicher Vertikal-Verlauf, Vignette, dezente Akzentlinie, **kein** Schriftzug, **keine** Badges, **kein** „DRAFT PLACEHOLDER" mehr. Der ursprüngliche BA-20.2b-„Draft Look" im Asset-Runner bleibt **unverändert** (945+ Bestandstests).
- **Video-Reuse** (`_assign_media`): Liegen weniger Videos im `--asset-dir` als Szenen vor, bekommt **jede** Szene den letzten gültigen Clip; ffmpeg loopt/trimmt per `-stream_loop`. Warnung: `ba266_video_reuse_for_remaining_scenes`.
- **Default `--motion-mode=basic`** in der CLI (Ken-Burns / xfade aus BA 20.4). Funktionsaufrufe `run_ba265_url_to_final(motion_mode=…)` behalten den alten Default `static` (rückwärtskompatibel für Bestandsaufrufer).

**Reality-Lauf BA 26.6 (PowerShell, Repo-Root):**

```powershell
python scripts/run_url_to_final_mp4.py `
  --script-json fixtures/real_video_build_mini/generate_script_response.json `
  --out-dir output/ba266_visual_founder_smoke `
  --max-scenes 3 --duration-seconds 30 `
  --asset-dir output/runway_smoke_runway_smoke_002 `
  --run-id ba266_visual_founder_smoke `
  --motion-mode basic
```

**Erwartetes Ergebnis:**

- `output/ba266_visual_founder_smoke/final_video.mp4` (~30 s, ~5,5 MB)
- `run_summary.json` mit `ok: true`, `used_video_assets_count: 3`, `used_image_assets_count: 0`
- `generated_assets_*/scene_001.png` ≡ `scene_002.png` ≡ `scene_003.png` (bytegleich, textfrei)
- `warnings`: `ba266_video_reuse_for_remaining_scenes`, `existing_asset_used`, `ba266_cinematic_placeholder_applied:3`, `audio_missing_silent_render`

**Nicht in Scope (BA 26.6):** echte Voice (BA 26.7+), neuer Provider, Dashboard, Publishing, Render-Refactor, Subtitle-Burn-In im Founder-Pfad.

### BA 26.7 — ElevenLabs Voice Founder Integration

**Ziel:** Der BA-26.6-Founder-Run liefert ein `final_video.mp4` mit **Ton**. ElevenLabs ist der bevorzugte echte TTS-Pfad; ohne ENV bleibt der Smoke technisch nutzbar (`dummy`/`existing`). **Kein** neuer Voice-Provider, **kein** neues Dashboard, **kein** Refactor. Das gesamte Voice-Modul ist additiv in [`scripts/run_url_to_final_mp4.py`](../../scripts/run_url_to_final_mp4.py).

**Was BA 26.7 ändert:**

- **Neue CLI-Argumente** (alle optional): `--voice-mode none|existing|elevenlabs|dummy|openai` (Default `none` ⇒ unverändert), `--voice-file`, `--voice-output`, `--elevenlabs-voice-id`, `--elevenlabs-model`, `--tts-voice`. **Fit-to-Voice:** siehe **BA 26.7b** (`--fit-video-to-voice`, `--voice-fit-padding-seconds`, `--fit-min-seconds-per-scene`).
- **`voiceover_text.txt`** wird aus den geplanten Szenen (Hook + Kapitel-Narration) **labelfrei** zusammengesetzt — bewusst **ohne** „Szene 1" / „Chapter 1" / Asset-Type-Badges / IDs.
- **`_synthesize_voice(...)`** nutzt die vorhandene `synthesize_elevenlabs_mp3()` aus [`scripts/build_full_voiceover.py`](../../scripts/build_full_voiceover.py) (für `elevenlabs`), `synthesize_openai_mp3()` (für `openai`), und `_write_smoke_mp3_ffmpeg()` (für `dummy`).
- **Audio-Handoff** geht über `build_timeline_manifest(audio_path=…)` → `render_final_story_video` → `final_video.mp4`. Kein Rendering-Refactor.
- **`run_summary.json`** erhält additive Voice-Felder: `voice_used`, `voice_mode`, `voice_text_path`, `voice_file_path`, `voice_duration_seconds`, `audio_stream_expected`, `voice_warnings`, `voice_blocking_reasons`. Zusätzlich **BA 26.7b:** `fit_video_to_voice`, `voice_fit_padding_seconds`, `fitted_video_duration_seconds`, `original_requested_duration_seconds`.

**ENV (Secrets bleiben außerhalb des Repos):**

- `ELEVENLABS_API_KEY` — Pflicht für `--voice-mode elevenlabs`.
- `ELEVENLABS_VOICE_ID` — optional, sonst Projekt-Default `21m00Tcm4TlvDq8ikWAM`.
- `ELEVENLABS_MODEL_ID` — optional, sonst `eleven_multilingual_v2`.
- `OPENAI_API_KEY`, `OPENAI_TTS_VOICE`, `OPENAI_TTS_MODEL` — nur falls `--voice-mode openai`.
- `--elevenlabs-voice-id` / `--elevenlabs-model` überschreiben temporär die ENV ohne sie persistent zu verändern.

**Beispielbefehle (PowerShell, Repo-Root):**

```powershell
# 1) ElevenLabs (echte Voice — nur wenn ENV gesetzt ist)
python scripts/run_url_to_final_mp4.py `
  --script-json output/ba266_visual_founder_smoke/script.json `
  --out-dir output/ba267_voice_founder_smoke `
  --max-scenes 3 --duration-seconds 30 `
  --asset-dir output/runway_smoke_runway_smoke_002 `
  --voice-mode elevenlabs `
  --motion-mode basic

# 2) Existing Voice (vorhandene MP3/WAV/M4A)
python scripts/run_url_to_final_mp4.py `
  --script-json output/ba266_visual_founder_smoke/script.json `
  --out-dir output/ba267_existing_voice_smoke `
  --max-scenes 3 --duration-seconds 30 `
  --asset-dir output/runway_smoke_runway_smoke_002 `
  --voice-mode existing `
  --voice-file path\to\voiceover.mp3 `
  --motion-mode basic

# 3) Dummy Voice (Audio-Render-Smoke ohne API-Kosten)
python scripts/run_url_to_final_mp4.py `
  --script-json output/ba266_visual_founder_smoke/script.json `
  --out-dir output/ba267_dummy_voice_smoke `
  --max-scenes 3 --duration-seconds 30 `
  --asset-dir output/runway_smoke_runway_smoke_002 `
  --voice-mode dummy `
  --motion-mode basic
```

**Erwartete Ergebnisse:**

- `--voice-mode dummy` / `--voice-mode existing`: `voice_used: true`, **Audio-Stream im final_video.mp4**, `audio_missing_silent_render` verschwindet aus `warnings`. **`audio_shorter_than_timeline_padded_or_continued`** kann weiterhin erscheinen, wenn die Timeline deutlich länger als die Voice ist (typ. ohne **`--fit-video-to-voice`**); bei Fit + kleinem Padding wird sie durch eine höhere Vergleichstoleranz im Render oft unterdrückt (Slop ≈ 1,05 s — siehe **BA 26.7b**).
- `--voice-mode elevenlabs` ohne `ELEVENLABS_API_KEY`: `voice_used: false`, `voice_blocking_reasons: ["elevenlabs_missing_api_key"]`, **kein Secret im Output**, `final_video.mp4` wird trotzdem erzeugt (silent, mit `audio_missing_silent_render`).
- `--voice-mode none`: identisch zum BA-26.5/26.6-Verhalten.

**BA 26.7 — Live-Smoke Abschluss (ElevenLabs bestätigt):** Referenz-Artefakte unter **`output/baum_voice_custom_fit_5/`** — `run_summary.json`: **`voice_used: true`**, **`voice_mode: elevenlabs`**, **`voice_blocking_reasons: []`**, **`audio_stream_expected: true`**, **`fit_video_to_voice: true`**, **`fitted_video_duration_seconds`** gesetzt (Timeline an Voice + Padding). **`voiceover.mp3`** und **`final_video.mp4`** mit Audio-Stream; ohne **`audio_missing_silent_render`**. Typische frühere Ursachen bei Misserfolg: fehlender Key (`elevenlabs_missing_api_key`), **401** oder API-Key **ohne** nutzbare **TTS-Berechtigung**; Behebung über berechtigten Key und passende **Voice-ID** (ENV / `--elevenlabs-voice-id`) — **keine** Secrets oder Key-Literale in Doku oder Tickets.

### BA 26.7b — Fit Video Duration to Voice

**Problem ohne Fit:** `--duration-seconds 30` mit kurzer Voice (z. B. ~16 s ElevenLabs) → langes Video mit stummem Ende; Render-Warnung `audio_shorter_than_timeline_padded_or_continued`.

**Ziel:** Optional nach ermittelter **`voice_duration_seconds`** die Szenen-Timeline so setzen, dass **`final_video.mp4`** ungefähr mit der Voice (+ kleinem Puffer) endet — **ohne** neues Voice-System, **ohne** Render-Refactor der Segment-Pipeline.

**CLI:** `--fit-video-to-voice` (bool), `--voice-fit-padding-seconds` (float, Default **0,75**), `--fit-min-seconds-per-scene` (Default **2**).

**Ablauf:** Voice wie in BA 26.7 erzeugen oder `existing` laden → Dauer messen (ffprobe) → `_apply_fit_to_voice_durations` patcht **`asset_manifest.json`**, **`scene_plan.json`**, **`scene_asset_pack.json`** → `build_timeline_manifest` schreibt **`timeline_manifest.json`** mit angepassten `duration_seconds` pro Szene.

**`run_summary.json`:** `fit_video_to_voice`, `voice_fit_padding_seconds`, `fitted_video_duration_seconds`, `original_requested_duration_seconds`. Ohne nutzbare Voice-Dauer bei gesetztem Fit: Warning **`fit_video_to_voice_requested_but_no_voice_duration`** (kein Crash).

**Render:** Kleine Anpassung der Schwelle für `audio_shorter_than_timeline_padded_or_continued` (Slop ≈ **1,05 s**), damit das konfigurierte Padding nicht permanent dieselbe Warnung auslöst.

```powershell
# Reality-Smoke (script + Runway-Clip aus BA 26.6 — ElevenLabs nur wenn ENV gesetzt)
python scripts/run_url_to_final_mp4.py `
  --script-json output/ba266_visual_founder_smoke/script.json `
  --out-dir output/ba267b_fit_voice_smoke `
  --max-scenes 3 `
  --duration-seconds 30 `
  --asset-dir output/runway_smoke_runway_smoke_002 `
  --voice-mode elevenlabs `
  --fit-video-to-voice `
  --motion-mode basic

# Technischer Fit-Smoke ohne API (Dummy)
python scripts/run_url_to_final_mp4.py `
  --script-json fixtures/real_video_build_mini/generate_script_response.json `
  --asset-dir fixtures/real_video_build_mini/assets `
  --out-dir output/ba267_fit_voice_dummy `
  --max-scenes 3 --duration-seconds 60 `
  --motion-mode basic `
  --voice-mode dummy `
  --fit-video-to-voice `
  --run-id ba267_fit_voice_dummy

ffprobe -v error -show_entries format=duration -of csv=p=0 `
  output/ba267_fit_voice_dummy/final_video.mp4
# Erwartung: ≈ 9 s (Dummy-Default 8 s + Padding 0,75 → gerundet); Info-Warning ba267_video_fitted_to_voice:…target_total=…
```

**Nicht in Scope (BA 26.7 / 26.7b):** kein neuer Provider, kein Multi-Provider-System, kein Voice-Portal/Dashboard, kein OAuth, kein Cloud-Scheduler, kein großes Audio-Mixing (Audio-Längenkorrektur wird vom Bestand-Render gehandhabt), keine Vertragsänderung an `GenerateScriptResponse`.

### BA 26.4 — Real Provider Smoke (Start, ENV, Output, Anbindung BA 26.3)

**Ist-Stand (BA 26.4R):** **live-capable für Runway** (über BA 26.2), **Default Dry-Run** (kein HTTP). **Veo:** nur Dry-Stub; Live bewusst blockiert (`veo_provider_not_implemented`). Kein automatisierter Handoff ins `scene_asset_pack` — nach Live-Lauf den erzeugten Clip wie bei **BA 26.3** per `runway_clip_path` / `video_path` eintragen.

**Smoke starten (Repo-Root):**

```powershell
# Dry-Run (Default): Request-Shape, Blocking/Warnungen, kein Provider-HTTP
python scripts/run_real_provider_smoke.py --run-id my_smoke --out-dir output

# Runway Live (nur mit bewusster Freigabe): zusätzlich --live, --real-provider-enabled, RUNWAY_API_KEY
# $env:RUNWAY_API_KEY = "..."   # nicht committen; nicht in Logs ausgeben
python scripts/run_real_provider_smoke.py `
  --run-id my_smoke --out-dir output `
  --live --real-provider-enabled `
  --selected-provider runway `
  --assets-directory output/generated_assets_<leonardo_run_id> `
  --max-real-scenes 1
```

**Wichtige CLI-Flags:** `--dry-run` (explizit, entspricht Default ohne `--live`), `--live`, `--real-provider-enabled` (Gate), `--selected-provider runway|veo`, `--assets-directory` (Ordner mit `scene_*.png` für Runway), `--max-real-scenes` (Default 1), `--force-provider` (lokalen Clip im Beat ignorieren und Provider anfragen).

**Erwartete ENV:** `RUNWAY_API_KEY` für Runway-Live (siehe `runway_image_to_video_smoke`). Veo-Live: nicht implementiert.

**Output:**

- Immer: `output/real_provider_smoke_<run_id>/real_provider_smoke_result.json` (Dry- und Live-Lauf).
- Runway-Live zusätzlich: Unterordner im BA-26.2-Layout, z. B. `output/runway_smoke_<run_id>_scNNN/runway_clip.mp4` (konkreter Pfad steht im Result-JSON / Runway-Smoke-Report).

**Verbindung zu BA 26.3:** Den generierten `runway_clip.mp4` (oder kopierten Pfad) in `scene_asset_pack.json` im gewünschten Beat als `runway_clip_path` (oder `video_path`, …) setzen — relativ zum Ordner der Pack-JSON, wie im Abschnitt **BA 26.3** oben. Anschließend `run_asset_runner.py` → `build_timeline_manifest.py` → `render_final_story_video.py`.

### BA 26.3 — Vorhandenen lokalen Clip manuell testen (Reality-Pfad)

**Ziel:** Ohne neuen Provider-Call prüfen, ob ein **bereits vorhandener** MP4/MOV/WebM durch **Asset Runner → Timeline → Render** läuft (wie in [PIPELINE_PLAN.md](../../PIPELINE_PLAN.md), Abschnitt **BA 26.3R**).

**Voraussetzungen:** `ffmpeg` im PATH; eine gültige Videodatei (z. B. `output/runway_smoke_runway_smoke_002/runway_clip.mp4` nach BA 26.2).

**Erwartete Ordner nach Lauf:**

- `output/generated_assets_<run_id>/` — u. a. `scene_001.mp4` (Kopie des Quell-Clips), `scene_001.png` (Fallback-Placeholder), `asset_manifest.json`
- `output/timeline_<run_id>/timeline_manifest.json` — Szenen mit `media_type` `video` und `video_path`
- Gewähltes Ausgabe-MP4 (z. B. unter `output/.../clean.mp4`) — bei Erfolg `video_created` laut CLI-JSON

**Beispiel `scene_asset_pack.json`** (liegt am besten in einem eigenen Ordner; Pfade im Beat **relativ zum Ordner dieser JSON**):

```json
{
  "export_version": "18.2-v1",
  "source_label": "manual_ba263_clip_test",
  "hook": "Test",
  "scene_expansion": {
    "expanded_scene_assets": [
      {
        "chapter_index": 0,
        "beat_index": 0,
        "visual_prompt": "Lokaler Clip",
        "camera_motion_hint": "static",
        "duration_seconds": 6,
        "asset_type": "broll",
        "runway_clip_path": "../runway_smoke_runway_smoke_002/runway_clip.mp4"
      }
    ]
  }
}
```

Passe `runway_clip_path` an deine Datei an (alternativ: `video_path`, `local_video_path`, `clip_path`, `asset_video_path`).

**Beispiel-Befehle** (PowerShell, Repo-Root; `run_id` und Pfade anpassen):

```powershell
python scripts/run_asset_runner.py `
  --scene-asset-pack output/ba263r_reality_check/scene_asset_pack.json `
  --out-root output --run-id ba263r_demo --mode placeholder

python scripts/build_timeline_manifest.py `
  --asset-manifest output/generated_assets_ba263r_demo/asset_manifest.json `
  --out-root output --run-id ba263r_demo --scene-duration-seconds 6

python scripts/render_final_story_video.py `
  --timeline-manifest output/timeline_ba263r_demo/timeline_manifest.json `
  --output output/ba263r_reality_check/ba263r_clean.mp4 `
  --motion-mode static
```

**Troubleshooting**

| Symptom | Typische Ursache |
|--------|-------------------|
| Warnungen zu `local_video_*` im `asset_manifest` | Pfad falsch (relativ zur JSON), Datei fehlt, Endung nicht `.mp4`/`.mov`/`.webm`, oder Symlink |
| `missing_scene_media` / Render bricht ab | `video_path` in Timeline zeigt auf fehlende Datei im `generated_assets_*`‑Ordner (Asset Runner nicht gelaufen oder Manifest manuell verändert) |
| `ffmpeg_missing` / `ffmpeg_encode_failed` | ffmpeg nicht installiert oder Filter/Codec-Fehler; mit `--motion-mode static` den einfacheren Pfad probieren |
| Nur Warnung `audio_missing_silent_render` | Normal, wenn keine `--audio-path` an der Timeline gesetzt wurde |
| Kein Clip zum Testen | Zuerst BA 26.2 mit `RUNWAY_API_KEY` ausführen oder beliebigen kurzen MP4 lokal ablegen und im Pack referenzieren — **kein** Fake-API-Call nötig |

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

