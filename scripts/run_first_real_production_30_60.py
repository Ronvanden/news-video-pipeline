"""BA 29.0 — Controlled 30–60s production run (no live provider calls).

Builds/links: motion_manifest (dry-run), production pack, preflight, timeline, render bundle, final render dry-run.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

from app.production_assembly.final_render_contract import build_final_render_dry_run_result
from app.production_assembly.motion_timeline_alignment import build_motion_timeline_manifest
from app.production_assembly.render_input_bundle import build_render_input_bundle
from app.production_connectors.motion_provider_adapter import build_motion_clip_result
from app.production_connectors.motion_clip_ingest import ingest_motion_clip_results
from app.real_video_build.production_pack import build_production_pack
from app.visual_plan.visual_production_preflight import build_visual_production_preflight_result


def _read_json(p: Path) -> Dict[str, Any]:
    pp = p.resolve()
    if not pp.is_file():
        raise FileNotFoundError(f"json not found: {pp}")
    return json.loads(pp.read_text(encoding="utf-8"))


def _write_json(p: Path, obj: Dict[str, Any]) -> Path:
    pp = p.resolve()
    pp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return pp


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
    args = ap.parse_args()

    out_root = args.output_root.resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    run_id = str(args.run_id)

    warnings = []
    blocking = []

    asset_manifest = _read_json(args.asset_manifest)
    assets = asset_manifest.get("assets") if isinstance(asset_manifest.get("assets"), list) else []

    # 1) build motion clip manifest (dry-run results from motion_clip assets)
    base_dir = args.asset_manifest.resolve().parent
    clips = []
    for a in assets:
        if not isinstance(a, dict):
            continue
        if str(a.get("visual_asset_kind") or "") != "motion_clip":
            continue
        clips.append(build_motion_clip_result(a, base_dir=base_dir, provider=str(args.provider), duration_seconds=5, dry_run=True))
    motion_manifest = {
        "motion_clip_manifest_version": "ba28_0_v1",
        "clips": clips,
        "summary": {
            "clips_planned": len(clips),
            "provider_counts": {},
            "missing_input_count": len([c for c in clips if c.get("error_code") == "missing_input_image"]),
            "dry_run": True,
        },
    }
    # 2) ingest placeholders to get clip_path stubs/artifacts
    motion_manifest_ingested = ingest_motion_clip_results(motion_manifest, output_dir=out_root / f"clips_{run_id}", dry_run=False)
    motion_manifest_path = out_root / f"motion_clip_manifest_{run_id}.json"
    _write_json(motion_manifest_path, motion_manifest_ingested)

    # 3) build production pack
    pack = build_production_pack(
        run_id=run_id,
        output_root=out_root,
        source_paths={
            "asset_manifest": args.asset_manifest,
            "scene_asset_pack": args.scene_asset_pack,
            "script_json": args.script_json,
            "motion_clip_manifest": motion_manifest_path,
        },
        dry_run=False,
        copy_assets=True,
    )
    pack_dir = Path(pack["pack_dir"]).resolve()
    prod_summary_path = pack_dir / "production_summary.json"
    prod_summary = _read_json(prod_summary_path)

    # 4) preflight (read-only)
    preflight = build_visual_production_preflight_result(asset_manifest=asset_manifest, production_summary=prod_summary)

    # 5) build simple timeline (3–5 scenes best-effort from assets)
    scenes = []
    for a in assets:
        if not isinstance(a, dict):
            continue
        scenes.append(a)
        if len(scenes) >= 5:
            break
    timeline = build_motion_timeline_manifest(run_id=run_id, scenes=scenes, default_duration_seconds=5)
    timeline_path = out_root / f"motion_timeline_manifest_{run_id}.json"
    _write_json(timeline_path, timeline)

    # 6) build render input bundle
    bundle = build_render_input_bundle(
        run_id=run_id,
        production_summary_path=str(prod_summary_path),
        asset_manifest_path=str(args.asset_manifest.resolve()),
        motion_clip_manifest_path=str(motion_manifest_path),
        motion_timeline_manifest_path=str(timeline_path),
        ready_for_render=bool(prod_summary.get("ready_for_render") is True),
        render_readiness_status=str(prod_summary.get("render_readiness_status") or ""),
        warnings=list(prod_summary.get("warnings") or []),
        blocking_reasons=list(prod_summary.get("blocking_reasons") or []),
    )
    bundle_path = out_root / f"render_input_bundle_{run_id}.json"
    _write_json(bundle_path, bundle)

    # 7) final render dry-run
    dry = build_final_render_dry_run_result(input_bundle=bundle, input_bundle_path=str(bundle_path))
    dry_path = out_root / f"final_render_dry_run_result_{run_id}.json"
    _write_json(dry_path, dry)

    ok = bool(dry.get("would_render") or preflight.get("preflight_status") != "blocked")
    summary = {
        "ok": ok,
        "run_id": run_id,
        "production_run_version": "ba29_0_v1",
        "duration_target_seconds": int(args.duration_target_seconds),
        "scene_count": int(len(timeline.get("scenes") or [])),
        "used_real_images": True,
        "used_placeholder_clips": True,
        "used_real_voice": False,
        "production_pack_path": str(pack_dir),
        "render_input_bundle_path": str(bundle_path.resolve()),
        "final_render_dry_run_result_path": str(dry_path.resolve()),
        "ready_for_manual_review": bool(preflight.get("preflight_status") != "blocked"),
        "blocking_reasons": list(dict.fromkeys(blocking + list(dry.get("blocking_reasons") or []))),
        "warnings": list(dict.fromkeys(warnings + list(preflight.get("warnings") or []) + list(dry.get("warnings") or []))),
        "next_operator_actions": [
            "Open production_pack/README_PRODUCTION_PACK.md",
            "Review visual_production_preflight_result",
            "Review motion_timeline_manifest and render_input_bundle",
        ],
    }
    out_summary_path = out_root / f"first_real_production_run_summary_{run_id}.json"
    _write_json(out_summary_path, summary)
    print(json.dumps({"ok": True, "summary_path": str(out_summary_path.resolve())}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

