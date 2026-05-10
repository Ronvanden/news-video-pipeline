# BA 32.69 — Optional Live 2-Clip Smoke Checklist

## Purpose

This is a **manual operator checklist** for exactly one carefully confirmed live two-motion-clip production smoke. It is documentation-first and intentionally conservative: it does **not** authorize CI runs, repeated experiments, scale tests, publishing, or unattended provider usage.

## Hard safety rule: do not run in CI

- **Do not run this live smoke in CI, cron, deploy hooks, GitHub Actions, or unattended automation.**
- Run it only from a local/operator-controlled shell or manually controlled server session.
- If `CI` is present, if you cannot watch the run, or if billing/quota is unclear: **stop**.

## Scope and non-goals

- One manually confirmed live smoke only.
- No provider secrets in commits, screenshots, tickets, logs, PRs, or chat.
- Do not read `.env`; use the process/runtime secret configuration only.
- Do not change provider logic or render logic for this checklist.
- Keep `max_motion_clips=2`; do not increase it for the first live smoke.
- Automated tests remain mock-only.

## Required environment variable names only

Check **presence only**, never values:

| Provider area | Required variable names |
|---|---|
| Runway motion | `RUNWAY_API_KEY` |
| Gemini image provider | `GEMINI_API_KEY` or `GOOGLE_API_KEY` |
| OpenAI image provider | `OPENAI_API_KEY` |
| Leonardo image provider | `LEONARDO_API_KEY` |
| ElevenLabs voice provider | `ELEVENLABS_API_KEY` |
| OpenAI voice provider | `OPENAI_API_KEY` |

Optional/runtime tuning names that may be present without being logged: `GEMINI_IMAGE_MODEL`, `GEMINI_IMAGE_TRANSPORT`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_MODEL_ID`, `OPENAI_TTS_VOICE`, `OPENAI_TTS_MODEL`, `LEONARDO_MODEL_ID`, `LEONARDO_API_ENDPOINT`.

## Optional dry-run readiness helper

The helper is safe to run before the live smoke. It does **not** call Runway, OpenAI, Leonardo, ElevenLabs, Gemini, or any other external API. It only checks environment-variable presence and prints a checklist summary.

```bash
python scripts/check_live_2_clip_smoke_readiness.py \
  --image-provider gemini_image \
  --voice-provider elevenlabs \
  --duration-minutes 1 \
  --max-scenes 3 \
  --max-motion-clips 2 \
  --motion-clip-duration-seconds 10 \
  --confirm-provider-costs \
  --ack-live-provider-risk \
  --ack-not-ci
```

Expected helper behavior:

- Exit `0` only when required provider variables are present, operator confirmations are explicit, `CI` is not detected, and `max_motion_clips=2`.
- Exit `3` when readiness is blocked.
- Print only booleans for variable presence; it must never print secret values.

## Pre-run checklist

Proceed only if every item is true:

1. **Human control:** An operator is watching the run and can abort immediately.
2. **No CI:** This is not CI/automation; `CI` is not set for the live process.
3. **Provider-cost confirmation:** Billing/quota is understood and explicitly accepted for image provider, voice provider, and Runway motion.
4. **Runway key presence:** `RUNWAY_API_KEY` is present in runtime configuration; value is not displayed or logged.
5. **Image provider safety:** Select exactly one live image provider and confirm its matching variable name is present. Prefer the smallest image count that still allows two motion slots.
6. **Voice provider safety:** Select exactly one voice mode; for a first smoke prefer `elevenlabs` or `openai` only if billing is confirmed. Otherwise use smoke voice and record that this is not a full live voice smoke.
7. **Short duration:** Use **1–2 minutes**, not a 10-minute production run.
8. **Small scene cap:** Use **2–4 scenes**; recommended first attempt is `max_scenes=3`.
9. **Motion cap:** Set **`max_motion_clips=2`** exactly.
10. **Motion duration:** Use **5–10 seconds** per motion clip; recommended first attempt is `motion_clip_duration_seconds=10`.
11. **Known source URL:** Use a low-risk, short article URL already reviewed for editorial suitability.
12. **Abort plan:** Operator knows how to cancel with `Ctrl+C`, stop the local server/job, and revoke/rotate provider keys if accidentally exposed.

## Run-time guardrails

- Use the Founder Dashboard or API path deliberately; do not script repeated live submissions.
- Confirm the request includes live-cost confirmation (`confirm_provider_costs=true`) before enabling live flags.
- Keep image provider, voice provider, and motion settings visible to the operator before submit.
- Do not paste secrets into URL fields, titles, prompts, screenshots, logs, or issue reports.
- Abort immediately if the URL is wrong, the scene count expands unexpectedly, `max_motion_clips` is not `2`, provider warnings mention missing/invalid credentials, or cost/quota behavior is unclear.

## Expected output artifact locations

For Dashboard URL-to-video generation, inspect the run directory under:

- `output/video_generate/<run_id>/final_video.mp4`
- `output/video_generate/<run_id>/run_summary.json`
- `output/video_generate/<run_id>/asset_manifest.json` or generated-assets subfolder referenced by `run_summary.json`
- `output/video_generate/<run_id>/OPEN_ME_VIDEO_RESULT.html`
- Any `scene_###_motion.mp4` files referenced by `motion_clip_artifact.video_clip_paths` or asset rows

