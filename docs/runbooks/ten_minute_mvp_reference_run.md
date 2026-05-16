# Ten Minute MVP Reference Run

## Zweck

Dieser Runbook-Eintrag dokumentiert den final validierten 10-Minuten-MVP-Run des
Founder-Dashboard-Video-Generate-Flows. Der Run dient ab jetzt als Referenzpunkt
fuer den aktuellen produktionsnahen MVP-Stand: YouTube-Quelle, Longform-Skript,
YouTube Packaging V1, echte ElevenLabs Voice, echte OpenAI-Bilder, Visual Prompt
Anatomy und finaler Render funktionieren ohne Placeholder und ohne Blocking
Reasons zusammen.

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
- `enable_youtube_packaging`: `true`

## Run-ID und Artefakte

- Run-ID: `video_gen_10m_1778951237649`
- Status: `production_ready`
- Finalvideo: `output/video_generate/video_gen_10m_1778951237649/final_video.mp4`
- Script: `output/video_generate/video_gen_10m_1778951237649/script.json`
- Voiceover Text: `output/video_generate/video_gen_10m_1778951237649/voiceover_text.txt`
- Voiceover Audio: `output/video_generate/video_gen_10m_1778951237649/voiceover.mp3`
- Scene Asset Pack: `output/video_generate/video_gen_10m_1778951237649/scene_asset_pack.json`
- Asset Manifest: `output/video_generate/video_gen_10m_1778951237649/generated_assets_video_gen_10m_1778951237649/asset_manifest.json`
- YouTube Packaging Manifest: `output/video_generate/video_gen_10m_1778951237649/youtube_packaging_manifest.json`

## Akzeptanzwerte

- `target_word_count`: `1280`
- Originalscript: `1162` Woerter
- Packaged Script: `1253` Woerter
- `voice_duration`: `608.95s`
- `final_video_duration`: `610.04s`
- `duration_ratio`: `1.017`
- `scene_count`: `13`
- echte OpenAI-Bilder: `13/13`
- Placeholder: `0`
- `visual_prompt_anatomy`: `13/13`
- Audio-Gap: `1.05s`
- `blocking_reasons`: keine

## Was funktioniert hat

- YouTube-Watch-URL wurde als YouTube-Quelle verarbeitet.
- Transcript wurde als Source-Material fuer ein eigenstaendiges deutsches Skript genutzt.
- Longform-Skript und ElevenLabs Voice trafen die 10-Minuten-Zieldauer sehr stabil.
- YouTube Packaging V1 war aktiv und fuegte Intro, CTA und Outro in den gesprochenen Text ein.
- OpenAI Image erzeugte fuer alle 13 Szenen echte Bilder.
- Visual Prompt Anatomy blieb in allen Szenen im Asset-Pfad vorhanden.
- Timeline wurde stabil auf die Voice-Dauer angepasst.
- `final_video.mp4` wurde erzeugt und der Lauf erreichte `production_ready`.

## Nicht blockierende Warnings

- `youtube_source_rewrite_used`
- `transcript_used_as_source_material`
- Hinweis, dass das Skript eine eigenstaendige deutschsprachige Story-Formulierung ist.
- `Target word count: 1280, Actual word count: 1162`
- `Generated using LLM mode`
- `LLM longform expansion repaired toward target length`
- `youtube_packaging_v1_applied`
- Wiederholte OpenAI-Image-Metadaten zu Modell, Provider, Transport und Groesse.
- `voiceover_full_script_used`
- `elevenlabs_voice_id_default_fallback`
- `timeline_fit_to_voice_applied`

Diese Warnings sind fuer den MVP-Referenzlauf akzeptabel. Es gab keine Blocking
Reasons und keine Placeholder.

## MVP-Status

Der Stand ist als 10-Minuten-MVP technisch validiert. Fuer die naechste
Produktionsphase sollte die Qualitaet des gesprochenen Textes verbessert werden:
Das Script kann weiterhin strukturiert bleiben, aber der Voiceover-Text soll
weniger nach Kapitelstruktur und mehr nach menschlicher Erzaehlung klingen.

# BA Plan: Human Voiceover Narration V1

