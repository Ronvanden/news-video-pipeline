"""BA 32.72 — Founder Video Generate: OpenAI-Image-Parameterpfad (ohne Live-API)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.founder_dashboard.ba323_video_generate import (
    build_open_me_video_result_html,
    execute_dashboard_video_generate,
)
from app.main import app


def test_video_generate_route_forwards_allow_live_assets_and_openai_image_fields() -> None:
    captured: dict = {}

    def _stub_exec(**kwargs):
        captured.update(kwargs)
        return {
            "ok": True,
            "run_id": "ba372_route",
            "output_dir": "",
            "final_video_path": "",
            "script_path": "",
            "scene_asset_pack_path": "",
            "asset_manifest_path": None,
            "duration_target_seconds": 600,
            "max_scenes": 1,
            "max_live_assets": 1,
            "motion_strategy": {},
            "warnings": [],
            "blocking_reasons": [],
            "next_action": "ok",
        }

    client = TestClient(app)
    with patch("app.routes.founder_dashboard.execute_dashboard_video_generate", side_effect=_stub_exec):
        r = client.post(
            "/founder/dashboard/video/generate",
            json={
                "url": "https://example.com/smoke",
                "allow_live_assets": True,
                "confirm_provider_costs": True,
                "voice_mode": "none",
                "max_scenes": 1,
                "max_live_assets": 1,
                "max_motion_clips": 0,
                "image_provider": "openai_image",
                "openai_image_model": "gpt-image-2",
                "openai_image_size": "1024x1024",
            },
        )
    assert r.status_code == 200, r.text
    assert captured.get("allow_live_assets") is True
    assert captured.get("image_provider") == "openai_image"
    assert captured.get("openai_image_model") == "gpt-image-2"
    assert captured.get("openai_image_size") == "1024x1024"


def test_video_generate_route_accepts_dev_openai_key_override_without_leaking() -> None:
    captured: dict = {}

    def _stub_exec(**kwargs):
        captured.update(kwargs)
        return {
            "ok": True,
            "run_id": "ba372_dev_key",
            "output_dir": "",
            "final_video_path": "",
            "script_path": "",
            "scene_asset_pack_path": "",
            "asset_manifest_path": None,
            "duration_target_seconds": 600,
            "max_scenes": 1,
            "max_live_assets": 1,
            "motion_strategy": {},
            "warnings": ["openai_image_key_missing_fallback_placeholder"],
            "blocking_reasons": [],
            "next_action": "ok",
        }

    key = "sk-test-DO-NOT-LEAK"
    client = TestClient(app)
    with patch.dict("os.environ", {"VP_ALLOW_DEV_PROVIDER_KEY_OVERRIDES": "1"}, clear=False):
        with patch("app.routes.founder_dashboard.execute_dashboard_video_generate", side_effect=_stub_exec):
            r = client.post(
                "/founder/dashboard/video/generate",
                json={
                    "url": "https://example.com/devkey",
                    "allow_live_assets": True,
                    "confirm_provider_costs": True,
                    "voice_mode": "none",
                    "max_scenes": 1,
                    "max_live_assets": 1,
                    "max_motion_clips": 0,
                    "image_provider": "openai_image",
                    "openai_image_model": "gpt-image-2",
                    "openai_image_size": "1024x1024",
                    "dev_openai_api_key": key,
                },
            )
    assert r.status_code == 200, r.text
    assert captured.get("dev_openai_api_key") == key
    data = r.json()
    assert key not in json.dumps(data)
    op = data.get("open_me_report_path")
    assert isinstance(op, str) and op
    txt = Path(op).read_text(encoding="utf-8")
    assert key not in txt
    warns = list(data.get("warnings") or [])
    assert all(key not in str(w) for w in warns)


def test_execute_defaults_openai_model_to_gpt_image_2_when_openai_provider_and_unset() -> None:
    captured: dict = {}

    class _FakeMod:
        def run_ba265_url_to_final(self, **kwargs):
            captured.update(kwargs)
            out_dir = Path(str(kwargs.get("out_dir") or "")).resolve()
            gen_dir = out_dir / "generated_assets_def_oai"
            gen_dir.mkdir(parents=True, exist_ok=True)
            (gen_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            mp = gen_dir / "asset_manifest.json"
            mp.write_text(
                json.dumps(
                    {
                        "asset_count": 1,
                        "generation_mode": "placeholder",
                        "warnings": [],
                        "assets": [{"image_path": "scene_001.png", "generation_mode": "placeholder"}],
                    }
                ),
                encoding="utf-8",
            )
            return {
                "ok": True,
                "output_dir": str(out_dir),
                "final_video_path": "",
                "script_path": "x/script.json",
                "scene_asset_pack_path": "x/scene_asset_pack.json",
                "asset_manifest_path": str(mp),
                "warnings": [],
                "blocking_reasons": [],
                "asset_runner_audit": {"effective_image_provider": "openai_image"},
            }

    with patch("app.founder_dashboard.ba323_video_generate._load_run_url_to_final_mod", lambda: _FakeMod()):
        out = execute_dashboard_video_generate(
            url="https://example.com/a",
            output_dir=Path(tempfile.gettempdir()) / "vg_ba372_default_oai",
            run_id="ba372_def_oai",
            duration_target_seconds=600,
            max_scenes=1,
            max_live_assets=1,
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=0,
            allow_live_assets=True,
            allow_live_motion=False,
            voice_mode="none",
            motion_mode="basic",
            image_provider="openai_image",
            openai_image_model=None,
        )

    assert captured.get("openai_image_model") == "gpt-image-2"
    ia = out.get("image_asset_audit") or {}
    assert ia.get("requested_openai_image_model") == "gpt-image-2"


def test_execute_passes_openai_image_kwargs_to_run_ba265_when_live() -> None:
    captured: dict = {}

    class _FakeMod:
        def run_ba265_url_to_final(self, **kwargs):
            captured.update(kwargs)
            out_dir = Path(str(kwargs.get("out_dir") or "")).resolve()
            gen_dir = out_dir / "generated_assets_x"
            gen_dir.mkdir(parents=True, exist_ok=True)
            (gen_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            mp = gen_dir / "asset_manifest.json"
            mp.write_text(
                json.dumps(
                    {
                        "asset_count": 1,
                        "generation_mode": "placeholder",
                        "warnings": [],
                        "assets": [{"image_path": "scene_001.png", "generation_mode": "placeholder"}],
                    }
                ),
                encoding="utf-8",
            )
            return {
                "ok": True,
                "output_dir": str(out_dir),
                "final_video_path": "",
                "script_path": "x/script.json",
                "scene_asset_pack_path": "x/scene_asset_pack.json",
                "asset_manifest_path": str(mp),
                "warnings": [],
                "blocking_reasons": [],
                "asset_runner_audit": {
                    "effective_image_provider": "openai_image",
                    "openai_image_runner_options": {
                        "model": "gpt-image-2",
                        "size": "1024x1024",
                        "timeout_seconds": 90.0,
                    },
                },
            }

    with patch("app.founder_dashboard.ba323_video_generate._load_run_url_to_final_mod", lambda: _FakeMod()):
        out = execute_dashboard_video_generate(
            url="https://example.com/a",
            output_dir=Path(tempfile.gettempdir()) / "vg_ba372_kw",
            run_id="ba372_kw",
            duration_target_seconds=600,
            max_scenes=1,
            max_live_assets=1,
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=0,
            allow_live_assets=True,
            allow_live_motion=False,
            voice_mode="none",
            motion_mode="basic",
            image_provider="openai_image",
            openai_image_model="gpt-image-2",
            openai_image_size="1024x1024",
            openai_image_timeout_seconds=90.0,
        )

    assert captured.get("image_provider") == "openai_image"
    assert captured.get("openai_image_model") == "gpt-image-2"
    assert captured.get("openai_image_size") == "1024x1024"
    assert captured.get("openai_image_timeout_seconds") == 90.0
    ia = out.get("image_asset_audit") or {}
    assert ia.get("requested_image_provider") == "openai_image"
    assert ia.get("effective_image_provider") == "openai_image"
    assert ia.get("requested_openai_image_model") == "gpt-image-2"


def test_execute_warns_when_image_opts_without_live_assets() -> None:
    class _FakeMod:
        def run_ba265_url_to_final(self, **kwargs):
            assert "image_provider" not in kwargs
            assert "openai_image_model" not in kwargs
            out_dir = Path(str(kwargs.get("out_dir") or "")).resolve()
            gen_dir = out_dir / "generated_assets_ph"
            gen_dir.mkdir(parents=True, exist_ok=True)
            (gen_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            mp = gen_dir / "asset_manifest.json"
            mp.write_text(
                json.dumps(
                    {
                        "asset_count": 1,
                        "generation_mode": "placeholder",
                        "warnings": [],
                        "assets": [{"image_path": "scene_001.png", "generation_mode": "placeholder"}],
                    }
                ),
                encoding="utf-8",
            )
            return {
                "ok": True,
                "output_dir": str(out_dir),
                "final_video_path": "",
                "script_path": "x/script.json",
                "scene_asset_pack_path": "x/scene_asset_pack.json",
                "asset_manifest_path": str(mp),
                "warnings": [],
                "blocking_reasons": [],
            }

    with patch("app.founder_dashboard.ba323_video_generate._load_run_url_to_final_mod", lambda: _FakeMod()):
        out = execute_dashboard_video_generate(
            url="https://example.com/a",
            output_dir=Path(tempfile.gettempdir()) / "vg_ba372_warn",
            run_id="ba372_warn",
            duration_target_seconds=600,
            max_scenes=1,
            max_live_assets=1,
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=0,
            allow_live_assets=False,
            allow_live_motion=False,
            voice_mode="none",
            motion_mode="basic",
            image_provider="openai_image",
            openai_image_model="gpt-image-2",
        )

    warns = list(out.get("warnings") or [])
    assert any("ba372_image_generation_options_ignored_without_live_assets" in w for w in warns)


def test_open_me_includes_image_asset_audit_section() -> None:
    html = build_open_me_video_result_html(
        {
            "ok": True,
            "run_id": "r",
            "warnings": [],
            "blocking_reasons": [],
            "image_asset_audit": {
                "effective_image_provider": "openai_image",
                "requested_openai_image_model": "gpt-image-2",
                "real_asset_file_count": 1,
                "asset_manifest_path": "/tmp/manifest.json",
            },
        }
    )
    assert "Image Asset Audit (BA 32.72)" in html
    assert "openai_image" in html
    assert "gpt-image-2" in html


def test_video_generate_invalid_image_provider_422() -> None:
    client = TestClient(app)
    r = client.post(
        "/founder/dashboard/video/generate",
        json={
            "url": "https://example.com/z",
            "image_provider": "unknown_provider_xyz",
        },
    )
    assert r.status_code == 422


def test_run_local_asset_runner_image_provider_overrides_env(monkeypatch, tmp_path) -> None:
    from scripts.run_asset_runner import run_local_asset_runner

    monkeypatch.setenv("IMAGE_PROVIDER", "leonardo")
    pack = {
        "export_version": "18.2-v1",
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": "Test frame.",
                    "visual_prompt_effective": "Test frame.",
                    "visual_prompt_raw": "Test frame.",
                    "overlay_intent": [],
                    "text_sensitive": False,
                    "visual_asset_kind": "scene",
                    "routed_visual_provider": "",
                    "routed_image_provider": "",
                    "camera_motion_hint": "static",
                    "duration_seconds": 6,
                    "asset_type": "scene",
                    "continuity_note": "",
                    "safety_notes": [],
                }
            ]
        },
    }
    p = tmp_path / "pack.json"
    p.write_text(json.dumps(pack), encoding="utf-8")
    meta = run_local_asset_runner(
        p,
        tmp_path / "out",
        run_id="ba372_ov",
        mode="placeholder",
        image_provider="openai_image",
    )
    assert meta.get("effective_image_provider") == "openai_image"
