# Storyboard Live Production Run V1

This runbook covers the manual Founder Dashboard path for a first real Storyboard-based video run.

## Scope

- Dashboard-only operator flow.
- Live providers only after explicit cost confirmation.
- OpenAI Image up to 10 image tasks.
- ElevenLabs Voice up to 10 voice tasks.
- Runway Motion up to 3 motion tasks.
- Local render through the existing Storyboard local render execute path.
- No Firestore writes and no change to `GenerateScriptResponse`.

The normal `Run Full Pipeline` button remains plan-only and does not start live providers.

## Required Setup

Before opening the dashboard, configure provider credentials in the local shell that starts the app:

- OpenAI image credential expected by the existing OpenAI image connector.
- ElevenLabs credential and `ELEVENLABS_VOICE_ID`.
- Runway credential expected by the existing Runway connector.

Do not paste secrets into the dashboard output panels or commit them to files.

## Dashboard Steps

1. Start the app locally.
2. Open `GET /founder/dashboard`.
3. Fill or generate the input body.
4. Confirm all three cost checkboxes:
   - `OpenAI Image Kosten bestätigen`
   - `ElevenLabs Voice Kosten bestätigen`
   - `Runway Motion Kosten bestätigen`
5. Click `Live Production Run`.

The run executes:

1. Generate/body intake normalization.
2. Export Package.
3. Storyboard Plan.
4. Storyboard Readiness.
5. Asset Plan.
6. OpenAI Image Live.
7. ElevenLabs Voice Live.
8. Runway Motion Live.
9. Storyboard Render Timeline.
10. Storyboard Voice Mixdown.
11. Storyboard Local Render Package.
12. Storyboard Local Render Execute.
13. Storyboard Live Run Review.

## Expected Outputs

Artifacts are written below `output/storyboard_runs/`.

Expected successful signals:

- Image task outputs with `output_exists=true`.
- Voice task outputs with `output_exists=true`.
- Motion task outputs with `output_exists=true` for completed clips, or visible warnings for skipped/failed optional motion.
- `storyboard_voice_mixdown.mp3` when multiple scene voices need one renderer audio file.
- `asset_manifest.json`.
- `timeline_manifest.json`.
- `render_output_manifest.json`.
- `final_video.mp4`.

The `Storyboard Live Run Review` panel summarizes image files, voice files, motion clips, estimated provider calls, warnings, blockers, and the final video path. If the final MP4 exists, the dashboard embeds it and exposes read-only artifact links.

## Guard Behavior

- If any cost checkbox is missing, the run aborts before live provider calls.
- If Storyboard Readiness is blocked, downstream live steps do not proceed.
- If Runway does not return a clip, the Live Production Run continues image-only when images and voice are available; the Runway blocker is surfaced as a warning in the Review panel.
- A failed local render marks the Live Run Review as blocked or warning with a readable next action.

## Troubleshooting

- Missing ElevenLabs voice: verify `ELEVENLABS_VOICE_ID` in the shell that starts the app.
- Runway timeout: rerun only `Runway Motion erzeugen` after checking the source image output exists, then rebuild Render Timeline and Local Render.
- Final video missing: inspect `Storyboard Local Render Execute`, `render_output_manifest_path`, and the Review panel blockers.
