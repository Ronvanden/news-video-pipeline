"""BA 29.4 — Patch human_preview_review_result into production_summary.json (file-based)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.production_assembly.human_preview_review import apply_human_preview_review_patch


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 29.4 — Human preview review gate (patch production summary)")
    ap.add_argument("--production-summary", required=True, type=Path)
    ap.add_argument("--review-status", required=True, choices=["pending", "approved", "rejected", "needs_changes"])
    ap.add_argument("--reviewer", default="", type=str)
    ap.add_argument("--review-notes", default="", type=str)
    ap.add_argument(
        "--approved-for-final-render",
        default=None,
        dest="approved_ff",
        choices=["true", "false"],
        help="Optional explicit flag; default derives from review-status",
    )
    ap.add_argument("--output", type=Path, default=None, help="Defaults to --production-summary")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run")
    args = ap.parse_args()

    src = args.production_summary.resolve()
    if not src.is_file():
        print(json.dumps({"ok": False, "error": "file_not_found"}, ensure_ascii=False, indent=2))
        return 2
    try:
        doc: Dict[str, Any] = json.loads(src.read_text(encoding="utf-8"))
        aff: Optional[bool] = None
        if args.approved_ff == "true":
            aff = True
        elif args.approved_ff == "false":
            aff = False
        patched = apply_human_preview_review_patch(
            doc,
            review_status=args.review_status,
            reviewer=args.reviewer,
            review_notes=args.review_notes,
            approved_for_final_render=aff,
        )
        out_path = args.output.resolve() if args.output else src
        if not args.dry_run:
            out_path.write_text(json.dumps(patched, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "human_preview_review_result": patched.get("human_preview_review_result")}, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
