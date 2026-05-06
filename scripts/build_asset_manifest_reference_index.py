"""BA 27.7 — CLI: build asset_manifest_reference_index from asset_manifest.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from app.visual_plan.asset_manifest_reference_index import build_asset_manifest_reference_index


def _load_json(path: Path) -> Dict[str, Any]:
    p = path.resolve()
    if not p.is_file():
        raise FileNotFoundError(f"asset_manifest not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: Dict[str, Any]) -> Path:
    p = path.resolve()
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 27.7 — asset_manifest_reference_index builder")
    ap.add_argument("--manifest", type=Path, required=True, help="Path to asset_manifest.json")
    ap.add_argument("--output", type=Path, default=None, help="Output path (default: alongside manifest)")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run", help="Do not write files")
    args = ap.parse_args()

    try:
        man = _load_json(args.manifest)
        idx = build_asset_manifest_reference_index(man)
        out = args.output if args.output is not None else (args.manifest.resolve().parent / "asset_manifest_reference_index.json")
        if not bool(args.dry_run):
            _write_json(out, idx)
        print(json.dumps({"ok": True, "scenes_indexed": idx.get("summary", {}).get("scenes_indexed", 0), "output": str(out)}, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

