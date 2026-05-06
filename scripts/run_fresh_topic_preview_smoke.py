"""BA 30.2 — Fresh topic / URL / script.json → asset_manifest → preview smoke + OPEN_PREVIEW_SMOKE.md."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.production_assembly.fresh_topic_preview_smoke import run_fresh_topic_preview_smoke


def main() -> int:
    ap = argparse.ArgumentParser(
        description="BA 30.2 — Fresh input → placeholder assets → preview smoke (no upload; default no live providers)"
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--output-root", type=Path, default=Path("output"))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--topic", type=str, default=None, help="Plain topic / headline text (no URL fetch)")
    g.add_argument("--url", type=str, default=None, help="Article or page URL to extract")
    g.add_argument("--script-json", type=Path, default=None, help="Existing GenerateScriptResponse-like JSON")
    ap.add_argument("--duration-target-seconds", type=int, default=45)
    ap.add_argument("--provider", type=str, default="auto", help="Forwarded to BA 29.0 motion adapter (dry-run clips)")
    ap.add_argument("--max-scenes", type=int, default=5)
    ap.add_argument("--asset-dir", type=Path, default=None, help="Optional folder with images/videos to map onto scenes")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Stop after asset_manifest.json (no BA 29.0 / local preview / OPEN_PREVIEW_SMOKE)",
    )
    ap.add_argument(
        "--allow-live-assets",
        action="store_true",
        help="Use asset_runner live mode (Leonardo etc.); default is placeholder-only. Operator must supply keys.",
    )
    ap.add_argument(
        "--max-live-assets",
        type=int,
        default=None,
        metavar="N",
        help="BA 32.0: max Leonardo live generations in live mode (default: Asset Runner default 3).",
    )
    args = ap.parse_args()

    r = run_fresh_topic_preview_smoke(
        run_id=str(args.run_id),
        output_root=args.output_root.resolve(),
        topic=args.topic,
        url=args.url,
        script_json=args.script_json.resolve() if args.script_json else None,
        duration_target_seconds=int(args.duration_target_seconds),
        provider=str(args.provider),
        dry_run=bool(args.dry_run),
        max_scenes=int(args.max_scenes),
        asset_dir=args.asset_dir.resolve() if args.asset_dir else None,
        asset_runner_mode="live" if args.allow_live_assets else "placeholder",
        max_live_assets=args.max_live_assets,
    )
    print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
    if r.get("blocking_reasons"):
        return 2
    if not r.get("ok"):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
