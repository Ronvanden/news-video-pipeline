## BA 27.2 — Continuity-Aware Prompt Wiring (V1)

### Ziel
Reference-Daten werden **sichtbar** in Manifest/Pack vorbereitet – ohne Live-Reference-Uploads:
- welche Referenzen gelten (IDs, Pfade, Typen)
- wie stark Kontinuität sein soll
- welcher Prompt-Hinweis später an Provider gehen würde (Stub)
- ob Reference-Input „prepared“ ist

### Keine Live-Calls
V1 erzeugt **keine** Provider-spezifischen Uploads oder Reference-Calls. Es wird nur ein
`continuity_provider_payload_stub` geschrieben mit `no_live_upload=true`.

### CLI
```text
python scripts/run_continuity_prompt_wiring.py ^
  --manifest output/production_pack_run123/asset_manifest.json ^
  --reference-library output/production_pack_run123/reference_library.json ^
  --output output/production_pack_run123/asset_manifest_continuity.json
```

### Asset additive Felder (Auszug)
- `continuity_prompt_hint`
- `continuity_reference_paths[]`
- `continuity_reference_types[]`
- `continuity_provider_preparation_status`: `none|prepared|missing_reference|needs_review`
- `continuity_provider_payload_stub` (dict)
- `continuity_wiring_version: "ba27_2_v1"`

### Display (BA 27.3)
Die verdrahteten Felder werden zusätzlich operator-freundlich angezeigt:
- Prompt Cards: eine „Continuity“-Zeile pro Szene, wenn Felder vorhanden sind
- Production Pack README: Continuity-Counts (prepared/missing/needs_review/none) aus `continuity_wiring_summary`

