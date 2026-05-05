# Real Video Build Mini Fixture (BA 25.1)

Minimaler Eingangs-Pack für den **Real Video Build Orchestrator** (`scripts/run_real_video_build.py`).

Inhalt:

- `scene_asset_pack.json` — 3 Szenen-Beats, lokale/placeholder-fähige Prompts, ohne Binärdateien.

## Zweck

Smoke-Lauf für **BA 25.1**: vorhandene Bausteine (Asset Runner → Timeline → Voiceover Smoke → Render → Subtitles → Burn-in) mit **einer** `run_id` zu einem `output/real_build_<run_id>/`-Indexpaket verbinden.

**Nicht** in BA 25.1 enthalten:

- URL-Input (BA 25.3)
- Adapter aus `GenerateScriptResponse`/Story-Pack (BA 25.2)
- Echter Final-Render-Output (bleibt bestehender BA 24.x-Flow)

## Beispiel

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

Erwartung:

- `output/real_build_real_mini_001/real_video_build_result.json`
- typischerweise `output/subtitle_burnin_real_mini_001/preview_with_subtitles.mp4` (wenn ffmpeg im PATH)
- bei fehlendem ffmpeg: klare Warnungen / blocking reasons im Manifest

Governance: keine Secrets, keine Provider-Calls, keine Publishing-/Upload-Schritte.
