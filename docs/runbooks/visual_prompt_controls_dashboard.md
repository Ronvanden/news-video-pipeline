## Visual Prompt Controls Dashboard Note

The Founder Dashboard loads preset controls read-only from `GET /visual-plan/presets` or the config reference `visual_plan_relative.presets.path`.
Selections are stored locally in `window.visualPromptControls` and included in the existing session snapshot.
The preview area exposes `window.visualPromptControlsPreviewState` with `backend_payload: not_sent`.
This makes defaults, provider target, and text safety mode inspectable without changing Generate, provider, or render flows.
Storyboard results that include Visual Prompt Engine fields show compact `prompt_quality_score`, `prompt_risk_flags`, `visual_style_profile`, and optional `visual_prompt_anatomy`.
Future production wiring should stay additive and should land with explicit API contract tests.
