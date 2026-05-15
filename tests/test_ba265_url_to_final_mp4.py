"""BA 26.5 — URL/script.json + vorhandene Assets → final_video.mp4."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_url_to_final_mp4.py"


@pytest.fixture(scope="module")
def ba265_mod():
    spec = importlib.util.spec_from_file_location("run_url_to_final_mp4_t", _SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _ffmpeg_ok() -> bool:
    return shutil.which("ffmpeg") is not None


def _write_min_mp4(target: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=320x240:r=25",
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


def _minimal_script(path: Path, *, n_chapters: int = 4) -> None:
    chapters = [{"title": f"Kapitel {i+1}", "content": f"Inhalt Absatz {i+1}. " * 8} for i in range(n_chapters)]
    doc = {
        "title": "Testtitel",
        "hook": "Kurzer Hook für den Test.",
        "chapters": chapters,
        "full_script": "",
        "sources": ["https://example.com/a"],
        "warnings": [],
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_script_json_produces_run_summary_and_video(ba265_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=2)
    assets = tmp_path / "assets"
    assets.mkdir()
    clip = assets / "smoke.mp4"
    _write_min_mp4(clip)
    out = tmp_path / "out265"
    doc = ba265_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=3,
        duration_seconds=30,
        asset_dir=assets,
        run_id="t265",
        motion_mode="static",
    )
    summary = out / "run_summary.json"
    assert summary.is_file()
    loaded = json.loads(summary.read_text(encoding="utf-8"))
    assert loaded.get("input_mode") == "script_json"
    assert loaded.get("script_path")
    assert doc.get("ok") is True
    assert Path(doc["final_video_path"]).is_file()
    assert (out / "render_result.json").is_file()


def test_max_scenes_limits_scene_plan(ba265_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=6)
    out = tmp_path / "out265b"
    doc = ba265_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=2,
        duration_seconds=20,
        asset_dir=None,
        run_id="t265b",
        motion_mode="static",
    )
    if not _ffmpeg_ok():
        assert doc.get("ok") is False
        return
    plan = json.loads((out / "scene_plan.json").read_text(encoding="utf-8"))
    assert len(plan.get("scenes") or []) <= 2


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_mp4_in_asset_dir_becomes_runway_clip_path(ba265_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=1)
    assets = tmp_path / "assets"
    assets.mkdir()
    clip = assets / "clip_a.mp4"
    _write_min_mp4(clip)
    out = tmp_path / "out265c"
    ba265_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=2,
        duration_seconds=24,
        asset_dir=assets,
        run_id="t265c",
        motion_mode="static",
    )
    pack = json.loads((out / "scene_asset_pack.json").read_text(encoding="utf-8"))
    beats = (pack.get("scene_expansion") or {}).get("expanded_scene_assets") or []
    assert beats
    assert beats[0].get("runway_clip_path") == "../assets/clip_a.mp4" or "clip_a.mp4" in str(
        beats[0].get("runway_clip_path")
    )


def test_no_asset_dir_no_crash_warns(ba265_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=1)
    out = tmp_path / "out265d"
    doc = ba265_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=2,
        duration_seconds=20,
        asset_dir=None,
        run_id="t265d",
        motion_mode="static",
    )
    assert (out / "run_summary.json").is_file()
    w = " ".join(doc.get("warnings") or [])
    assert "no_assets_in_asset_dir_using_placeholder" in w or "no_existing_video_asset_found_using_fallback" in w
    if _ffmpeg_ok():
        assert doc.get("ok") is True
        assert Path(doc["final_video_path"]).is_file()


def test_url_extraction_empty_blocks(ba265_mod, tmp_path):
    out = tmp_path / "out265e"
    with patch.object(ba265_mod, "extract_text_from_url", return_value=("", [])):
        doc = ba265_mod.run_ba265_url_to_final(
            url="https://example.com/missing",
            script_json_path=None,
            out_dir=out,
            max_scenes=2,
            duration_seconds=20,
            asset_dir=None,
            run_id="t265e",
            motion_mode="static",
        )
    assert doc.get("ok") is False
    assert "url_extraction_empty_use_script_json" in (doc.get("blocking_reasons") or [])


def test_scene_asset_pack_uses_visual_prompt_engine_for_openai_image(ba265_mod, tmp_path):
    scene_rows = [
        {
            "title": "Warum Vertrauen in Experten plötzlich bröckelt",
            "narration": (
                "Ein neuer Gesundheitsfall sorgt für öffentliche Unsicherheit. Experten erklären ruhig, "
                "während Bürger zwischen Fakten, Angst und Misstrauen schwanken."
            ),
            "duration_seconds": 8,
        }
    ]
    pack = ba265_mod._build_scene_asset_pack(
        scene_rows,
        script={"title": "Visual Test", "hook": "", "video_template": "documentary_story"},
        rel_videos=[],
        pack_parent=tmp_path,
        image_provider="openai_image",
    )
    beats = (pack.get("scene_expansion") or {}).get("expanded_scene_assets") or []
    assert beats
    beat = beats[0]
    raw = str(beat.get("visual_prompt_raw") or "")
    effective = str(beat.get("visual_prompt_effective") or "")
    assert raw.strip()
    assert "Subject:" in raw
    assert "Environment:" in raw
    assert "Composition:" in raw
    assert "Subject:" in effective
    assert "[visual_no_text_guard_v26_4]" in effective
    assert effective.strip() != "[visual_no_text_guard_v26_4]"
    assert str(beat.get("negative_prompt") or "").strip()
    assert isinstance(beat.get("visual_prompt_anatomy"), dict)
    assert beat["visual_prompt_anatomy"].get("subject_description")
    assert (beat.get("normalized_controls") or {}).get("provider_target") == "openai_image"


def test_youtube_style_scene_asset_pack_derives_non_generic_anatomy(ba265_mod, tmp_path):
    scene_rows = [
        {
            "title": "Kapitel 1: Die Demokratie in Deutschland",
            "narration": (
                "Sarah Bosetti aeussert in ihrer neuesten Folge, dass menschliches Handeln zu dumm "
                "fuer die Demokratie sei. Doch wie steht es wirklich um die Demokratie in Deutschland?"
            ),
            "duration_seconds": 8,
        }
    ]
    pack = ba265_mod._build_scene_asset_pack(
        scene_rows,
        script={"title": "YouTube Visual Test", "hook": "", "video_template": "documentary_story"},
        rel_videos=[],
        pack_parent=tmp_path,
        image_provider="openai_image",
    )
    beat = ((pack.get("scene_expansion") or {}).get("expanded_scene_assets") or [])[0]
    anatomy = beat["visual_prompt_anatomy"]
    subject = anatomy["subject_description"].lower()
    environment = anatomy["environment"].lower()
    action = anatomy["action"].lower()
    assert anatomy["subject_description"] != scene_rows[0]["title"]
    assert "grounded documentary environment / editorial real-world setting" not in environment
    assert any(term in subject for term in ["political commentator", "documentary host", "public political debate"])
    assert any(term in environment for term in ["editorial studio", "newsroom desk", "political talk", "public media"])
    assert any(term in action for term in ["explains", "reviews", "public debate", "public reactions"])
