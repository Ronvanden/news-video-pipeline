"""BA 26.3 — Lokaler Runway-/Video-Clip-Ingest (ohne neuen Provider-Call)."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_ASSET_RUNNER = _ROOT / "scripts" / "run_asset_runner.py"
_TIMELINE = _ROOT / "scripts" / "build_timeline_manifest.py"
_RENDER = _ROOT / "scripts" / "render_final_story_video.py"
_REAL_BUILD = _ROOT / "scripts" / "run_real_video_build.py"


@pytest.fixture(scope="module")
def asset_mod():
    spec = importlib.util.spec_from_file_location("run_asset_runner_ba263", _ASSET_RUNNER)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def timeline_mod():
    spec = importlib.util.spec_from_file_location("build_timeline_ba263", _TIMELINE)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def render_mod():
    spec = importlib.util.spec_from_file_location("render_ba263", _RENDER)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def real_build_mod():
    spec = importlib.util.spec_from_file_location("real_build_ba263", _REAL_BUILD)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _write_min_mp4(target: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=320x240:r=25",
            "-t",
            "1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(target),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def test_scene_pack_runway_clip_path_manifest_has_video(asset_mod, tmp_path):
    pack_dir = tmp_path / "pack"
    pack_dir.mkdir()
    clip_name = "clip.mp4"
    clip = pack_dir / clip_name
    if _ffmpeg_available():
        _write_min_mp4(clip)
    else:
        clip = pack_dir / "clip.avi"
        clip_name = "clip.avi"
        clip.write_bytes(b"nope")
    pack = {
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": "Test",
                    "camera_motion_hint": "static",
                    "duration_seconds": 4,
                    "asset_type": "detail",
                    "runway_clip_path": clip_name,
                }
            ]
        }
    }
    pack_path = pack_dir / "scene_asset_pack.json"
    pack_path.write_text(json.dumps(pack), encoding="utf-8")

    meta = asset_mod.run_local_asset_runner(
        pack_path, tmp_path / "out", run_id="ba263v", mode="placeholder"
    )
    assert meta["ok"] is True
    man = json.loads(Path(meta["manifest_path"]).read_text(encoding="utf-8"))
    if _ffmpeg_available():
        assert man["local_video_scene_count"] == 1
        a0 = man["assets"][0]
        assert a0["asset_type"] == "video"
        assert a0["video_path"].endswith(".mp4")
        assert "image_path" in a0
        assert a0["duration_seconds"] == 4
    else:
        assert man["local_video_scene_count"] == 0
        assert any("local_video_bad_extension" in w for w in man["warnings"])


def test_invalid_clip_path_warns_and_image_fallback(asset_mod, tmp_path):
    pack_dir = tmp_path / "pack2"
    pack_dir.mkdir()
    pack = {
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": "X",
                    "camera_motion_hint": "static",
                    "duration_seconds": 3,
                    "asset_type": "detail",
                    "clip_path": "does_not_exist.mp4",
                }
            ]
        }
    }
    pack_path = pack_dir / "p.json"
    pack_path.write_text(json.dumps(pack), encoding="utf-8")
    meta = asset_mod.run_local_asset_runner(pack_path, tmp_path / "o2", run_id="inv", mode="placeholder")
    man = json.loads(Path(meta["manifest_path"]).read_text(encoding="utf-8"))
    assert man["assets"][0].get("video_path") is None
    assert man["assets"][0]["image_path"] == "scene_001.png"
    assert any("local_video" in w for w in man["warnings"])


def test_timeline_manifest_video_fields(timeline_mod, tmp_path):
    adir = tmp_path / "ga"
    adir.mkdir(parents=True)
    (adir / "scene_001.mp4").write_bytes(b"x")
    (adir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    man = {
        "run_id": "t1",
        "assets": [
            {
                "scene_number": 1,
                "chapter_index": 0,
                "beat_index": 0,
                "asset_type": "video",
                "image_path": "scene_001.png",
                "video_path": "scene_001.mp4",
                "duration_seconds": 5,
                "camera_motion_hint": "static",
            }
        ],
    }
    am_path = adir / "asset_manifest.json"
    am_path.write_text(json.dumps(man), encoding="utf-8")
    _, body = timeline_mod.write_timeline_manifest(
        timeline_mod.load_asset_manifest(am_path),
        asset_manifest_path=am_path,
        audio_path=None,
        run_id="tvid",
        scene_duration_seconds=6,
        out_root=tmp_path / "tlout",
    )
    sc = body["scenes"][0]
    assert sc["media_type"] == "video"
    assert sc["video_path"] == "scene_001.mp4"
    assert sc["image_path"] == "scene_001.png"


def test_render_accepts_video_timeline(render_mod, tmp_path):
    """Command-/Pfad-Ebene: ffmpeg wird mit stream_loop für Video-Eingang aufgerufen."""
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (assets / "a.mp4").write_bytes(b"x")
    tl = {
        "assets_directory": str(assets),
        "audio_path": "",
        "scenes": [
            {
                "scene_number": 1,
                "media_type": "video",
                "video_path": "a.mp4",
                "image_path": "a.png",
                "duration_seconds": 2,
                "transition": "fade",
                "camera_motion_hint": "",
                "zoom_type": "static",
                "pan_direction": "none",
                "chapter_index": 0,
                "beat_index": 0,
            }
        ],
    }
    tlp = tmp_path / "tlv.json"
    tlp.write_text(json.dumps(tl), encoding="utf-8")
    out = tmp_path / "outv.mp4"
    captured: list[list[str]] = []

    def fake_run(cmd, check=True, capture_output=True, text=True):
        captured.append(list(cmd))
        Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
        Path(cmd[-1]).write_bytes(b"vid")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    with patch.object(render_mod.subprocess, "run", side_effect=fake_run):
        meta = render_mod.render_final_story_video(
            tlp, output_video=out, motion_mode="basic", ffmpeg_bin="ffmpeg_x", ffprobe_bin=None
        )
    assert meta["video_created"] is True
    assert captured and any("-stream_loop" in arg for arg in captured[0])


def test_real_video_build_orchestrator_passes_video_pack(real_build_mod, tmp_path):
    pack_dir = tmp_path / "orch_pack"
    pack_dir.mkdir()
    clip = pack_dir / "local_test_clip.mp4"
    if _ffmpeg_available():
        _write_min_mp4(clip)
    else:
        pytest.skip("ffmpeg nicht verfügbar für Mini-MP4")
    pack = {
        "hook": "H",
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": "V",
                    "narration": "Eins.",
                    "camera_motion_hint": "static",
                    "duration_seconds": 4,
                    "asset_type": "establishing",
                    "runway_clip_path": "local_test_clip.mp4",
                }
            ]
        },
    }
    pack_path = pack_dir / "scene_asset_pack.json"
    pack_path.write_text(json.dumps(pack), encoding="utf-8")

    asset_manifest_holder: dict = {}

    def fake_timeline(am, *, asset_manifest_path, audio_path, run_id, scene_duration_seconds, out_root):
        am_data = json.loads(Path(asset_manifest_path).read_text(encoding="utf-8"))
        asset_manifest_holder["assets"] = am_data.get("assets", [])
        body = {
            "run_id": run_id,
            "assets_directory": str(Path(asset_manifest_path).parent),
            "audio_path": "",
            "scenes": [],
            "estimated_duration_seconds": 4,
        }
        for x in sorted(am_data.get("assets") or [], key=lambda z: int(z.get("scene_number", 0))):
            row = {
                "scene_number": x["scene_number"],
                "duration_seconds": int(x.get("duration_seconds") or scene_duration_seconds),
                "transition": "fade",
                "camera_motion_hint": str(x.get("camera_motion_hint") or ""),
                "zoom_type": "static",
                "pan_direction": "none",
                "chapter_index": int(x.get("chapter_index", 0)),
                "beat_index": int(x.get("beat_index", 0)),
            }
            vp = str(x.get("video_path") or "").strip()
            ip = str(x.get("image_path") or "").strip()
            if vp and (Path(asset_manifest_path).parent / vp).is_file():
                row["media_type"] = "video"
                row["video_path"] = vp
                if ip:
                    row["image_path"] = ip
            else:
                row["media_type"] = "image"
                row["image_path"] = ip
            body["scenes"].append(row)
        outd = Path(out_root) / f"timeline_{run_id}"
        outd.mkdir(parents=True, exist_ok=True)
        tf = outd / "timeline_manifest.json"
        tf.write_text(json.dumps(body), encoding="utf-8")
        return tf, body

    def fake_voice(*, pack_data, run_id, out_root, voice_mode, voiceover_mod, **kw):
        d = Path(out_root) / f"full_voice_{run_id}"
        d.mkdir(parents=True, exist_ok=True)
        mp3 = d / "full_voiceover.mp3"
        mp3.write_bytes(b"\x00")
        ns = d / "narration_script.txt"
        ns.write_text("a", encoding="utf-8")
        step = real_build_mod._step("voiceover_smoke", ok=True, output=str(mp3))
        return step, {"voiceover_audio": str(mp3), "narration_script": str(ns)}

    def fake_render(timeline_path, *, output_video, motion_mode, subtitle_path, run_id, write_output_manifest,
                    manifest_root, **kw):
        Path(output_video).parent.mkdir(parents=True, exist_ok=True)
        Path(output_video).write_bytes(b"v")
        return {
            "video_created": True,
            "warnings": [],
            "blocking_reasons": [],
            "output_path": str(Path(output_video).resolve()),
        }

    def fake_sub(narration_script_path, *, timeline_manifest_path, out_root, run_id, subtitle_mode,
                 subtitle_source, subtitle_style, audio_path, **kw):
        p = Path(tmp_path) / "sub" / "m.json"
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps({"subtitles_srt_path": str(p.parent / "x.srt")}), encoding="utf-8")
        (p.parent / "x.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nA.\n", encoding="utf-8")
        return {
            "ok": True,
            "subtitle_manifest_path": str(p),
            "subtitles_srt_path": str(p.parent / "x.srt"),
            "warnings": [],
            "blocking_reasons": [],
        }

    def fake_burn(input_video, subtitle_manifest, *, out_root, run_id, force, **kw):
        out_mp4 = Path(tmp_path) / "prev.mp4"
        out_mp4.write_bytes(b"p")
        return {
            "ok": True,
            "skipped": False,
            "output_video_path": str(out_mp4),
            "warnings": [],
            "blocking_reasons": [],
        }

    result = real_build_mod.run_real_video_build(
        scene_asset_pack=pack_path,
        out_root=tmp_path / "obase",
        run_id="ba263_orch",
        asset_mode="placeholder",
        voice_mode="smoke",
        subtitle_mode="simple",
        timeline_writer_fn=fake_timeline,
        voiceover_smoke_fn=fake_voice,
        render_fn=fake_render,
        subtitle_build_fn=fake_sub,
        burn_in_fn=fake_burn,
    )
    assert result.get("status") == "completed"
    assert asset_manifest_holder.get("assets")
    assert asset_manifest_holder["assets"][0].get("video_path")


@pytest.mark.skipif(not _ffmpeg_available(), reason="ffmpeg für Integrations-Render")
def test_render_creates_mp4_from_video_timeline(render_mod, tmp_path):
    assets = tmp_path / "ga_r"
    assets.mkdir()
    png = assets / "scene_001.png"
    png.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    vpath = assets / "scene_001.mp4"
    _write_min_mp4(vpath)
    tl = {
        "assets_directory": str(assets),
        "audio_path": "",
        "scenes": [
            {
                "scene_number": 1,
                "media_type": "video",
                "video_path": "scene_001.mp4",
                "image_path": "scene_001.png",
                "duration_seconds": 2,
                "transition": "fade",
                "camera_motion_hint": "static",
                "zoom_type": "static",
                "pan_direction": "none",
                "chapter_index": 0,
                "beat_index": 0,
            }
        ],
    }
    tlf = tmp_path / "tlr.json"
    tlf.write_text(json.dumps(tl), encoding="utf-8")
    out_mp4 = tmp_path / "render_out.mp4"
    meta = render_mod.render_final_story_video(
        tlf, output_video=out_mp4, motion_mode="static", ffmpeg_bin=shutil.which("ffmpeg")
    )
    assert meta["video_created"] is True
    assert out_mp4.is_file() and out_mp4.stat().st_size > 100
