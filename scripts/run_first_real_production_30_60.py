"""BA 29.0 — Controlled 30–60s production run (no live provider calls).

Builds/links: motion_manifest (dry-run), production pack, preflight, timeline, render bundle, final render dry-run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.production_assembly.controlled_production_run import run_controlled_production_run


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 29.0 — First real 30–60 second production run (controlled)")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--output-root", required=True, type=Path)
    ap.add_argument("--asset-manifest", required=True, type=Path)
    ap.add_argument("--scene-asset-pack", required=False, type=Path, default=None)
    ap.add_argument("--script-json", required=False, type=Path, default=None)
    ap.add_argument("--duration-target-seconds", type=int, default=45)
    ap.add_argument("--provider", type=str, default="auto")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument(
        "--render-local-preview",
        action="store_true",
        dest="render_local_preview",
        help="BA 29.3: build local_preview.mp4 from render_input_bundle (requires local FFmpeg).",
    )
    ap.add_argument(
        "--max-timeline-scenes",
        type=int,
        default=5,
        metavar="N",
        help="BA 32.0: max assets in motion_timeline_manifest (default 5).",
    )
    args = ap.parse_args()

    run_controlled_production_run(
        run_id=str(args.run_id),
        output_root=args.output_root.resolve(),
        asset_manifest_path=args.asset_manifest.resolve(),
        scene_asset_pack=args.scene_asset_pack.resolve() if args.scene_asset_pack else None,
        script_json=args.script_json.resolve() if args.script_json else None,
        duration_target_seconds=int(args.duration_target_seconds),
        provider=str(args.provider),
        render_local_preview=bool(args.render_local_preview),
        max_timeline_scenes=int(args.max_timeline_scenes),
    )
    out_root = args.output_root.resolve()
    summ = out_root / f"first_real_production_run_summary_{args.run_id}.json"
    print(json.dumps({"ok": True, "summary_path": str(summ.resolve())}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
