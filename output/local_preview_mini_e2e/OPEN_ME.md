# Local Preview Package

## Status
Verdict: **WARNING**

## Founder Decision (BA 21.5)
- **Entscheidung:** `REVIEW_REQUIRED` — Kein harter Blocker — Founder-Review empfohlen (Warnungen oder Prüfpunkte).
- **Top-Thema:** Warnung [WARNING]: audio_missing_silent_render
- **Nächster Schritt:** Öffne die Preview, prüfe die Warnungen und entscheide, ob ein Repair nötig ist.

## Open First
Preview Video: `C:\Users\buicr\news-to-video-pipeline\output\local_preview_mini_e2e\preview_with_subtitles.mp4`
Founder Report: `C:\Users\buicr\news-to-video-pipeline\output\local_preview_mini_e2e\local_preview_report.md`

## What This Is
Dieser Ordner enthält einen lokalen Preview-Lauf der Video-Pipeline.

## Key Artefacts
- Clean Video: `C:\Users\buicr\news-to-video-pipeline\output\local_preview_mini_e2e\clean_video.mp4`
- Preview Video: `C:\Users\buicr\news-to-video-pipeline\output\local_preview_mini_e2e\preview_with_subtitles.mp4`
- Subtitle File: `C:\Users\buicr\news-to-video-pipeline\output\subtitles_mini_e2e\subtitle_manifest.json`
- Founder Report: `C:\Users\buicr\news-to-video-pipeline\output\local_preview_mini_e2e\local_preview_report.md`
- Pipeline Folder: `C:\Users\buicr\news-to-video-pipeline\output\local_preview_mini_e2e`

## Warnings
- subtitle_timeline_duration_used
- audio_missing_silent_render
- subtitle_typewriter_ass_renderer_used
- preview_with_subtitles_already_exists

## Warning Levels (BA 21.4)
Höchste Stufe: **WARNING**
4 WARNING, 4 INFO


## Blocking Reasons
- Keine

## Quality Checklist
- [PASS] Preview video exists
- [PASS] Preview video non-empty
- [PASS] Founder report exists
- [PASS] OPEN_ME exists
- [PASS] Subtitle quality
- [WARNING] Audio/video sync
- [PASS] Blocking reasons clear
- [WARNING] Warnings present


## Subtitle Quality
- Status: PASS
- Hinweis: 14 cues; status=pass


## Sync Guard
- Status: WARNING
- Hinweis: Kein Audio vorhanden; Silent Render verwendet.


## Next Step
Öffne die Preview, prüfe die Warnungen und entscheide, ob ein Repair nötig ist.
