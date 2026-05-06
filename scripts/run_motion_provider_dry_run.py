"""BA 28.0 — CLI: build motion_clip_manifest.json from asset_manifest.json (dry-run only)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from app.production_connectors.motion_provider_adapter import build_motion_clip_result


def _load_json(path: Path) -> Dict[str, Any]:
    p = path.resolve()
    if not p.is_file():
        raise FileNotFoundError(f"asset_manifest not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: Dict[str, Any]) -> Path:
    p = path.resolve()
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def build_motion_clip_manifest(
    asset_manifest: Dict[str, Any],
    *,
    base_dir: Path,
    provider: str,
    duration_seconds: int,
    dry_run: bool,
) -> Dict[str, Any]:
    man = asset_manifest if isinstance(asset_manifest, dict) else {}
    assets = man.get("assets")
    if not isinstance(assets, list):
        assets = []

    clips: List[Dict[str, Any]] = []
    provider_counts: Dict[str, int] = {}
    missing_input = 0

    for a in assets:
        if not isinstance(a, dict):
            continue
        kind = str(a.get("visual_asset_kind") or "")
        if kind != "motion_clip":
            continue
        res = build_motion_clip_result(a, base_dir=base_dir, provider=provider, duration_seconds=duration_seconds, dry_run=dry_run)
        clips.append(res)
        prov = str(res.get("provider") or "")
        if prov:
            provider_counts[prov] = int(provider_counts.get(prov, 0)) + 1
        if res.get("ok") is False and res.get("error_code") == "missing_input_image":
            missing_input += 1

    return {
        "motion_clip_manifest_version": "ba28_0_v1",
        "clips": clips,
        "summary": {
            "clips_planned": int(len(clips)),
            "provider_counts": provider_counts,
            "missing_input_count": int(missing_input),
            "dry_run": bool(dry_run),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 28.0 — Motion provider dry-run (no live calls)")
    ap.add_argument("--manifest", type=Path, required=True, help="Path to asset_manifest.json")
    ap.add_argument("--output", type=Path, required=True, help="Output motion_clip_manifest.json path")
    ap.add_argument("--provider", type=str, default="auto", help="runway|seedance|auto")
    ap.add_argument("--duration-seconds", type=int, default=5)
    ap.add_argument("--dry-run", action="store_true", default=True, help="Dry-run only (default true)")
    args = ap.parse_args()

    try:
        man = _load_json(args.manifest)
        base_dir = args.manifest.resolve().parent
        out = build_motion_clip_manifest(
            man,
            base_dir=base_dir,
            provider=str(args.provider or "auto"),
            duration_seconds=int(args.duration_seconds),
            dry_run=bool(args.dry_run),
        )
        _write_json(args.output, out)
        print(json.dumps({"ok": True, "clips_planned": out["summary"]["clips_planned"], "output": str(args.output.resolve())}, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:300]}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

