"""BA 19.1 / BA 19.2 — build_timeline_manifest.py + render_final_story_video.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
from subprocess import CompletedProcess

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_BUILD_SCRIPT = _ROOT / "scripts" / "build_timeline_manifest.py"
_RENDER_SCRIPT = _ROOT / "scripts" / "render_final_story_video.py"


@pytest.fixture(scope="module")
def timeline_build_mod():
    spec = importlib.util.spec_from_file_location("build_timeline_manifest", _BUILD_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def final_render_mod():
    spec = importlib.util.spec_from_file_location("render_final_story_video", _RENDER_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _asset_manifest(tmp_path: Path, *, run_id: str = "mr19") -> Path:
    """Minimales asset_manifest.json wie nach BA 19.0 (relative image_path)."""
    assets_dir = tmp_path / f"generated_assets_{run_id}"
    assets_dir.mkdir(parents=True, exist_ok=True)
    for name in ("scene_002.png", "scene_001.png"):
        (assets_dir / name).write_bytes(b"\x89PNG\r\n\x1a\n")
    man = {
        "run_id": run_id,
        "asset_count": 2,
        "assets": [
            {
                "scene_number": 2,
                "chapter_index": 1,
                "beat_index": 0,
                "image_path": "scene_002.png",
                "camera_motion_hint": "slow pull out",
            },
            {
                "scene_number": 1,
                "chapter_index": 0,
                "beat_index": 0,
                "image_path": "scene_001.png",
                "camera_motion_hint": "pan left establishing",
            },
        ],
    }
    p = assets_dir / "asset_manifest.json"
    p.write_text(json.dumps(man), encoding="utf-8")
    return p


def test_build_timeline_writes_manifest_and_timing(timeline_build_mod, tmp_path):
    am_path = _asset_manifest(tmp_path, run_id="sort19")
    out_file, body = timeline_build_mod.write_timeline_manifest(
        timeline_build_mod.load_asset_manifest(am_path),
        asset_manifest_path=am_path,
        audio_path=None,
        run_id="sort19",
        scene_duration_seconds=5,
        out_root=tmp_path / "output",
    )
    assert out_file.parent.name == "timeline_sort19"
    assert out_file.name == "timeline_manifest.json"
    assert body["total_scenes"] == 2
    assert body["estimated_duration_seconds"] == 10
    assert len(body["scenes"]) == 2
    # sortiert nach scene_number
    assert body["scenes"][0]["scene_number"] == 1
    assert body["scenes"][0]["start_time"] == 0.0
    assert body["scenes"][0]["end_time"] == 5.0
    assert body["scenes"][0]["duration_seconds"] == 5
    assert body["scenes"][0]["transition"] == "fade"
    assert body["scenes"][0]["zoom_type"] == "static"
    assert body["scenes"][0]["pan_direction"] == "left"
    assert body["scenes"][1]["scene_number"] == 2
    assert body["scenes"][1]["zoom_type"] == "slow_pull"
    assert body["scenes"][1]["pan_direction"] == "none"
    disk = json.loads(out_file.read_text(encoding="utf-8"))
    assert disk["total_scenes"] == len(disk["scenes"]) == 2


def test_timeline_scene_count_matches_asset_manifest(timeline_build_mod, tmp_path):
    am_path = _asset_manifest(tmp_path, run_id="cnt19")
    am = timeline_build_mod.load_asset_manifest(am_path)
    body = timeline_build_mod.build_timeline_manifest_data(
        am,
        asset_manifest_path=am_path,
        audio_path=None,
        run_id="cnt19",
        scene_duration_seconds=6,
    )
    assert body["total_scenes"] == len(am["assets"])
    assert len(body["scenes"]) == len(am["assets"])


def test_render_missing_ffmpeg_graceful(final_render_mod, tmp_path):
    tl = {
        "run_id": "x",
        "assets_directory": str(tmp_path),
        "audio_path": "",
        "scenes": [{"image_path": "nope.png", "duration_seconds": 1}],
    }
    tlp = tmp_path / "tl.json"
    tlp.write_text(json.dumps(tl), encoding="utf-8")
    out = tmp_path / "v.mp4"
    meta = final_render_mod.render_final_story_video(tlp, output_video=out, ffmpeg_bin="")
    assert meta["video_created"] is False
    assert "ffmpeg_missing" in meta["blocking_reasons"]
    assert meta["scene_count"] == 1


def test_render_missing_timeline_graceful(final_render_mod, tmp_path):
    out = tmp_path / "v.mp4"
    meta = final_render_mod.render_final_story_video(tmp_path / "missing.json", output_video=out)
    assert meta["video_created"] is False
    assert "timeline_manifest_invalid_or_missing" in meta["blocking_reasons"]
    assert meta["scene_count"] == 0


def test_render_invalid_json_timeline_graceful(final_render_mod, tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    meta = final_render_mod.render_final_story_video(p, output_video=tmp_path / "v.mp4")
    assert meta["video_created"] is False
    assert "timeline_manifest_invalid_or_missing" in meta["blocking_reasons"]


def test_render_empty_scenes_graceful(final_render_mod, tmp_path):
    p = tmp_path / "empty.json"
    p.write_text(json.dumps({"scenes": []}), encoding="utf-8")
    meta = final_render_mod.render_final_story_video(p, output_video=tmp_path / "v.mp4")
    assert meta["video_created"] is False
    assert "timeline_scenes_empty" in meta["blocking_reasons"]


def test_render_assets_directory_missing(final_render_mod, tmp_path):
    p = tmp_path / "tl.json"
    p.write_text(
        json.dumps(
            {
                "assets_directory": str(tmp_path / "nonexistent_dir_xyz"),
                "scenes": [{"image_path": "a.png", "duration_seconds": 1}],
            }
        ),
        encoding="utf-8",
    )
    meta = final_render_mod.render_final_story_video(
        p, output_video=tmp_path / "v.mp4", ffmpeg_bin="ffmpeg_placeholder"
    )
    assert meta["video_created"] is False
    assert "assets_directory_missing" in meta["blocking_reasons"]


def _setup_two_scene_assets(assets_dir: Path) -> None:
    assets_dir.mkdir(parents=True, exist_ok=True)
    for name in ("scene_001.png", "scene_002.png"):
        (assets_dir / name).write_bytes(b"\x89PNG\r\n\x1a\n")


def test_render_short_audio_uses_timeline_not_shortest(final_render_mod, tmp_path, monkeypatch):
    """Kurzes Audio darf die Videolänge nicht auf -shortest kürzen; apad auf Timeline."""
    assets = tmp_path / "gen"
    _setup_two_scene_assets(assets)
    (tmp_path / "short.mp3").write_bytes(b"fake")  # wird von ffmpeg nicht gelesen (mock)

    tl_path = tmp_path / "tl.json"
    tl_path.write_text(
        json.dumps(
            {
                "assets_directory": str(assets),
                "audio_path": str(tmp_path / "short.mp3"),
                "scenes": [
                    {"image_path": "scene_001.png", "duration_seconds": 6},
                    {"image_path": "scene_002.png", "duration_seconds": 6},
                ],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "out.mp4"
    captured: list[list[str]] = []

    def fake_run(cmd, check=True, capture_output=True, text=True):
        captured.append(list(cmd))
        out.touch()
        return CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(final_render_mod.subprocess, "run", fake_run)

    def fake_probe_audio(_path, _ffprobe):
        return 2.0, []

    monkeypatch.setattr(final_render_mod, "_probe_audio_duration", fake_probe_audio)
    monkeypatch.setattr(final_render_mod, "_probe_video_duration", lambda _v, _f: (12.0, []))

    meta = final_render_mod.render_final_story_video(
        tl_path,
        output_video=out,
        motion_mode="static",
        ffmpeg_bin="ffmpeg_mock",
        ffprobe_bin="ffprobe_mock",
    )
    assert meta["video_created"] is True
    assert meta["duration_seconds"] == 12.0
    assert meta.get("motion_applied") is False
    assert "audio_shorter_than_timeline_padded_or_continued" in meta["warnings"]
    assert captured, "ffmpeg sollte aufgerufen werden"
    cmd = captured[0]
    assert "-shortest" not in cmd
    fc = next(x for x in cmd if x.startswith("[1:a]"))
    assert "atrim=duration=12.000000" in fc
    assert "apad=whole_dur=12.000000" in fc


def test_render_missing_audio_still_silent_an(final_render_mod, tmp_path, monkeypatch):
    assets = tmp_path / "gen2"
    _setup_two_scene_assets(assets)
    tl_path = tmp_path / "tl2.json"
    tl_path.write_text(
        json.dumps(
            {
                "assets_directory": str(assets),
                "audio_path": "",
                "scenes": [
                    {"image_path": "scene_001.png", "duration_seconds": 6},
                    {"image_path": "scene_002.png", "duration_seconds": 6},
                ],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "silent.mp4"
    captured: list[list[str]] = []

    def fake_run(cmd, check=True, capture_output=True, text=True):
        captured.append(list(cmd))
        out.touch()
        return CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(final_render_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(final_render_mod, "_probe_video_duration", lambda _v, _f: (12.0, []))

    meta = final_render_mod.render_final_story_video(
        tl_path,
        output_video=out,
        motion_mode="static",
        ffmpeg_bin="ffmpeg_mock",
        ffprobe_bin="ffprobe_mock",
    )
    assert meta["video_created"] is True
    assert meta.get("motion_applied") is False
    assert "audio_missing_silent_render" in meta["warnings"]
    cmd = captured[0]
    assert "-an" in cmd
    assert "-shortest" not in cmd
    assert "-filter_complex" not in cmd


def test_basic_motion_builds_filter_script_with_xfade_and_zoompan(final_render_mod, tmp_path, monkeypatch):
    assets = tmp_path / "genm"
    _setup_two_scene_assets(assets)
    tl_path = tmp_path / "tl_motion.json"
    tl_path.write_text(
        json.dumps(
            {
                "assets_directory": str(assets),
                "audio_path": "",
                "scenes": [
                    {
                        "image_path": "scene_001.png",
                        "duration_seconds": 6,
                        "zoom_type": "slow_push",
                        "pan_direction": "none",
                        "transition": "fade",
                    },
                    {
                        "image_path": "scene_002.png",
                        "duration_seconds": 6,
                        "zoom_type": "static",
                        "pan_direction": "left",
                        "transition": "fade",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "motion.mp4"
    captured: list[list[str]] = []
    script_snapshots: list[str] = []

    def fake_run(cmd, check=True, capture_output=True, text=True):
        captured.append(list(cmd))
        if "-filter_complex_script" in cmd:
            si = cmd.index("-filter_complex_script") + 1
            script_snapshots.append(Path(cmd[si]).read_text(encoding="utf-8"))
        out.touch()
        return CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(final_render_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(final_render_mod, "_probe_video_duration", lambda _v, _f: (11.65, []))

    meta = final_render_mod.render_final_story_video(
        tl_path,
        output_video=out,
        motion_mode="basic",
        ffmpeg_bin="ffmpeg_mock",
        ffprobe_bin="ffprobe_mock",
    )
    assert meta["video_created"] is True
    assert meta.get("motion_applied") is True
    assert meta.get("motion_mode") == "basic"
    cmd = captured[0]
    assert "-filter_complex_script" in cmd
    assert script_snapshots, "Skript sollte vor ffmpeg-Löschung eingelesen werden"
    script = script_snapshots[0]
    assert "xfade" in script
    assert "zoompan" in script
    assert "-f concat" not in " ".join(cmd)


def test_basic_motion_failure_falls_back_static(final_render_mod, tmp_path, monkeypatch):
    assets = tmp_path / "genfb"
    _setup_two_scene_assets(assets)
    tl_path = tmp_path / "tl_fb.json"
    tl_path.write_text(
        json.dumps(
            {
                "assets_directory": str(assets),
                "audio_path": "",
                "scenes": [
                    {"image_path": "scene_001.png", "duration_seconds": 4, "zoom_type": "slow_push"},
                    {"image_path": "scene_002.png", "duration_seconds": 4, "zoom_type": "static"},
                ],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "fallback.mp4"
    calls: list[list[str]] = []

    def fake_run(cmd, check=True, capture_output=True, text=True):
        calls.append(list(cmd))
        if len(calls) == 1:
            raise subprocess.CalledProcessError(1, cmd, stderr="motion_graph_failed")
        Path(cmd[-1]).touch()
        return CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(final_render_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(final_render_mod, "_probe_video_duration", lambda _v, _f: (8.0, []))

    meta = final_render_mod.render_final_story_video(
        tl_path,
        output_video=out,
        motion_mode="basic",
        ffmpeg_bin="ffmpeg_mock",
        ffprobe_bin="ffprobe_mock",
    )
    assert meta["video_created"] is True
    assert "motion_render_failed_fallback_static" in meta["warnings"]
    assert meta.get("motion_applied") is False
    assert len(calls) == 2
    assert any("-filter_complex_script" in c for c in calls)
    assert any("-f" in c and "concat" in c for c in calls)


def test_motion_mode_unknown_warns_and_uses_basic(final_render_mod, tmp_path, monkeypatch):
    assets = tmp_path / "genunk"
    _setup_two_scene_assets(assets)
    tl_path = tmp_path / "tl_unk.json"
    tl_path.write_text(
        json.dumps(
            {
                "assets_directory": str(assets),
                "audio_path": "",
                "scenes": [
                    {"image_path": "scene_001.png", "duration_seconds": 3},
                    {"image_path": "scene_002.png", "duration_seconds": 3},
                ],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "unk.mp4"

    def fake_run(cmd, check=True, capture_output=True, text=True):
        out.touch()
        return CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(final_render_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(final_render_mod, "_probe_video_duration", lambda _v, _f: (5.65, []))

    meta = final_render_mod.render_final_story_video(
        tl_path,
        output_video=out,
        motion_mode="not_a_mode",
        ffmpeg_bin="ffmpeg_mock",
        ffprobe_bin="ffprobe_mock",
    )
    assert any(w.startswith("motion_mode_unknown_defaulting_basic:") for w in meta["warnings"])
    assert meta.get("motion_mode") == "basic"
