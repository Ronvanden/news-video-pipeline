# YouTube Source → Originalskript → Video (BA 32.58)

Manueller Smoke für den **YouTube-Source-Modus** über `POST /founder/dashboard/video/generate`.

## Produktidee

1. **Eingabe:** `source_youtube_url` (oder Alias `youtube_url`) — normale Watch-/Shorts-/youtu.be-URL.
2. **Transkript:** wird über die bestehende Transkript-Hilfe geladen (**kein** Zwang zur YouTube Data API).
3. **Skript:** daraus entsteht ein **neues** Skript (eigener Hook, Struktur, Formulierung). Das Transkript ist nur Quellenmaterial — **kein** 1:1-Reupload und keine lange wörtliche Übernahme.
4. **Video:** unverändert der bestehende Pfad (`script.json` → Szene → Assets → Voice → Render).

## Request (Minimal)

```json
{
  "source_youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "video_template": "documentary_story",
  "duration_target_seconds": 600,
  "max_scenes": 8,
  "voice_mode": "elevenlabs_or_safe_default",
  "allow_live_assets": true,
  "confirm_provider_costs": true
}
```

Optional: `rewrite_style`, weiteres `video_template` aus dem Katalog, `target_language` (Default `de`), `title` (Override des Skript-Titels). Für dokumentarische YouTube-Quellen ist **`documentary_story`** (API-Alias) bzw. kanonisch **`documentary`** der empfohlene Default — seit **BA 32.60** wird der Alias **ohne** „Unbekanntes video_template“-Warnung auf `documentary` normalisiert (kein stiller Fallback auf `generic`).

### BA 32.60 — `documentary_story`: Ton & Bild-Leitplanken

- **Wann:** Reale Ereignisse, Reportage, Doku-Erzählung aus YouTube-Transkript — **nicht** Mystery/Fantasy als Ziel-Ästhetik.
- **Skript:** dokumentarisch-spannend und emotional zugänglich, aber **nicht** tabloid-reißerisch (Story-Engine-Prompt-Addon + Kapitel-Strukturhinweise).
- **Bild-Prompts (Pipeline):** Schwerpunkt auf **realistic documentary photography**, **natural light**, **real-world locations**, **glaubwürdige** Alltagsmenschen und Umgebungen; **vermeidet** bewusst Fantasy-, Surreal-, Horror-Monster-, Gore- und „Fake-News“-Übertreibungs-Ästhetik. Zusätzliche **Negative-Segmente** (z. B. `no_fantasy`, `no_surreal`, `no_horror_monster`, …) werden im **Scene-Blueprint** (`/story-engine/scene-plan` → `negative_hints`) zusammengeführt; der **URL→MP4-Pfad** setzt die Leitplanken primär über den **positiven** Visual-Prompt in `script.json` / `scene_asset_pack`.
- **Erwartung:** Stills wirken **geerdeter und dokumentarischer** als bei generischem „dramatischem B-Roll“-Default.

**Priorität der Eingaben (wichtig):** `script_text` → YouTube-URL → `raw_text` → Artikel-`url`.

## Erwartete Response / `run_summary.json` (Auszug)

- `input_mode`: `youtube_source`
- `source_youtube_url`: kanonische Watch-URL
- `transcript_available`: `true` / `false`
- `generated_original_script`: `true` nach erfolgreichem Rewrite
- Warnungen u. a.: `youtube_source_rewrite_used`, `transcript_used_as_source_material`
- Bei fehlendem Transkript: `blocking_reasons` enthält `youtube_transcript_missing` (oder `youtube_url_invalid`) — **kein** Provider-Lauf, **kein** `url_extraction_empty_use_script_json`.

## Rechtliches / Redaktion

- Ergebnis ist ein **eigenes** Werk; trotzdem Quellen/Transkript-Hinweise in `warnings`/`sources` beachten.
- Kein automatischer Reupload fremder Videos; Fokus ist **neue Story** aus Recherchebasis.

