# URL-to-Final-Video Smoke — Operator

- **schema_version**: `ba_25_6_url_to_final_video_result_v1`
- **run_id**: `ba25_mvp_no_approval`
- **ok**: `False`
- **status**: `blocked`
- **auto_approved**: `False`

## Pfade
- Result JSON: `C:\Users\buicr\news-to-video-pipeline\output\url_to_final_video_ba25_mvp_no_approval\url_to_final_video_result.json`
- Final Video: ``
- Human Approval: `—`

## Hinweis
Ohne Auto-Approve wird **kein** `human_approval.json` erzeugt und kein Final Render ausgeführt. Für den Smoke-Flow mit finalem Video: Standard (Auto-Approve an) oder manuell freigeben und `run_final_render.py` starten.

## Nächster Schritt
Human approval required before final render. Ohne `--no-auto-approve` legt der Smoke-Runner eine Dev-Freigabe an; oder manuell `human_approval.json` im Paket `local_preview_<run_id>/` erstellen und `scripts/run_final_render.py` ausführen.

Kein Publishing, kein Upload in diesem Schritt.
