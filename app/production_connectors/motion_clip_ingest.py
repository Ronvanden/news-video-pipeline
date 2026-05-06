"""BA 28.2 — Motion clip ingest for dry-run placeholders (no video rendering)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _s(v: Any) -> str:
    return str(v or "").strip()


def create_placeholder_motion_clip_file(
    *,
    output_dir: Path,
    scene_number: int,
    provider: str,
    payload: Dict[str, Any],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    p = (output_dir / f"scene_{int(scene_number):03d}_{_s(provider) or 'provider'}_motion_stub.json").resolve()
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def ingest_motion_clip_results(
    motion_manifest: Dict[str, Any],
    *,
    output_dir: Path,
    dry_run: bool,
) -> Dict[str, Any]:
    mm = motion_manifest if isinstance(motion_manifest, dict) else {}
    clips = mm.get("clips")
    if not isinstance(clips, list):
        clips = []

    out_clips: List[Dict[str, Any]] = []
    for c in clips:
        if not isinstance(c, dict):
            continue
        row = dict(c)
        sn = int(row.get("scene_number") or 0) or 0
        prov = _s(row.get("provider") or "provider")
        ok = bool(row.get("ok") is True)
        if not ok:
            row["clip_artifact_type"] = "placeholder"
            row["clip_ingest_status"] = "missing_input" if row.get("error_code") == "missing_input_image" else "failed"
            out_clips.append(row)
            continue

        payload = {
            "schema": "motion_clip_placeholder_v1",
            "scene_number": sn,
            "provider": prov,
            "dry_run": bool(row.get("dry_run")),
            "note": "BA 28.2 placeholder artifact; no real clip rendered.",
            "reference_payload_used": row.get("reference_payload_used"),
        }
        if dry_run:
            row["clip_artifact_type"] = "placeholder"
            row["clip_ingest_status"] = "placeholder_ready"
            out_clips.append(row)
            continue

        ph = create_placeholder_motion_clip_file(output_dir=output_dir, scene_number=sn, provider=prov, payload=payload)
        row["clip_path"] = str(ph)
        row["clip_artifact_type"] = "placeholder"
        row["clip_ingest_status"] = "placeholder_ready"
        out_clips.append(row)

    out = dict(mm)
    out["clips"] = out_clips
    out["motion_clip_ingest_version"] = "ba28_2_v1"
    return out


def apply_motion_clip_paths_to_manifest(asset_manifest: Dict[str, Any], motion_manifest: Dict[str, Any]) -> Dict[str, Any]:
    man = dict(asset_manifest or {})
    assets = man.get("assets")
    if not isinstance(assets, list):
        return man
    clips = motion_manifest.get("clips") if isinstance(motion_manifest, dict) else None
    if not isinstance(clips, list):
        return man

    by_scene: Dict[int, Dict[str, Any]] = {}
    for c in clips:
        if not isinstance(c, dict):
            continue
        try:
            sn = int(c.get("scene_number") or 0)
        except Exception:
            continue
        if sn >= 1:
            by_scene[sn] = c

    out_assets: List[Dict[str, Any]] = []
    for a in assets:
        if not isinstance(a, dict):
            continue
        row = dict(a)
        sn = int(row.get("scene_number") or row.get("scene_index") or 0) or 0
        c = by_scene.get(sn)
        if c and _s(c.get("clip_path")):
            row["video_path"] = row.get("video_path") or c.get("clip_path")
        out_assets.append(row)

    man["assets"] = out_assets
    return man

