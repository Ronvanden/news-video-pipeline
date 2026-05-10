"""BA 32.66 — Bounded Runway Motion-Slots → Asset-Manifest (max. 2 Slots pro Lauf)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.production_connectors.runway_video_connector import (
    RunwaySmokeRunner,
    run_runway_motion_clip_live,
)
from app.real_video_build.motion_slot_planner import build_motion_slots

_DEFAULT_VIDEO_PROMPT_FALLBACK = (
    "cinematic documentary video clip, realistic, grounded, natural light"
)


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def scenes_and_total_from_asset_manifest(manifest: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
    raw = manifest.get("assets") or []
    rows = [x for x in raw if isinstance(x, dict)]
    rows.sort(key=lambda x: int(x.get("scene_number") or 0))
    t = 0.0
    scenes: List[Dict[str, Any]] = []
    for a in rows:
        sn = int(a.get("scene_number") or len(scenes) + 1)
        d = a.get("duration_seconds")
        if d is None:
            d = a.get("estimated_duration_seconds")
        try:
            di = max(1, int(d)) if d is not None else 6
        except (TypeError, ValueError):
            di = 6
        st = t
        en = t + float(di)
        scenes.append(
            {
                "scene_number": sn,
                "start_time": round(st, 3),
                "end_time": round(en, 3),
                "duration_seconds": di,
            }
        )
        t = en
    total_i = int(round(t))
    return scenes, total_i


def visual_prompt_for_scene_from_pack(pack: Dict[str, Any], scene_number: int) -> str:
    se = pack.get("scene_expansion") if isinstance(pack.get("scene_expansion"), dict) else {}
    beats = se.get("expanded_scene_assets") or []
    if not isinstance(beats, list):
        return ""
    idx = max(0, int(scene_number) - 1)
    if 0 <= idx < len(beats):
        b = beats[idx]
        if isinstance(b, dict):
            for k in ("visual_prompt_effective", "visual_prompt", "narration", "voiceover_text"):
                s = str(b.get(k) or "").strip()
                if s:
                    return s
    return ""


def apply_first_runway_motion_slot_to_manifest(
    *,
    manifest_path: Path,
    pack_path: Path,
    run_id: str,
    motion_clip_every_seconds: int,
    motion_clip_duration_seconds: int,
    max_motion_clips: int,
    smoke_runner: Optional[RunwaySmokeRunner] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any], List[str]]:
    """
    Plant Motion-Slots (wie BA 32.62), versucht höchstens **zwei** Runway-Clips.

    Kompatibilität/Safety:
    - ``max_motion_clips=0`` plant keine Slots und führt keine Provider-Calls aus.
    - ``max_motion_clips=1`` bleibt der bisherige First-Slot-Smoke.
    - ``max_motion_clips>=2`` ist in BA 32.66 bewusst auf zwei Slots pro Lauf begrenzt.

    Schreibt ``asset_manifest.json`` bei Erfolg neu (video_path + Metadaten je Szene).
    """
    extra: List[str] = []
    artifact: Dict[str, Any] = {
        "planned_count": 0,
        "attempted_count": 0,
        "rendered_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "max_render_attempts": 0,
        "video_clip_paths": [],
        "slot_results": [],
        "warnings": [],
    }

    man = _load_json(Path(manifest_path))
    if not man:
        extra.append("runway_motion_manifest_unreadable")
        plan_off: Dict[str, Any] = {
            "enabled": False,
            "motion_clip_every_seconds": int(motion_clip_every_seconds),
            "motion_clip_duration_seconds": int(motion_clip_duration_seconds),
            "max_motion_clips": int(max_motion_clips),
            "planned_count": 0,
            "slots": [],
        }
        return plan_off, artifact, extra

    pack = _load_json(Path(pack_path)) or {}

    scenes, total = scenes_and_total_from_asset_manifest(man)
    plan, pw = build_motion_slots(
        scenes,
        total,
        motion_clip_every_seconds=motion_clip_every_seconds,
        motion_clip_duration_seconds=motion_clip_duration_seconds,
        max_motion_clips=max_motion_clips,
    )
    extra.extend(pw)
    artifact["planned_count"] = int(plan.get("planned_count") or 0)

    slots = list(plan.get("slots") or [])
    if not plan.get("enabled") or not slots:
        return plan, artifact, extra

    max_attempts = max(0, min(2, int(max_motion_clips), len(slots)))
    artifact["max_render_attempts"] = max_attempts
    if int(max_motion_clips) > 2:
        extra.append("runway_motion_clips_capped_at_2")

    target_indexes = list(range(max_attempts))
    if not smoke_runner and not (os.environ.get("RUNWAY_API_KEY") or "").strip():
        for idx in target_indexes:
            slot = dict(slots[idx])
            slot["status"] = "skipped"
            slots[idx] = slot
            artifact["slot_results"].append(
                {
                    "slot_index": int(slot.get("slot_index") or idx + 1),
                    "scene_number": int(slot.get("scene_number") or 0),
                    "status": "skipped",
                    "reason": "runway_key_missing_motion_skipped",
                }
            )
        plan["slots"] = slots
        artifact["skipped_count"] = len(target_indexes)
        extra.append("runway_key_missing_motion_skipped")
        return plan, artifact, extra

    assets = man.get("assets") or []
    gen_dir = Path(manifest_path).resolve().parent
    rendered_paths: List[str] = []
    warnings_seen: List[str] = []
    processed_scene_numbers: set[int] = set()
    manifest_dirty = False

    for idx in target_indexes:
        slot = dict(slots[idx])
        slot_idx = int(slot.get("slot_index") or idx + 1)
        sn = int(slot.get("scene_number") or 1)

        if sn in processed_scene_numbers:
            slot["status"] = "skipped"
            slots[idx] = slot
            artifact["skipped_count"] = int(artifact["skipped_count"] or 0) + 1
            artifact["slot_results"].append(
                {
                    "slot_index": slot_idx,
                    "scene_number": sn,
                    "status": "skipped",
                    "reason": "runway_motion_duplicate_scene_skipped",
                }
            )
            extra.append("runway_motion_duplicate_scene_skipped")
            continue

        row: Optional[Dict[str, Any]] = None
        for a in assets:
            if isinstance(a, dict) and int(a.get("scene_number") or 0) == sn:
                row = a
                break
        if row is None:
            slot["status"] = "failed"
            slots[idx] = slot
            artifact["failed_count"] = int(artifact["failed_count"] or 0) + 1
            artifact["slot_results"].append(
                {
                    "slot_index": slot_idx,
                    "scene_number": sn,
                    "status": "failed",
                    "reason": "asset_row_missing",
                }
            )
            extra.append("runway_video_generation_failed:asset_row_missing")
            continue

        img_rel = str(row.get("image_path") or "").strip()
        if not img_rel:
            slot["status"] = "failed"
            slots[idx] = slot
            artifact["failed_count"] = int(artifact["failed_count"] or 0) + 1
            artifact["slot_results"].append(
                {
                    "slot_index": slot_idx,
                    "scene_number": sn,
                    "status": "failed",
                    "reason": "image_path_missing",
                }
            )
            extra.append("runway_video_generation_failed:image_path_missing")
            continue

        vp = visual_prompt_for_scene_from_pack(pack, sn).strip() or _DEFAULT_VIDEO_PROMPT_FALLBACK
        img_abs = gen_dir / img_rel
        clip_name = f"scene_{sn:03d}_motion.mp4" if slot_idx == 1 else f"scene_{sn:03d}_motion_s{slot_idx:03d}.mp4"
        clip_abs = gen_dir / clip_name
        dur = int(slot.get("duration_seconds") or motion_clip_duration_seconds)
        rid = f"{(run_id or '').strip() or 'run'}_ms{slot_idx}"

        artifact["attempted_count"] = int(artifact["attempted_count"] or 0) + 1
        res = run_runway_motion_clip_live(
            prompt=vp,
            duration_seconds=max(5, min(10, dur)),
            image_path=img_abs,
            output_path=clip_abs,
            run_id=rid,
            smoke_runner=smoke_runner,
        )

        for w in res.warnings:
            sw = str(w or "").strip()
            if sw and sw not in extra:
                extra.append(sw)
            if sw and sw not in warnings_seen:
                warnings_seen.append(sw)

        if not res.ok:
            slot["status"] = "failed"
            slots[idx] = slot
            artifact["failed_count"] = int(artifact["failed_count"] or 0) + 1
            reason = (res.safe_failure_reason or "unknown")[:80]
            processed_scene_numbers.add(sn)
            artifact["slot_results"].append(
                {
                    "slot_index": slot_idx,
                    "scene_number": sn,
                    "status": "failed",
                    "reason": reason,
                }
            )
            if not any("runway_video_generation_failed" in x for x in extra):
                extra.append(f"runway_video_generation_failed:{reason}")
            continue

        row["video_path"] = clip_name
        row["generation_mode"] = res.generation_mode
        row["provider_used"] = res.provider_used
        row["motion_slot_index"] = slot_idx
        try:
            drow = row.get("duration_seconds")
            if drow is None:
                drow = row.get("estimated_duration_seconds")
            scene_total_i = max(1, int(drow)) if drow is not None else 0
        except (TypeError, ValueError):
            scene_total_i = 0
        if scene_total_i <= 0:
            scene_total_i = max(1, int(slot.get("duration_seconds") or motion_clip_duration_seconds))
        slot_play = int(slot.get("duration_seconds") or motion_clip_duration_seconds)
        playback = max(1, min(slot_play, scene_total_i))
        rest = max(0, scene_total_i - playback)
        row["motion_clip_playback_seconds"] = playback
        row["motion_clip_rest_image_seconds"] = rest
        row["motion_clip_window_respected"] = True

        slot["status"] = "rendered"
        slots[idx] = slot
        processed_scene_numbers.add(sn)
        rendered_paths.append(clip_name)
        artifact["rendered_count"] = int(artifact["rendered_count"] or 0) + 1
        artifact["slot_results"].append(
            {
                "slot_index": slot_idx,
                "scene_number": sn,
                "status": "rendered",
                "video_path": clip_name,
            }
        )
        manifest_dirty = True

    plan["slots"] = slots
    artifact["video_clip_paths"] = rendered_paths
    artifact["warnings"] = warnings_seen

    if manifest_dirty:
        try:
            Path(manifest_path).write_text(
                json.dumps(man, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            reason = type(exc).__name__
            artifact["failed_count"] = int(artifact["failed_count"] or 0) + int(artifact["rendered_count"] or 0)
            artifact["rendered_count"] = 0
            artifact["video_clip_paths"] = []
            extra.append(f"runway_video_generation_failed:{reason}")

    return plan, artifact, extra
