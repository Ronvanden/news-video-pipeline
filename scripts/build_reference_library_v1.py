"""BA 27.1 — Build Reference Library V1 (file-based, no provider calls).

Minimal usage (PowerShell):
python scripts/build_reference_library_v1.py ^
  --run-id run123 ^
  --output output/production_pack_run123/reference_library.json ^
  --reference id=main_character_ref_01,type=character,path=references/main_character.png,label="Main character",strength=high,notes="same face"

Optional attach to asset_manifest:
  --asset-manifest output/production_pack_run123/asset_manifest.json ^
  --attach scene_number=1,reference_id=main_character_ref_01,strength=high
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.visual_plan.reference_library import (
    attach_reference_ids_to_asset,
    build_reference_library,
    build_reference_library_summary,
    read_reference_library,
    write_reference_library,
)


def _parse_kv_csv(s: str) -> Dict[str, str]:
    """
    Parses: k=v,k2=v2 (values may contain spaces if quoted by shell; argparse keeps it as one string).
    We keep it simple: split on comma, then first '='.
    """
    out: Dict[str, str] = {}
    raw = (s or "").strip()
    if not raw:
        return out
    for part in raw.split(","):
        p = part.strip()
        if not p:
            continue
        if "=" not in p:
            out[p] = ""
            continue
        k, v = p.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _find_asset_index(manifest: Dict[str, Any], scene_number: int) -> int:
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        return -1
    for i, a in enumerate(assets):
        if isinstance(a, dict) and int(a.get("scene_number", 0) or 0) == int(scene_number):
            return i
    return -1


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 27.1 — Build Reference Library V1 (no live calls).")
    ap.add_argument("--run-id", default=None, dest="run_id")
    ap.add_argument("--output", required=True, type=Path, dest="output")
    ap.add_argument("--reference", action="append", default=[], dest="references", help="Reference asset kv list.")

    ap.add_argument("--asset-manifest", default=None, type=Path, dest="asset_manifest")
    ap.add_argument("--attach", action="append", default=[], dest="attach", help="Attach kv list: scene_number=1,reference_id=...,strength=high")
    args = ap.parse_args()

    warnings: List[str] = []
    ref_assets: List[Dict[str, Any]] = []
    for r in args.references or []:
        kv = _parse_kv_csv(r)
        if not kv:
            continue
        ref_assets.append(
            {
                "id": kv.get("id") or "",
                "type": kv.get("type") or "other",
                "path": kv.get("path") or "",
                "label": kv.get("label") or None,
                "usage": kv.get("usage") or None,
                "reference_strength": kv.get("strength") or kv.get("reference_strength") or "medium",
                "continuity_notes": kv.get("notes") or kv.get("continuity_notes") or None,
                "provider_hint": kv.get("provider_hint") or None,
                "safety_notes": [],
            }
        )

    lib = build_reference_library(ref_assets, run_id=args.run_id)
    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_reference_library(out_path, lib)

    attached_assets_count = 0
    if args.asset_manifest and args.attach:
        man_path = Path(args.asset_manifest).resolve()
        try:
            man = _load_json(man_path)
        except Exception as exc:
            print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)[:200]}, ensure_ascii=False, indent=2))
            return 2
        assets = man.get("assets")
        if not isinstance(assets, list):
            assets = []
            man["assets"] = assets

        # attach instructions
        for a in args.attach or []:
            kv = _parse_kv_csv(a)
            try:
                sn = int(kv.get("scene_number") or "0")
            except ValueError:
                warnings.append("attach_invalid_scene_number")
                continue
            rid = (kv.get("reference_id") or "").strip()
            strength = (kv.get("strength") or "medium").strip()
            prompt_hint = (kv.get("prompt_hint") or "").strip()
            provider_status = (kv.get("provider_status") or "").strip()
            if sn <= 0 or not rid:
                warnings.append("attach_missing_scene_or_reference_id")
                continue
            idx = _find_asset_index(man, sn)
            if idx < 0:
                warnings.append(f"attach_scene_not_found:{sn}")
                continue
            patched = attach_reference_ids_to_asset(
                assets[idx],
                [rid],
                continuity_strength=strength,
                continuity_prompt_hint=prompt_hint or None,
                reference_provider_status=provider_status or None,
            )
            assets[idx] = patched
            attached_assets_count += 1

        # Update policy statuses best-effort by re-building summary with assets (no mutation beyond attach)
        _ = build_reference_library_summary(lib, assets=[x for x in assets if isinstance(x, dict)])

        try:
            _write_json(man_path, man)
        except Exception as exc:
            warnings.append(f"asset_manifest_write_failed:{type(exc).__name__}")

    stdout = {
        "ok": True,
        "reference_count": len(lib.get("reference_assets") or []),
        "attached_assets_count": int(attached_assets_count),
        "output": str(out_path),
        "warnings": list(dict.fromkeys((lib.get("warnings") or []) + warnings)),
    }
    print(json.dumps(stdout, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

