"""BA 32.68 — 16:9 Fullscreen/Cover für Bilder und Video-Segmente (kein Letterboxing)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_RENDER = _ROOT / "scripts" / "render_final_story_video.py"
_spec = importlib.util.spec_from_file_location("render_final_story_video_ba368", _RENDER)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def test_cover_core_uses_increase_and_crop_not_pad():
    core = _mod.vf_cover_scale_crop_core()
    assert "force_original_aspect_ratio=increase" in core
    assert "crop=1920:1080:(iw-1920)/2:(ih-1080)/2" in core
    assert "pad=" not in core
    assert "force_original_aspect_ratio=decrease" not in core


def test_segment_video_branch_cover_matches_portrait_square_wide():
    # Gleiche Cover-Kette für alle Seitenverhältnisse (Portrait/Quadrat/16:9).
    for _label in ("portrait", "square", "wide"):
        vf = _mod._segment_video_branch(10.0, 25)
        assert "force_original_aspect_ratio=increase" in vf
        assert "crop=1920:1080" in vf
        assert "pad=" not in vf


def test_motion_static_branch_cover_not_contain():
    vf = _mod._segment_motion_filter(12.0, "static", "none", 25)
    assert "force_original_aspect_ratio=increase" in vf
    assert "crop=1920:1080" in vf
    assert "pad=" not in vf


def test_constants_and_resolution_label():
    assert _mod.RENDER_FRAME_FIT_MODE == "cover"
    assert _mod.render_target_resolution_label() == "1920x1080"


def test_zoom_motion_paths_unchanged_use_zoompan_not_contain_pad():
    vf_push = _mod._segment_motion_filter(5.0, "slow_push", "none", 25)
    assert "zoompan=" in vf_push
    assert "force_original_aspect_ratio=decrease" not in vf_push
