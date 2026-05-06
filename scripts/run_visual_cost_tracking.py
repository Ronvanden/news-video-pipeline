"""BA 26.8c — CLI: Visual Cost Tracking (patch asset_manifest.json, heuristisch)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.visual_plan.visual_costs import (
    apply_visual_cost_to_asset,
    build_visual_cost_summary,
    get_default_visual_unit_costs,
)


def _s(v: Any) -> str:
    return str(v or "").strip()


def load_asset_manifest(path: Path) -> Dict[str, Any]:
    p = path.resolve()
    if not p.is_file():
        raise FileNotFoundError(f"asset_manifest not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _unit_costs_from_args(args) -> Dict[str, float]:
    base = dict(get_default_visual_unit_costs())
    if args.openai_images_cost is not None:
        base["openai_images"] = float(args.openai_images_cost)
    if args.leonardo_cost is not None:
        base["leonardo"] = float(args.leonardo_cost)
    if args.runway_cost is not None:
        base["runway"] = float(args.runway_cost)
    if args.seedance_cost is not None:
        base["seedance"] = float(args.seedance_cost)
    if args.render_layer_cost is not None:
        base["render_layer"] = float(args.render_layer_cost)
    return base


def run_cost_tracking(manifest: Dict[str, Any], *, unit_costs: Dict[str, float]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = dict(manifest or {})
    assets = out.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("asset_manifest.assets empty or missing")
    patched: List[Dict[str, Any]] = []
    for a in assets:
        if isinstance(a, dict):
            patched.append(apply_visual_cost_to_asset(a, unit_costs=unit_costs))
        else:
            patched.append({"raw": str(a)})
    out["assets"] = patched
    summary = build_visual_cost_summary(patched, unit_costs=unit_costs)
    out["visual_cost_summary"] = summary
    out["visual_cost_tracking_run"] = {"version": "ba26_8c_v1"}
    return out, summary


def write_json(path: Path, obj: Dict[str, Any]) -> Path:
    p = path.resolve()
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 26.8c — Visual Cost Tracking (asset_manifest.json)")
    ap.add_argument("--manifest", type=Path, required=True, help="Path to asset_manifest.json")
    ap.add_argument("--output", type=Path, default=None, help="Optional output path (default: overwrite manifest)")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run", help="Do not write any file.")
    ap.add_argument("--openai-images-cost", type=float, default=None, dest="openai_images_cost")
    ap.add_argument("--leonardo-cost", type=float, default=None, dest="leonardo_cost")
    ap.add_argument("--runway-cost", type=float, default=None, dest="runway_cost")
    ap.add_argument("--seedance-cost", type=float, default=None, dest="seedance_cost")
    ap.add_argument("--render-layer-cost", type=float, default=None, dest="render_layer_cost")
    args = ap.parse_args()

    try:
        doc = load_asset_manifest(args.manifest)
        uc = _unit_costs_from_args(args)
        patched, summary = run_cost_tracking(doc, unit_costs=uc)
        out_path = args.output if args.output is not None else args.manifest
        if not bool(args.dry_run):
            write_json(out_path, patched)
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps({"ok": True, "visual_cost_summary": summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

