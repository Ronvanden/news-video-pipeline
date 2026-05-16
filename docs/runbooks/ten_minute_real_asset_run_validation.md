# Ten Minute Real Asset Run Validation

## Zweck des Tests

Dieser Runbook-Eintrag dokumentiert den ersten kontrollierten 10-Minuten-Real-Asset-Test des Founder-Dashboard-Video-Generate-Flows. Ziel war zu prüfen, ob der Pfad mit echter YouTube-Quelle, echten OpenAI-Image-Assets, echter ElevenLabs-Voice und finalem Render stabil bis zu einem produktionsnahen Ergebnis skaliert.

Der Test war ein Validierungsrun, kein Publishing- oder Qualitäts-Final.

## Request-Kurzform

- Endpoint: `POST /founder/dashboard/video/generate`
- URL: `https://www.youtube.com/watch?v=1wa5pf9Ibp4`
- `duration_target_seconds`: `600`
- `max_scenes`: `15`
- `max_live_assets`: `15`
- `allow_live_assets`: `true`
- `allow_live_motion`: `false`
- `confirm_provider_costs`: `true`
- `voice_mode`: `elevenlabs`
- `image_provider`: `openai_image`
- `generate_thumbnail_pack`: `false`

## Run-ID und Artefakte

- Run-ID: `video_gen_10m_1778944639733`
- Status: `production_ready`
- Finalvideo: `output/video_generate/video_gen_10m_1778944639733/final_video.mp4`
- Script: `output/video_generate/video_gen_10m_1778944639733/script.json`
- Scene Asset Pack: `output/video_generate/video_gen_10m_1778944639733/scene_asset_pack.json`
- Asset Manifest: `output/video_generate/video_gen_10m_1778944639733/generated_assets_video_gen_10m_1778944639733/asset_manifest.json`
- Voiceover: `output/video_generate/video_gen_10m_1778944639733/voiceover.mp3`

## Akzeptanzwerte

- `target_word_count`: `1280`
- `script_word_count`: `1172`
- Zielwort-Prozent: `91.6%`
- `voice_duration`: `560.29s`
- `final_video_duration`: `561.04s`
- `duration_ratio`: `0.935`
- `scene_count`: `9`
- echte OpenAI-Bilder: `9/9`
- `visual_prompt_anatomy`: `9/9`
- Audio-Gap: `0.71s`
- `blocking_reasons`: keine

## Was funktioniert hat

- YouTube-Watch-URL wurde als YouTube-Quelle erkannt.
- Transcript wurde als Source-Material genutzt.
- Longform-Skript erreichte mehr als 90% der Zielwortzahl.
- ElevenLabs erzeugte eine echte Voice-Datei.
- OpenAI Image erzeugte echte Szenenbilder ohne Placeholder.
- Visual Prompt Anatomy blieb im Asset-Pfad vorhanden.
- Timeline wurde stabil auf Voice-Dauer angepasst.
- `final_video.mp4` wurde erzeugt.
- Der Run erreichte `production_ready`.

## Warnings, aber nicht blockierend

- `youtube_source_rewrite_used`
- `transcript_used_as_source_material`
- Hinweis, dass das Skript eine eigenständige deutsche Story-Formulierung ist und keine wörtliche Abschrift.
- `Target word count: 1280, Actual word count: 1172`
- `Generated using LLM mode`
- `LLM longform expansion repaired toward target length`
- Wiederholte OpenAI-Image-Metadaten zu Provider, Modell, Transport und Größe.
- `elevenlabs_voice_id_default_fallback`
- Timeline wurde per `fit_to_voice` an die Voice angepasst.

Diese Warnings sind für den Validierungszweck akzeptabel und haben den Run nicht blockiert.

## Restschwächen

- Szenenvarianz und Themenbindung sollten weiter verbessert werden.
- Szene 9 wirkte in der visuellen Stichprobe etwas generisch.
- Motion war bewusst deaktiviert.
- Thumbnail-Pack war deaktiviert.
- Intro, Outro und CTA/Subscribe-Layer sind noch nicht Teil dieses validierten Pfads.
- YouTube-Metadaten und Publishing-Vorbereitung sind noch nicht abgedeckt.

## Empfohlene nächste BA-Blöcke

A) 10-Minuten-Video qualitativ prüfen.

B) Intro/Outro/CTA/Subscribe-Layer ergänzen.

C) Thumbnail-Pack wieder aktivieren.

D) Motion optional kontrolliert testen.

E) YouTube-Metadaten/Publishing vorbereiten.
