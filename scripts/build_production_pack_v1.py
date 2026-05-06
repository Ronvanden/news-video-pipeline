"""BA 27.0 — Build Production Pack V1 (file-based).

Beispiel (PowerShell):
python scripts/build_production_pack_v1.py `
  --run-id test_001 `
  --output-root output `
  --asset-manifest output/generated_assets_test_001/asset_manifest.json `
  --scene-asset-pack output/generated_assets_test_001/scene_asset_pack.json `
  --script-json output/generated_assets_test_001/script.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.real_video_build.production_pack import build_production_pack


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 27.0 — Build Production Pack V1 (no live calls).")
    ap.add_argument("--run-id", required=True, dest="run_id")
    ap.add_argument("--output-root", required=True, type=Path, dest="output_root")
    ap.add_argument("--pack-dir", default=None, type=Path, dest="pack_dir")

    ap.add_argument("--asset-manifest", required=False, type=Path, dest="asset_manifest")
    ap.add_argument("--scene-asset-pack", required=False, type=Path, dest="scene_asset_pack")
    ap.add_argument("--script-json", required=False, type=Path, dest="script_json")

    ap.add_argument("--voice-manifest", required=False, type=Path, dest="voice_manifest")
    ap.add_argument("--overlay-manifest", required=False, type=Path, dest="overlay_manifest")
    ap.add_argument("--render-manifest", required=False, type=Path, dest="render_manifest")
    ap.add_argument("--visual-cost-summary", required=False, type=Path, dest="visual_cost_summary")
    ap.add_argument("--provider-quality-summary", required=False, type=Path, dest="provider_quality_summary")
    ap.add_argument("--reference-library", required=False, type=Path, dest="reference_library")

    ap.add_argument("--no-copy-assets", action="store_true", dest="no_copy_assets")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run")
    args = ap.parse_args()

    if not str(args.run_id or "").strip():
        print(json.dumps({"ok": False, "error": "invalid_run_id"}, ensure_ascii=False, indent=2))
        return 2

    source_paths: Dict[str, Any] = {
        "asset_manifest": args.asset_manifest,
        "scene_asset_pack": args.scene_asset_pack,
        "script_json": args.script_json,
        "voice_manifest": args.voice_manifest,
        "overlay_manifest": args.overlay_manifest,
        "render_manifest": args.render_manifest,
        "visual_cost_summary": args.visual_cost_summary,
        "provider_quality_summary": args.provider_quality_summary,
        "reference_library": args.reference_library,
    }

    try:
        res = build_production_pack(
            run_id=args.run_id,
            output_root=args.output_root,
            source_paths=source_paths,
            pack_dir=args.pack_dir,
            copy_assets=not bool(args.no_copy_assets),
            dry_run=bool(args.dry_run),
        )
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2

    stdout_summary = {
        "ok": bool(res.get("ok")),
        "pack_dir": res.get("pack_dir"),
        "ready_for_render": bool(res.get("ready_for_render")),
        "render_readiness_status": res.get("render_readiness_status"),
        "approval_status": res.get("approval_status"),
        "production_pack_summary": res.get("production_pack_summary") or None,
        "files_written": len(res.get("files_written") or []),
        "warnings": res.get("warnings") or [],
        "blocking_reasons": res.get("blocking_reasons") or [],
    }
    print(json.dumps(stdout_summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

