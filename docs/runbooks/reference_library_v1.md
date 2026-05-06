## BA 27.1 — Visual Reference Library / Continuity Anchors (V1)

### Ziel
Eine **file-basierte Reference Library** verwaltet Referenzbilder und Kontinuitätsanker pro Story/Production Pack:
- gleiche Hauptfigur / Ort / Gegenstand
- konsistenter visueller Stil
- konsistenter Thumbnail-Look

V1 ist **nur Struktur + Manifest + Pack-Integration** – keine Provider-Uploads, keine Live-Calls.

### Provider Payload Stubs (BA 27.4)
Optional kann das Asset-Manifest zusätzlich provider-kompatible Payload-Stubs enthalten (ohne Live-Uploads):
- `reference_provider_payloads`
- `recommended_reference_provider_payload`
- `reference_provider_payload_status`

### Dateien / Module
- Helper: `app/visual_plan/reference_library.py`
- CLI: `scripts/build_reference_library_v1.py`

### Library Schema (`reference_library.json`)
- `reference_library_version`: `"ba27_1_v1"`
- `run_id`: optional
- `reference_assets[]`: Einträge mit u. a.:
  - `id`, `type`, `path`, `label`, `provider_hint`, `reference_strength`, `continuity_notes`, `safety_notes`
- `warnings[]`

### Asset additive Felder (z. B. in `asset_manifest.json`)
- `reference_asset_ids: list[str]`
- `continuity_strength: "low"|"medium"|"high"`
- `continuity_notes: string|null`
- `continuity_prompt_hint: string|null` (optional, z. B. per CLI Attach)
- `reference_provider_status: string|null` (V1: Status-Flag, keine Live-Uploads)
- `reference_policy_status: "none"|"attached"|"missing_reference"|"needs_review"`

### CLI Beispiel (PowerShell)
```text
python scripts/build_reference_library_v1.py ^
  --run-id run123 ^
  --output output/production_pack_run123/reference_library.json ^
  --reference id=main_character_ref_01,type=character,path=references/main_character.png,label="Main character",strength=high,notes="same face"
```

Optional Attach:
```text
python scripts/build_reference_library_v1.py ^
  --output output/production_pack_run123/reference_library.json ^
  --reference id=main_character_ref_01,type=character,path=references/main_character.png,strength=high ^
  --asset-manifest output/production_pack_run123/asset_manifest.json ^
  --attach scene_number=1,reference_id=main_character_ref_01,strength=high,prompt_hint="Keep same face",provider_status=prepared
```

