"""BA 32.80 — Gold-Mini-Run: Status-Normalisierung (strict_ready, Bundle, Motion, Voice)."""

from __future__ import annotations

from app.founder_dashboard.ba323_video_generate import (
    _filter_warnings_for_fallback_join_ba3280,
    build_video_generate_operator_ui_ba3280,
    derive_video_generate_status,
    scrub_video_generate_warnings_ba3280,
)
from app.founder_dashboard.html import get_founder_dashboard_html
from scripts.run_asset_runner import resolve_openai_image_model_for_runner


def _gold_base() -> dict:
    return {
        "ok": True,
        "blocking_reasons": [],
        "final_video_path": "/tmp/final.mp4",
        "readiness_audit": {
            "motion_requested": False,
            "motion_ready": True,
            "allow_live_motion_requested": False,
            "asset_strict_ready": True,
        },
        "voice_artifact": {
            "effective_voice_mode": "elevenlabs",
            "requested_voice_mode": "elevenlabs",
            "is_dummy": False,
            "voice_ready": True,
            "voice_file_path": "/tmp/voice.mp3",
        },
        "asset_artifact": {
            "asset_quality_gate": {"status": "production_ready", "strict_ready": True},
            "real_asset_file_count": 13,
            "asset_manifest_file_count": 13,
        },
        "thumbnail_pack": {"thumbnail_pack_status": "ready"},
        "production_bundle": {
            "production_bundle_status": "ready",
            "bundled_files": [{"label": "OPEN_ME_VIDEO_RESULT", "exists": True}],
        },
    }


def test_strict_ready_benign_elevenlabs_default_warning_is_gold_not_fallback() -> None:
    p = _gold_base()
    p["warnings"] = ["elevenlabs_voice_id_default_fallback", "noise_xyz"]
    assert derive_video_generate_status(p) == "gold_mini_ready"


def test_motion_requested_but_not_ready_is_mixed_not_gold() -> None:
    p = _gold_base()
    p["warnings"] = []
    p["readiness_audit"] = {
        **p["readiness_audit"],
        "motion_requested": True,
        "motion_ready": False,
    }
    assert derive_video_generate_status(p) == "mixed_preview"


def test_voice_none_with_silent_audio_can_be_gold_when_pack_ready() -> None:
    p = _gold_base()
    p["warnings"] = ["audio_missing_silent_render"]
    p["voice_artifact"] = {
        "effective_voice_mode": "none",
        "requested_voice_mode": "none",
        "is_dummy": False,
        "voice_ready": False,
        "voice_file_path": None,
    }
    p["readiness_audit"] = {**p["readiness_audit"], "silent_render_expected": True}
    assert derive_video_generate_status(p) == "gold_mini_ready"


def test_dummy_voice_when_productive_voice_requested_is_mixed() -> None:
    p = _gold_base()
    p["warnings"] = ["ba323_voice_mode_fallback_dummy_no_elevenlabs_key"]
    p["voice_artifact"] = {
        "effective_voice_mode": "dummy",
        "requested_voice_mode": "elevenlabs",
        "is_dummy": True,
        "voice_ready": False,
        "voice_file_path": None,
    }
    assert derive_video_generate_status(p) == "mixed_preview"


def test_scrub_stale_production_bundle_open_me_warning_when_resolved() -> None:
    p = {
        "warnings": ["production_bundle_open_me_source_missing", "keep_me"],
        "production_bundle": {
            "production_bundle_status": "ready",
            "bundled_files": [{"label": "OPEN_ME_VIDEO_RESULT", "exists": True}],
        },
    }
    scrub_video_generate_warnings_ba3280(p)
    assert p["warnings"] == ["keep_me"]


def test_operator_strings_for_gold_mini() -> None:
    p = _gold_base()
    p["warnings"] = []
    op = build_video_generate_operator_ui_ba3280("gold_mini_ready", p)
    assert op["headline"] == "Gold-Mini-Run erstellt"
    assert "Motion-Clips" in op["subline"]


def test_dashboard_openai_mini_preset_still_sets_gpt_image_2() -> None:
    html = get_founder_dashboard_html()
    assert 'oaiModel.value = "gpt-image-2"' in html


def test_green_escape_aligns_manifest_counts_despite_noise_warnings() -> None:
    p = _gold_base()
    p["warnings"] = [
        "runway_key_missing_motion_skipped",
        "openai_image_model:gpt-image-2",
        "elevenlabs_voice_id_default_fallback",
        "audio_missing_silent_render",
    ]
    assert derive_video_generate_status(p) == "gold_mini_ready"


def test_filter_warnings_drop_runway_skipped_when_motion_optional() -> None:
    p = {
        "warnings": ["runway_key_missing_motion_skipped", "kept_code"],
        "readiness_audit": {"motion_requested": False, "allow_live_motion_requested": False},
    }
    assert _filter_warnings_for_fallback_join_ba3280(p) == ["kept_code"]


def test_resolve_openai_image_model_for_runner_pipeline_default() -> None:
    assert resolve_openai_image_model_for_runner("openai_image", None) == "gpt-image-2"
    assert resolve_openai_image_model_for_runner("openai_image", "gpt-image-1") == "gpt-image-1"
    assert resolve_openai_image_model_for_runner("leonardo", None) is None
