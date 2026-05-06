"""BA 28.3 — Build a motion timeline manifest from voice + clip paths (no render)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


def _s(v: Any) -> str:
    return str(v or "").strip()


def _float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def build_motion_timeline_manifest(
    *,
    run_id: str,
    scenes: List[Dict[str, Any]],
    default_duration_seconds: int = 5,
) -> Dict[str, Any]:
    out_scenes: List[Dict[str, Any]] = []
    t = 0.0
    warnings: List[str] = []
    missing_voice = 0
    missing_clip = 0

    for sc in scenes or []:
        if not isinstance(sc, dict):
            continue
        sn = int(sc.get("scene_number") or sc.get("scene_index") or 0) or 0
        voice_path = _s(sc.get("voice_path"))
        clip_path = _s(sc.get("clip_path") or sc.get("video_path"))
        image_path = _s(sc.get("image_path") or sc.get("selected_asset_path") or sc.get("generated_image_path"))

        dur = _float(sc.get("duration_seconds") or sc.get("voice_duration_seconds") or sc.get("clip_duration_seconds"))
        if dur <= 0:
            dur = float(default_duration_seconds)
        start = t
        end = t + dur
        t = end

        status = "aligned"
        if not voice_path:
            missing_voice += 1
            status = "missing_voice"
        if not clip_path:
            missing_clip += 1
            status = "missing_clip" if status == "aligned" else status
        if status != "aligned":
            warnings.append(f"scene_{sn}:{status}")

        out_scenes.append(
            {
                "scene_number": int(sn or len(out_scenes) + 1),
                "start_seconds": float(start),
                "end_seconds": float(end),
                "duration_seconds": float(dur),
                "voice_path": voice_path or None,
                "clip_path": clip_path or None,
                "image_path": image_path or None,
                "subtitle_text": _s(sc.get("subtitle_text")) or None,
                "alignment_status": status,
            }
        )

    return {
        "timeline_version": "ba28_3_v1",
        "run_id": _s(run_id),
        "scenes": out_scenes,
        "total_duration_seconds": float(t),
        "warnings": list(dict.fromkeys([_s(w) for w in warnings if _s(w)])),
        "counts": {"missing_voice": int(missing_voice), "missing_clip": int(missing_clip)},
    }

