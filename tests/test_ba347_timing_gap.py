"""BA 32.48 — Timing Gap Helper (unit-ish, ohne Provider)."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_ba265_mod():
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "run_url_to_final_mp4.py"
    spec = importlib.util.spec_from_file_location("run_url_to_final_ba347", script)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_compute_timing_gap_ok_minor_major_unknown_and_fallback():
    m = _load_ba265_mod()

    g = m._compute_timing_gap(voice_duration_seconds=10.0, timeline_duration_seconds=10.5, final_video_duration_seconds=None)
    assert g["timing_gap_abs_seconds"] == 0.5
    assert g["timing_gap_status"] == "ok"

    g = m._compute_timing_gap(voice_duration_seconds=10.0, timeline_duration_seconds=13.0, final_video_duration_seconds=None)
    assert g["timing_gap_abs_seconds"] == 3.0
    assert g["timing_gap_status"] == "minor_gap"

    g = m._compute_timing_gap(voice_duration_seconds=10.0, timeline_duration_seconds=18.0, final_video_duration_seconds=None)
    assert g["timing_gap_abs_seconds"] == 8.0
    assert g["timing_gap_status"] == "major_gap"

    g = m._compute_timing_gap(voice_duration_seconds=None, timeline_duration_seconds=10.0, final_video_duration_seconds=None)
    assert g["timing_gap_abs_seconds"] is None
    assert g["timing_gap_status"] == "unknown"

    # fallback: timeline missing -> use final video duration vs voice
    g = m._compute_timing_gap(voice_duration_seconds=10.0, timeline_duration_seconds=None, final_video_duration_seconds=13.0)
    assert g["timing_gap_abs_seconds"] == 3.0
    assert g["timing_gap_status"] == "minor_gap"

