"""BA 28.3 — Motion timeline alignment tests."""

from __future__ import annotations

from app.production_assembly.motion_timeline_alignment import build_motion_timeline_manifest


def test_build_timeline_three_scenes_and_missing_counts():
    scenes = [
        {"scene_number": 1, "voice_path": "voice1.mp3", "clip_path": "clip1.mp4", "duration_seconds": 5},
        {"scene_number": 2, "voice_path": "", "clip_path": "clip2.mp4", "duration_seconds": 5},
        {"scene_number": 3, "voice_path": "voice3.mp3", "clip_path": "", "duration_seconds": 5},
    ]
    out = build_motion_timeline_manifest(run_id="r1", scenes=scenes, default_duration_seconds=5)
    assert out["timeline_version"] == "ba28_3_v1"
    assert len(out["scenes"]) == 3
    assert out["counts"]["missing_voice"] == 1
    assert out["counts"]["missing_clip"] == 1

