"""BA 29.2 — Render local preview MP4 from render_input_bundle.json (optional FFmpeg)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.production_assembly.local_preview_render import run_local_preview_from_bundle


def _read_json(p: Path) -> Dict[str, Any]:
    pp = p.resolve()
    if not pp.is_file():
        raise FileNotFoundError(f"bundle not found: {pp}")
    return json.loads(pp.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 29.2 — Local preview render from render_input_bundle.json")
    ap.add_argument("--bundle", required=True, type=Path, help="Path to render_input_bundle.json")
    ap.add_argument("--output-dir", required=True, type=Path, help="Directory for preview MP4 + sidecar files")
    ap.add_argument("--timeline", required=False, type=Path, default=None, help="Optional motion_timeline_manifest.json override")
    ap.add_argument("--output-name", default="local_preview.mp4", help="Preview video filename (default: local_preview.mp4)")
    ap.add_argument("--scene-seconds", type=float, default=5.0, help="Default still duration if timeline lacks per-scene duration")
    args = ap.parse_args()
    result: Dict[str, Any] = {}

    try:
        bundle = _read_json(args.bundle)
        timeline_doc = None
        if args.timeline is not None:
            timeline_doc = _read_json(args.timeline)
        result = run_local_preview_from_bundle(
            bundle=bundle,
            bundle_path=str(args.bundle.resolve()),
            output_dir=args.output_dir,
            output_video_name=str(args.output_name),
            timeline_override=timeline_doc,
            default_scene_seconds=float(args.scene_seconds),
        )
        out_dir = args.output_dir.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        result_path = out_dir / "local_preview_render_result.json"
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": bool(result.get("ok")), "result_path": str(result_path)}, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:400]}, ensure_ascii=False, indent=2))
        return 2
    return 0 if result.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
