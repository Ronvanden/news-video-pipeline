"""BA 32.78 — Thumbnail Pack Auto-Attach (Video Generate, keine Live-API in CI)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.founder_dashboard.ba323_video_generate import (
    build_open_me_video_result_html,
    execute_dashboard_video_generate,
)
from app.main import app
from app.routes.founder_dashboard import VideoGenerateRequest


def _minimal_ba265_doc(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    sp = out_dir / "script.json"
    sp.write_text(json.dumps({"title": "Titel X", "hook": "Hook Y", "full_script": "Body"}), encoding="utf-8")
    return {
        "ok": True,
        "input_mode": "url",
        "title": "Titel X",
        "output_dir": str(out_dir.resolve()),
        "final_video_path": str((out_dir / "final_video.mp4").resolve()),
        "script_path": str(sp.resolve()),
        "scene_asset_pack_path": str((out_dir / "pack.json").resolve()),
        "asset_manifest_path": str((out_dir / "manifest.json").resolve()),
        "warnings": [],
        "blocking_reasons": [],
        "generated_original_script": False,
    }


def _fake_candidates_ok(**kwargs: object) -> dict:
    from PIL import Image

    out = Path(str(kwargs.get("output_dir") or "")).resolve()
    out.mkdir(parents=True, exist_ok=True)
    p = out / "thumbnail_candidate_thumb_a.png"
    Image.new("RGB", (512, 512), color=(40, 50, 60)).save(p, format="PNG")
    return {
        "ok": True,
        "model": "gpt-image-2",
        "size": "1024x1024",
        "generated_count": 1,
        "failed_count": 0,
        "candidate_paths": {"thumb_a": str(p.resolve())},
        "candidate_briefs": {},
        "warnings": [],
        "result_path": str((out / "thumbnail_candidates_result.json").resolve()),
        "thumbnail_candidates_version": "ba32_74_v1",
    }


def test_request_validates_candidate_and_output_bounds() -> None:
    VideoGenerateRequest(
        url="https://example.com/a",
        confirm_provider_costs=True,
        generate_thumbnail_pack=True,
        thumbnail_candidate_count=3,
        thumbnail_max_outputs=6,
    )
    with pytest.raises(ValidationError):
        VideoGenerateRequest(
            url="https://example.com/a",
            confirm_provider_costs=True,
            generate_thumbnail_pack=True,
            thumbnail_candidate_count=4,
        )
    with pytest.raises(ValidationError):
        VideoGenerateRequest(
            url="https://example.com/a",
            confirm_provider_costs=True,
            generate_thumbnail_pack=True,
            thumbnail_max_outputs=7,
        )


def test_route_422_when_thumb_pack_without_cost_confirm() -> None:
    client = TestClient(app)
    r = client.post(
        "/founder/dashboard/video/generate",
        json={
            "url": "https://example.com/x",
            "confirm_provider_costs": False,
            "generate_thumbnail_pack": True,
            "voice_mode": "none",
            "max_motion_clips": 0,
        },
    )
    assert r.status_code == 422


def test_generate_false_no_attach_warnings(tmp_path: Path) -> None:
    class _M:
        def run_ba265_url_to_final(self, **kwargs):
            return _minimal_ba265_doc(Path(kwargs["out_dir"]))

    with patch("app.founder_dashboard.ba323_video_generate._load_run_url_to_final_mod", lambda: _M()):
        out = execute_dashboard_video_generate(
            url="https://example.com/a",
            output_dir=tmp_path / "vg1",
            run_id="r1",
            duration_target_seconds=600,
            max_scenes=1,
            max_live_assets=0,
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=0,
            allow_live_assets=False,
            allow_live_motion=False,
            voice_mode="none",
            motion_mode="basic",
            generate_thumbnail_pack=False,
        )
    warns = " ".join(str(w) for w in (out.get("warnings") or []))
    assert "ba3278_" not in warns
    tp = out.get("thumbnail_pack") or {}
    assert not tp.get("thumbnail_pack_auto_attach")


def test_generate_true_attaches_pack_with_mocks(tmp_path: Path) -> None:
    class _M:
        def run_ba265_url_to_final(self, **kwargs):
            return _minimal_ba265_doc(Path(kwargs["out_dir"]))

    out_root = tmp_path / "vg2"
    with patch("app.founder_dashboard.ba323_video_generate._load_run_url_to_final_mod", lambda: _M()):
        with patch(
            "app.founder_dashboard.ba323_video_generate.run_thumbnail_candidates_v1",
            side_effect=_fake_candidates_ok,
        ):
            out = execute_dashboard_video_generate(
                url="https://example.com/a",
                output_dir=out_root,
                run_id="r2",
                duration_target_seconds=600,
                max_scenes=1,
                max_live_assets=0,
                motion_clip_every_seconds=60,
                motion_clip_duration_seconds=10,
                max_motion_clips=0,
                allow_live_assets=False,
                allow_live_motion=False,
                voice_mode="none",
                motion_mode="basic",
                generate_thumbnail_pack=True,
                thumbnail_candidate_count=1,
                thumbnail_max_outputs=3,
                dev_openai_api_key="sk-test-local-only",
            )
    assert out.get("ok") is True
    tp = out.get("thumbnail_pack") or {}
    assert tp.get("thumbnail_pack_auto_attach") is True
    assert tp.get("thumbnail_pack_status") == "ready"
    assert str(tp.get("thumbnail_recommended_path") or "").endswith(".png")
    assert (out_root / "thumbnail_pack" / "thumbnail_batch_overlay_result.json").is_file()
    warns = out.get("warnings") or []
    assert not any("sk-" in str(w) for w in warns)


def test_openai_key_missing_does_not_break_video(tmp_path: Path) -> None:
    class _M:
        def run_ba265_url_to_final(self, **kwargs):
            return _minimal_ba265_doc(Path(kwargs["out_dir"]))

    out_root = tmp_path / "vg3"
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        with patch("app.founder_dashboard.ba323_video_generate._load_run_url_to_final_mod", lambda: _M()):
            out = execute_dashboard_video_generate(
                url="https://example.com/a",
                output_dir=out_root,
                run_id="r3",
                duration_target_seconds=600,
                max_scenes=1,
                max_live_assets=0,
                motion_clip_every_seconds=60,
                motion_clip_duration_seconds=10,
                max_motion_clips=0,
                allow_live_assets=False,
                allow_live_motion=False,
                voice_mode="none",
                motion_mode="basic",
                generate_thumbnail_pack=True,
                thumbnail_candidate_count=1,
                thumbnail_max_outputs=2,
            )
    assert out.get("ok") is True
    assert any("ba3278_thumbnail_pack_openai_key_missing" in str(w) for w in (out.get("warnings") or []))
    tp = out.get("thumbnail_pack") or {}
    assert tp.get("thumbnail_pack_status") == "warning"


def test_batch_failure_does_not_fail_video(tmp_path: Path) -> None:
    class _M:
        def run_ba265_url_to_final(self, **kwargs):
            return _minimal_ba265_doc(Path(kwargs["out_dir"]))

    out_root = tmp_path / "vg4"

    def _boom(**kwargs: object) -> dict:
        raise RuntimeError("batch_intentional")

    with patch("app.founder_dashboard.ba323_video_generate._load_run_url_to_final_mod", lambda: _M()):
        with patch(
            "app.founder_dashboard.ba323_video_generate.run_thumbnail_candidates_v1",
            side_effect=_fake_candidates_ok,
        ):
            with patch(
                "app.founder_dashboard.ba323_video_generate.run_thumbnail_batch_overlay_v1",
                side_effect=_boom,
            ):
                out = execute_dashboard_video_generate(
                    url="https://example.com/a",
                    output_dir=out_root,
                    run_id="r4",
                    duration_target_seconds=600,
                    max_scenes=1,
                    max_live_assets=0,
                    motion_clip_every_seconds=60,
                    motion_clip_duration_seconds=10,
                    max_motion_clips=0,
                    allow_live_assets=False,
                    allow_live_motion=False,
                    voice_mode="none",
                    motion_mode="basic",
                    generate_thumbnail_pack=True,
                    thumbnail_candidate_count=1,
                    thumbnail_max_outputs=2,
                    dev_openai_api_key="sk-fake-test-key",
                )
    assert out.get("ok") is True
    assert any("ba3278_thumbnail_pack_attach_failed:RuntimeError" in str(w) for w in (out.get("warnings") or []))
    body = json.dumps(out, ensure_ascii=False)
    assert "sk-fake" not in body
    html = build_open_me_video_result_html(out)
    assert "sk-fake" not in html
    assert "Thumbnail Pack (BA 32.77)" in html


def test_route_forwards_thumbnail_fields() -> None:
    captured: dict = {}

    def _stub(**kwargs):
        captured.update(kwargs)
        return {
            "ok": True,
            "run_id": "t78",
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
            "thumbnail_pack": {},
        }

    client = TestClient(app)
    with patch("app.routes.founder_dashboard.execute_dashboard_video_generate", side_effect=_stub):
        r = client.post(
            "/founder/dashboard/video/generate",
            json={
                "url": "https://example.com/fwd",
                "confirm_provider_costs": True,
                "voice_mode": "none",
                "max_scenes": 1,
                "max_live_assets": 1,
                "max_motion_clips": 0,
                "generate_thumbnail_pack": True,
                "thumbnail_candidate_count": 2,
                "thumbnail_max_outputs": 4,
                "thumbnail_model": "gpt-image-2",
                "thumbnail_size": "1024x1024",
                "thumbnail_style_presets": ["impact_youtube"],
            },
        )
    assert r.status_code == 200, r.text
    assert captured.get("generate_thumbnail_pack") is True
    assert captured.get("thumbnail_candidate_count") == 2
    assert captured.get("thumbnail_max_outputs") == 4
    assert captured.get("thumbnail_model") == "gpt-image-2"
