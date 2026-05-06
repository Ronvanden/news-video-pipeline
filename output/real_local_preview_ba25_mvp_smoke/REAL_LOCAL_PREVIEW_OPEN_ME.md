# Real Local Preview Run — ba25_mvp_smoke

BA 25.4 hat aus einem realen `generate_script_response.json` ein lokales Preview-Paket gebaut (BA 25.2 Adapter → BA 25.1 Orchestrator).

- **Status**: completed
- **Script-Input**: `C:\Users\buicr\news-to-video-pipeline\output\url_script_ba25_mvp_smoke\generate_script_response.json`
- **Scene Asset Pack**: `C:\Users\buicr\news-to-video-pipeline\output\real_local_preview_ba25_mvp_smoke\scene_asset_pack.json`
- **Real Build Result**: `C:\Users\buicr\news-to-video-pipeline\output\real_build_ba25_mvp_smoke\real_video_build_result.json`
- **Preview Video**: `C:\Users\buicr\news-to-video-pipeline\output\subtitle_burnin_ba25_mvp_smoke\preview_with_subtitles.mp4`

BA 25.4 ändert weder den `GenerateScriptResponse`-Vertrag noch das `scene_asset_pack.json`- oder `real_video_build_result.json`-Schema. Final Render bleibt der bestehende BA 24.x-Flow (`scripts/run_final_render.py`).