## Wenn nur Provider getestet werden sollen

Wie in [real_image_provider_smoke.md](real_image_provider_smoke.md): **`raw_text`** oder fertiges **`script_text`** nutzen — ohne Abhängigkeit von YouTube-Untertiteln.

---

## BA 32.59 – Erster erfolgreicher YouTube Source → Original Video Smoke

### Kurze Zusammenfassung

Der erste erfolgreiche YouTube-Source-Smoke hat den eigentlichen Produktflow bestätigt: Aus einer YouTube-URL mit verfügbarem Transkript wurde ein neues eigenständiges deutsches Skript erzeugt, daraus fünf Gemini/Nano-Banana-Bildassets, eine echte ElevenLabs-Voice und ein finales MP4 mit Fit-to-Voice.

**BA 32.60:** `documentary_story` ist ein **API-Alias** für das kanonische Template **`documentary`** — Smokes mit `video_template: "documentary_story"` sollten **ohne** „Unbekanntes video_template“-Warnung laufen (Normalisierung auf `documentary`, kein Fallback auf `generic`).

### Referenzwerte (ohne Secrets, ohne lokale Pfade)

Chronik: dieser Lauf fand **vor** BA 32.60 statt; die Tabelle dokumentiert die **historischen** Ist-Werte inkl. Template-Fallback.

| Feld | Wert |
|------|------|
| `source_youtube_url` | `https://www.youtube.com/watch?v=bGZ4IlKohoA` |
| `input_mode` | `youtube_source` |
| `transcript_available` | `true` |
| `generated_original_script` | `true` |
| `rewrite_style` | `dramatic_documentary` |
| `video_template` (Anfrage) | `documentary_story` |
| `video_template` (effektiv, historisch BA 32.59) | `generic` (Fallback, **vor** BA 32.60) |
| `video_template` (Ziel ab BA 32.60) | `documentary_story` = effektiv, ohne Fallback-Warnung |
| `asset_manifest_file_count` | `5` |
| `real_asset_file_count` | `5` |
| `placeholder_asset_count` | `0` |
| `generation_mode` (Verteilung) | `gemini_image_live`: 5 Szenen |
| `asset_quality_gate.status` | `production_ready` |
| `voice_ready` | `true` |
| `voice_is_dummy` | `false` |
| `voice_duration_seconds` | ca. `118.38` |
| `timing_gap_status` | `ok` |
| `timing_gap_abs_seconds` | ca. `0.62` |
| `fit_strategy` | `fit_to_voice` |
| `timeline_duration_seconds` | ca. `119.0` |
| `final_video_duration_seconds` | ca. `119.04` |
| `render_used_placeholders` | `false` |
| `provider_blockers` | u. a. `live_motion_not_available` (kein angeforderter Motion-Lauf; kein produktiver Blocker) |

### Hinweise zum Referenzlauf (Einordnung)

- **Quelle vs. Skript:** Das YouTube-Transkript wurde als **Quellen-/Recherchematerial** genutzt. Das Skript ist eine **neue eigenständige deutschsprachige Story-Formulierung**, keine wörtliche Abschrift.
- **Gemini:** Es gab **eine** Antwort mit ungültigem Bild-Teil (`gemini_image_response_invalid` / `gemini_image_no_image_part`); **ein Retry** (`gemini_image_retry_1_after:gemini_image_response_invalid`) hat nachgezogen — anschließend fünf echte Bilder.
- **`video_template`:** Zum Zeitpunkt von BA 32.59 war weder `documentary` noch der Alias `documentary_story` im Kanon — daher Fallback auf **`generic`** und die Warnung „Unbekanntes video_template …“. **BA 32.60** führt **`documentary`** als kanonische ID und **`documentary_story`** als Alias (siehe `templates/template_registry.json` / `VIDEO_TEMPLATE_ALIASES`); neue Smokes können weiter `documentary_story` wie im Request-Beispiel senden.
- **Skriptlänge:** Warnungen wie Target-/Actual-Word-Count und **`LLM output shorter than target`** sind **Längen-/Qualitätshinweise**, kein Pipeline-Failure.
- **Fit-to-Voice:** `timeline_fit_to_voice_applied` und zugehörige BA-267-Hinweise sind **positiv** (Timeline an Voice-Dauer angepasst).
- **Motion:** `live_motion_not_available` spiegelt wider, dass **Runway/Motion** in diesem Lauf **nicht** angefordert war — kein Blocker für den statischen Bild+Voice-Pfad.

