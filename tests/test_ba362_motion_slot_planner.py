"""BA 32.62 — Motion-Slot-Planer (nur Planung, kein Provider)."""

from __future__ import annotations

import unittest

from app.real_video_build.motion_slot_planner import build_motion_slots


def _scenes_uniform(total: int, n: int) -> list:
    """``n`` aneinandergereihte Szenen mit ganzzahliger Dauer, Summe ``total``."""
    base = total // n
    rem = total % n
    scenes = []
    t = 0.0
    for i in range(n):
        d = base + (1 if i < rem else 0)
        st = t
        en = t + d
        scenes.append(
            {
                "scene_number": i + 1,
                "start_time": round(st, 3),
                "end_time": round(en, 3),
                "duration_seconds": d,
            }
        )
        t = en
    return scenes


class MotionSlotPlannerTests(unittest.TestCase):
    def test_eight_minutes_eight_slots(self):
        scenes = _scenes_uniform(480, 8)
        plan, w = build_motion_slots(
            scenes,
            480,
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=8,
        )
        self.assertEqual(w, [])
        self.assertTrue(plan["enabled"])
        self.assertEqual(plan["planned_count"], 8)
        self.assertEqual(len(plan["slots"]), 8)
        self.assertEqual(plan["slots"][0]["at_second"], 0)
        self.assertEqual(plan["slots"][-1]["at_second"], 420)
        for s in plan["slots"]:
            self.assertEqual(s["duration_seconds"], 10)
            self.assertEqual(s["status"], "planned")

    def test_ten_minutes_ten_slots(self):
        scenes = _scenes_uniform(600, 10)
        plan, w = build_motion_slots(
            scenes,
            600,
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=10,
        )
        self.assertEqual(w, [])
        self.assertEqual(plan["planned_count"], 10)

    def test_twelve_minutes_twelve_slots(self):
        scenes = _scenes_uniform(720, 12)
        plan, w = build_motion_slots(
            scenes,
            720,
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=12,
        )
        self.assertEqual(w, [])
        self.assertEqual(plan["planned_count"], 12)

    def test_max_zero_disabled(self):
        scenes = _scenes_uniform(120, 2)
        plan, w = build_motion_slots(
            scenes,
            120,
            max_motion_clips=0,
        )
        self.assertFalse(plan["enabled"])
        self.assertEqual(plan["planned_count"], 0)
        self.assertEqual(plan["slots"], [])
        self.assertEqual(w, [])

    def test_invalid_interval_no_slots(self):
        scenes = _scenes_uniform(120, 2)
        plan, w = build_motion_slots(
            scenes,
            120,
            motion_clip_every_seconds=0,
            max_motion_clips=5,
        )
        self.assertFalse(plan["enabled"])
        self.assertTrue(any("motion_slot_plan_invalid_interval_or_duration" in x for x in w))

    def test_short_remainder_truncates_duration(self):
        scenes = [
            {"scene_number": 1, "start_time": 0.0, "end_time": 65.0, "duration_seconds": 65},
        ]
        plan, w = build_motion_slots(
            scenes,
            65,
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=10,
        )
        self.assertEqual(plan["planned_count"], 2)
        self.assertEqual(plan["slots"][0]["duration_seconds"], 10)
        self.assertEqual(plan["slots"][1]["at_second"], 60)
        self.assertEqual(plan["slots"][1]["duration_seconds"], 5)

    def test_empty_scenes_no_crash(self):
        plan, w = build_motion_slots(
            [],
            120,
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=4,
        )
        self.assertFalse(plan["enabled"])
        self.assertEqual(plan["planned_count"], 0)
        self.assertTrue(any("motion_slot_plan_no_timeline_scenes" in x for x in w))

    def test_scene_assignment_second_segment(self):
        scenes = [
            {"scene_number": 1, "start_time": 0.0, "end_time": 30.0, "duration_seconds": 30},
            {"scene_number": 2, "start_time": 30.0, "end_time": 60.0, "duration_seconds": 30},
        ]
        plan, _ = build_motion_slots(
            scenes,
            60,
            motion_clip_every_seconds=45,
            motion_clip_duration_seconds=10,
            max_motion_clips=2,
        )
        self.assertEqual(plan["slots"][0]["scene_number"], 1)
        self.assertEqual(plan["slots"][1]["scene_number"], 2)
        self.assertEqual(plan["slots"][1]["at_second"], 45)

    def test_fit_to_voice_total_used_not_requested_duration(self):
        """Simuliert gekürzte Timeline (z. B. 119 s nach Fit-to-Voice) — nur zwei Slots bei every=60."""
        scenes = [
            {
                "scene_number": 1,
                "start_time": 0.0,
                "end_time": 119.0,
                "duration_seconds": 119,
            },
        ]
        plan, w = build_motion_slots(
            scenes,
            119,
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=10,
        )
        self.assertEqual(w, [])
        self.assertEqual(plan["planned_count"], 2)
        self.assertEqual(plan["slots"][1]["at_second"], 60)


if __name__ == "__main__":
    unittest.main()
