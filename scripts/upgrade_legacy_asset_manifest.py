"""BA 29.1 — Upgrade legacy asset_manifest.json for modern production / gate paths (no live calls)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.visual_plan.asset_approval_gate import apply_production_asset_approval_to_manifest, evaluate_production_asset_approval
from app.visual_plan.legacy_manifest_upgrade import build_legacy_manifest_upgrade_summary, detect_legacy_asset_manifest_issues, upgrade_legacy_asset_manifest
from app.visual_plan.visual_costs import apply_visual_cost_to_asset, build_visual_cost_summary, get_default_visual_unit_costs


def load_asset_manifest(path: Path) -> Dict[str, Any]:
    p = path.resolve()
    if not p.is_file():
        raise FileNotFoundError(f"asset_manifest not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Dict[str, Any]) -> Path:
    p = path.resolve()
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


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


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 29.1 — Legacy asset_manifest upgrade (additive, dry-run capable)")
    ap.add_argument("--manifest", type=Path, required=True, help="Path to asset_manifest.json")
    ap.add_argument("--output", type=Path, required=True, help="Output path for upgraded JSON")
    ap.add_argument("--mode", type=str, default="smoke_safe", help="Upgrade mode (default: smoke_safe)")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run", help="Print summary JSON only; do not write output file.")
    ap.add_argument("--run-approval-gate", action="store_true", dest="run_approval_gate", help="After upgrade, run production asset approval gate.")
    ap.add_argument("--run-cost-tracking", action="store_true", dest="run_cost_tracking", help="After upgrade, apply heuristic visual cost fields + visual_cost_summary.")
    args = ap.parse_args()

    try:
        doc = load_asset_manifest(args.manifest)
        before = detect_legacy_asset_manifest_issues(doc)
        upgraded = upgrade_legacy_asset_manifest(doc, mode=args.mode)
        if bool(args.run_cost_tracking):
            upgraded, _cost_summ = run_cost_tracking(upgraded, unit_costs=get_default_visual_unit_costs())
        approval_res: Optional[Dict[str, Any]] = None
        if bool(args.run_approval_gate):
            approval_res = evaluate_production_asset_approval(upgraded)
            upgraded = apply_production_asset_approval_to_manifest(upgraded)

        summ = build_legacy_manifest_upgrade_summary(upgraded)
        summ["issues_before"] = before
        upgraded["legacy_manifest_upgrade_summary"] = summ

        out_payload = {
            "ok": True,
            "issues_before": before,
            "legacy_manifest_upgrade_summary": summ,
            "approval_result": approval_res,
        }
        if not bool(args.dry_run):
            write_json(args.output, upgraded)
        print(json.dumps(out_payload, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:500]}, ensure_ascii=False, indent=2))
        return 2

    if bool(args.run_approval_gate) and approval_res and approval_res.get("approval_status") not in ("approved", "needs_review"):
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
