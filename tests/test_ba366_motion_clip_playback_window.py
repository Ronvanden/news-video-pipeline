"""BA 32.66 — Motion-Clip nur im Slot-Fenster; kein Loop über volle Szenenlänge."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_RENDER = _ROOT / "scripts" / "render_final_story_video.py"
_spec = importlib.util.spec_from_file_location("render_final_story_video_ba366", _RENDER)
assert _spec and _spec.loader
_render_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_render_mod)

expand = _render_mod.expand_timeline_scenes_for_motion_clip_windows


def _scene_video(
    *,
    sn: int,
    dur: int,
    pb: int,
    image: str = "s.png",
) -> dict:
    return {
        "scene_number": sn,
        "duration_seconds": dur,
        "media_type": "video",
        "video_path": "clip.mp4",
        "image_path": image,
        "motion_clip_playback_seconds": pb,
        "motion_clip_rest_image_seconds": max(0, dur - pb),
        "motion_clip_window_respected": True,
    }


def test_expand_26s_scene_10s_clip_splits_video_then_image():
    sc = [_scene_video(sn=1, dur=26, pb=10)]
    kinds = ["video"]
    w: list[str] = []
    out, kinds_out = expand(sc, kinds, w)
    assert kinds_out == ["video", "image"]
    assert len(out) == 2
    assert out[0]["duration_seconds"] == 10
    assert out[0].get("motion_video_single_decode") is True
    assert out[0].get("video_path")
    assert out[1]["duration_seconds"] == 16
    assert out[1].get("media_type") == "image"
    assert not str(out[1].get("video_path") or "").strip()
    assert sum(s["duration_seconds"] for s in out) == 26


def test_expand_8s_scene_10s_clip_single_video_segment():
    sc = [_scene_video(sn=1, dur=8, pb=10)]
    kinds = ["video"]
    w: list[str] = []
    out, kinds_out = expand(sc, kinds, w)
    assert kinds_out == ["video"]
    assert len(out) == 1
    assert out[0]["duration_seconds"] == 8
    assert out[0].get("motion_video_single_decode") is True
    assert float(out[0].get("_motion_video_decode_seconds") or 0) <= 8


def test_expand_no_image_path_long_rest_warns_and_freeze_pad():
    sc = [
        {
            "scene_number": 1,
            "duration_seconds": 26,
            "media_type": "video",
            "video_path": "c.mp4",
            "image_path": "",
            "motion_clip_playback_seconds": 10,
        }
    ]
    kinds = ["video"]
    w: list[str] = []
    out, kinds_out = expand(sc, kinds, w)
    assert kinds_out == ["video"]
    assert len(out) == 1
    assert out[0]["duration_seconds"] == 26
    assert float(out[0].get("_motion_video_freeze_pad_seconds") or 0) == pytest.approx(16.0)
    assert any("motion_clip_rest_no_image_fallback" in x for x in w)


def test_expand_without_playback_field_pass_through():
    sc = [
        {
            "scene_number": 1,
            "duration_seconds": 60,
            "media_type": "video",
            "video_path": "long.mp4",
            "image_path": "x.png",
        }
    ]
    kinds = ["video"]
    w: list[str] = []
    out, kinds_out = expand(sc, kinds, w)
    assert len(out) == 1 and kinds_out == ["video"]
    assert out[0].get("motion_clip_playback_seconds") is None
    assert out[0].get("motion_video_single_decode") is None


def test_build_timeline_copies_motion_clip_fields(tmp_path):
    build_path = _ROOT / "scripts" / "build_timeline_manifest.py"
    spec = importlib.util.spec_from_file_location("build_timeline_manifest_ba366", build_path)
    assert spec and spec.loader
    bmod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bmod)

    assets_dir = tmp_path / "a"
    assets_dir.mkdir()
    (assets_dir / "i.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (assets_dir / "v.mp4").write_bytes(b"not real mp4")

    man = {
        "run_id": "r1",
        "assets": [
            {
                "scene_number": 1,
                "image_path": "i.png",
                "video_path": "v.mp4",
                "duration_seconds": 20,
                "motion_clip_playback_seconds": 10,
                "motion_clip_rest_image_seconds": 10,
                "motion_clip_window_respected": True,
            }
        ],
    }
    mp = tmp_path / "asset_manifest.json"
    mp.write_text(__import__("json").dumps(man), encoding="utf-8")
    tl = bmod.build_timeline_manifest_data(
        man,
        asset_manifest_path=mp,
        audio_path=None,
        run_id="r1",
        scene_duration_seconds=6,
    )
    row = tl["scenes"][0]
    assert row.get("motion_clip_playback_seconds") == 10
    assert row.get("motion_clip_rest_image_seconds") == 10
    assert row.get("motion_clip_window_respected") is True
