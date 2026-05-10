"""BA 32.71c — Mini-Video-Smoke-Orchestrierung (Mocks, keine API / kein ffmpeg)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from app.production_connectors.openai_image_mini_video_smoke import (
    SMOKE_VERSION,
    run_openai_image_mini_video_smoke_v1,
)


def test_cli_returns_3_without_confirm_flag(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    script_path = root / "scripts" / "run_openai_image_mini_video_smoke.py"
    spec = importlib.util.spec_from_file_location("openai_mini_vid_cli_ba371c", script_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(sys, "argv", [str(script_path), "--run-id", "gate_only"])
    assert mod.main() == 3


def test_mini_video_ok_with_image_path_and_mock_render(tmp_path):
    png = tmp_path / "in.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n\x00")

    def fake_render(timeline_path: Path, **kwargs):
        out = kwargs.get("output_video")
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_bytes(b"\x00\x00\x00\x18ftypmp42")
        return {
            "video_created": True,
            "duration_seconds": 12.0,
            "warnings": ["audio_missing_silent_render"],
            "blocking_reasons": [],
        }

    body = run_openai_image_mini_video_smoke_v1(
        run_id="ba371c_img",
        out_root=tmp_path / "out",
        model="gpt-image-2",
        size="1024x1024",
        duration_seconds=12,
        image_path=png,
        openai_image_timeout_seconds=30.0,
        invoke_pipeline=None,
        invoke_render=fake_render,
    )
    assert body["ok"] is True
    assert body["smoke_version"] == SMOKE_VERSION
    assert body["model"] == "gpt-image-2"
    assert body["bytes_written"] >= 4
    assert Path(body["video_path"]).is_file()
    assert Path(body["image_path"]).name == "scene_001.png"
    assert any("audio_missing_silent_render" in w for w in body["warnings"])


def test_mini_video_stops_when_pipeline_not_ok(tmp_path):
    def bad_pipeline(**kwargs):
        return {
            "ok": False,
            "model": "gpt-image-2",
            "manifest_path": "",
            "warnings": ["openai_image_http_403", "openai_image_model_access_denied:gpt-image-2"],
            "asset_paths": [],
        }

    body = run_openai_image_mini_video_smoke_v1(
        run_id="ba371c_fail",
        out_root=tmp_path / "out2",
        model="gpt-image-2",
        size="1024x1024",
        duration_seconds=12,
        image_path=None,
        openai_image_timeout_seconds=30.0,
        invoke_pipeline=bad_pipeline,
        invoke_render=lambda *a, **k: (_ for _ in ()).throw(AssertionError("render must not run")),
    )
    assert body["ok"] is False
    assert any("openai_image_http_403" in w for w in body["warnings"])
    assert any("openai_image_model_access_denied" in w for w in body["warnings"])


def test_mini_video_pipeline_ok_and_mock_render(tmp_path):
    work = tmp_path / "mv_flow"
    gen = work / "generated_assets_x"
    gen.mkdir(parents=True, exist_ok=True)
    png = gen / "scene_001.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n")
    mp = gen / "asset_manifest.json"
    mp.write_text(
        json.dumps(
            {
                "run_id": "x",
                "assets": [
                    {
                        "scene_number": 1,
                        "generation_mode": "openai_image_live",
                        "image_path": "scene_001.png",
                        "duration_seconds": 8,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    def good_pipeline(**kwargs):
        return {
            "ok": True,
            "model": "gpt-image-2",
            "manifest_path": str(mp),
            "output_dir": str(gen),
            "asset_paths": [str(png)],
            "warnings": ["openai_image_model:gpt-image-2"],
        }

    def fake_render(timeline_path: Path, **kwargs):
        out = kwargs.get("output_video")
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_bytes(b"\x00\x00\x00\x20ftypmp42extra")
        return {
            "video_created": True,
            "duration_seconds": 11.5,
            "warnings": [],
            "blocking_reasons": [],
        }

    body = run_openai_image_mini_video_smoke_v1(
        run_id="ba371c_pipe",
        out_root=tmp_path / "out3",
        model=None,
        size="1024x1024",
        duration_seconds=12,
        image_path=None,
        openai_image_timeout_seconds=30.0,
        invoke_pipeline=good_pipeline,
        invoke_render=fake_render,
    )
    assert body["ok"] is True
    assert body["duration_seconds"] == 11.5
    man_after = json.loads(mp.read_text(encoding="utf-8"))
    assert man_after["assets"][0]["duration_seconds"] == 12


def test_image_path_missing_returns_diagnostic(tmp_path):
    body = run_openai_image_mini_video_smoke_v1(
        run_id="ba371c_miss",
        out_root=tmp_path / "out4",
        model="gpt-image-2",
        size="1024x1024",
        duration_seconds=12,
        image_path=tmp_path / "nope.png",
        openai_image_timeout_seconds=30.0,
        invoke_render=lambda *a, **k: (_ for _ in ()).throw(AssertionError("no render")),
    )
    assert body["ok"] is False
    assert "mini_video_smoke_image_path_not_found" in body["warnings"]
