# Prompt Patterns V1

Dieses Dokument enthält wiederverwendbare Baupläne für zukünftige BA-Prompts. Es ergänzt `docs/PROMPT_OPERATING_SYSTEM.md`.

## Standard BA Module Contract

Verwende **`PPOS_STANDARD_BA`**, wenn eine einzelne Bauphase ein klar abgegrenztes Modul ergänzt.

Pflichtstruktur:

- **Modul:** Zielpfad und fachliche Verantwortung.
- **Kernfunktion:** Eine zentrale Funktion mit stabilem Namen, z. B. `build_*`, `evaluate_*`, `execute_*`.
- **Schema:** Pydantic-Modelle oder bestehende Schemas, Felder, Statuswerte, Defaults.
- **Integration:** Wo der Schritt in bestehende Pipeline/Route/Service-Schicht eingehängt wird.
- **Tests:** Neue Testdatei oder Erweiterung bestehender Tests; Pflichtfälle inklusive Regression.
- **Doku:** `PIPELINE_PLAN.md` und ggf. README/Runbook/Pattern.
- **Checks:** `python -m compileall app` und `python -m pytest`.

## Full Suite Contract

Verwende **`PPOS_FULL_SUITE`**, wenn mehrere BAs zusammen eine Schicht bilden.

Pflichtstruktur:

- mehrere Module mit eindeutigen BA-Nummern,
- gemeinsamer Pipeline-Flow in definierter Reihenfolge,
- additive API-/Plan-Erweiterung nur wenn explizit Teil der Produktlogik,
- zentrale Suite-Funktion, z. B. `apply_*_suite(plan)`,
- Test-Suite pro BA plus ein API-Feld-Test,
- `PIPELINE_PLAN.md`-Abschnitt mit Unterschied zur Vorgängerschicht und Anschluss zur Folgeschicht.

Suite-Flow-Template:

```text
previous_suite_result
→ ba_x0_result
→ ba_x1_result
→ ba_x2_result
→ final_suite_summary_result
```

## Connector Pattern (BA 10+)

Verwende **`PPOS_CONNECTOR`** für Provider-, API-, Safety- und Execution-Schichten.

Regeln:

- Dry-Run ist Default.
- Live nur mit explizitem Flag und Safety Contract.
- Secrets nie lesen, außer ein BA fordert Runtime-Presence-Checks ausdrücklich.
- Secret-Werte nie loggen oder persistieren.
- Provider einzeln aktivierbar und blockierbar.
- Fehler werden strukturiert als Status, Warnings, Blocker oder Recovery-Hinweise zurückgegeben.
- Keine Firestore-Writes, sofern nicht ausdrücklich verlangt.

Typische Module:

- `*_connector.py`
- `*_safety.py`
- `*_policy.py`
- `*_guard.py`
- `*_queue.py`
- `*_recovery.py`

## Assembly Pattern (BA 12+)

Verwende **`PPOS_ASSEMBLY`** für die Zusammenführung vorhandener Assets in Produktionspakete.

Regeln:

- Keine Provider-Ausführung.
- Keine Downloads/Writes als Pflicht.
- Bestehende Live-/Mock-/Persistence-Ergebnisse lesen.
- Manifest zuerst, danach Gruppierung, Timeline, Alignment, Render-Package, Bundle, Human Review.
- Fehlende Assets führen zu `partial` oder `blocked`, nicht zu stillen Erfolgen.

Standard-Flow:

```text
live_provider_suite
→ master_asset_manifest_result
→ multi_asset_assembly_result
→ final_timeline_result
→ voice_scene_alignment_result
→ render_instruction_package_result
→ downloadable_production_bundle_result
→ human_final_review_package_result
```

## Publishing Pattern (BA 13+ vorbereitet)

Verwende **`PPOS_PUBLISHING`** für Publishing-Preparation, nicht für echte Veröffentlichung.

Regeln:

- Kein Auto-Publishing.
- Kein YouTube Upload ohne ausdrückliche Freigabe.
- Metadatenpakete statt Upload-Seiteneffekte.
- Scheduling-Readiness statt Scheduler-Deploy.
- Human Gate vor jedem externen Veröffentlichungsschritt.
- Title, Description, Tags, Thumbnail, Compliance, Cost und Safety getrennt bewerten.

Mögliche BA-Module:

- metadata package,
- title/description quality,
- thumbnail publishing readiness,
- schedule contract,
- publishing readiness gate,
- human publish approval package.

## Pattern-Auswahl

- Einzelnes Modul ohne Pipeline-Kette: **`PPOS_STANDARD_BA`**
- Mehrere zusammenhängende BAs: **`PPOS_FULL_SUITE`**
- Provider/API/Safety: **`PPOS_CONNECTOR`**
- Asset-/Render-Paketstruktur: **`PPOS_ASSEMBLY`**
- Upload-/Veröffentlichungsvorbereitung: **`PPOS_PUBLISHING`**
