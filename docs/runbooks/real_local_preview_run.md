# Real Local Preview Run (BA 25.4) Runbook

## Ziel

Aus einem realen `generate_script_response.json` (z. B. aus BA 25.3 oder manuellem Export) lokal ein Preview-Paket bauen — ohne Final Render, ohne Publishing, ohne neue Provider-Integrationen.

## Voraussetzungen

- Python 3.11+ und Repo-Root als Arbeitsverzeichnis.
- Optional `ffmpeg` / `ffprobe` im PATH (sonst entfallen MP3-Smoke und Render mit Warnungen / Blockern, sichtbar im `real_video_build_result.json`).
- Eine Datei `generate_script_response.json` mit den sechs `GenerateScriptResponse`-Pflichtfeldern (`title`, `hook`, `chapters`, `full_script`, `sources`, `warnings`).

Eine schnelle Quelle: BA 25.3 Bridge (`scripts/run_url_to_script_bridge.py`) erzeugt eine kompatible Datei unter `output/url_script_<run_id>/generate_script_response.json`.

## Befehl

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

## Ablauf intern

1. Adapter (BA 25.2) liest das Script-JSON und schreibt `output/real_local_preview_<run_id>/scene_asset_pack.json`.
2. Orchestrator (BA 25.1, `scripts/run_real_video_build.py`) baut nacheinander Asset Runner → Voiceover Smoke → Timeline → Clean Render → Subtitles → Burn-in und schreibt `output/real_build_<run_id>/real_video_build_result.json` plus `output/subtitle_burnin_<run_id>/preview_with_subtitles.mp4`.
3. BA 25.4 schreibt das Aggregat `output/real_local_preview_<run_id>/real_local_preview_result.json` (Schema `real_local_preview_result_v1`) mit Pfaden zum Pack, Build-Result und Preview-Video sowie eine kurze `REAL_LOCAL_PREVIEW_OPEN_ME.md`.

## Ergebnisse / Pfade

```text
output/
├── real_local_preview_<run_id>/
│   ├── scene_asset_pack.json                # Adapter-Output (BA 25.2)
│   ├── real_local_preview_result.json       # BA 25.4 Aggregat (V1)
│   └── REAL_LOCAL_PREVIEW_OPEN_ME.md        # Operator-Hilfe
├── real_build_<run_id>/
│   ├── clean_video.mp4
│   └── real_video_build_result.json         # BA 25.1 Index (V1)
├── subtitle_burnin_<run_id>/
│   └── preview_with_subtitles.mp4           # Endprodukt der Preview-Kette
├── full_voice_<run_id>/                     # Smoke MP3 + narration_script.txt
├── timeline_<run_id>/                       # timeline_manifest.json
├── subtitles_<run_id>/                      # subtitle_manifest.json + .srt
└── generated_assets_<run_id>/               # Placeholder-PNGs + asset_manifest.json
```

## Exit-Codes

| Code | Bedeutung |
|------|-----------|
| 0 | `completed` (`preview_with_subtitles.mp4` vorhanden) |
| 1 | `failed` (Orchestrator-Fehler, Schreibfehler) |
| 2 | `blocked` (z. B. ffmpeg fehlt, Preview konnte nicht erzeugt werden) |
| 3 | `invalid input` (run_id ungültig, Script-JSON fehlt/ungültig) |

## Offline-Smoke-Test

Tests `tests/test_ba254_local_preview_run.py` simulieren den BA-25.1-Orchestrator mit Stub-Artefakten und benötigen weder ffmpeg noch Provider-Keys. Sie sind die Referenz für CI-Smoke-Läufe.

## Nicht-Ziele

- Kein Final Render — nutzt weiterhin den bestehenden BA-24.x-Flow (`scripts/run_final_render.py`).
- Kein YouTube-Upload, kein Scheduling, kein Dashboard-Redesign.
- Keine Änderung an `GenerateScriptResponse`, `scene_asset_pack.json` oder `real_video_build_result.json`.
- Keine `.env`-Inhalte werden gelesen oder geloggt.