### Representative `warnings` (Auszug)

- `youtube_source_rewrite_used`
- `transcript_used_as_source_material`
- `Quelle: YouTube-Untertitel/Transkript; das Skript ist eine eigenständige deutschsprachige Story-Formulierung, keine wörtliche Abschrift.`
- `youtube_rewrite_style:dramatic_documentary`
- `Unbekanntes video_template 'documentary_story'; verwende 'generic'. Erlaubt: generic, history_deep_dive, mystery_explainer, true_crime.`
- `Target word count: 420, Actual word count: 315`
- `Generated using LLM mode`
- `LLM output shorter than target`
- `gemini_image_model:gemini-2.5-flash-image`
- `gemini_image_provider:gemini_image`
- `gemini_image_transport:rest`
- `gemini_image_response_invalid`
- `gemini_image_no_image_part`
- `gemini_image_retry_1_after:gemini_image_response_invalid`
- `ba267_video_fitted_to_voice:voice_audio~118.38s_padding=0.75s_target_total=119s_scenes=5`
- `timeline_fit_to_voice_applied`

### Was dieser Lauf beweist

- YouTube-Transkript-Intake funktioniert (mit verfügbaren Untertiteln).
- Aus dem Transkript wird ein **neues originales deutsches Skript** erzeugt; die Pipeline zielt **nicht** auf eine bloße 1:1-Abschrift.
- **Gemini / Nano Banana** erzeugt echte Bildassets im Live-Modus.
- **Retry** bei Gemini-„invalid response“ funktioniert in der Praxis.
- **ElevenLabs** erzeugt echte Voice (nicht Dummy).
- **Fit-to-Voice** funktioniert; finales MP4 schließt nahtlos an Voice/Timeline an.
- **`final_video.mp4`** wird erzeugt — der **End-to-End-Produktflow** ist technisch funktionsfähig.

### Was dieser Lauf noch nicht beweist

- Videos **ohne** (ausreichendes) YouTube-Transkript / Untertitel.
- **Audio-Transkription** direkt aus dem YouTube-Audio (ohne vorhandene Untertitel).
- **Visuelle Analyse** des Originalvideos.
- **Motion- / Runway-Clips** in der Timeline.
- **Publishing** oder Plattform-Upload.
- **Finale YouTube-Upload-Qualität** (Metadaten, Thumbnail-Politik, Content-ID-Risiko usw.).
- **Langform- / 12-Minuten-Produktion** speziell aus YouTube-Quelle (nur ein Referenzlauf mit gegebener Dauer/Szenenzahl).

### BA 32.60 – Documentary Story Template Alignment (erledigt)

- Kanonisch ist **`documentary`** in `STORY_TEMPLATE_IDS` und im öffentlichen Template-Katalog (`GET /story-engine/templates`); **`documentary_story`** ist ein **Eingabe-Alias** (ohne Extra-Warnung) gemäß `VIDEO_TEMPLATE_ALIASES` / `templates/template_registry.json` → `template_aliases`.
- Die Founder-Template-Registry (Python) listet **`documentary`** als „Documentary Story“.
- YouTube-Source-Smokes können weiter **`video_template: "documentary_story"`** senden; intern wird **`documentary`** verwendet — kein Fallback auf `generic` bei diesem Alias.
- Unbekannte Template-IDs verhalten sich weiter wie bisher: Warnung + Fallback auf `generic` (explizit in der Warnung genannt).
