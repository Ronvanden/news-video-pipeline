"""BA 32.40 — OpenAI Image Spike (IMAGE_PROVIDER=openai_image), keine echten Calls."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.founder_dashboard.ba323_video_generate import build_asset_artifact

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_asset_runner.py"


@pytest.fixture(scope="module")
def ar_mod():
    spec = importlib.util.spec_from_file_location("run_asset_runner_ba340", _SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _one_beat_pack(tmp_path: Path) -> Path:
    pack = {
        "export_version": "18.2-v1",
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": "Establishing editorial still, skyline, no readable text.",
                    "visual_prompt_effective": "Establishing editorial still, skyline, no readable text.\n\n[visual_no_text_guard_v26_4]\nNo readable text.",
                    "visual_prompt_raw": "Establishing editorial still, skyline, no readable text.",
                    "camera_motion_hint": "static",
                    "duration_seconds": 8,
                    "asset_type": "establishing",
                    "overlay_intent": [],
                    "text_sensitive": False,
                    "visual_asset_kind": "cinematic_broll",
                    "routed_visual_provider": "leonardo",
                    "continuity_note": "",
                    "safety_notes": [],
                }
            ]
        },
    }
    p = tmp_path / "pack.json"
    p.write_text(json.dumps(pack), encoding="utf-8")
    return p


@pytest.fixture(autouse=True)
def _unset_image_provider(monkeypatch):
    monkeypatch.delenv("IMAGE_PROVIDER", raising=False)


def test_openai_image_live_success_manifest_and_gate(ar_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "openai_image")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-placeholder")

    def _stub(vp, dest, **_kw):
        dest.write_bytes(b"\x89PNG\r\n\x1a\n")
        return (
            True,
            ["openai_image_model:test-model-z", "openai_image_provider:openai_image"],
            {"ok": True, "model": "test-model-z", "bytes_written": 8, "dry_run": False},
        )

    pack = _one_beat_pack(tmp_path)
    with patch.object(ar_mod, "run_openai_image_live_to_png", side_effect=_stub):
        meta = ar_mod.run_local_asset_runner(pack, tmp_path / "out", run_id="ba340ok", mode="live", max_assets_live=1)
    out = Path(meta["output_dir"])
    man = json.loads((out / "asset_manifest.json").read_text(encoding="utf-8"))
    assert meta["ok"] is True
    assert man["generation_mode"] == "openai_image_live"
    a0 = man["assets"][0]
    assert a0["generation_mode"] == "openai_image_live"
    assert a0.get("provider_used") == "openai_image"
    assert (out / "scene_001.png").is_file()
    aa = build_asset_artifact(asset_manifest_path=str(out / "asset_manifest.json"))
    assert int((aa.get("generation_modes") or {}).get("openai_image_live", 0)) >= 1
    assert aa.get("real_asset_file_count") == 1
    assert aa.get("placeholder_asset_count") == 0
    assert (aa.get("asset_quality_gate") or {}).get("status") == "production_ready"


def test_openai_image_live_uses_effective_visual_prompt_and_keeps_anatomy(ar_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "openai_image")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-placeholder")
    raw = (
        "Create a realistic documentary-style image.\n"
        "Subject: concerned citizens listening to a calm public health expert.\n"
        "Environment: modern public information room.\n"
        "Composition: foreground subject, midground context, softly defocused background."
    )
    effective = f"{raw}\n\n[visual_no_text_guard_v26_4]\nNo readable text, no lettering, no logos."
    pack_doc = {
        "export_version": "18.2-v1",
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": effective,
                    "visual_prompt_effective": effective,
                    "visual_prompt_raw": raw,
                    "negative_prompt": "text, captions, labels, logos",
                    "visual_prompt_anatomy": {
                        "subject_description": "concerned citizens listening to a calm public health expert",
                        "environment": "modern public information room",
                    },
                    "visual_style_profile": {"preset": "documentary_realism"},
                    "prompt_quality_score": 91,
                    "prompt_risk_flags": ["visual_subject_derived"],
                    "normalized_controls": {"provider_target": "openai_image"},
                    "camera_motion_hint": "static",
                    "duration_seconds": 8,
                    "asset_type": "broll",
                    "overlay_intent": [],
                    "text_sensitive": True,
                    "visual_asset_kind": "keyframe_still",
                    "routed_image_provider": "openai_image",
                    "continuity_note": "",
                    "safety_notes": [],
                }
            ]
        },
    }
    pack = tmp_path / "pack_engine_fields.json"
    pack.write_text(json.dumps(pack_doc), encoding="utf-8")
    captured = {}

    def _stub(vp, dest, **_kw):
        captured["prompt"] = vp
        dest.write_bytes(b"\x89PNG\r\n\x1a\n")
        return (
            True,
            ["openai_image_provider:openai_image"],
            {"ok": True, "bytes_written": 8, "dry_run": False},
        )

    with patch.object(ar_mod, "run_openai_image_live_to_png", side_effect=_stub):
        meta = ar_mod.run_local_asset_runner(pack, tmp_path / "out", run_id="ba340_engine", mode="live", max_assets_live=1)
    out = Path(meta["output_dir"])
    man = json.loads((out / "asset_manifest.json").read_text(encoding="utf-8"))
    asset = man["assets"][0]
    assert captured["prompt"].startswith("Create a realistic documentary-style image.")
    assert "Subject: concerned citizens" in captured["prompt"]
    assert "[visual_no_text_guard_v26_4]" in captured["prompt"]
    assert captured["prompt"].strip() != "[visual_no_text_guard_v26_4]"
    assert asset.get("visual_prompt_raw") == raw
    assert asset.get("visual_prompt_effective") == effective
    assert asset.get("negative_prompt") == "text, captions, labels, logos"
    assert (asset.get("visual_prompt_anatomy") or {}).get("subject_description")
    assert asset.get("prompt_quality_score") == 91
    assert (asset.get("normalized_controls") or {}).get("provider_target") == "openai_image"


def test_openai_image_missing_key_top_level_manifest(ar_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "openai_image")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("app.config.settings.openai_api_key", "", raising=False)

    pack = _one_beat_pack(tmp_path)
    meta = ar_mod.run_local_asset_runner(pack, tmp_path / "out", run_id="ba340_miss", mode="live", max_assets_live=1)
    assert "openai_image_key_missing_fallback_placeholder" in meta["warnings"]
    out = Path(meta["output_dir"])
    man = json.loads((out / "asset_manifest.json").read_text(encoding="utf-8"))
    assert man["generation_mode"] == "openai_image_fallback_placeholder"
    codes = aa_codes(out / "asset_manifest.json")
    assert any("openai_image_key_missing_fallback_placeholder" in str(c) for c in codes)


def test_openai_image_generation_failure_row(ar_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("IMAGE_PROVIDER", "openai_image")
    monkeypatch.setenv("OPENAI_API_KEY", "present")

    def _stub_fail(_vp, dest, **_kw):
        dest.write_bytes(b"not-a-real-display")  # overwritten by runner placeholder drawer
        return (
            False,
            ["openai_image_generation_failed:http_error"],
            {},
        )

    pack = _one_beat_pack(tmp_path)
    with patch.object(ar_mod, "run_openai_image_live_to_png", side_effect=_stub_fail):
        meta = ar_mod.run_local_asset_runner(pack, tmp_path / "out", run_id="ba340_bad", mode="live", max_assets_live=1)
    assert any("openai_image_generation_failed" in str(w) for w in (meta.get("warnings") or []))
    out = Path(meta["output_dir"])
    man = json.loads((out / "asset_manifest.json").read_text(encoding="utf-8"))
    assert man["assets"][0]["generation_mode"] == "openai_image_fallback_placeholder"


def aa_codes(manifest_path: Path):
    aa = build_asset_artifact(asset_manifest_path=str(manifest_path))
    return list(aa.get("asset_provider_warning_codes") or [])


def test_asset_artifact_collects_openai_image_warning_codes(tmp_path):
    gen_dir = tmp_path / "g"
    gen_dir.mkdir()
    mp = gen_dir / "asset_manifest.json"
    mp.write_text(
        json.dumps(
            {
                "warnings": ["openai_image_provider:openai_image", "openai_image_generation_failed:test"],
                "assets": [{"image_path": "x.png"}],
            }
        ),
        encoding="utf-8",
    )
    (gen_dir / "x.png").write_bytes(b"x")
    aa = build_asset_artifact(asset_manifest_path=str(mp))
    codes = [str(c) for c in aa.get("asset_provider_warning_codes") or []]
    assert any(c.startswith("openai_image_generation_failed") for c in codes)


def test_leonardo_path_unchanged_default_provider(ar_mod, tmp_path, monkeypatch):
    """Ohne IMAGE_PROVIDER bleibt Leonardo der Default-Live-Pfad."""
    monkeypatch.delenv("LEONARDO_API_KEY", raising=False)
    monkeypatch.delenv("IMAGE_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    pack = _one_beat_pack(tmp_path)
    meta = ar_mod.run_local_asset_runner(pack, tmp_path / "out", run_id="ba340_ld", mode="live")
    assert "leonardo_env_missing_fallback_placeholder" in meta["warnings"]