## Ziel

Human Voiceover Narration V1 soll aus dem strukturierten `script.json` einen
natuerlichen, fluessigen gesprochenen Text ableiten, ohne die bestehenden
Script-, Provider- oder Render-Contracts zu brechen.

## Problem

Der aktuelle MVP-Run ist technisch stabil, aber der Voiceover-Text kann noch zu
stark nach Strukturvorlage klingen. Besonders stoerend fuer ein echtes
YouTube-Video sind Kapitelnummern, interne Strukturbegriffe und mechanische
Uebergaenge.

## V1-Scope

- `script.json` darf weiter Kapitel, Hook und strukturierte Felder enthalten.
- `voiceover_text.txt` soll eine geglaettete Narrationsfassung enthalten.
- Keine gesprochenen Kapitelmarker wie `Kapitel 1`, `Kapitel 2` oder `In diesem Kapitel`.
- Keine internen Strukturbegriffe wie `Hook`, `Outro`, `CTA`, `Abschnitt` oder `Kapitel`.
- Bessere Uebergaenge zwischen Szenen und Gedanken.
- CTA natuerlicher und kuerzer formulieren.
- Transcript-Material weiterhin paraphrasieren und einordnen, nicht 1:1 uebernehmen.
- Keine neuen Fakten erfinden.
- YouTube Packaging V1 bleibt optional und default aus.

## Nicht-Ziele

- Keine neue Voice-Provider-Integration.
- Kein Render-Refactor.
- Kein neues Dashboard-UI-Konzept.
- Kein Publishing- oder Upload-Flow.
- Keine Aenderung am bestehenden `GenerateScriptResponse`-Contract.
- Keine Entfernung der strukturierten Kapitel aus `script.json`.

## Empfohlene Architektur

- Einen kleinen deterministischen Voiceover-Narration-Layer zwischen Script-Finalisierung
  und Voice-Erzeugung einfuegen.
- Input: `script.json` plus optionales YouTube-Packaging-Ergebnis.
- Output: geglaetteter `voiceover_text`.
- Persistenz: zusaetzliches Manifest, z. B. `voiceover_narration_manifest.json`, mit
  `narration_applied`, entfernten Strukturmarkern, Wortzahl und Warnings.
- Existing Flow: Voice Provider liest weiterhin aus dem finalen Voiceover-Text, nicht
  direkt aus den Kapitelstrukturen.

## Minimaler Umsetzungsblock

1. Helper bauen, z. B. `app/voice/human_narration.py`.
2. Funktion `build_human_voiceover_text(script, packaged_script=None, language="de")`.
3. Kapitelueberschriften aus dem gesprochenen Text entfernen oder in weiche Uebergaenge umformen.
4. CTA/Outro natuerlicher glaetten, besonders bei Packaging V1.
5. Manifest schreiben und `run_summary` additiv ergaenzen.
6. Tests fuer Marker-Entfernung, Wortzahlerhalt, Packaging-Kombination und Default-Verhalten.

## Testplan

- Unit-Test: `Kapitel 1`, `Kapitel 2`, `In diesem Kapitel` kommen nicht in `voiceover_text` vor.
- Unit-Test: Strukturierte Kapitel bleiben in `script.json` erhalten.
- Unit-Test: Voiceover-Text enthaelt sinnvolle Uebergaenge statt Kapitelmarker.
- Integration-Test: `voiceover_text.txt` nutzt geglaettete Narration.
- Integration-Test: Packaging V1 Intro/CTA/Outro bleiben vorhanden, aber klingen natuerlich.
- Regression-Test: Default-Verhalten ohne aktivierten Narration-Layer bleibt stabil.
- Smoke-Test: ein 120s-Run vor erneutem 600s-Run.

## Agent-Empfehlung

Der naechste BA sollte klein bleiben: zuerst den Voiceover-Text vorbereiten und
testen, ohne Provider oder Render anzufassen. Danach erst einen 120s Real-Asset-
Run mit Human Narration aktivieren. Wenn der Text natuerlicher klingt und die
Duration Ratio stabil bleibt, folgt ein 600s-Validierungslauf gegen diesen MVP-
Referenzrun.
