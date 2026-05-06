"""BA 28.4 — Render input bundle builder (no render). BA 29.2b — media path hydration from asset_manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _s(v: Any) -> str:
    return str(v or "").strip()


def _resolve_media_path_raw(raw: str, base: Path) -> Path:
    p = Path(raw.strip())
    if p.is_absolute():
        return p.resolve()
    return (base / p).resolve()


def extract_hydrated_media_paths_from_manifest(
    manifest: Dict[str, Any],
    *,
    manifest_dir: Path,
) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """
    Collect image/clip paths from ``manifest["assets"]`` with priority rules,
    resolve relatives against ``manifest_dir``, dedupe (order preserved).
    Returns (image_paths, clip_paths, media_path_hydration_summary).
    """
    manifest_dir = manifest_dir.resolve()
    images_order: List[str] = []
    clips_order: List[str] = []
    missing: List[str] = []

    assets = manifest.get("assets") if isinstance(manifest.get("assets"), list) else []
    for a in assets:
        if not isinstance(a, dict):
            continue
        img_raw = _s(a.get("selected_asset_path")) or _s(a.get("generated_image_path")) or _s(a.get("image_path"))
        if img_raw:
            resolved = _resolve_media_path_raw(img_raw, manifest_dir)
            rs = str(resolved)
            images_order.append(rs)
            if not resolved.is_file():
                missing.append(rs)

        vp = _s(a.get("video_path"))
        cp = _s(a.get("clip_path"))
        for raw in (vp, cp):
            if not raw:
                continue
            resolved = _resolve_media_path_raw(raw, manifest_dir)
            rs = str(resolved)
            clips_order.append(rs)
            if not resolved.is_file():
                missing.append(rs)

    images = list(dict.fromkeys(images_order))
    clips = list(dict.fromkeys(clips_order))
    missing_u = list(dict.fromkeys([m for m in missing if _s(m)]))

    images_existing = sum(1 for p in images if Path(p).is_file())
    clips_existing = sum(1 for p in clips if Path(p).is_file())

    summary: Dict[str, Any] = {
        "hydration_version": "ba29_2b_v1",
        "images_found": int(images_existing),
        "clips_found": int(clips_existing),
        "missing_paths": missing_u,
        "images_collected": len(images),
        "clips_collected": len(clips),
    }
    return images, clips, summary


def _resolve_path_list(paths: List[str], base: Optional[Path]) -> List[str]:
    if not base:
        return [p for p in paths if _s(p)]
    out: List[str] = []
    for raw in paths:
        if not _s(raw):
            continue
        out.append(str(_resolve_media_path_raw(raw, base)))
    return out


def build_render_input_bundle(
    *,
    run_id: str,
    production_summary_path: Optional[str] = None,
    asset_manifest_path: Optional[str] = None,
    motion_clip_manifest_path: Optional[str] = None,
    motion_timeline_manifest_path: Optional[str] = None,
    subtitle_path: Optional[str] = None,
    voice_paths: Optional[List[str]] = None,
    clip_paths: Optional[List[str]] = None,
    image_paths: Optional[List[str]] = None,
    overlay_intents: Optional[List[str]] = None,
    ready_for_render: bool = False,
    render_readiness_status: str = "",
    warnings: Optional[List[str]] = None,
    blocking_reasons: Optional[List[str]] = None,
    asset_manifest: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    bundle_warnings: List[str] = [_s(w) for w in (warnings or []) if _s(w)]

    am: Optional[Dict[str, Any]] = asset_manifest if isinstance(asset_manifest, dict) else None
    manifest_dir: Optional[Path] = None
    if _s(asset_manifest_path):
        manifest_dir = Path(str(asset_manifest_path)).resolve().parent
    if am is None and _s(asset_manifest_path):
        p = Path(str(asset_manifest_path)).resolve()
        try:
            if p.is_file():
                am = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            bundle_warnings.append("asset_manifest_unreadable_for_hydration")

    hyd_imgs: List[str] = []
    hyd_clips: List[str] = []
    hyd_summary: Optional[Dict[str, Any]] = None
    if isinstance(am, dict):
        md = manifest_dir if manifest_dir is not None else Path.cwd().resolve()
        hyd_imgs, hyd_clips, hyd_summary = extract_hydrated_media_paths_from_manifest(am, manifest_dir=md)

    incoming_imgs = [p for p in (image_paths or []) if _s(p)]
    incoming_clips = [p for p in (clip_paths or []) if _s(p)]
    base_incoming: Optional[Path] = manifest_dir
    if base_incoming is None and (incoming_imgs or incoming_clips):
        base_incoming = Path.cwd().resolve()
    inc_imgs_res = _resolve_path_list(incoming_imgs, base_incoming)
    inc_clips_res = _resolve_path_list(incoming_clips, base_incoming)

    merged_imgs = list(dict.fromkeys([*inc_imgs_res, *hyd_imgs]))
    merged_clips = list(dict.fromkeys([*inc_clips_res, *hyd_clips]))

    if hyd_summary and hyd_summary.get("missing_paths"):
        bundle_warnings.append(f"media_hydration_missing_paths:{len(hyd_summary['missing_paths'])}")

    bundle_warnings = list(dict.fromkeys([w for w in bundle_warnings if _s(w)]))

    out: Dict[str, Any] = {
        "render_input_bundle_version": "ba28_4_v1",
        "run_id": _s(run_id),
        "ready_for_render": bool(ready_for_render),
        "render_readiness_status": _s(render_readiness_status),
        "production_summary_path": production_summary_path,
        "asset_manifest_path": asset_manifest_path,
        "motion_clip_manifest_path": motion_clip_manifest_path,
        "motion_timeline_manifest_path": motion_timeline_manifest_path,
        "subtitle_path": subtitle_path,
        "voice_paths": [p for p in (voice_paths or []) if _s(p)],
        "clip_paths": merged_clips,
        "image_paths": merged_imgs,
        "overlay_intents": [x for x in (overlay_intents or []) if _s(x)],
        "warnings": bundle_warnings,
        "blocking_reasons": list(dict.fromkeys([_s(b) for b in (blocking_reasons or []) if _s(b)])),
    }
    if hyd_summary is not None:
        out["media_path_hydration_summary"] = hyd_summary
    return out
