"""BA 26.7c — CLI: Provider Quality Compare Smoke (patch asset_manifest.json, no live calls)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from app.visual_plan.provider_quality_compare import (
    apply_provider_quality_compare,
    build_provider_quality_summary,
)


def _s(v: Any) -> str:
    return str(v or "").strip()


def load_asset_manifest(path: Path) -> Dict[str, Any]:
    p = path.resolve()
    if not p.is_file():
        raise FileNotFoundError(f"asset_manifest not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def run_compare(manifest: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = dict(manifest or {})
    assets = out.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("asset_manifest.assets empty or missing")
    patched: List[Dict[str, Any]] = []
    for a in assets:
        if isinstance(a, dict):
            patched.append(apply_provider_quality_compare(a))
        else:
            patched.append({"raw": str(a)})
    out["assets"] = patched
    out["provider_quality_compare_run"] = {"version": "ba26_7c_v1"}
    summary = build_provider_quality_summary(patched)
    return out, summary


def write_json(path: Path, obj: Dict[str, Any]) -> Path:
    p = path.resolve()
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 26.7c — Provider Quality Compare Smoke (patch asset_manifest)")
    ap.add_argument("--manifest", type=Path, required=True, help="Path to asset_manifest.json")
    ap.add_argument("--output", type=Path, default=None, help="Optional output path (default: overwrite manifest)")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run", help="Do not write any file.")
    args = ap.parse_args()

    try:
        doc = load_asset_manifest(args.manifest)
        patched, summary = run_compare(doc)
        out_path = args.output if args.output is not None else args.manifest
        if not bool(args.dry_run):
            write_json(out_path, patched)
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())

