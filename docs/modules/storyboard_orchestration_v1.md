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
- Full pipeline order: Generate -> Export Package -> Storyboard Plan -> Storyboard Readiness -> Asset Plan -> Asset Execution Stub -> Preview -> Readiness -> Optimize -> CTR -> Founder Summary -> Production Bundle

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
