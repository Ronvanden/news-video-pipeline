"""BA 25.1 — Tests für scripts/run_real_video_build.py (Orchestrator)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_real_video_build.py"


@pytest.fixture(scope="module")
def real_build_mod():
    spec = importlib.util.spec_from_file_location("run_real_video_build", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_pack(tmp: Path, *, beats: int = 3) -> Path:
    expanded: List[Dict[str, Any]] = []
    for j in range(beats):
        expanded.append(
            {
                "chapter_index": 0,
                "beat_index": j,
                "visual_prompt": f"Establishing shot {j + 1} mit ruhiger Bildsprache.",
                "camera_motion_hint": "static",
                "duration_seconds": 4,
                "asset_type": "establishing",
                "continuity_note": "",
                "safety_notes": [],
            }
        )
    pack = {
        "export_version": "18.2-v1",
        "source_label": "test:fixture",
        "template_type": "documentary_news",
        "video_template": "documentary_explainer",
        "hook": "Kurze Test-Story.",
        "scene_expansion": {"expanded_scene_assets": expanded},
    }
    p = tmp / "scene_asset_pack.json"
    p.write_text(json.dumps(pack), encoding="utf-8")
    return p


def _ok_steps(real_build_mod, tmp_path: Path):
    """Liefert ein Set fertiger Step-Mocks, die einen erfolgreichen Lauf simulieren."""
    asset_dir = tmp_path / "generated_assets_x"
    asset_dir.mkdir(parents=True, exist_ok=True)
    asset_manifest = asset_dir / "asset_manifest.json"
    asset_manifest.write_text(
        json.dumps(
            {
                "run_id": "x",
                "source_pack": "x",
                "asset_count": 3,
                "generation_mode": "placeholder",
                "warnings": [],
                "assets": [
                    {"scene_number": i + 1, "image_path": f"scene_{i + 1:03d}.png"}
                    for i in range(3)
                ],
            }
        ),
        encoding="utf-8",
    )

    timeline_dir = tmp_path / "timeline_x"
    timeline_dir.mkdir(parents=True, exist_ok=True)
    timeline_manifest = timeline_dir / "timeline_manifest.json"

    def fake_asset_runner(pack_path, out_root, *, run_id, mode, **kw):
        return {
            "ok": True,
            "manifest_path": str(asset_manifest),
            "asset_count": 3,
            "warnings": [],
        }

    def fake_timeline_writer(am_data, *, asset_manifest_path, audio_path, run_id,
                             scene_duration_seconds, out_root):
        body = {
            "run_id": run_id,
            "audio_path": str(audio_path) if audio_path else "",
            "scenes": [
                {"scene_number": 1, "image_path": "scene_001.png", "duration_seconds": 4},
                {"scene_number": 2, "image_path": "scene_002.png", "duration_seconds": 4},
                {"scene_number": 3, "image_path": "scene_003.png", "duration_seconds": 4},
            ],
            "estimated_duration_seconds": 12,
        }
        timeline_manifest.write_text(json.dumps(body), encoding="utf-8")
        return timeline_manifest, body

    def fake_voiceover(*, pack_data, run_id, out_root, voice_mode, voiceover_mod, **kw):
        voice_dir = Path(out_root).resolve() / f"full_voice_{run_id}"
        voice_dir.mkdir(parents=True, exist_ok=True)
        narration = voice_dir / "narration_script.txt"
        narration.write_text("# header\nNarration body line.", encoding="utf-8")
        mp3 = voice_dir / "full_voiceover.mp3"
        mp3.write_bytes(b"\x00\x01")
        step = real_build_mod._step(
            "voiceover_smoke",
            ok=True,
            output=str(mp3),
            warnings=[],
            blocking_reasons=[],
            extra={"real_tts_generated": False},
        )
        return step, {"voiceover_audio": str(mp3), "narration_script": str(narration)}

    def fake_render(timeline_path, *, output_video, motion_mode, subtitle_path,
                    run_id, write_output_manifest, manifest_root, **kw):
        Path(output_video).parent.mkdir(parents=True, exist_ok=True)
        Path(output_video).write_bytes(b"clean")
        return {"video_created": True, "warnings": [], "blocking_reasons": [],
                "output_path": str(Path(output_video).resolve())}

    sub_dir = tmp_path / "subtitles_x"
    sub_dir.mkdir(parents=True, exist_ok=True)
    srt_path = sub_dir / "subtitles.srt"
    srt_path.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nA.\n\n2\n00:00:02,100 --> 00:00:04,000\nB.\n",
        encoding="utf-8",
    )
    sub_man = sub_dir / "subtitle_manifest.json"
    sub_man.write_text(json.dumps({"subtitles_srt_path": str(srt_path)}), encoding="utf-8")

    def fake_subtitle_build(narration_script_path, *, timeline_manifest_path, out_root,
                            run_id, subtitle_mode, subtitle_source, subtitle_style,
                            audio_path, **kw):
        return {
            "ok": True,
            "subtitle_manifest_path": str(sub_man),
            "subtitles_srt_path": str(srt_path),
            "warnings": [],
            "blocking_reasons": [],
        }

    def fake_burn_in(input_video, subtitle_manifest, *, out_root, run_id, force, **kw):
        burn_dir = Path(out_root).resolve() / f"subtitle_burnin_{run_id}"
        burn_dir.mkdir(parents=True, exist_ok=True)
        out_mp4 = burn_dir / "preview_with_subtitles.mp4"
        out_mp4.write_bytes(b"preview")
        return {
            "ok": True,
            "skipped": False,
            "output_video_path": str(out_mp4),
            "warnings": [],
            "blocking_reasons": [],
        }

    return {
        "asset_runner_fn": fake_asset_runner,
        "timeline_writer_fn": fake_timeline_writer,
        "voiceover_smoke_fn": fake_voiceover,
        "render_fn": fake_render,
        "subtitle_build_fn": fake_subtitle_build,
        "burn_in_fn": fake_burn_in,
    }


def test_validate_run_id(real_build_mod):
    assert real_build_mod._validate_run_id("real_test_001") is True
    assert real_build_mod._validate_run_id("Run-2026") is True
    assert real_build_mod._validate_run_id("") is False
    assert real_build_mod._validate_run_id("../escape") is False
    assert real_build_mod._validate_run_id("a/b") is False
    assert real_build_mod._validate_run_id("a\\b") is False


def test_derive_narration_uses_visual_prompts(real_build_mod):
    pack = {
        "hook": "Hook line.",
        "scene_expansion": {
            "expanded_scene_assets": [
                {"chapter_index": 0, "beat_index": 0, "visual_prompt": "Alpha visual."},
                {"chapter_index": 0, "beat_index": 1, "visual_prompt": "Beta visual."},
            ],
        },
    }
    text = real_build_mod.derive_narration_from_scene_pack(pack)
    assert "Hook line." in text
    assert "Szene 1" in text
    assert "Alpha visual" in text
    assert "Szene 2" in text
    assert "Beta visual" in text


def test_derive_narration_empty_pack(real_build_mod):
    assert real_build_mod.derive_narration_from_scene_pack({}) == ""
    assert real_build_mod.derive_narration_from_scene_pack({"scene_expansion": {}}) == ""


def test_run_real_video_build_happy_path(real_build_mod, tmp_path):
    pack = _write_pack(tmp_path)
    fns = _ok_steps(real_build_mod, tmp_path)

    result = real_build_mod.run_real_video_build(
        run_id="rid_happy",
        scene_asset_pack=pack,
        out_root=tmp_path,
        **fns,
    )
    assert result["schema_version"] == "real_video_build_result_v1"
    assert result["run_id"] == "rid_happy"
    assert result["status"] == "completed"
    assert result["ok"] is True
    assert result["blocking_reasons"] == []
    names = [s["name"] for s in result["steps"]]
    assert names == [
        "asset_runner",
        "voiceover_smoke",
        "timeline_builder",
        "clean_render",
        "subtitle_build",
        "burn_in_preview",
    ]
    expected_keys = {
        "scene_asset_pack",
        "asset_manifest",
        "timeline_manifest",
        "voiceover_audio",
        "narration_script",
        "clean_video",
        "subtitle_manifest",
        "subtitle_file",
        "preview_with_subtitles",
        "local_preview_dir",
        "final_render_dir",
        "final_video",
    }
    assert set(result["paths"].keys()) == expected_keys
    assert result["paths"]["preview_with_subtitles"].endswith("preview_with_subtitles.mp4")
    assert result["paths"]["final_render_dir"] == ""
    assert result["paths"]["final_video"] == ""

    build_dir = Path(result["build_dir"])
    assert build_dir.is_dir()
    result_file = build_dir / "real_video_build_result.json"
    assert result_file.is_file()
    parsed = json.loads(result_file.read_text(encoding="utf-8"))
    assert parsed["schema_version"] == "real_video_build_result_v1"
    assert parsed["status"] == "completed"


def test_invalid_run_id_returns_blocked(real_build_mod, tmp_path):
    pack = _write_pack(tmp_path)
    result = real_build_mod.run_real_video_build(
        run_id="../bad",
        scene_asset_pack=pack,
        out_root=tmp_path,
    )
    assert result["status"] == "blocked"
    assert result["ok"] is False
    assert "invalid_run_id" in result["blocking_reasons"]


def test_missing_scene_asset_pack_returns_blocked(real_build_mod, tmp_path):
    missing = tmp_path / "does_not_exist.json"
    result = real_build_mod.run_real_video_build(
        run_id="rid_missing",
        scene_asset_pack=missing,
        out_root=tmp_path,
    )
    assert result["status"] == "blocked"
    assert result["ok"] is False
    assert "scene_asset_pack_missing" in result["blocking_reasons"]
    # result file is still written for transparency
    result_file = Path(result["build_dir"]) / "real_video_build_result.json"
    assert result_file.is_file()


def test_asset_runner_failure_marks_failed(real_build_mod, tmp_path):
    pack = _write_pack(tmp_path)
    fns = _ok_steps(real_build_mod, tmp_path)

    def fail_asset(*_a, **_k):
        return {"ok": False, "manifest_path": "", "warnings": ["asset_failed"], "asset_count": 0}

    fns["asset_runner_fn"] = fail_asset

    result = real_build_mod.run_real_video_build(
        run_id="rid_assetfail",
        scene_asset_pack=pack,
        out_root=tmp_path,
        **fns,
    )
    assert result["status"] == "failed"
    assert result["ok"] is False
    assert any(s["name"] == "asset_runner" and s["ok"] is False for s in result["steps"])
    # Should NOT have continued to later steps
    names = [s["name"] for s in result["steps"]]
    assert "voiceover_smoke" not in names
    assert "asset_runner_failed" in result["blocking_reasons"]


def test_render_failure_marks_failed(real_build_mod, tmp_path):
    pack = _write_pack(tmp_path)
    fns = _ok_steps(real_build_mod, tmp_path)

    def fail_render(*_a, **_k):
        return {"video_created": False, "warnings": ["motion_render_failed_fallback_static"],
                "blocking_reasons": ["ffmpeg_encode_failed"]}

    fns["render_fn"] = fail_render

    result = real_build_mod.run_real_video_build(
        run_id="rid_renderfail",
        scene_asset_pack=pack,
        out_root=tmp_path,
        **fns,
    )
    assert result["status"] == "failed"
    assert result["ok"] is False
    assert "ffmpeg_encode_failed" in result["blocking_reasons"]
    names = [s["name"] for s in result["steps"]]
    assert "subtitle_build" not in names
    assert "burn_in_preview" not in names


def test_burn_in_failure_marks_failed(real_build_mod, tmp_path):
    pack = _write_pack(tmp_path)
    fns = _ok_steps(real_build_mod, tmp_path)

    def fail_burn(*_a, **_k):
        return {"ok": False, "skipped": False, "output_video_path": "",
                "warnings": ["ffmpeg_burnin_failed"], "blocking_reasons": ["ffmpeg_encode_failed"]}

    fns["burn_in_fn"] = fail_burn

    result = real_build_mod.run_real_video_build(
        run_id="rid_burnfail",
        scene_asset_pack=pack,
        out_root=tmp_path,
        **fns,
    )
    assert result["status"] == "failed"
    assert result["ok"] is False
    assert "ffmpeg_encode_failed" in result["blocking_reasons"]
    assert any(s["name"] == "burn_in_preview" and s["ok"] is False for s in result["steps"])


def test_voiceover_silent_path_does_not_block_render(real_build_mod, tmp_path):
    """Wenn smoke MP3 nicht erzeugt werden kann, läuft die Pipeline silent weiter."""
    pack = _write_pack(tmp_path)
    fns = _ok_steps(real_build_mod, tmp_path)

    def silent_voice(*, pack_data, run_id, out_root, voice_mode, voiceover_mod, **kw):
        # narration text vorhanden, aber kein MP3 (ffmpeg fehlt-Simulation)
        voice_dir = Path(out_root).resolve() / f"full_voice_{run_id}"
        voice_dir.mkdir(parents=True, exist_ok=True)
        nar = voice_dir / "narration_script.txt"
        nar.write_text("body", encoding="utf-8")
        step = real_build_mod._step(
            "voiceover_smoke",
            ok=True,
            output=str(nar),
            warnings=["voiceover_smoke_skipped_ffmpeg_missing"],
            blocking_reasons=[],
        )
        return step, {"voiceover_audio": "", "narration_script": str(nar)}

    fns["voiceover_smoke_fn"] = silent_voice

    result = real_build_mod.run_real_video_build(
        run_id="rid_silent",
        scene_asset_pack=pack,
        out_root=tmp_path,
        **fns,
    )
    assert result["status"] == "completed"
    assert result["paths"]["voiceover_audio"] == ""
    assert "timeline_audio_path_not_wired" in result["warnings"]


def test_no_url_input_in_cli(real_build_mod):
    """BA 25.1: CLI darf keinen URL-Eingang haben (kommt erst BA 25.2/25.3)."""
    parser_help = real_build_mod.main.__doc__ or ""
    # negativ checken: kein --url im argparse
    with pytest.raises(SystemExit) as exc:
        real_build_mod.main(["--url", "https://example.com", "--run-id", "x"])
    assert exc.value.code != 0
    # auch der Source darf "--url" nicht als option aufnehmen
    src = _SCRIPT.read_text(encoding="utf-8")
    assert '"--url"' not in src
    assert "manual_source_url" not in src


def test_cli_requires_run_id_and_pack(real_build_mod):
    with pytest.raises(SystemExit):
        real_build_mod.main([])
    with pytest.raises(SystemExit):
        real_build_mod.main(["--run-id", "rid"])


def test_cli_invalid_run_id_exit_3(real_build_mod, tmp_path, capsys):
    pack = _write_pack(tmp_path)
    rc = real_build_mod.main([
        "--run-id", "../bad",
        "--scene-asset-pack", str(pack),
        "--out-root", str(tmp_path),
        "--print-json",
    ])
    assert rc == 3
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["status"] == "blocked"
    assert "invalid_run_id" in parsed["blocking_reasons"]


def test_cli_missing_pack_exit_3(real_build_mod, tmp_path, capsys):
    rc = real_build_mod.main([
        "--run-id", "rid",
        "--scene-asset-pack", str(tmp_path / "nope.json"),
        "--out-root", str(tmp_path),
        "--print-json",
    ])
    assert rc == 3
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert "scene_asset_pack_missing" in parsed["blocking_reasons"]


def test_print_json_outputs_parsable_json(real_build_mod, tmp_path, capsys, monkeypatch):
    """--print-json soll parsebares JSON ausgeben (Happy-Path mit Mocks via monkeypatch)."""
    pack = _write_pack(tmp_path)
    fns = _ok_steps(real_build_mod, tmp_path)

    original_run = real_build_mod.run_real_video_build

    def patched_run(**kwargs):
        return original_run(**kwargs, **fns)

    monkeypatch.setattr(real_build_mod, "run_real_video_build", patched_run)

    rc = real_build_mod.main([
        "--run-id", "rid_print",
        "--scene-asset-pack", str(pack),
        "--out-root", str(tmp_path),
        "--print-json",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["run_id"] == "rid_print"
    assert parsed["status"] == "completed"


def test_result_manifest_has_all_required_path_keys(real_build_mod, tmp_path):
    pack = _write_pack(tmp_path)
    fns = _ok_steps(real_build_mod, tmp_path)
    result = real_build_mod.run_real_video_build(
        run_id="rid_keys",
        scene_asset_pack=pack,
        out_root=tmp_path,
        **fns,
    )
    for key in real_build_mod._REQUIRED_PATH_KEYS:
        assert key in result["paths"], f"missing path key: {key}"


def test_metadata_persisted(real_build_mod, tmp_path):
    pack = _write_pack(tmp_path)
    fns = _ok_steps(real_build_mod, tmp_path)
    result = real_build_mod.run_real_video_build(
        run_id="rid_meta",
        scene_asset_pack=pack,
        out_root=tmp_path,
        asset_mode="placeholder",
        voice_mode="smoke",
        motion_mode="static",
        subtitle_style="typewriter",
        subtitle_mode="simple",
        force=True,
        **fns,
    )
    md = result["metadata"]
    assert md["asset_mode"] == "placeholder"
    assert md["voice_mode"] == "smoke"
    assert md["motion_mode"] == "static"
    assert md["subtitle_style"] == "typewriter"
    assert md["subtitle_mode"] == "simple"
    assert md["force"] is True
