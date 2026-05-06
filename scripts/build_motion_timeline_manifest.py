"""BA 28.3 — CLI: build motion_timeline_manifest.json from asset_manifest + motion_clip_manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.production_assembly.motion_timeline_alignment import build_motion_timeline_manifest


def _read_json(p: Optional[Path]) -> Optional[Dict[str, Any]]:
    if p is None:
        return None
    pp = p.resolve()
    if not pp.is_file():
        raise FileNotFoundError(f"json not found: {pp}")
    return json.loads(pp.read_text(encoding="utf-8"))


def _write_json(p: Path, obj: Dict[str, Any]) -> Path:
    pp = p.resolve()
    pp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return pp


def _index_by_scene(items: Any) -> Dict[int, Dict[str, Any]]:
    out: Dict[int, Dict[str, Any]] = {}
    if not isinstance(items, list):
        return out
    for it in items:
        if not isinstance(it, dict):
            continue
        try:
            sn = int(it.get("scene_number") or it.get("scene_index") or 0)
        except Exception:
            continue
        if sn >= 1:
            out[sn] = it
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 28.3 — build motion timeline manifest (no render)")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--asset-manifest", required=True, type=Path)
    ap.add_argument("--motion-clip-manifest", required=False, type=Path, default=None)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--default-duration-seconds", type=int, default=5)
    args = ap.parse_args()

    try:
        man = _read_json(args.asset_manifest) or {}
        mm = _read_json(args.motion_clip_manifest) if args.motion_clip_manifest else None
        assets = man.get("assets") if isinstance(man.get("assets"), list) else []
        clips = (mm.get("clips") if isinstance(mm, dict) else None) or []
        by_clip = _index_by_scene(clips)
        scenes: List[Dict[str, Any]] = []
        for a in assets:
            if not isinstance(a, dict):
                continue
            sn = int(a.get("scene_number") or a.get("scene_index") or 0) or 0
            row = dict(a)
            c = by_clip.get(sn)
            if isinstance(c, dict):
                row["clip_path"] = row.get("clip_path") or c.get("clip_path") or c.get("clip_path")
                row["duration_seconds"] = row.get("duration_seconds") or c.get("duration_seconds")
            scenes.append(row)
        out = build_motion_timeline_manifest(run_id=args.run_id, scenes=scenes, default_duration_seconds=int(args.default_duration_seconds))
        _write_json(args.output, out)
        print(json.dumps({"ok": True, "scenes": len(out.get("scenes") or []), "output": str(args.output.resolve())}, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

