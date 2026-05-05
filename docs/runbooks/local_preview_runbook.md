# Runbook — Local Preview (BA 21.6 / BA 21.7)

Bedienungsanleitung für **lokalen Preview-Start**, **Ergebnisprüfung**, **typische Reparaturen** und **Aufräumen** alter Preview-Ordner. Technische BAs: **BA 20.9–20.13** (Pipeline, Report, OPEN_ME, Cleanup), **BA 21.0–21.5** (Mini-Fixture, FFmpeg-Preflight, Artefakt-Pfade, Quality-/Sync-/Warning-/Founder-Schichten), **BA 21.7** (stabiles JSON-Contract für Dashboard/Integration). Kanonischer Gesamtplan: [PIPELINE_PLAN.md](../../PIPELINE_PLAN.md).

---

## 1. Wann dieses Runbook nutzen

- Du willst **ohne Cloud** prüfen, ob Timeline + Narration + Render + Untertitel-Burn-in zu einem **Preview-Video** und **Operator-Artefakten** führen.
- Du brauchst eine **reproduzierbare Smoke-Basis** (Mini-Fixture) oder einen Lauf mit **eigenen Manifest-/Skript-Pfaden**.
- Du willst **alte `local_preview_*`-Ordner** sicher listen oder löschen (**BA 20.13**).

**Nicht-Ziele:** Keine Secrets in Befehlen oder Logs; kein Publishing; der Mini-Lauf braucht **keine** `.env` / API-Keys (Narration-Modus).

---

## 2. Voraussetzungen

| Voraussetzung | Hinweis |
|---------------|---------|
| **Arbeitsverzeichnis** | Alle Beispielbefehle **vom Repository-Root**, damit relative Pfade in Manifesten (z. B. `assets_directory`) stimmen. |
| **Python** | Wie im restlichen Repo (siehe [README.md](../../README.md)); Skripte unter `scripts/`. |
| **ffmpeg / ffprobe** | Für **echten** Render und Burn-in im PATH. Der Shortcut **`run_local_preview_mini_fixture.py`** führt standardmäßig einen **Preflight** aus (**BA 21.0d**); bei Fehlen: klare Meldung, Exit **1**, optional **`--skip-preflight`** nur bewusst zum Umgehen. |
| **Windows** | PowerShell-Zeilenumbruch mit `` ` `` (Backtick) fortsetzen, wie in [fixtures/local_preview_mini/README.md](../../fixtures/local_preview_mini/README.md). |

---

## 3. Preview starten

### 3.1 Empfohlen: Mini-Fixture (Smoke)

Ein Befehl, feste Pfade unter `fixtures/local_preview_mini/`:

```bash
python scripts/run_local_preview_mini_fixture.py
```

Optional: **`--out-root`**, **`--run-id`** (Default `mini_e2e`), **`--print-json`**, **`--motion-mode`**, **`--subtitle-style`**, **`--skip-preflight`**.

Zusätzliche Smoke-Flags (z. B. **`--force-burn`**) werden an `run_local_preview_smoke` durchgereicht (über **`parse_known_args`** oder alles nach einem freistehenden **`--`**):

```bash
python scripts/run_local_preview_mini_fixture.py --force-burn
python scripts/run_local_preview_mini_fixture.py -- --force-burn
```

### 3.2 Smoke mit eigenen Dateien

Gleiche Oberfläche wie die Pipeline, aber **kompakte Zusammenfassung** und Smoke-Exit-Codes (**BA 20.11**):

```bash
python scripts/run_local_preview_smoke.py \
  --timeline-manifest PFAD/zum/timeline_manifest.json \
  --narration-script PFAD/zum/narration.txt \
  --out-root output \
  --run-id mein_lauf \
  --motion-mode static \
  --subtitle-style typewriter
