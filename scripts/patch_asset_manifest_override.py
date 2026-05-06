"""BA 26.6c — CLI: Patch asset_manifest.json with manual overrides (local, deterministic).

Kein Dashboard-Write, keine Provider-Calls. Nur JSON lesen/patchen/schreiben.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.visual_plan.asset_override import (
    apply_scene_asset_override,
    mark_scene_asset_accepted,
    mark_scene_asset_locked,
    mark_scene_asset_rejected,
    request_scene_asset_regeneration,
)


def _s(v: Any) -> str:
    return str(v or "").strip()


def load_asset_manifest(path: Path) -> Dict[str, Any]:
    p = path.resolve()
    if not p.is_file():
        raise FileNotFoundError(f"asset_manifest not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _find_asset_index(manifest: Dict[str, Any], scene_number: int) -> int:
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        return -1
    for i, a in enumerate(assets):
        if isinstance(a, dict) and int(a.get("scene_number", -1)) == int(scene_number):
            return i
    return -1


def patch_asset_manifest(
    manifest: Dict[str, Any],
    *,
    scene_number: int,
    status: Optional[str],
    selected_asset_path: Optional[str],
    manual_provider_override: Optional[str],
    manual_prompt_override: Optional[str],
    reason: Optional[str],
    candidate_asset_paths: Optional[List[str]],
    now_iso: Optional[str],
) -> Dict[str, Any]:
    out = dict(manifest or {})
    assets = list(out.get("assets") or [])
    if not assets:
        raise ValueError("asset_manifest.assets empty or missing")
    idx = _find_asset_index(out, int(scene_number))
    if idx < 0:
        raise ValueError(f"scene_number not found in asset_manifest.assets: {int(scene_number)}")
    asset = assets[idx]
    if not isinstance(asset, dict):
        raise ValueError("asset_manifest.assets entry is not an object")

    st = (_s(status).lower() if status is not None else "").strip()
    if st in ("accepted",):
        patched = mark_scene_asset_accepted(asset, reason, now_iso=now_iso)
    elif st in ("rejected",):
        patched = mark_scene_asset_rejected(asset, reason, now_iso=now_iso)
    elif st in ("locked",):
        patched = mark_scene_asset_locked(asset, reason, now_iso=now_iso)
    elif st in ("needs_regeneration", "regenerate"):
        patched = request_scene_asset_regeneration(asset, reason, now_iso=now_iso)
    elif st in ("pending", ""):
        patched = asset
    else:
        raise ValueError(f"invalid --status: {st}")

    patched = apply_scene_asset_override(
        patched,
        selected_asset_path=selected_asset_path,
        manual_provider_override=manual_provider_override,
        manual_prompt_override=manual_prompt_override,
        manual_override_reason=reason,
        decision_status=(st if st else None),
        candidate_asset_paths=candidate_asset_paths,
        now_iso=now_iso,
    )

    assets[idx] = patched
    out["assets"] = assets
    out["override_patch_version"] = "ba26_6c_v1"
    return out


def write_asset_manifest(path: Path, manifest: Dict[str, Any]) -> Path:
    p = path.resolve()
    p.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description="BA 26.6c — Patch asset_manifest.json with manual overrides")
    ap.add_argument("--manifest", type=Path, required=True, help="Path to asset_manifest.json")
    ap.add_argument("--scene-number", type=int, required=True, dest="scene_number")
    ap.add_argument(
        "--status",
        default="",
        help="pending|accepted|rejected|locked|needs_regeneration",
    )
    ap.add_argument("--selected-asset-path", default="", dest="selected_asset_path")
    ap.add_argument("--manual-provider-override", default="", dest="manual_provider_override")
    ap.add_argument("--manual-prompt-override", default="", dest="manual_prompt_override")
    ap.add_argument("--reason", default="", dest="reason")
    ap.add_argument(
        "--candidate-asset-path",
        action="append",
        default=[],
        dest="candidate_asset_paths",
        help="Repeatable. Add candidate asset path(s).",
    )
    ap.add_argument(
        "--now-iso",
        default="",
        dest="now_iso",
        help="Optional deterministic timestamp for replacement_history entries.",
    )
    ap.add_argument(
        "--in-place",
        action="store_true",
        dest="in_place",
        help="Write back into the same manifest file (default).",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=None,
        dest="output",
        help="Optional output path (if not set: overwrite --manifest).",
    )
    args = ap.parse_args()

    mpath: Path = args.manifest
    out_path = args.output if args.output is not None else mpath

    try:
        doc = load_asset_manifest(mpath)
        patched = patch_asset_manifest(
            doc,
            scene_number=int(args.scene_number),
            status=(args.status or "").strip() or None,
            selected_asset_path=_s(args.selected_asset_path) or None,
            manual_provider_override=_s(args.manual_provider_override) or None,
            manual_prompt_override=_s(args.manual_prompt_override) or None,
            reason=_s(args.reason) or None,
            candidate_asset_paths=[_s(x) for x in (args.candidate_asset_paths or []) if _s(x)],
            now_iso=_s(args.now_iso) or None,
        )
        write_asset_manifest(out_path, patched)
    except Exception as e:
        err = {"ok": False, "error": type(e).__name__, "message": str(e)[:300]}
        print(json.dumps(err, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps({"ok": True, "manifest": str(out_path.resolve())}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

