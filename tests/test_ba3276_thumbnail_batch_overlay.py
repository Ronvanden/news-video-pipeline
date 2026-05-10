"""BA 32.76 — Thumbnail Batch Overlay + Selection V1 (local only)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

from app.production_connectors.thumbnail_batch_overlay import run_thumbnail_batch_overlay_v1


def _write_candidate_png(path: Path, size=(1024, 1024), color=(50, 60, 80)) -> None:
    from PIL import Image

    im = Image.new("RGB", size, color=color)
    im.save(path, format="PNG")


def test_batch_generates_outputs_and_recommendation(tmp_path: Path) -> None:
    cdir = tmp_path / "cands"
    cdir.mkdir()
    a = cdir / "thumbnail_candidate_thumb_a.png"
    b = cdir / "thumbnail_candidate_thumb_b.png"
    c = cdir / "thumbnail_candidate_thumb_c.png"
    _write_candidate_png(a, color=(40, 50, 70))
    _write_candidate_png(b, color=(30, 30, 30))
    _write_candidate_png(c, color=(70, 60, 40))

    out_dir = tmp_path / "out"
    res = run_thumbnail_batch_overlay_v1(
        candidate_paths=[str(a), str(b), str(c)],
        title="Der Mann, der spurlos verschwand",
        summary=None,
        output_dir=out_dir,
        language="de",
        max_outputs=4,
        style_presets=["impact_youtube", "urgent_mystery"],
        text_variants=None,
    )
    assert res["thumbnail_batch_overlay_version"] == "ba32_76_v1"
    assert res["generated_count"] <= 4
    outs = res["outputs"]
    assert len(outs) == res["generated_count"]
    assert res["recommended_thumbnail"] is not None
    for o in outs:
        assert 0 <= int(o["score"]) <= 100
        assert isinstance(o.get("score_reasons"), list) and len(o["score_reasons"]) > 0
        op = Path(o["output_path"])
        assert op.is_file()
        from PIL import Image

        im = Image.open(op)
        assert im.size == (1280, 720)
    rp = Path(res["result_path"])
    assert rp.is_file()


def test_cli_candidate_dir_works(tmp_path: Path, capsys) -> None:
    cand = tmp_path / "cand_dir"
    cand.mkdir()
    _write_candidate_png(cand / "thumbnail_candidate_thumb_a.png")

    script = Path(__file__).resolve().parents[1] / "scripts" / "run_thumbnail_batch_overlay_smoke.py"
    spec = importlib.util.spec_from_file_location("run_thumb_batch_smoke_ba3276", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with patch.object(
        sys,
        "argv",
        [
            "run_thumbnail_batch_overlay_smoke.py",
            "--candidate-dir",
            str(cand),
            "--run-id",
            "x",
            "--title",
            "Der Mann, der spurlos verschwand",
            "--out-root",
            str(tmp_path),
            "--max-outputs",
            "2",
        ],
    ):
        rc = mod.main()
    assert rc == 0
    j = json.loads(capsys.readouterr().out)
    assert j.get("ok") is True
    assert j.get("generated_count") >= 1


def test_cli_no_candidates_exit_2(capsys, tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "run_thumbnail_batch_overlay_smoke.py"
    spec = importlib.util.spec_from_file_location("run_thumb_batch_smoke_ba3276b", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with patch.object(sys, "argv", ["run_thumbnail_batch_overlay_smoke.py", "--title", "t"]):
        rc = mod.main()
    assert rc == 2
    j = json.loads(capsys.readouterr().out)
    assert j.get("blocking_reason") == "thumbnail_batch_overlay_no_candidates"

