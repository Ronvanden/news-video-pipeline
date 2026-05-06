# Local Preview Founder Report

## Verdict
Status: **WARNING**

## Founder Decision (BA 21.5)
- **Entscheidung:** `REVIEW_REQUIRED` — Kein harter Blocker — Founder-Review empfohlen (Warnungen oder Prüfpunkte).
- **Top-Thema:** Warnung [WARNING]: audio_missing_silent_render
- **Nächster Schritt:** Öffne die Preview, prüfe die Warnungen und entscheide, ob ein Repair nötig ist.
- **Faktoren:**
  - Verdict: WARNING
  - Quality-Checkliste: WARNING
  - Subtitle Quality: PASS
  - Sync Guard: WARNING
  - Höchste Warnstufe: WARNING
- **Signale:** Verdict=WARNING, Quality=warning, Subtitle=pass, Sync=warning, Warnstufe=WARNING

## Preview
Preview erzeugt: **ja**
Datei öffnen: `C:\Users\buicr\news-to-video-pipeline\output\local_preview_mini_e2e\preview_with_subtitles.mp4`

## Run
Run ID: `mini_e2e`
Pipeline Ordner: `C:\Users\buicr\news-to-video-pipeline\output\local_preview_mini_e2e`

## Steps
- **build_subtitles**: WARNING
  - output: `C:\Users\buicr\news-to-video-pipeline\output\subtitles_mini_e2e\subtitle_manifest.json`
  - warning: subtitle_timeline_duration_used
- **render_clean**: WARNING
  - output: `C:\Users\buicr\news-to-video-pipeline\output\local_preview_mini_e2e\clean_video.mp4`
  - warning: audio_missing_silent_render
- **burnin_preview**: WARNING
  - output: `C:\Users\buicr\news-to-video-pipeline\output\subtitle_burnin_mini_e2e\preview_with_subtitles.mp4`
  - warning: subtitle_typewriter_ass_renderer_used, preview_with_subtitles_already_exists

## Warnings
- subtitle_timeline_duration_used
- audio_missing_silent_render
- subtitle_typewriter_ass_renderer_used
- preview_with_subtitles_already_exists

## Warning Classification (BA 21.4)
Höchste Stufe: **WARNING**
Übersicht: 4 WARNING, 4 INFO

Klassifizierte Codes:
- [INFO] `subtitle_timeline_duration_used`
- [WARNING] `audio_missing_silent_render`
- [INFO] `subtitle_typewriter_ass_renderer_used`
- [INFO] `preview_with_subtitles_already_exists`
- [INFO] `sync_guard_no_audio_file`
- [WARNING] `sync_guard_preview_vs_timeline_warn`
- [WARNING] `sync_guard_preview_vs_clean_warn`
- [WARNING] `sync_guard_warning`


## Blocking Reasons
- *(keine)*

## Quality Checklist
- [PASS] Preview video exists — file present (`C:\Users\buicr\news-to-video-pipeline\output\local_preview_mini_e2e\preview_with_subtitles.mp4`)
- [PASS] Preview video non-empty — 70070 bytes (`C:\Users\buicr\news-to-video-pipeline\output\local_preview_mini_e2e\preview_with_subtitles.mp4`)
- [PASS] Founder report exists (`C:\Users\buicr\news-to-video-pipeline\output\local_preview_mini_e2e\local_preview_report.md`)
- [PASS] OPEN_ME exists (`C:\Users\buicr\news-to-video-pipeline\output\local_preview_mini_e2e\OPEN_ME.md`)
- [PASS] Subtitle quality — 14 cues; status=pass (`C:\Users\buicr\news-to-video-pipeline\output\subtitles_mini_e2e\subtitle_manifest.json`)
- [WARNING] Audio/video sync — status=warning; tl=6.0s; sub=6.0s; clean=6.0s; pv=8.0s
- [PASS] Blocking reasons clear — no blocking reasons after sanitize
- [WARNING] Warnings present — 4 warning(s)


## Subtitle Quality
- Status: **PASS**
- Summary: 14 cues; status=pass


## Sync Guard
Status: **WARNING**
- Timeline: 6.0s
- Subtitle: 6.0s
- Audio: nicht verfügbar
- Clean: 6.0s
- Preview: 8.0s
- Hinweis: Kein Audio vorhanden; Silent Render verwendet.
- [WARNING] Audio duration available — no audio file (silent render possible)
- [WARNING] Preview video vs timeline — preview 8.00s vs timeline 6.00s
- [WARNING] Preview vs clean video — preview 8.00s vs clean 6.04s


## Next Step
Öffne die Preview, prüfe die Warnungen und entscheide, ob ein Repair nötig ist.
