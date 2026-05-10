"""BA 32.56 — Live Smoke Runner (Mocks, keine echten Provider)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_live_video_smoke.py"


@pytest.fixture(scope="module")
def smoke_mod():
    name = "run_live_video_smoke_ba356"
    spec = importlib.util.spec_from_file_location(name, _SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def test_abort_without_confirm_provider_costs(smoke_mod):
    with patch.object(sys, "argv", ["run_live_video_smoke.py", "--profile", "mini"]):
        assert smoke_mod.main() == 2


def test_abort_8min_without_allow_long_runs(smoke_mod):
    with patch.object(
        sys,
        "argv",
        [
            "run_live_video_smoke.py",
            "--profile",
            "8min",
            "--confirm-provider-costs",
        ],
    ):
        assert smoke_mod.main() == 2


def test_classify_pass(smoke_mod, tmp_path):
    vid = tmp_path / "f.mp4"
    vid.write_bytes(b"moov")
    ef = {
        "ok": True,
        "run_id": "r1",
        "warnings": [],
        "blocking_reasons": [],
        "asset_quality_status": "production_ready",
        "real_asset_file_count": 3,
        "placeholder_asset_count": 0,
        "generation_modes": {"gemini_image_live": 3},
        "voice_ready": True,
        "is_dummy": False,
        "voice_file_path": str(tmp_path / "v.mp3"),
        "timing_gap_status": "ok",
        "fit_strategy": "fit_to_voice",
        "render_used_placeholders": False,
        "voice_file_ready": True,
        "asset_strict_ready": True,
        "provider_blockers": ["live_motion_not_available"],
        "final_video_path": str(vid),
        "final_video_size_bytes": 4,
    }
    assert smoke_mod.classify_smoke(ef) == ("PASS", ["criteria_met"])


def test_classify_warn_mixed_assets(smoke_mod, tmp_path):
    vid = tmp_path / "f.mp4"
    vid.write_bytes(b"x")
    ef = {
        "ok": True,
        "run_id": "r2",
        "warnings": [],
        "blocking_reasons": [],
        "asset_quality_status": "mixed_assets",
        "placeholder_asset_count": 1,
        "voice_ready": True,
        "is_dummy": False,
        "render_used_placeholders": False,
        "timing_gap_status": "ok",
        "provider_blockers": [],
        "final_video_path": str(vid),
        "final_video_size_bytes": 1,
    }
    o, r = smoke_mod.classify_smoke(ef)
    assert o == "WARN"
    assert "mixed_assets" in r


def test_classify_warn_major_gap(smoke_mod, tmp_path):
    vid = tmp_path / "f.mp4"
    vid.write_bytes(b"x")
    ef = {
        "ok": True,
        "run_id": "r3",
        "warnings": [],
        "blocking_reasons": [],
        "asset_quality_status": "production_ready",
        "placeholder_asset_count": 0,
        "voice_ready": True,
        "is_dummy": False,
        "render_used_placeholders": False,
        "timing_gap_status": "major_gap",
        "provider_blockers": [],
        "final_video_path": str(vid),
        "final_video_size_bytes": 2,
    }
    o, r = smoke_mod.classify_smoke(ef)
    assert o == "WARN"
    assert "timing_major_gap" in r


def test_classify_fail_ok_false(smoke_mod, tmp_path):
    vid = tmp_path / "f.mp4"
    vid.write_bytes(b"x")
    ef = {
        "ok": False,
        "run_id": "r4",
        "warnings": [],
        "blocking_reasons": [],
        "asset_quality_status": "production_ready",
        "placeholder_asset_count": 0,
        "voice_ready": True,
        "is_dummy": False,
        "render_used_placeholders": False,
        "timing_gap_status": "ok",
        "provider_blockers": [],
        "final_video_path": str(vid),
        "final_video_size_bytes": 1,
    }
    assert smoke_mod.classify_smoke(ef)[0] == "FAIL"


def test_redact_secrets_in_warning(smoke_mod):
    s = "prefix sk-12345678901234567890 suffix"
    assert "[REDACTED]" in smoke_mod.redact_secrets_text(s)
    assert "sk-12345678901234567890" not in smoke_mod.redact_secrets_text(s)


def test_run_profile_uses_base_url(smoke_mod, tmp_path):
    profs = smoke_mod._profiles()
    p = profs["mini"]
    captured: dict = {}

    def _fake_post(url: str, body: dict, timeout: float = 30.0):
        captured["url"] = url
        captured["body"] = body
        vid = tmp_path / "out" / "final_video.mp4"
        vid.parent.mkdir(parents=True, exist_ok=True)
        vid.write_bytes(b"data")
        return 200, {
            "ok": True,
            "run_id": "run_test",
            "output_dir": str(tmp_path / "out"),
            "final_video_path": str(vid),
            "warnings": [],
            "blocking_reasons": [],
            "asset_artifact": {
                "real_asset_file_count": 3,
                "placeholder_asset_count": 0,
                "generation_modes": {"gemini_image_live": 3},
                "asset_quality_gate": {"status": "production_ready"},
            },
            "voice_artifact": {
                "voice_ready": True,
                "is_dummy": False,
                "voice_file_path": str(tmp_path / "v.mp3"),
            },
            "readiness_audit": {
                "render_used_placeholders": False,
                "voice_file_ready": True,
                "asset_strict_ready": True,
                "provider_blockers": ["live_motion_not_available"],
            },
            "timing_audit": {"timing_gap_status": "ok", "fit_strategy": "fit_to_voice"},
        }

    r = smoke_mod.run_profile(
        profile=p,
        base_url="http://127.0.0.1:9999",
        confirm_provider_costs=True,
        post_json=_fake_post,
        request_timeout=30.0,
    )
    assert captured["url"] == "http://127.0.0.1:9999/founder/dashboard/video/generate"
    assert captured["body"]["confirm_provider_costs"] is True
    assert captured["body"]["allow_live_assets"] is True
    assert len(captured["body"].get("raw_text") or "") > 100
    assert r["outcome"] == "PASS"


def test_main_writes_reports(smoke_mod, tmp_path, monkeypatch):
    monkeypatch.setattr(smoke_mod, "_REPORT_DIR", tmp_path / "rep")

    def _fake_post(url: str, body: dict, timeout: float = 30.0):
        vid = tmp_path / "fv.mp4"
        vid.write_bytes(b"mp4")
        return 200, {
            "ok": True,
            "run_id": "rid_w",
            "final_video_path": str(vid),
            "warnings": ["gemini_image_transport:rest"],
            "blocking_reasons": [],
            "asset_artifact": {
                "real_asset_file_count": 1,
                "placeholder_asset_count": 0,
                "generation_modes": {"gemini_image_live": 1},
                "asset_quality_gate": {"status": "production_ready"},
            },
            "voice_artifact": {"voice_ready": True, "is_dummy": False, "voice_file_path": str(tmp_path / "a.mp3")},
            "readiness_audit": {
                "render_used_placeholders": False,
                "voice_file_ready": True,
                "asset_strict_ready": True,
                "provider_blockers": ["live_motion_not_available"],
            },
            "timing_audit": {"timing_gap_status": "ok", "fit_strategy": "fit_to_voice"},
        }

    monkeypatch.setattr(smoke_mod, "_post_json", _fake_post)
    with patch.object(
        sys,
        "argv",
        [
            "run_live_video_smoke.py",
            "--profile",
            "mini",
            "--confirm-provider-costs",
            "--base-url",
            "http://example.test:8020",
        ],
    ):
        code = smoke_mod.main()
    assert code == 0
    reps = list((tmp_path / "rep").glob("live_smoke_*_mini.json"))
    assert len(reps) == 1
    data = json.loads(reps[0].read_text(encoding="utf-8"))
    assert data["outcome"] == "PASS"
    mds = list((tmp_path / "rep").glob("live_smoke_*_mini.md"))
    assert len(mds) == 1
    assert "PASS" in mds[0].read_text(encoding="utf-8")
