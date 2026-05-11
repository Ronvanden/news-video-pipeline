# Storyboard Orchestration V1

Plan-only orchestration layer between script/prompt planning and later production execution.

## Scope

- Builds `StoryboardPlan` from either a `ProductionPromptPlan` or script-style chapters.
- Reuses existing scene blueprint / scene prompt logic.
- Produces per-scene visual intent, voice text, image prompt, video prompt, duration, transition, and asset type.
- No provider calls, no persistence, no secrets, no `.env` reads.
- `GenerateScriptResponse` remains unchanged.

## Endpoint

`POST /story-engine/storyboard-plan`

Input:

- `prompt_plan` optional full `ProductionPromptPlan`
- or `hook`, `chapters[]`, optional `scene_prompts[]`, `video_template`

Output:

- `storyboard_version`
- `status`
- `source_type`
- `total_duration_seconds`
- `scenes[]`
- `warnings`
- `dashboard_ready`

## Downstream Use

The storyboard is designed as the stable handoff for later image generation, Runway/Kling clip planning, voice alignment, and render timeline assembly. It intentionally does not start those steps.

## Founder Dashboard Use

The Founder Dashboard exposes the endpoint as a plan-only step:

- Button: `Storyboard erstellen`
- Output panel: `Storyboard Plan`
- Button: `Storyboard prüfen`
- Output panel: `Storyboard Readiness`
- Button: `Asset Plan erstellen`
- Output panel: `Asset Plan`
- Button: `Asset Tasks simulieren`
- Output panel: `Asset Execution Stub`
- Button: `Render Timeline bauen`
- Output panel: `Storyboard Render Timeline`
- Button: `Voice Mixdown`
- Output panel: `Storyboard Voice Mixdown`
- Button: `Local Render Package bauen`
- Output panel: `Storyboard Local Render Package`
- Button: `Local Render starten`
- Output panel: `Storyboard Local Render Execute`
- Full pipeline order: Generate -> Export Package -> Storyboard Plan -> Storyboard Readiness -> Asset Plan -> Asset Execution Stub -> Render Timeline -> Local Render Package -> Preview -> Readiness -> Optimize -> CTR -> Founder Summary -> Production Bundle

On failure, the dashboard marks the Storyboard timeline step as failed, shows the readable error message, and stops the flow. The dashboard call does not write to Firestore, does not start providers, and does not change `GenerateScriptResponse`.

## Readiness Gate

`POST /story-engine/storyboard-readiness` evaluates a provided `StoryboardPlan` through a plan-only production gate before image, motion, voice, or render providers are allowed to run.

Result fields:

- `overall_status`: `ready`, `warning`, or `blocked`
- `score`: 0-100
- `blocking_issues`
- `warnings`
- `scene_results[]`
- `production_recommendation`

The gate blocks missing scenes, zero total duration, missing visual intent, missing voice text, required prompt gaps, and invalid scene duration. It warns on missing provider hints, too short/long scenes, and duplicate or near-duplicate prompts. Dashboard flow stops only on `blocked`; `warning` can continue.

## Asset Generation Plan

`POST /story-engine/asset-generation-plan` converts a checked `StoryboardPlan` into deterministic, plan-only asset tasks. It accepts:

- `storyboard_plan`
- optional `readiness_result`

The endpoint plans tasks only; it does not call OpenAI Image, Kling, Runway, voice providers, renderers, Firestore, or the filesystem.

Task fields:

- `task_id`
- `scene_id` / `scene_number`
- `asset_type`: `image`, `video`, `voice`, `thumbnail`, `music`, `subtitle`, `render_hint`
- `provider_hint`
- `prompt`
- `duration_seconds`
- `output_path`
- `status`: `planned`
- `dependencies`
- `warnings`

If Storyboard Readiness is `blocked`, the asset plan returns `plan_status=blocked` and no normal provider task list. For `ready` or `warning`, it plans image/video/voice tasks per scene, plus subtitle/render hints and a global thumbnail task with deterministic IDs and output paths.

## Asset Execution Stub

`POST /story-engine/asset-execution-stub` simulates execution of an `AssetGenerationPlan` without provider calls, file writes, or Firestore writes.

Input:

- `asset_generation_plan`
- `dry_run` (default `true`)

Output:

- `execution_status`: `dry_run`, `completed_stub`, `skipped`, or `failed`
- `task_results[]`
- `warnings`
- `blocking_issues`
- `estimated_provider_calls`
- `estimated_outputs`

Blocked asset plans return `failed` and no normal task execution. Planned tasks return `dry_run` in dry-run mode or `completed_stub` in stub mode. Missing prompts or missing provider hints are reported per task so later real provider adapters can replace the stub result shape directly.

## OpenAI Image Live V1

`POST /story-engine/openai-image-live-execution` is the first live provider path for the Storyboard chain. It executes capped `image` tasks from an `AssetGenerationPlan` through the existing OpenAI Image connector.

Safety defaults:

- requires `confirm_provider_costs=true`
- `max_live_image_tasks` is capped at `10`
- default model: `gpt-image-2`
- default size: `1024x1024`
- output root: `output`
- output path pattern: `output/storyboard_runs/<run_id>/<scene_id>/image.png`

The Founder Dashboard exposes this as a manual action only: `OpenAI Bild erzeugen` plus the `OpenAI Image Kosten bestätigen` checkbox. It can generate up to ten storyboard image tasks in one confirmed run. It is intentionally not part of the automatic full-pipeline button, so the plan-only flow remains safe by default.

## ElevenLabs Voice Live V1

`POST /story-engine/elevenlabs-voice-live-execution` is the first live voice provider path for the Storyboard chain. It executes capped `voice` tasks from an `AssetGenerationPlan` through ElevenLabs and writes MP3 files to deterministic local paths.