Depending on orchestration details, related handoff artifacts may also appear under `output/generated_assets_<run_id>/`, `output/timeline_<run_id>/`, `output/render_<run_id>/`, or `output/final_render_<run_id>/`.

## What to inspect after the run

1. `run_summary.json`
   - `motion_slot_plan.enabled=true`
   - `motion_slot_plan.planned_count` is at most `2`
   - rendered/skipped/failed slot statuses are understandable
   - `motion_clip_artifact.rendered_count` matches the intended two-clip smoke outcome
   - warnings do not hide provider failures or placeholder fallbacks
2. `asset_manifest.json`
   - Real motion rows have `video_path`, `provider_used: runway`, and `generation_mode: runway_video_live`.
   - Placeholder rows are clearly marked by placeholder generation modes/providers and are not mistaken for real clips.
   - `motion_clip_playback_seconds`, `motion_clip_rest_image_seconds`, and `motion_clip_window_respected` are present for Runway clip rows when applicable.
3. `final_video.mp4`
   - Video opens locally.
   - Motion clips play only in their bounded windows and do not loop across full scenes.
   - Still-image fallback after a motion window is acceptable.
   - Voice is present if a live voice provider was selected; otherwise document smoke/silent voice behavior.
4. `OPEN_ME_VIDEO_RESULT.html`
   - Operator-facing readiness, warnings, provider blockers, and output links are consistent with the JSON artifacts.

## How to identify placeholders vs. real clips

- **Real Runway clips:** `generation_mode: runway_video_live`, `provider_used: runway`, non-empty `video_path`, and a matching local `scene_###_motion.mp4` file.
- **Placeholder images:** placeholder/smoke generation mode or provider metadata, generated placeholder PNGs, or warnings indicating fallback/placeholder asset creation.
- **Smoke/silent voice:** voice manifest or summary fields indicating dummy/smoke voice, missing provider key, or silent render warning.
- Do not judge by file existence alone; always cross-check manifest metadata and warnings.

## Audit artifacts to save

Save only secret-free artifacts:

- Screenshot of the Dashboard request settings before submit, with no secret values visible.
- Screenshot of final Dashboard/`OPEN_ME_VIDEO_RESULT.html` status and warnings.
- `run_summary.json` with secret-free paths if needed.
- `asset_manifest.json` after confirming it contains no secret values.
- File listing of the run folder showing `final_video.mp4` and motion clips.
- Short local playback note: timestamps where the two motion clips appear, whether voice is live/smoke, and any warnings.

## Stop / abort safely

- Before provider dispatch: cancel the browser/API request or press `Ctrl+C` in the foreground process.
- During local server use: stop the server/job from the controlling terminal; do not retry automatically.
- If secrets appear in output: stop, remove/redact the artifact from any shared location, rotate the affected key, and log an incident in `ISSUES_LOG.md` without the secret value.
- If provider costs spike, quota errors appear, or a loop/retry is suspected: stop immediately and do not rerun until the cause is understood.

## Rollback and cleanup notes

- This checklist does not require code rollback; it is an operational gate.
- Keep successful audit artifacts only as long as needed for review.
- Remove failed large media outputs from local `output/` when no longer needed.
- Do not delete artifacts before recording run ID, warnings, provider modes, and whether clips were real or placeholders.
- Revert any accidental local config changes outside the repo; never commit runtime secret configuration.

## When not to proceed

Do **not** run the live smoke if any of these apply:

- `RUNWAY_API_KEY` is missing or key ownership/billing is unclear.
- Image or voice provider key presence does not match the selected live provider.
- `confirm_provider_costs` is not explicitly accepted.
- The run would happen in CI, unattended automation, or a shared shell with visible secrets.
- Requested duration is longer than 2 minutes or scene cap is above 4 for the first live two-clip smoke.
- `max_motion_clips` is not exactly `2`.
- The source URL is unreviewed, legally risky, paywalled in a way the extractor cannot handle, or editorially unsuitable.
- Recent mock tests are failing.
- The operator cannot inspect artifacts immediately after the run.
