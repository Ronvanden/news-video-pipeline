"""BA 26.9c — CLI: Production Asset Approval Gate (asset_manifest.json)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Tuple

from app.visual_plan.asset_approval_gate import (
    apply_production_asset_approval_to_manifest,
    evaluate_production_asset_approval,
)


def load_asset_manifest(path: Path) -> Dict[str, Any]:
    p = path.resolve()
    if not p.is_file():
        raise FileNotFoundError(f"asset_manifest not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Dict[str, Any]) -> Path:
    p = path.resolve()
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 26.9c — Production Asset Approval Gate (asset_manifest.json)")
    ap.add_argument("--manifest", type=Path, required=True, help="Path to asset_manifest.json")
    ap.add_argument("--output", type=Path, default=None, help="Optional output path (default: overwrite manifest)")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run", help="Do not write any file.")
    args = ap.parse_args()

    try:
        doc = load_asset_manifest(args.manifest)
        res = evaluate_production_asset_approval(doc)
        out_doc = apply_production_asset_approval_to_manifest(doc)
        out_path = args.output if args.output is not None else args.manifest
        if not bool(args.dry_run):
            write_json(out_path, out_doc)
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(res, ensure_ascii=False, indent=2))
    # Exit code: 0 approved/needs_review, 3 blocked
    return 0 if res.get("approval_status") in ("approved", "needs_review") else 3


if __name__ == "__main__":
    raise SystemExit(main())

