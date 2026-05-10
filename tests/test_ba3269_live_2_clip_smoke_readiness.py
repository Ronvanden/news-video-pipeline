"""BA 32.69 — live two-clip smoke readiness helper tests (mock/env only)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _import_cli():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "check_live_2_clip_smoke_readiness.py"
    spec = importlib.util.spec_from_file_location("check_live_2_clip_smoke_readiness", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_readiness_blocks_without_required_confirmations_and_keys(monkeypatch):
    mod = _import_cli()
    for name in ("RUNWAY_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "ELEVENLABS_API_KEY", "CI"):
        monkeypatch.delenv(name, raising=False)

    res = mod.build_readiness_summary(
        image_provider="gemini_image",
        voice_provider="elevenlabs",
        duration_minutes=1.0,
        max_scenes=3,
        max_motion_clips=2,
        motion_clip_duration_seconds=10,
        confirm_provider_costs=False,
        ack_live_provider_risk=False,
        ack_not_ci=False,
    )

    assert res["ready"] is False
    assert "runway_api_key_missing" in res["blockers"]
    assert "confirm_provider_costs_required" in res["blockers"]
    assert "gemini_image_env_missing" in res["blockers"]
    assert "elevenlabs_env_missing" in res["blockers"]


def test_ready_summary_uses_presence_only_and_hides_secret_values(monkeypatch, capsys):
    mod = _import_cli()
    monkeypatch.setenv("RUNWAY_API_KEY", "secret-runway-value")
    monkeypatch.setenv("GEMINI_API_KEY", "secret-gemini-value")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "secret-eleven-value")
    monkeypatch.delenv("CI", raising=False)

    code = mod.main(
        [
            "--image-provider",
            "gemini_image",
            "--voice-provider",
            "elevenlabs",
            "--confirm-provider-costs",
            "--ack-live-provider-risk",
            "--ack-not-ci",
        ]
    )
    out = capsys.readouterr().out
    doc = json.loads(out)

    assert code == 0
    assert doc["ready"] is True
    assert doc["env_presence"]["RUNWAY_API_KEY"] is True
    assert "secret-runway-value" not in out
    assert "secret-gemini-value" not in out
    assert "secret-eleven-value" not in out


def test_ci_and_wrong_motion_cap_are_blockers(monkeypatch):
    mod = _import_cli()
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("RUNWAY_API_KEY", "x")
    monkeypatch.setenv("OPENAI_API_KEY", "x")

    res = mod.build_readiness_summary(
        image_provider="openai_image",
        voice_provider="openai",
        duration_minutes=1.0,
        max_scenes=3,
        max_motion_clips=3,
        motion_clip_duration_seconds=10,
        confirm_provider_costs=True,
        ack_live_provider_risk=True,
        ack_not_ci=True,
    )

    assert res["ready"] is False
    assert "ci_environment_detected_do_not_run_live_smoke" in res["blockers"]
    assert "max_motion_clips_must_equal_2_for_ba3269" in res["blockers"]
