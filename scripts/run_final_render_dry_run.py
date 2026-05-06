"""BA 28.5 — CLI: final render dry-run from render_input_bundle.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from app.production_assembly.final_render_contract import build_final_render_dry_run_result


def _read_json(p: Path) -> Dict[str, Any]:
    pp = p.resolve()
    if not pp.is_file():
        raise FileNotFoundError(f"json not found: {pp}")
    return json.loads(pp.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 28.5 — final render dry-run (no ffmpeg call)")
    ap.add_argument("--bundle", required=True, type=Path)
    args = ap.parse_args()
    try:
        b = _read_json(args.bundle)
        res = build_final_render_dry_run_result(input_bundle=b, input_bundle_path=str(args.bundle.resolve()))
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("would_render") else 3
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

