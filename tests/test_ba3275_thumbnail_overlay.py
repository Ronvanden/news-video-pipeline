"""BA 32.75 — Thumbnail Text Overlay V1 (local only)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

from app.production_connectors.thumbnail_overlay import (
    build_thumbnail_text_variants_v1,
    render_thumbnail_overlay_v1,
    run_thumbnail_overlay_v1,
)


def _write_test_png(path: Path, size=(1024, 1024)) -> None:
    from PIL import Image

    im = Image.new("RGB", size, color=(30, 40, 60))
    im.save(path, format="PNG")


def test_text_variants_for_german_title_mann() -> None:
    out = build_thumbnail_text_variants_v1(
        title="Der Mann, der spurlos verschwand",
        summary="",
        language="de",
        max_variants=3,
    )
    assert out["thumbnail_overlay_version"] == "ba32_75_v1"
    tv = out["text_variants"]
    assert len(tv) == 3
    a = tv[0]
    assert a["variant_id"] == "text_a"
    assert a["line_1"] == "SPURLOS"
    assert a["line_2"] == "WEG"
    for v in tv:
        # max 2 lines
        assert "line_1" in v
        # Ensure uppercase and not empty
        assert str(v["line_1"]).strip() == str(v["line_1"]).strip().upper()


def test_overlay_renders_png_1280x720(tmp_path: Path) -> None:
    src = tmp_path / "in.png"
    dst = tmp_path / "out.png"
    _write_test_png(src, (800, 800))
    r = render_thumbnail_overlay_v1(
        image_path=src,
        output_path=dst,
        line_1="DER MANN",
        line_2="VERSCHWAND",
        position="auto_right",
        canvas_size=(1280, 720),
        style_preset="impact_youtube",
    )
    assert r["ok"] is True
    assert Path(r["output_path"]).is_file()
    assert r.get("style_preset") == "impact_youtube"
    from PIL import Image

    im = Image.open(dst)
    assert im.size == (1280, 720)


def test_run_thumbnail_overlay_writes_report(tmp_path: Path) -> None:
    src = tmp_path / "cand.png"
    _write_test_png(src, (1024, 1024))
    out = run_thumbnail_overlay_v1(
        image_path=src,
        title="Der Mann, der spurlos verschwand",
        summary=None,
        text_variant=None,
        output_dir=tmp_path / "out",
        position="auto_right",
        language="de",
    )
    assert out["thumbnail_overlay_version"] == "ba32_75_v1"
    op = Path(out["output_path"])
    assert op.is_file()
    rp = Path(out["result_path"])
    assert rp.is_file()
    j = json.loads(rp.read_text(encoding="utf-8"))
    assert j["output_path"].endswith("thumbnail_final.png")


def test_cli_smoke_works_with_test_image(tmp_path: Path, capsys) -> None:
    src = tmp_path / "img.png"
    _write_test_png(src, (1024, 1024))

    script = Path(__file__).resolve().parents[1] / "scripts" / "run_thumbnail_overlay_smoke.py"
    spec = importlib.util.spec_from_file_location("run_thumb_overlay_smoke_ba3275", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with patch.object(
        sys,
        "argv",
        [
            "run_thumbnail_overlay_smoke.py",
            "--image-path",
            str(src),
            "--run-id",
            "t1",
            "--title",
            "Der Mann, der spurlos verschwand",
            "--out-root",
            str(tmp_path),
            "--text",
            "DER MANN|VERSCHWAND",
            "--style-preset",
            "impact_youtube",
        ],
    ):
        rc = mod.main()
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert Path(out["output_path"]).is_file()

