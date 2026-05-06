"""BA 29.2c / BA 30.1 — Auto preview smoke + OPEN_PREVIEW_SMOKE.md operator report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.production_assembly.preview_smoke_auto import execute_preview_smoke_auto


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 29.2c/30.1 — Preview smoke auto-runner (no live providers)")
    ap.add_argument("--run-id", required=True, help="Unique run id, e.g. smoke_292c_auto_001")
    ap.add_argument("--output-root", type=Path, default=Path("output"), help="Pipeline output root (default: output)")
    ap.add_argument(
        "--asset-manifest",
        type=Path,
        default=None,
        help="Optional asset_manifest.json; default: newest usable under output-root",
    )
    ap.add_argument("--duration-target-seconds", type=int, default=45)
    ap.add_argument("--provider", type=str, default="auto")
    ap.add_argument(
        "--max-timeline-scenes",
        type=int,
        default=5,
        metavar="N",
        help="BA 32.0: max assets in motion_timeline_manifest (default 5).",
    )
    args = ap.parse_args()

    out_root = args.output_root.resolve()
    summary, code = execute_preview_smoke_auto(
        run_id=str(args.run_id),
        output_root=out_root,
        asset_manifest=args.asset_manifest.resolve() if args.asset_manifest else None,
        duration_target_seconds=int(args.duration_target_seconds),
        provider=str(args.provider),
        max_timeline_scenes=int(args.max_timeline_scenes),
    )
    summary_path = out_root / f"preview_smoke_auto_summary_{args.run_id}.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_obj: dict = {
        "ok": bool(summary.get("ok")),
        "exit_code": code,
        "summary_path": str(summary_path.resolve()),
        "failure_class": summary.get("failure_class"),
        "operator_blocking_reasons": summary.get("operator_blocking_reasons"),
    }
    rp = summary.get("open_preview_smoke_report_path")
    if rp:
        out_obj["open_preview_smoke_report_path"] = str(rp)
    print(json.dumps(out_obj, ensure_ascii=False, indent=2))
    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
