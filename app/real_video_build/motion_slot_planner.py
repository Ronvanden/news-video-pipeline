"""BA 32.62 — Motion-Slot-Planung für Hybrid-Videos (nur Planung, kein Runway/Provider)."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple


def _sorted_timeline_scenes(
    timeline_scenes: Optional[Sequence[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    if not timeline_scenes:
        return []
    rows = [x for x in timeline_scenes if isinstance(x, dict)]
    try:
        return sorted(rows, key=lambda s: float(s.get("start_time", 0.0)))
    except (TypeError, ValueError):
        return rows


def _pick_scene_for_instant(
    scenes: Sequence[Dict[str, Any]], at_second: float
) -> Optional[Dict[str, Any]]:
    """Szene, die ``at_second`` enthält; sonst nächste mit end > at; sonst letzte."""
    if not scenes:
        return None
    t = float(at_second)
    for sc in scenes:
        try:
            st = float(sc.get("start_time", 0.0))
            en = float(sc.get("end_time", st))
        except (TypeError, ValueError):
            continue
        if st <= t < en:
            return sc
    for sc in scenes:
        try:
            en = float(sc.get("end_time", 0.0))
        except (TypeError, ValueError):
            continue
        if t < en:
            return sc
    return scenes[-1]


def build_motion_slots(
    timeline_scenes: Optional[Sequence[Dict[str, Any]]],
    total_duration_seconds: float | int | None,
    *,
    motion_clip_every_seconds: int = 60,
    motion_clip_duration_seconds: int = 10,
    max_motion_clips: int = 10,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Plant zeitliche Motion-Clip-Slots auf einer fertigen Timeline (z. B. nach Fit-to-Voice).

    Rückgabe: ``(motion_slot_plan, warnings)``. Alle Slots haben ``status``/``source`` ``planned``.
    """
    warnings: List[str] = []
    every = int(motion_clip_every_seconds)
    clip_req = int(motion_clip_duration_seconds)
    max_c = int(max_motion_clips)

    plan: Dict[str, Any] = {
        "enabled": False,
        "motion_clip_every_seconds": every,
        "motion_clip_duration_seconds": clip_req,
        "max_motion_clips": max_c,
        "planned_count": 0,
        "slots": [],
    }

    if max_c <= 0:
        return plan, warnings

    if every <= 0 or clip_req <= 0:
        warnings.append("motion_slot_plan_invalid_interval_or_duration")
        return plan, warnings

    try:
        td = float(total_duration_seconds) if total_duration_seconds is not None else 0.0
    except (TypeError, ValueError):
        td = 0.0
    if td <= 0:
        warnings.append("motion_slot_plan_no_positive_total_duration")
        return plan, warnings

    scenes = _sorted_timeline_scenes(timeline_scenes)
    if not scenes:
        warnings.append("motion_slot_plan_no_timeline_scenes")
        return plan, warnings

    plan["enabled"] = True

    slot_times: List[float] = []
    t_at = 0.0
    while len(slot_times) < max_c and t_at < td:
        slot_times.append(t_at)
        t_at += float(every)

    slots_out: List[Dict[str, Any]] = []
    slot_index = 1
    for at_sec in slot_times:
        sc = _pick_scene_for_instant(scenes, at_sec)
        if sc is None:
            warnings.append("motion_slot_no_scene_for_timestamp")
            continue
        try:
            scene_end = float(sc.get("end_time", 0.0))
        except (TypeError, ValueError):
            scene_end = at_sec
        rem_video = td - at_sec
        rem_scene = scene_end - at_sec
        try:
            dur_f = min(float(clip_req), float(rem_video), float(rem_scene))
        except (TypeError, ValueError):
            dur_f = 0.0
        dur_i = int(math.floor(dur_f))
        if dur_i < 1:
            warnings.append("motion_slot_skipped_short_remainder")
            continue
        try:
            sn = int(sc.get("scene_number") or 0)
        except (TypeError, ValueError):
            sn = 0
        if sn < 1:
            sn = slot_index
        start_i = int(math.floor(float(at_sec)))
        slots_out.append(
            {
                "slot_index": slot_index,
                "at_second": start_i,
                "scene_number": sn,
                "start_second": start_i,
                "duration_seconds": dur_i,
                "source": "planned",
                "status": "planned",
            }
        )
        slot_index += 1

    plan["slots"] = slots_out
    plan["planned_count"] = len(slots_out)
    return plan, warnings
