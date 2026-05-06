"""BA 29.2 — Local preview render from render input bundle."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from app.production_assembly.local_preview_render import (
    build_preview_scenes,
    run_local_preview_from_bundle,
)


def test_ffmpeg_missing_returns_controlled_result(tmp_path: Path):
    bundle = {"run_id": "r", "image_paths": [str(tmp_path / "x.png")]}
    p = tmp_path / "bundle.json"
    p.write_text(json.dumps(bundle), encoding="utf-8")
    r = run_local_preview_from_bundle(
        bundle=bundle,
        bundle_path=str(p),
        output_dir=tmp_path / "out",
        _which=lambda x: None,
        _run=lambda *a, **k: None,
    )
    assert r["ok"] is False
    assert r.get("error_code") == "ffmpeg_missing"
    assert r["ffmpeg_available"] is False
    assert "ffmpeg_missing" in (r.get("blocking_reasons") or [])


def test_no_scenes_blocks(tmp_path: Path):
    bundle = {"run_id": "r", "image_paths": []}
    bp = tmp_path / "b.json"
    bp.write_text(json.dumps(bundle), encoding="utf-8")
    r = run_local_preview_from_bundle(
        bundle=bundle,
        bundle_path=str(bp),
        output_dir=tmp_path / "o",
        _which=lambda x: "/ffmpeg",
        _run=lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    assert r["ok"] is False
    assert "no_preview_scenes_derived" in (r.get("blocking_reasons") or [])


def _mk_run_creates_outputs():
    def _run(cmd, **kwargs):
        class P:
            returncode = 0
            stdout = ""
            stderr = ""

        out = Path(cmd[-1])
        if out.suffix.lower() == ".mp4":
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(b"fakevid")
        return P()

    return _run


def test_single_image_preview_ok_with_mock_ffmpeg(tmp_path: Path):
    img = tmp_path / "scene.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    timeline = {
        "timeline_version": "ba28_3_v1",
        "scenes": [{"scene_number": 1, "duration_seconds": 0.5, "image_path": str(img)}],
    }
    tm_path = tmp_path / "tl.json"
    tm_path.write_text(json.dumps(timeline), encoding="utf-8")
    bundle = {
        "run_id": "r1",
        "motion_timeline_manifest_path": str(tm_path),
    }
    bp = tmp_path / "bundle.json"
    bp.write_text(json.dumps(bundle), encoding="utf-8")
    r = run_local_preview_from_bundle(
        bundle=json.loads(bp.read_text(encoding="utf-8")),
        bundle_path=str(bp),
        output_dir=tmp_path / "rend",
        _which=lambda x: "/fake/ffmpeg" if x == "ffmpeg" else None,
        _run=_mk_run_creates_outputs(),
    )
    assert r["ok"] is True
    assert r["preview_render_version"] == "ba29_2_v1"
    assert Path(r["output_video_path"]).is_file()
    assert r["used_images_count"] >= 1


def test_build_preview_scenes_from_bundle_images(tmp_path: Path):
    img = tmp_path / "a.png"
    img.write_bytes(b"x")
    b = {"image_paths": [str(img)]}
    scenes, _w = build_preview_scenes(bundle=b, bundle_path=None, timeline=None, default_duration_seconds=3.0)
    assert len(scenes) == 1
    assert scenes[0]["duration_seconds"] == 3.0
