"""BA 29.0 — Controlled production run core (callable from scripts/tests)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from app.production_assembly.final_render_contract import build_final_render_dry_run_result
from app.production_assembly.local_preview_render import run_local_preview_from_bundle
from app.production_assembly.motion_timeline_alignment import build_motion_timeline_manifest
from app.production_assembly.render_input_bundle import build_render_input_bundle
from app.production_connectors.motion_clip_ingest import ingest_motion_clip_results
from app.production_connectors.motion_provider_adapter import build_motion_clip_result
from app.production_connectors.runway_live_readiness import (
    augment_motion_clip_manifest_summary,
    controlled_run_blocking_reasons_for_live_motion,
)
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


def _voice_paths_and_doc_from_manifest(vm_path: Optional[Path]) -> tuple[list[str], Dict[str, Any]]:
    """BA 32.2 — Pfade aus voice_manifest.json für Render-Bundle (keine Secrets)."""
    if vm_path is None:
        return [], {}
    try:
        p = Path(vm_path).resolve()
        if not p.is_file():
            return [], {}
        doc = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return [], {}
    if not isinstance(doc, dict):
        return [], {}
    paths: list[str] = []
    fv = str(doc.get("full_voiceover_path") or "").strip()
    if fv:
        paths.append(fv)
    vp = doc.get("voice_paths")
    if isinstance(vp, list):
        paths.extend(str(x).strip() for x in vp if str(x or "").strip())
    return list(dict.fromkeys(paths)), doc


def run_controlled_production_run(
    *,
    run_id: str,
    output_root: Path,
    asset_manifest_path: Path,
    scene_asset_pack: Optional[Path] = None,
    script_json: Optional[Path] = None,
    duration_target_seconds: int = 45,
    provider: str = "auto",
    render_local_preview: bool = False,
    max_timeline_scenes: int = 5,
    allow_live_motion: bool = False,
    max_live_motion_clips: int = 0,
    voice_manifest_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    BA 29.0 core flow. Returns paths and artefact dicts (no printing).

    ``max_timeline_scenes``: max number of manifest assets included in ``motion_timeline_manifest``
    (default **5**, conservative; raise for long-form e.g. 20–24).

    ``allow_live_motion`` / ``max_live_motion_clips``: Runway-Live-Wunsch (BA 32.1); Pipeline-Connector
    noch Stub — Blocker/Readiness siehe ``motion_clip_manifest``-Summary.

    ``voice_manifest_path``: optional ``voice_manifest.json`` (z. B. von ``build_full_voiceover``) —
    Pfade werden ins Render-Bundle und Production Pack übernommen (BA 32.2).
    """
    out_root = Path(output_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    rid = str(run_id)
    warnings: list[str] = []
    blocking: list[str] = []
    blocking.extend(controlled_run_blocking_reasons_for_live_motion(allow_live_motion=allow_live_motion))

    am_path = Path(asset_manifest_path).resolve()
    asset_manifest = _read_json(am_path)
    assets = asset_manifest.get("assets") if isinstance(asset_manifest.get("assets"), list) else []

    base_dir = am_path.parent
    motion_cap: Optional[int] = int(max_live_motion_clips) if int(max_live_motion_clips or 0) > 0 else None
    clip_assets: list[Dict[str, Any]] = [
        a
        for a in assets
        if isinstance(a, dict) and str(a.get("visual_asset_kind") or "") == "motion_clip"
    ]
    clips = []
    for idx, a in enumerate(clip_assets):
        clips.append(
            build_motion_clip_result(
                a,
                base_dir=base_dir,
                provider=str(provider),
                duration_seconds=5,
                dry_run=True,
                allow_live_motion=bool(allow_live_motion),
                live_motion_clip_index=int(idx),
                max_live_motion_clips=motion_cap,
            )
        )
    summary_core = {
        "clips_planned": len(clips),
        "provider_counts": {},
        "missing_input_count": len([c for c in clips if c.get("error_code") == "missing_input_image"]),
        "dry_run": True,
    }
    summary_core = augment_motion_clip_manifest_summary(
        summary_core,
        allow_live_motion=bool(allow_live_motion),
        max_live_motion_clips=int(max_live_motion_clips or 0),
    )
    motion_manifest = {
        "motion_clip_manifest_version": "ba28_0_v1",
        "clips": clips,
        "summary": summary_core,
    }
    motion_manifest_ingested = ingest_motion_clip_results(motion_manifest, output_dir=out_root / f"clips_{rid}", dry_run=False)
    motion_manifest_path = out_root / f"motion_clip_manifest_{rid}.json"
    _write_json(motion_manifest_path, motion_manifest_ingested)

    src_paths: Dict[str, Any] = {
        "asset_manifest": am_path,
        "scene_asset_pack": scene_asset_pack,
        "script_json": script_json,
        "motion_clip_manifest": motion_manifest_path,
    }
    if voice_manifest_path:
        src_paths["voice_manifest"] = Path(voice_manifest_path).resolve()

    pack = build_production_pack(
        run_id=rid,
        output_root=out_root,
        source_paths=src_paths,
        dry_run=False,
        copy_assets=True,
    )
    pack_dir = Path(pack["pack_dir"]).resolve()
    prod_summary_path = pack_dir / "production_summary.json"
    prod_summary = _read_json(prod_summary_path)

    voice_audio_paths, voice_doc = _voice_paths_and_doc_from_manifest(voice_manifest_path)
    prod_warnings = (
        list(prod_summary.get("warnings") or []) if isinstance(prod_summary.get("warnings"), list) else []
    )
    prod_blocking = (
        list(prod_summary.get("blocking_reasons") or [])
        if isinstance(prod_summary.get("blocking_reasons"), list)
        else []
    )
    if voice_doc:
        if isinstance(voice_doc.get("warnings"), list):
            prod_warnings.extend(str(w) for w in voice_doc["warnings"] if str(w or "").strip())
        if isinstance(voice_doc.get("blocking_reasons"), list):
            prod_blocking.extend(str(w) for w in voice_doc["blocking_reasons"] if str(w or "").strip())

    preflight = build_visual_production_preflight_result(asset_manifest=asset_manifest, production_summary=prod_summary)

    cap = max(1, int(max_timeline_scenes))
    scenes = []
    for a in assets:
        if not isinstance(a, dict):
            continue
        scenes.append(a)
        if len(scenes) >= cap:
            break
    timeline = build_motion_timeline_manifest(run_id=rid, scenes=scenes, default_duration_seconds=5)
    timeline_path = out_root / f"motion_timeline_manifest_{rid}.json"
    _write_json(timeline_path, timeline)

    bundle = build_render_input_bundle(
        run_id=rid,
        production_summary_path=str(prod_summary_path),
        asset_manifest_path=str(am_path),
        asset_manifest=asset_manifest,
        motion_clip_manifest_path=str(motion_manifest_path),
        motion_timeline_manifest_path=str(timeline_path),
        voice_paths=voice_audio_paths,
        ready_for_render=bool(prod_summary.get("ready_for_render") is True),
        render_readiness_status=str(prod_summary.get("render_readiness_status") or ""),
        warnings=prod_warnings,
        blocking_reasons=prod_blocking,
    )
    bundle_path = out_root / f"render_input_bundle_{rid}.json"
    _write_json(bundle_path, bundle)

    dry = build_final_render_dry_run_result(input_bundle=bundle, input_bundle_path=str(bundle_path))
    dry_path = out_root / f"final_render_dry_run_result_{rid}.json"
    _write_json(dry_path, dry)

    local_preview_result_path: Optional[Path] = None
    if render_local_preview:
        prev = run_local_preview_from_bundle(
            bundle=bundle,
            bundle_path=str(bundle_path.resolve()),
            output_dir=out_root,
            output_video_name=f"local_preview_{rid}.mp4",
            timeline_override=timeline,
            default_scene_seconds=5.0,
        )
        local_preview_result_path = out_root / f"local_preview_render_result_{rid}.json"
        _write_json(local_preview_result_path, prev)
        prod_summary2 = _read_json(prod_summary_path)
        prod_summary2["local_preview_render_result"] = prev
        prod_summary2["local_preview_render_result_path"] = str(local_preview_result_path.resolve())
        prod_summary2["local_preview_video_path"] = str(prev.get("output_video_path") or "")
        prod_summary2["local_preview_status"] = "available" if prev.get("ok") else "failed"
        _write_json(prod_summary_path, prod_summary2)
        if prev.get("ok") and prev.get("output_video_path") and Path(str(prev["output_video_path"])).is_file():
            try:
                shutil.copy2(Path(str(prev["output_video_path"])), pack_dir / "local_preview.mp4")
                shutil.copy2(local_preview_result_path, pack_dir / "local_preview_render_result.json")
            except OSError:
                pass

    ok = bool(dry.get("would_render") or preflight.get("preflight_status") != "blocked")
    first_summary = {
        "ok": ok,
        "run_id": rid,
        "production_run_version": "ba29_0_v1",
        "duration_target_seconds": int(duration_target_seconds),
        "scene_count": int(len(timeline.get("scenes") or [])),
        "used_real_images": True,
        "used_placeholder_clips": True,
        "used_real_voice": bool(voice_doc.get("real_tts_generated") is True),
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
        "local_preview_render_result_path": str(local_preview_result_path.resolve()) if local_preview_result_path else None,
    }
    out_summary_path = out_root / f"first_real_production_run_summary_{rid}.json"
    _write_json(out_summary_path, first_summary)

    return {
        "first_real_production_run_summary_path": str(out_summary_path.resolve()),
        "first_real_production_run_summary": first_summary,
        "bundle_path": bundle_path.resolve(),
        "bundle": bundle,
        "timeline": timeline,
        "timeline_path": timeline_path.resolve(),
        "pack_dir": pack_dir,
        "production_summary_path": prod_summary_path.resolve(),
        "asset_manifest_path_used": str(am_path),
        "dry_path": dry_path.resolve(),
        "preflight": preflight,
        "dry": dry,
        "local_preview_render_result_path": str(local_preview_result_path.resolve()) if local_preview_result_path else None,
    }
