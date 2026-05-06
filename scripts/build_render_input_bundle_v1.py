"""BA 28.4 — CLI: build render_input_bundle.json (no render)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

from app.production_assembly.render_input_bundle import build_render_input_bundle


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


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 28.4 — render input bundle builder (no render)")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--production-summary", required=True, type=Path)
    ap.add_argument("--asset-manifest", required=True, type=Path)
    ap.add_argument("--motion-clip-manifest", required=False, type=Path, default=None)
    ap.add_argument("--motion-timeline-manifest", required=False, type=Path, default=None)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    try:
        ps = _read_json(args.production_summary) or {}
        am = _read_json(args.asset_manifest) or {}
        mm = _read_json(args.motion_clip_manifest) if args.motion_clip_manifest else None
        tm = _read_json(args.motion_timeline_manifest) if args.motion_timeline_manifest else None

        # derive minimal paths list for diagnostics
        voice_paths = []
        clip_paths = []
        image_paths = []
        overlay_intents = []
        for a in (am.get("assets") or []) if isinstance(am.get("assets"), list) else []:
            if not isinstance(a, dict):
                continue
            if a.get("voice_path"):
                voice_paths.append(str(a.get("voice_path")))
            if a.get("video_path") or a.get("clip_path"):
                clip_paths.append(str(a.get("video_path") or a.get("clip_path")))
            if a.get("selected_asset_path") or a.get("image_path") or a.get("generated_image_path"):
                image_paths.append(str(a.get("selected_asset_path") or a.get("image_path") or a.get("generated_image_path")))
            if isinstance(a.get("overlay_intent"), list):
                overlay_intents.extend([str(x) for x in (a.get("overlay_intent") or []) if str(x).strip()])

        out = build_render_input_bundle(
            run_id=args.run_id,
            production_summary_path=str(args.production_summary.resolve()),
            asset_manifest_path=str(args.asset_manifest.resolve()),
            motion_clip_manifest_path=str(args.motion_clip_manifest.resolve()) if args.motion_clip_manifest else None,
            motion_timeline_manifest_path=str(args.motion_timeline_manifest.resolve()) if args.motion_timeline_manifest else None,
            ready_for_render=bool(ps.get("ready_for_render") is True),
            render_readiness_status=str(ps.get("render_readiness_status") or ""),
            warnings=list(ps.get("warnings") or []) if isinstance(ps.get("warnings"), list) else [],
            blocking_reasons=list(ps.get("blocking_reasons") or []) if isinstance(ps.get("blocking_reasons"), list) else [],
            voice_paths=voice_paths,
            clip_paths=clip_paths,
            image_paths=image_paths,
            overlay_intents=overlay_intents,
        )
        _write_json(args.output, out)
        print(json.dumps({"ok": True, "output": str(args.output.resolve())}, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

