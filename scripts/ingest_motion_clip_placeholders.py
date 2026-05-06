"""BA 28.2 — CLI: ingest motion clip placeholders (no video rendering)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

from app.production_connectors.motion_clip_ingest import ingest_motion_clip_results


def _read_json(p: Path) -> Dict[str, Any]:
    pp = p.resolve()
    if not pp.is_file():
        raise FileNotFoundError(f"json not found: {pp}")
    return json.loads(pp.read_text(encoding="utf-8"))


def _write_json(p: Path, obj: Dict[str, Any]) -> Path:
    pp = p.resolve()
    pp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return pp


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 28.2 — ingest motion clip placeholders (dry-run safe)")
    ap.add_argument("--motion-manifest", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true", dest="dry_run")
    args = ap.parse_args()

    try:
        mm = _read_json(args.motion_manifest)
        out = ingest_motion_clip_results(mm, output_dir=args.output_dir, dry_run=bool(args.dry_run))
        if not bool(args.dry_run):
            _write_json(args.output, out)
        print(json.dumps({"ok": True, "clips": len(out.get("clips") or []), "output": str(args.output.resolve())}, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

