"""BA 26.6 — Visual Founder Upgrade: textfreie cinematic Placeholder + Video-Reuse."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_url_to_final_mp4.py"


@pytest.fixture(scope="module")
def ba266_mod():
    spec = importlib.util.spec_from_file_location("run_url_to_final_mp4_ba266", _SCRIPT)
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
            "color=c=blue:s=320x240:r=25",
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


def _minimal_script(path: Path, *, n_chapters: int) -> None:
    chapters = [{"title": f"Kapitel {i+1}", "content": f"Inhalt {i+1}. " * 6} for i in range(n_chapters)]
    doc = {
        "title": "Founder-Test",
        "hook": "Kurzer Hook für BA 26.6.",
        "chapters": chapters,
        "full_script": "",
        "sources": [],
        "warnings": [],
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Cinematic Placeholder ist textfrei (keine Drawtext-Aufrufe)
# ---------------------------------------------------------------------------


def test_cinematic_placeholder_function_uses_no_drawtext(ba266_mod):
    import inspect

    src = inspect.getsource(ba266_mod._draw_cinematic_placeholder_png)
    assert "draw.text" not in src, "Cinematic Placeholder darf keinen Text zeichnen"
    assert "ImageFont" not in src, "Cinematic Placeholder darf keine Schriftart laden"


def test_cinematic_placeholder_renders_png(ba266_mod, tmp_path):
    target = tmp_path / "scene_001.png"
    ba266_mod._draw_cinematic_placeholder_png(target, scene_number=1, total_scenes=3)
    assert target.is_file()
    assert target.stat().st_size > 1000


# ---------------------------------------------------------------------------
# Asset-Runner-Override: Bild-Szenen-PNGs werden cinematic überschrieben
# (kein scene-spezifischer Text mehr → Pixelflächen vergleichbar)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_image_scene_pngs_are_text_free_after_ba266_override(ba266_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=3)
    out = tmp_path / "out266a"
    doc = ba266_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=3,
        duration_seconds=24,
        asset_dir=None,
        run_id="t266a",
        motion_mode="basic",
    )
    assert doc.get("ok") is True
    gen_dirs = list(out.glob("generated_assets_*"))
    assert gen_dirs, "Asset-Runner muss generated_assets_* erzeugen"
    pngs = sorted(gen_dirs[0].glob("scene_*.png"))
    assert len(pngs) >= 2
    sizes = {p.stat().st_size for p in pngs}
    assert len(sizes) == 1, (
        f"BA 26.6 erwartet textfreie cinematic Placeholder pro Szene → identische Bytegröße. "
        f"Gefundene Größen: {sizes}"
    )
    base_bytes = pngs[0].read_bytes()
    for p in pngs[1:]:
        assert p.read_bytes() == base_bytes, "Cinematic Placeholder pro Szene muss identisch sein"
    warns = " ".join(doc.get("warnings") or [])
    assert "ba266_cinematic_placeholder_applied" in warns


# ---------------------------------------------------------------------------
# Video-Reuse: weniger Videos als Szenen → derselbe Clip wird allen Szenen zugewiesen
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_single_video_reused_across_all_scenes(ba266_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=3)
    assets = tmp_path / "assets"
    assets.mkdir()
    clip = assets / "single_clip.mp4"
    _write_min_mp4(clip)
    out = tmp_path / "out266b"
    doc = ba266_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=3,
        duration_seconds=24,
        asset_dir=assets,
        run_id="t266b",
        motion_mode="static",
    )
    assert doc.get("ok") is True
    pack = json.loads((out / "scene_asset_pack.json").read_text(encoding="utf-8"))
    beats = (pack.get("scene_expansion") or {}).get("expanded_scene_assets") or []
    assert len(beats) == 3
    paths = [str(b.get("runway_clip_path") or "") for b in beats]
    assert all("single_clip.mp4" in p for p in paths), f"alle Szenen müssen den Clip referenzieren: {paths}"
    warns = " ".join(doc.get("warnings") or [])
    assert "ba266_video_reuse_for_remaining_scenes" in warns
    assert int(doc.get("used_video_assets_count") or 0) == 3


# ---------------------------------------------------------------------------
# Mehr Videos als Szenen → jede Szene bekommt ihr eigenes Video, kein Reuse
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _ffmpeg_ok(), reason="ffmpeg not available")
def test_multiple_videos_no_reuse_warning(ba266_mod, tmp_path):
    script_p = tmp_path / "in.json"
    _minimal_script(script_p, n_chapters=2)
    assets = tmp_path / "assets"
    assets.mkdir()
    _write_min_mp4(assets / "a.mp4")
    _write_min_mp4(assets / "b.mp4")
    out = tmp_path / "out266c"
    doc = ba266_mod.run_ba265_url_to_final(
        url=None,
        script_json_path=script_p,
        out_dir=out,
        max_scenes=2,
        duration_seconds=20,
        asset_dir=assets,
        run_id="t266c",
        motion_mode="static",
    )
    warns = " ".join(doc.get("warnings") or [])
    assert "ba266_video_reuse_for_remaining_scenes" not in warns
    pack = json.loads((out / "scene_asset_pack.json").read_text(encoding="utf-8"))
    beats = (pack.get("scene_expansion") or {}).get("expanded_scene_assets") or []
    paths = [str(b.get("runway_clip_path") or "") for b in beats]
    assert any("a.mp4" in p for p in paths)
    assert any("b.mp4" in p for p in paths)
