"""BA 27.2 — CLI: Continuity Prompt Wiring (patch asset_manifest.json, no live calls)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from app.visual_plan.continuity_prompt import apply_continuity_prompt_wiring_to_manifest
from app.visual_plan.reference_library import read_reference_library


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
    ap = argparse.ArgumentParser(description="BA 27.2 — Continuity Prompt Wiring (asset_manifest.json)")
    ap.add_argument("--manifest", type=Path, required=True, help="Path to asset_manifest.json")
    ap.add_argument("--reference-library", type=Path, default=None, help="Optional reference_library.json")
    ap.add_argument("--output", type=Path, default=None, help="Optional output path (default: overwrite manifest)")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run", help="Do not write any file.")
    args = ap.parse_args()

    try:
        man = load_asset_manifest(args.manifest)
        ref = read_reference_library(args.reference_library) if args.reference_library else None
        patched = apply_continuity_prompt_wiring_to_manifest(man, reference_library=ref)
        out_path = args.output if args.output is not None else args.manifest
        if not bool(args.dry_run):
            write_json(out_path, patched)
        summ = patched.get("continuity_wiring_summary") if isinstance(patched.get("continuity_wiring_summary"), dict) else {}
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2

    stdout = {
        "ok": True,
        "assets_checked": int(summ.get("assets_checked") or 0),
        "prepared_count": int(summ.get("prepared_count") or 0),
        "missing_reference_count": int(summ.get("missing_reference_count") or 0),
        "needs_review_count": int(summ.get("needs_review_count") or 0),
        "none_count": int(summ.get("none_count") or 0),
        "warnings": summ.get("warnings") or [],
    }
    print(json.dumps(stdout, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