```

Wichtige Optionen: **`--subtitle-mode`**, **`--subtitle-source`** (`narration` \| `audio`), **`--audio-path`**, **`--force-burn`**, **`--print-json`**.

### 3.3 Volle Pipeline nur JSON (Operator/Debug)

**`run_local_preview_pipeline.py`**: stdout ist das **Pipeline-JSON**; bei Fehler typischerweise Exit **3** (unabhängig vom späteren PASS/WARNING/FAIL-**Verdict**). Optional **`--print-report`** für den Markdown-Founder-Report auf stdout.

---

## 4. Ergebnis prüfen

### 4.1 Ausgabeordner

Nach erfolgreichem Durchlauf (abhängig von **`--out-root`** und **`--run-id`**):

- **`output/local_preview_<run_id>/`** (bzw. `<out-root>/local_preview_<run_id>/`) — zentrales Paket (**BA 21.0c**): u. a. **`preview_with_subtitles.mp4`**, **`OPEN_ME.md`**, **`local_preview_report.md`**.

Zuerst **`OPEN_ME.md`** öffnen: kuratierte Pfade und Hinweise. Tiefer geht **`local_preview_report.md`** (Founder Report, **BA 20.10** + Quality-Schichten).

### 4.2 Smoke-Zeilen (Was bedeuten sie?)

Die Smoke-Ausgabe enthält u. a.:

- **Status:** PASS / WARNING / FAIL (**Verdict**, aus `ok`, Blocking und sanitisierten Gründen).
- **Quality:** / **Subtitle Quality:** / **Sync Guard:** — Checklisten- bzw. Guard-Status (**BA 21.1–21.3**).
- **Warning level:** — Klassifikation INFO / CHECK / WARNING / BLOCKING (**BA 21.4**).
- **Founder decision:** — BLOCK / REVIEW_REQUIRED / GO_PREVIEW (**BA 21.5**).
- **Preview öffnen** / **Report öffnen** / **Open-Me Datei** — konkrete Pfade.
- **Nächster Schritt** — kurzer Handlungsvorschlag aus dem Verdict.

Mit **`--print-json`** folgt das vollständige Pipeline-Ergebnis (Steps, `paths`, `warnings`, `blocking_reasons`, strukturierte Quality-Felder).

### 4.3 Exit-Codes (Smoke)

| Code | Bedeutung |
|------|-----------|
| **0** | PASS |
| **2** | WARNING (Lauf technisch möglich, aber Qualität/Signale prüfen) |
| **1** | FAIL |

Hinweis: **`run_local_preview_pipeline.py`** allein nutzt bei **`ok: false`** typischerweise Exit **3** — für CI/Operatoren ist die Smoke-CLI die klarere PASS/WARNING/FAIL-Semantik.

### 4.4 JSON-Ergebniscontract (BA 21.7)

Jedes vollständige Ergebnis von **`run_local_preview_pipeline`** (nach **`finalize_local_preview_operator_artifacts`**) enthält stabil:

- **`result_contract`**: `id` = **`local_preview_result_v1`**, **`schema_version`** = **1** (Konstanten im Modul **`scripts/run_local_preview_pipeline.py`**).
- **`verdict`**: **`PASS`** \| **`WARNING`** \| **`FAIL`** — identisch zu **`founder_quality_decision.signals.verdict`** bei normalem Lauf.
- **`paths`**: alle Schlüssel aus **`LOCAL_PREVIEW_RESULT_PATH_KEYS`** (fehlende Werte als leerer String **`""`**).
- **`steps`**: immer die Keys **`build_subtitles`**, **`render_clean`**, **`burnin_preview`** (Wert **`null`** / **`None`** im JSON, wenn der Schritt nicht lief).
- Zusätzlich die bestehenden Objekte **`quality_checklist`**, **`subtitle_quality_check`**, **`sync_guard`**, **`warning_classification`**, **`founder_quality_decision`**.

Programmatische Nachbearbeitung nur in Ausnahmefällen: **`apply_local_preview_result_contract(result)`** (gleiches Modul).

**Dashboard (BA 22.0–23.0):** Mit laufender FastAPI-App liefert **GET `/founder/dashboard/local-preview/panel`** eine read-only-Übersicht der Ordner **`local_preview_*`** unter dem Repository-**`output/`** (Artefakt-Flags, keine Dateiinhalte). **BA 22.1** ergänzt **Status-Karten** aus **`local_preview_result.json`**, falls vorhanden; ohne diese Datei (ältere Läufe) zeigen die Karten **UNKNOWN**. **BA 22.2** erlaubt das Öffnen/Einbetten von Preview, Report, OPEN_ME und JSON nur über **GET `/founder/dashboard/local-preview/file/{run_id}/{filename}`** (Whitelist, kein Zugriff außerhalb des jeweiligen **`local_preview_*`**-Ordners). **BA 22.3** ergänzt im Dashboard einen Operator-Button „Preview erstellen“, der den festen Mini-Fixture-Run startet (mit Preflight) und danach das Panel aktualisiert. **BA 22.4** zeigt eine Kostenkarte (Cost/Production Estimate), sofern im `local_preview_result.json` Kostendaten vorhanden sind; sonst Status **UNKNOWN** mit Hinweis. **BA 22.5** ergänzt ein Human-Approval-Gate (Approve/Revoke) für lokale Runs; es löst **keinen** Final Render aus. **BA 22.6** zeigt eine Final-Render-Readiness (ready/locked/blocked/unknown) und einen vorbereiteten Button; die tatsächliche Final-Render-Ausführung folgt später. **BA 23.0** ordnet den Local-Preview-Bereich im Dashboard in Founder Summary, Actions, Diagnostics, Approval, Final Render und Recent Runs. Die Seite **GET `/founder/dashboard`** lädt das Panel per `fetch` im Browser; der **CLI-Flow** bleibt unverändert nutzbar.

---

## 5. Typische Probleme und Reparatur

| Symptom | Maßnahme |
|---------|----------|
| Preflight meldet fehlendes **ffmpeg** / **ffprobe** | Installation (Windows-Hinweis in der Tool-Ausgabe, u. a. **winget**); danach neues Terminal/PATH prüfen. |
| Pfade zu Assets / Manifest **nicht gefunden** | Lauf **vom Repo-Root**; Manifest-Pfade und `assets_directory` prüfen. |
| Wiederholter Lauf, alte Preview-Datei | **BA 21.0e:** bestehendes Preview blockiert nicht; ggf. Warnung. Für harten Neu-Burn: **`--force-burn`**. |
| Blocking / FAIL wegen Render oder Burn-in | Founder Report und JSON-**`blocking_reasons`** / **`steps`** lesen; Eingaben (Timeline, Narration, optional Audio) verifizieren. |
| Nur Struktur testen ohne FFmpeg | Mini-Fixture mit **`--skip-preflight`** — sinnvoll nur für bewusstes Debug; ohne funktionierendes FFmpeg kein valides Video. |

---

## 6. Cleanup (Retention)

Skript: **`scripts/cleanup_local_previews.py`** (**BA 20.13**).

- **Standard:** Dry-Run — listet nur, was bei **`--apply`** gelöscht würde.
- **`--out-root`**: Wurzel, unter der nur **direkte** Unterordner **`local_preview_*`** berücksichtigt werden (keine Symlinks, keine tieferen Ordner).
- **`--keep-latest`**: wie viele neueste Runs behalten (Default **5**).
- **`--max-delete`**: Obergrenze pro Lauf (Default **20**).
- **`--apply`**: Löschung ausführen.
- **`--print-json`**: strukturierte Ausgabe (ohne Ballastfeld **`discovered_paths`**).

Beispiel Dry-Run:

```bash
python scripts/cleanup_local_previews.py --out-root output
```

Beispiel mit Löschung:

```bash
python scripts/cleanup_local_previews.py --out-root output --apply
```

---

## 7. Verwandte Dokumente

- [fixtures/local_preview_mini/README.md](../../fixtures/local_preview_mini/README.md) — Mini-Fixture, Bash- und PowerShell-Beispiele.
- [PIPELINE_PLAN.md](../../PIPELINE_PLAN.md) — Abschnitte **BA 20.9–20.13**, **BA 21**, **BA 21.4–22.x**.
- [OPERATOR_RUNBOOK.md](../../OPERATOR_RUNBOOK.md) — Gesamtbetrieb (nicht nur Preview).

Governance: Keine Geheimnisse in Runbooks; bei Vorfällen [ISSUES_LOG.md](../../ISSUES_LOG.md).
