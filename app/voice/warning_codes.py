"""Phase 7.x — einheitliche Voice-Warn-Präfixe (keine Logik)."""

# Preview / Commit
W_INVALID_ID = "[voice_synth:invalid_id]"
W_PLAN_MISSING = "[voice_synth:voice_plan_missing]"
W_NO_BLOCKS = "[voice_synth:no_blocks]"
W_DRY_RUN = "[voice_synth:dry_run]"
W_PLAN_STATUS_FAILED = "[voice_synth:voice_plan_status_failed]"
W_HINT_IGNORED = "[voice_synth:provider_hint_ignored]"
W_MISSING_KEY = "[voice_synth:missing_api_key]"
W_PREVIEW_OMITTED = "[voice_synth:preview_audio_omitted]"
W_INPUT_TRUNCATED = "[voice_synth:input_truncated]"
W_EMPTY_TEXT = "[voice_synth:empty_text]"
W_TRANSPORT_ERROR = "[voice_synth:transport_error]"
W_HTTP_ERROR = "[voice_synth:openai_http_error]"

# Commit (production_files)
W_COMMIT_DRY_RUN = "[voice_commit:dry_run]"
W_COMMIT_SKIPPED_READY = "[voice_commit:skipped_ready]"
W_COMMIT_FAILED = "[voice_commit:synth_failed]"
