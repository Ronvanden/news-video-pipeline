"""BA 32.46 — Timing Audit / OPEN_ME Section (no providers)."""

from __future__ import annotations

from app.founder_dashboard.ba323_video_generate import build_open_me_video_result_html


def test_open_me_includes_timing_voice_fit_and_summary_text():
    payload = {
        "ok": True,
        "run_id": "x",
        "warnings": ["audio_shorter_than_timeline_padded_or_continued"],
        "blocking_reasons": [],
        "final_video_path": "final.mp4",
        "output_dir": "out",
        "script_path": "script.json",
        "scene_asset_pack_path": "scene_asset_pack.json",
        "asset_manifest_path": "asset_manifest.json",
        "asset_artifact": {"asset_quality_gate": {"status": "production_ready", "strict_ready": True}},
        "voice_artifact": {"effective_voice_mode": "elevenlabs", "voice_ready": True},
        "readiness_audit": {"render_used_placeholders": False},
        "timing_audit": {
            "voice_duration_seconds": 28.93,
            "timeline_duration_seconds": 36.93,
            "final_video_duration_seconds": 36.93,
            "requested_duration_seconds": 600,
            "timeline_minus_voice_seconds": 8.0,
            "timing_gap_abs_seconds": 8.0,
            "timing_gap_status": "major_gap",
            "audio_shorter_than_timeline": True,
            "padding_or_continue_applied": True,
            "fit_strategy": "padded_or_continued",
            "summary": "Voice ist 8.00s kürzer als Timeline. Audio ist kürzer als Timeline; Video wurde gepadded oder fortgeführt.",
        },
    }
    html = build_open_me_video_result_html(payload)
    assert "Timing / Voice Fit" in html
    assert "timing_gap_abs_seconds" in html
    assert "28.93s" in html
    assert "36.93s" in html
    assert "600.00s" in html
    assert "8.00s" in html
    assert "Audio ist kürzer als Timeline" in html

