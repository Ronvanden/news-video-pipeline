"""BA 27.9 — CLI: build visual_production_preflight_result from asset_manifest + optional production_summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

from app.visual_plan.visual_production_preflight import build_visual_production_preflight_result


def _read_json(path: Optional[Path]) -> Optional[Dict[str, Any]]:
    if path is None:
        return None
    p = path.resolve()
    if not p.is_file():
        raise FileNotFoundError(f"json not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 27.9 — visual production preflight (read-only)")
    ap.add_argument("--asset-manifest", type=Path, required=True, help="Path to asset_manifest.json")
    ap.add_argument("--production-summary", type=Path, default=None, help="Optional production_summary.json")
    args = ap.parse_args()

    try:
        man = _read_json(args.asset_manifest) or {}
        ps = _read_json(args.production_summary)
        res = build_visual_production_preflight_result(asset_manifest=man, production_summary=ps)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("preflight_status") != "blocked" else 3
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

