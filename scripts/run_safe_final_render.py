"""BA 29.6 — Safe final local render (dry-run default; --execute for copy/ffmpeg)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.production_assembly.final_render_execution import build_final_render_execution_result


def _read_json(p: Path) -> Dict[str, Any]:
    if not p.is_file():
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 29.6 — Safe final render (explicit --execute)")
    ap.add_argument("--production-summary", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--execute", action="store_true", help="Run lightweight final encode/copy (requires readiness ready).")
    ap.add_argument("--preview-video", type=str, default=None, help="Override preview video path")
    args = ap.parse_args()

    res: Dict[str, Any] = {}
    try:
        ps = _read_json(args.production_summary.resolve())
        res = build_final_render_execution_result(
            production_summary=ps,
            output_dir=args.output_dir,
            execute=bool(args.execute),
            preview_video_path=args.preview_video,
        )
        ps["final_render_execution_result"] = res
        out_dir = args.output_dir.resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        result_path = out_dir / "final_render_execution_result.json"
        result_path.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # also patch summary on disk for operator trail
        args.production_summary.write_text(json.dumps(ps, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": bool(res.get("ok")), "result_path": str(result_path)}, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2
    if not res.get("ok"):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
