"""BA 25.2 — CLI: GenerateScriptResponse/Story-Pack JSON → scene_asset_pack.json.

Kein URL-Input, kein /generate-script Call, kein LLM/Provider.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.real_video_build.script_input_adapter import (
    build_scene_asset_pack_from_generate_script_response,
    build_scene_asset_pack_from_story_pack,
    write_scene_asset_pack,
)


def _load_json(path: Path) -> Dict[str, Any]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("input JSON must be an object (dict)")
    return raw


def _looks_like_generate_script_response(d: Dict[str, Any]) -> bool:
    keys = set(d.keys())
    return bool({"chapters", "full_script", "hook", "title"} & keys) and ("chapters" in keys or "full_script" in keys)


def main(argv: Any = None) -> int:
    p = argparse.ArgumentParser(
        description="BA 25.2 — Adaptiert Script/Story-Pack JSON zu scene_asset_pack.json (lokal, ohne Provider)."
    )
    p.add_argument("--input", type=Path, required=True, dest="input_path")
    p.add_argument("--output", type=Path, required=True, dest="output_path")
    p.add_argument("--run-id", default="", dest="run_id")
    p.add_argument("--print-json", action="store_true", dest="print_json")
    args = p.parse_args(argv)

    try:
        data = _load_json(args.input_path)
        if _looks_like_generate_script_response(data):
            pack = build_scene_asset_pack_from_generate_script_response(data, run_id=args.run_id)
            adapter = "generate_script_response"
        else:
            pack = build_scene_asset_pack_from_story_pack(data, run_id=args.run_id)
            adapter = "story_pack"
        out_p = write_scene_asset_pack(pack, args.output_path)
    except Exception as exc:
        err = {"ok": False, "error": type(exc).__name__, "message": str(exc)[:400]}
        if args.print_json:
            print(json.dumps(err, ensure_ascii=False, indent=2))
        return 2

    meta = {
        "ok": True,
        "adapter": adapter,
        "output_path": str(out_p),
        "run_id": (args.run_id or "").strip(),
        "beat_count": len(((pack.get("scene_expansion") or {}).get("expanded_scene_assets") or [])),
    }
    if args.print_json:
        print(json.dumps({"pack": pack, "meta": meta}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

