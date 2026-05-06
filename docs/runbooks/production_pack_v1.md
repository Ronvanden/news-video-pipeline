## BA 27.0 — Real End-to-End Production Pack V1

### Ziel
Ein **kopierbarer Produktionsordner** bündelt die wichtigsten Artefakte, Reports und Entscheidungen und sagt klar:
- **ready_for_render**: `true/false`
- **warum** (blocking reasons / warnings)
- **welche Provider / Costs / Policy-Status** enthalten sind
- **welche Dateien** im Pack liegen

### Strikte Readiness-Regel
- `approval_status == "approved"` → `ready_for_render=true`, `render_readiness_status="ready"`
- `approval_status == "needs_review"` → `ready_for_render=false`, `render_readiness_status="needs_review"`
- `approval_status == "blocked"` → `ready_for_render=false`, `render_readiness_status="blocked"`
- fehlendes `production_asset_approval_result` → `ready_for_render=false` + Warning `approval_result_missing`

### Implementierung
- Helper: `app/real_video_build/production_pack.py`
- CLI: `scripts/build_production_pack_v1.py`
- Tests: `tests/test_ba270_production_pack_v1.py`

### Optional: Reference Library (BA 27.1)
Wenn vorhanden, wird `reference_library.json` in den Pack kopiert und in `production_summary.json` additiv referenziert:
- `reference_library_path`
- `reference_library_summary`

### Optional: Continuity Wiring (BA 27.2)
Wenn das `asset_manifest.json` Continuity-Wiring-Felder enthält (oder `continuity_wiring_summary`), wird dies in `production_summary.json` additiv gespiegelt:
- `continuity_wiring_summary`

### Display (BA 27.3)
Wenn `continuity_wiring_summary` vorhanden ist, enthält `README_PRODUCTION_PACK.md` zusätzlich einen kurzen Abschnitt **„Continuity“** mit Counts.

### Optional: Reference Provider Payloads (BA 27.4)
Wenn `asset_manifest.json` bereits `reference_provider_payload_summary` enthält, spiegelt `production_summary.json` dies additiv:
- `reference_provider_payload_summary`

### Optional: Reference Payload Mirror Summary (BA 27.6)
Wenn sowohl `asset_manifest.json` als auch `scene_asset_pack.json` vorhanden sind, ergänzt `production_summary.json` additiv:
- `reference_payload_mirror_summary` (best-effort Mirror per `scene_number`; Summary-only)

### Output-Struktur
`output/production_pack_<run_id>/`
- `script.json` (falls vorhanden)
- `scene_asset_pack.json` (falls vorhanden)
- `asset_manifest.json` (falls vorhanden)
- `production_asset_approval.json` (aus `asset_manifest.production_asset_approval_result`, falls vorhanden)
- `production_summary.json`
- `README_PRODUCTION_PACK.md`
- `reference_library.json` (optional, BA 27.1)
- `assets/`
  - `images/`, `clips/`, `voice/`, `overlays/`

### CLI Beispiel (PowerShell)
```text
python scripts/build_production_pack_v1.py ^
  --run-id test_001 ^
  --output-root output ^
  --asset-manifest output/generated_assets_test_001/asset_manifest.json ^
  --scene-asset-pack output/generated_assets_test_001/scene_asset_pack.json ^
  --script-json output/generated_assets_test_001/script.json
```

### Optional: Lokale Vorschau (BA 29.3)
Nach `scripts/render_local_preview_from_bundle.py` können Preview-Artefakte in den Pack gemischt werden:
- `--local-preview-render-result` → `local_preview_render_result.json`
- `--preview-video` → `local_preview.mp4`

`production_summary.json` enthält dann additiv u. a. `local_preview_status`, `local_preview_video_path`, `local_preview_render_result` (embedded, falls JSON geladen werden kann).

Siehe: `docs/runbooks/local_preview_render_v1.md`, `docs/runbooks/founder_production_flow_v1.md`.

### Render Input Bundle & Hydration (BA 29.2b)
`scripts/build_render_input_bundle_v1.py` nutzt `build_render_input_bundle` mit eingebettetem `asset_manifest`; Bild- und Clip-Pfade kommen aus der **Media-Path-Hydration** (Manifest-Ordner als Basis für relative Pfade). So kann die lokale Preview auch dann Standbilder finden, wenn im Bundle zuvor nur `asset_manifest_path` stand.

