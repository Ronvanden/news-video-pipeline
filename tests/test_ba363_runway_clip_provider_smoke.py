"""BA 32.63 — Runway Motion-Slot → Manifest (Mocks, keine Live-Calls)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from app.founder_dashboard.ba323_video_generate import derive_motion_readiness_fields
from app.real_video_build.runway_motion_integration import apply_first_runway_motion_slot_to_manifest


def _fake_smoke_ok(**kwargs: object) -> dict:
    out_root = Path(str(kwargs["out_root"]))
    rid = str(kwargs["run_id"])
    dest = out_root / f"runway_smoke_{rid}" / "runway_clip.mp4"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom")
    return {
        "ok": True,
        "output_video_path": str(dest),
        "warnings": [],
        "blocking_reasons": [],
    }


def _fake_smoke_fail(**kwargs: object) -> dict:
    return {
        "ok": False,
        "output_video_path": "",
        "warnings": [],
        "blocking_reasons": ["task_failed"],
    }


def _write_fixtures(gen_dir: Path) -> None:
    gen_dir.mkdir(parents=True, exist_ok=True)
    img = gen_dir / "scene_001.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    man = {
        "assets": [
            {
                "scene_number": 1,
                "chapter_index": 0,
                "beat_index": 0,
                "image_path": "scene_001.png",
                "duration_seconds": 120,
                "estimated_duration_seconds": 120,
                "generation_mode": "test_image",
            }
        ]
    }
    (gen_dir / "asset_manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    pack = {
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "visual_prompt": "city skyline at dusk, documentary",
                    "chapter_index": 0,
                    "beat_index": 0,
                }
            ]
        }
    }
    (gen_dir / "scene_asset_pack.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")


def test_runway_key_missing_skips_without_crash(tmp_path: Path):
    gen = tmp_path / "gen"
    _write_fixtures(gen)
    with patch.dict(os.environ, {"RUNWAY_API_KEY": ""}, clear=False):
        plan, art, extra = apply_first_runway_motion_slot_to_manifest(
            manifest_path=gen / "asset_manifest.json",
            pack_path=gen / "scene_asset_pack.json",
            run_id="t1",
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=2,
        )
    assert plan.get("enabled")
    assert "runway_key_missing_motion_skipped" in extra
    assert art["skipped_count"] == 1
    assert art["rendered_count"] == 0
    assert plan["slots"][0]["status"] == "skipped"


def test_ba3264_readiness_derived_after_successful_slot(tmp_path: Path):
    gen = tmp_path / "gen"
    _write_fixtures(gen)
    with patch.dict(os.environ, {"RUNWAY_API_KEY": ""}, clear=False):
        plan, art, _ = apply_first_runway_motion_slot_to_manifest(
            manifest_path=gen / "asset_manifest.json",
            pack_path=gen / "scene_asset_pack.json",
            run_id="t_rd",
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=2,
            smoke_runner=_fake_smoke_ok,
        )
    man = json.loads((gen / "asset_manifest.json").read_text(encoding="utf-8"))
    modes: dict = {}
    for a in man.get("assets") or []:
        if isinstance(a, dict):
            g = str(a.get("generation_mode") or "").strip().lower()
            if g:
                modes[g] = int(modes.get(g, 0)) + 1
    rd = derive_motion_readiness_fields(
        allow_live_motion=False,
        live_motion_available=False,
        max_motion_clips=2,
        motion_slot_plan=plan,
        motion_clip_artifact=art,
        generation_modes=modes,
    )
    assert rd["motion_rendered"] is True
    assert rd["motion_ready"] is True
    assert rd["motion_requested"] is True


def test_mocked_runway_success_writes_video_path(tmp_path: Path):
    gen = tmp_path / "gen"
    _write_fixtures(gen)
    with patch.dict(os.environ, {"RUNWAY_API_KEY": ""}, clear=False):
        plan, art, extra = apply_first_runway_motion_slot_to_manifest(
            manifest_path=gen / "asset_manifest.json",
            pack_path=gen / "scene_asset_pack.json",
            run_id="t2",
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=2,
            smoke_runner=_fake_smoke_ok,
        )
    assert art["rendered_count"] == 1
    assert art["video_clip_paths"] == ["scene_001_motion.mp4"]
    assert plan["slots"][0]["status"] == "rendered"
    man = json.loads((gen / "asset_manifest.json").read_text(encoding="utf-8"))
    row = man["assets"][0]
    assert row.get("video_path") == "scene_001_motion.mp4"
    assert row.get("generation_mode") == "runway_video_live"
    assert row.get("provider_used") == "runway"
    assert (gen / "scene_001_motion.mp4").is_file()
    assert not any("runway_video_generation_failed" in x for x in extra)


def test_mocked_runway_failure_marks_failed(tmp_path: Path):
    gen = tmp_path / "gen"
    _write_fixtures(gen)
    with patch.dict(os.environ, {"RUNWAY_API_KEY": ""}, clear=False):
        plan, art, extra = apply_first_runway_motion_slot_to_manifest(
            manifest_path=gen / "asset_manifest.json",
            pack_path=gen / "scene_asset_pack.json",
            run_id="t3",
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=2,
            smoke_runner=_fake_smoke_fail,
        )
    assert art["failed_count"] == 1
    assert plan["slots"][0]["status"] == "failed"
    man = json.loads((gen / "asset_manifest.json").read_text(encoding="utf-8"))
    assert "video_path" not in man["assets"][0]
    assert any("runway_video_generation_failed" in x for x in extra)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
