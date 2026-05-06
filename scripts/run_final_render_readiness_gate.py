"""BA 29.5 — Final render readiness gate (technical + human preview review)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.production_assembly.final_render_readiness import build_final_render_readiness_result


def _read_json(p: Path) -> Dict[str, Any]:
    if not p.is_file():
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 29.5 — Final render readiness gate")
    ap.add_argument("--production-summary", required=True, type=Path)
    ap.add_argument("--final-render-dry-run", type=Path, default=None)
    ap.add_argument("--local-preview-render-result", type=Path, default=None)
    ap.add_argument("--output", type=Path, default=None, help="Write patched summary (default: --production-summary)")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run")
    args = ap.parse_args()
    rr: Dict[str, Any] = {}

    try:
        ps = _read_json(args.production_summary.resolve())
        dry_doc = _read_json(args.final_render_dry_run) if args.final_render_dry_run else None
        lp_doc: Optional[Dict[str, Any]] = None
        if args.local_preview_render_result:
            lp_doc = _read_json(args.local_preview_render_result)
        rr = build_final_render_readiness_result(
            production_summary=ps,
            final_render_dry_run=dry_doc,
            local_preview_render_result=lp_doc,
        )
        ps["final_render_readiness_result"] = rr
        out_path = args.output.resolve() if args.output else args.production_summary.resolve()
        if not args.dry_run:
            out_path.write_text(json.dumps(ps, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(rr, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2
    return 0 if rr.get("readiness_status") != "blocked" else 3


if __name__ == "__main__":
    raise SystemExit(main())