Safety defaults:

- requires `confirm_provider_costs=true`
- requires an ElevenLabs voice id from the request or `ELEVENLABS_VOICE_ID`
- requires `ELEVENLABS_API_KEY` for real provider execution
- `max_live_voice_tasks` is capped at `10`
- default model: `eleven_multilingual_v2`
- output root: `output`
- output path pattern: `output/storyboard_runs/<run_id>/<scene_id>/voice.mp3`

The Founder Dashboard exposes this as a manual action only: `ElevenLabs Voice erzeugen` plus the `ElevenLabs Voice Kosten bestätigen` checkbox. The automatic full-pipeline button still stops at plan/stub execution and does not start live voice providers.

## Runway Motion Live V1

`POST /story-engine/runway-motion-live-execution` is the first live motion provider path for the Storyboard chain. It executes capped `video` tasks from an `AssetGenerationPlan` through the existing Runway image-to-video connector.

Safety defaults:

- requires `confirm_provider_costs=true`
- requires a completed live image result for the same scene
- `max_live_motion_tasks` is capped at `3`; the dashboard uses `3`
- default clip duration: `5` seconds
- output root: `output`
- output path pattern: `output/storyboard_runs/<run_id>/<scene_id>/motion.mp4`

The Founder Dashboard exposes this as a manual action only: `Runway Motion erzeugen` plus the `Runway Motion Kosten bestätigen` checkbox. The automatic full-pipeline button still does not start live motion providers. Successful results are passed into `POST /story-engine/storyboard-render-timeline` as `motion_execution_result`, so scenes with live clips switch from `image_only` fallback to `video_clip`.

## Storyboard Render Timeline V1

`POST /story-engine/storyboard-render-timeline` combines:

- `storyboard_plan`
- optional `asset_generation_plan`
- optional `image_execution_result`
- optional `voice_execution_result`
- optional `motion_execution_result`

The endpoint returns a deterministic render handoff:

- `overall_status`: `ready`, `warning`, or `blocked`
- `segments[]` with scene timing, image path, optional video path, optional voice path, transition, render mode, motion status, warnings and blockers
- aggregate counts for ready image/voice/video segments and skipped motion segments
- `render_recommendation`

No render is started and no files are written. If a scene requested motion but no clip path exists while an image is available, the segment uses `render_mode=image_only`, `motion_status=skipped`, and warning `motion_requested_but_no_clip_fallback_to_image` instead of treating the missing clip as a placeholder. The Founder Dashboard exposes this as `Render Timeline bauen`.

## Storyboard Local Render Package V1

`POST /story-engine/storyboard-local-render-package` converts a `StoryboardRenderTimelineResult` into deterministic manifest shapes for the existing local renderer.

Input:

- `render_timeline`
- `run_id` (default `storyboard_local_render_v1`)
- `output_root` (default `output`)

Output:

- `timeline_manifest_path`
- `asset_manifest_path`
- `final_video_path`
- `timeline_manifest`
- `asset_manifest`
- `render_command_hint`
- `warnings`
- `blocking_issues`
- `render_recommendation`

This step does not write manifest files and does not start ffmpeg. It prepares the handoff for a later local render step. Multiple per-scene Voice files are surfaced as `storyboard_render_voice_mixdown_required`, because the current renderer expects one global `audio_path`.

## Storyboard Local Render Execute V1

`POST /story-engine/storyboard-local-render-execute` writes the planned `asset_manifest.json` and `timeline_manifest.json` from a `StoryboardLocalRenderPackageResult` and then invokes the existing `scripts/render_final_story_video.py` path.

Input:

- `local_render_package`
- `run_id` (default `storyboard_local_render_execute_v1`)
- `output_root` (default `output`)
- `dry_run` (default `false`)
- `motion_mode` (default `basic`)

Output:

- `execution_status`
- `asset_manifest_path`
- `timeline_manifest_path`
- `final_video_path`
- `render_output_manifest_path`
- `manifest_written`
- `video_created`
- `output_exists`
- `file_size_bytes`
- `warnings`
- `blocking_issues`
- `render_recommendation`

With `dry_run=true`, the step writes manifests only. With `dry_run=false`, it runs the existing local renderer and returns the resulting `final_video_path` plus `render_output_manifest_path` when available. No provider calls, no Firestore writes, and no `GenerateScriptResponse` changes occur here.

The Founder Dashboard turns returned paths below `output/storyboard_runs/<run_id>/` into read-only artifact links via `GET /founder/dashboard/storyboard-render/file/{run_id}/{artifact_path}`. When `output_exists=true`, the dashboard embeds the local MP4 with `<video controls>` and exposes links for the final video plus render, timeline, and asset manifests. The route is limited to Storyboard render runs and allowed artifact suffixes; it does not write files or start providers.

## Storyboard Voice Mixdown V1

`POST /story-engine/storyboard-voice-mixdown` merges scene-level Voice files from a `StoryboardRenderTimelineResult` into one local MP3 for the renderer.

Input:

- `render_timeline`
- `run_id` (default `storyboard_voice_mixdown_v1`)
- `output_root` (default `output`)
- `dry_run` (default `false`)

Output:

- `execution_status`
- `mixed_audio_path`
- `output_exists`
- `file_size_bytes`
- `input_voice_paths`
- `warnings`
- `blocking_issues`
- `render_recommendation`

With `dry_run=true`, the endpoint only plans the mixdown path. With `dry_run=false`, it uses local ffmpeg concat when multiple scene MP3s exist, or passthrough-copy when exactly one Voice file exists. No provider calls, no Firestore writes, and no `GenerateScriptResponse` changes occur here.
