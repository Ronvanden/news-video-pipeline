# Local Preview Mini Fixture

Enthält:

- `mini_timeline_manifest.json` — minimales Timeline-Manifest (3 Szenen à 2 s, ohne Audio)
- `mini_narration.txt` — kurzer deutscher Demo-Text für Untertitel (Narration)
- `assets/` — drei kleine PNGs (`scene_001.png` … `scene_003.png`)

## Zweck

Mini-E2E / Operator-Smoke für **lokale Preview-Läufe** (BA 21.0), aufbauend auf **BA 20.9–20.13**.

Voraussetzung: Kommando **vom Repository-Root** ausführen, damit `assets_directory` in der JSON-Datei aufgelöst wird.

## Beispiel: Smoke (empfohlen)

### Bash / macOS / Linux

```bash
python scripts/run_local_preview_smoke.py \
  --timeline-manifest fixtures/local_preview_mini/mini_timeline_manifest.json \
  --narration-script fixtures/local_preview_mini/mini_narration.txt \
  --out-root output \
  --run-id mini_e2e \
  --motion-mode static \
  --subtitle-style typewriter
```

### Windows (PowerShell)

```powershell
python scripts/run_local_preview_smoke.py `
  --timeline-manifest fixtures/local_preview_mini/mini_timeline_manifest.json `
  --narration-script fixtures/local_preview_mini/mini_narration.txt `
  --out-root output `
  --run-id mini_e2e `
  --motion-mode static `
  --subtitle-style typewriter
```

## Shortcut (Komfort)

Vom Repository-Root:

```bash
python scripts/run_local_preview_mini_fixture.py
```

Optional: `--out-root`, `--run-id`, `--print-json` (werden an den Smoke-Lauf durchgereicht).

## Nach dem Lauf

- Es entsteht u. a. `output/local_preview_<run_id>/` (Standard `--run-id` im Shortcut: `mini_e2e`).
- **`OPEN_ME.md`** und **`local_preview_report.md`** im gleichen Ordner öffnen.
- Smoke-Ausgabe nennt **Preview**, **Report** und **Open-Me Datei**.

## Hinweise

- Ohne funktionierendes **ffmpeg** / fehlende Bilder: **Warnings** oder **FAIL** — siehe Smoke-Status und Founder Report.
- Keine **Secrets** / keine **`.env`** nötig für diesen Mini-Lauf (Narration-Modus, kein Audio-Transkript).
- Alte Preview-Ordner: `python scripts/cleanup_local_previews.py --out-root output` (Dry-Run).
