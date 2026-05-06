## BA 27.4 — Reference-Aware Provider Adapter Preparation (V1)

### Ziel
Reference-/Continuity-Daten werden **provider-kompatibel als Payload-Stubs** vorbereitet, ohne Live-Uploads oder Provider-Calls:
- welche Referenzen vorhanden sind (IDs/Pfade)
- welcher Provider theoretisch unterstützt wird (Modus)
- welcher Payload-Stub entstehen würde
- Status: `prepared|missing_reference|needs_review|not_supported|none`

### Keine Live-Uploads
Alle Payloads enthalten `no_live_upload: true`. Es werden **keine** SDKs importiert und **keine** HTTP-Calls ausgeführt.

### Manifest Felder (additiv pro Asset)
- `reference_provider_payloads`:
  - `openai_images`, `leonardo`, `runway`, `seedance`
  - je Provider: `supported_mode`, `reference_paths`, `continuity_prompt_hint`, `status`, `warnings`, …
- `recommended_reference_provider_payload` (nach Priorität `provider_used` → `recommended_provider` → …)
- `reference_provider_payload_status`
- `reference_provider_payload_version: "ba27_4_v1"`

### OpenAI Images: provider-spezifisches Stub-Format (BA 27.5)
Innerhalb von `reference_provider_payloads.openai_images` wird additiv ein strukturiertes Unterformat ergänzt:
- `payload_format: "openai_images_reference_stub_v1"`
- `payload.reference_images[]`: aus `continuity_reference_paths`, je Eintrag `{ "input_type": "file_path", "path": "..." }`
- weiterhin strikt: `payload.no_live_upload: true`

### Dashboard Display (BA 27.5b)
Im Founder Dashboard erscheint (read-only) pro Szene/Prompt Card eine deutsche Operator-Zeile, wenn Reference Payload Felder vorhanden sind, z. B.:
- „Referenz-Provider: vorbereitet · Provider: OpenAI Images · Modus: Bildreferenz vorbereitet · Kein Live-Upload“

### Wiring / Spiegelung (BA 27.6)
Damit die Szene-Zeile stabil angezeigt werden kann, werden Reference-Felder additiv durch operator-nahe Artefakte gespiegelt, z. B.:
`asset_manifest → production_summary / optimize payload → prompt cards → dashboard`.

### CLI
```text
python scripts/run_reference_provider_payloads.py ^
  --manifest output/production_pack_run123/asset_manifest_continuity.json ^
  --output output/production_pack_run123/asset_manifest_reference_payloads.json
```

