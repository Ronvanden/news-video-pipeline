"""BA 32.63 — Erster Motion-Slot → Runway-Clip → Asset-Manifest (max. 1 Slot pro Lauf)."""

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
    Plant Motion-Slots (wie BA 32.62), versucht höchstens **einen** Runway-Clip für Slot 1.

    Schreibt ``asset_manifest.json`` bei Erfolg neu (video_path + Metadaten für die Szene).
    """
    extra: List[str] = []
    artifact: Dict[str, Any] = {
        "planned_count": 0,
        "rendered_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "video_clip_paths": [],
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

    # Nur erster Slot (Smoke / minimaler Hybrid).
    slot0 = dict(slots[0])
    slot_idx = int(slot0.get("slot_index") or 1)
    sn = int(slot0.get("scene_number") or 1)

    if not smoke_runner and not (os.environ.get("RUNWAY_API_KEY") or "").strip():
        slot0["status"] = "skipped"
        slots[0] = slot0
        plan["slots"] = slots
        artifact["skipped_count"] = 1
        extra.append("runway_key_missing_motion_skipped")
        return plan, artifact, extra

    vp = visual_prompt_for_scene_from_pack(pack, sn).strip()
    if not vp:
        vp = _DEFAULT_VIDEO_PROMPT_FALLBACK

    assets = man.get("assets") or []
    row: Optional[Dict[str, Any]] = None
    for a in assets:
        if isinstance(a, dict) and int(a.get("scene_number") or 0) == sn:
            row = a
            break
    gen_dir = Path(manifest_path).resolve().parent
    if row is None:
        slot0["status"] = "failed"
        slots[0] = slot0
        plan["slots"] = slots
        artifact["failed_count"] = 1
        extra.append("runway_video_generation_failed:asset_row_missing")
        return plan, artifact, extra

    img_rel = str(row.get("image_path") or "").strip()
    if not img_rel:
        slot0["status"] = "failed"
        slots[0] = slot0
        plan["slots"] = slots
        artifact["failed_count"] = 1
        extra.append("runway_video_generation_failed:image_path_missing")
        return plan, artifact, extra

    img_abs = gen_dir / img_rel
    clip_name = f"scene_{sn:03d}_motion.mp4"
    clip_abs = gen_dir / clip_name

    dur = int(slot0.get("duration_seconds") or motion_clip_duration_seconds)
    rid = f"{(run_id or '').strip() or 'run'}_ms{slot_idx}"

    res = run_runway_motion_clip_live(
        prompt=vp,
        duration_seconds=max(5, min(10, dur)),
        image_path=img_abs,
        output_path=clip_abs,
        run_id=rid,
        smoke_runner=smoke_runner,
    )

    for w in res.warnings:
        if w and w not in extra:
            extra.append(str(w))
    artifact["warnings"] = [x for x in res.warnings if x]

    if not res.ok:
        slot0["status"] = "failed"
        slots[0] = slot0
        plan["slots"] = slots
        artifact["failed_count"] = 1
        if not any("runway_video_generation_failed" in x for x in extra):
            extra.append(
                f"runway_video_generation_failed:{(res.safe_failure_reason or 'unknown')[:80]}"
            )
        return plan, artifact, extra

    row["video_path"] = clip_name
    row["generation_mode"] = res.generation_mode
    row["provider_used"] = res.provider_used
    row["motion_slot_index"] = slot_idx
    # Timeline bevorzugt video wenn Datei existiert; image_path als Fallback beibehalten.
    # BA 32.66: Render nutzt Playback-Fenster (kein Loop über die volle Szenenlänge).
    try:
        drow = row.get("duration_seconds")
        if drow is None:
            drow = row.get("estimated_duration_seconds")
        scene_total_i = max(1, int(drow)) if drow is not None else 0
    except (TypeError, ValueError):
        scene_total_i = 0
    if scene_total_i <= 0:
        scene_total_i = max(1, int(slot0.get("duration_seconds") or motion_clip_duration_seconds))
    slot_play = int(slot0.get("duration_seconds") or motion_clip_duration_seconds)
    playback = max(1, min(slot_play, scene_total_i))
    rest = max(0, scene_total_i - playback)
    row["motion_clip_playback_seconds"] = playback
    row["motion_clip_rest_image_seconds"] = rest
    row["motion_clip_window_respected"] = True

    try:
        Path(manifest_path).write_text(
            json.dumps(man, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        slot0["status"] = "failed"
        slots[0] = slot0
        plan["slots"] = slots
        artifact["failed_count"] = 1
        extra.append(f"runway_video_generation_failed:{type(exc).__name__}")
        return plan, artifact, extra

    slot0["status"] = "rendered"
    slots[0] = slot0
    plan["slots"] = slots
    artifact["rendered_count"] = 1
    artifact["video_clip_paths"] = [clip_name]
    return plan, artifact, extra
