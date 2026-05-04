"""BA 21.0c — Preview-Artefakt Co-location / Pfad-Ausrichtung (ohne ffmpeg)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Dict

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_PIPELINE = _ROOT / "scripts" / "run_local_preview_pipeline.py"
_SMOKE = _ROOT / "scripts" / "run_local_preview_smoke.py"


@pytest.fixture(scope="module")
def preview_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_pipeline", _PIPELINE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def smoke_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_smoke", _SMOKE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._pipeline_mod = None
    yield mod
    mod._pipeline_mod = None


def test_colocate_copies_and_sets_preview_paths(preview_mod, tmp_path):
    pd = tmp_path / "local_preview_coloc1"
    pd.mkdir(parents=True)
    ext = tmp_path / "subtitle_burnin_x" / "preview_with_subtitles.mp4"
    ext.parent.mkdir(parents=True)
    ext.write_bytes(b"vid")
    r: Dict[str, Any] = {
        "ok": True,
        "run_id": "coloc1",
        "pipeline_dir": str(pd),
        "warnings": [],
        "blocking_reasons": [],
        "steps": {
            "burnin_preview": {"ok": True, "skipped": False, "output_video_path": str(ext), "warnings": []},
        },
        "paths": {"preview_with_subtitles": str(ext), "clean_video": str(pd / "clean_video.mp4")},
    }
    out = preview_mod.colocate_local_preview_video(r)
    central = pd / "preview_with_subtitles.mp4"
    assert central.is_file()
    assert central.read_bytes() == b"vid"
    assert Path(out["paths"]["preview_with_subtitles"]) == central.resolve()
    assert out["paths"]["preview_video"] == out["paths"]["preview_with_subtitles"]
    assert Path(out["paths"]["burnin_preview_source"]) == ext.resolve()


def test_colocate_missing_source_warns_no_crash(preview_mod, tmp_path):
    pd = tmp_path / "local_preview_coloc2"
    pd.mkdir()
    missing = tmp_path / "nope" / "preview_with_subtitles.mp4"
    r: Dict[str, Any] = {
        "ok": True,
        "pipeline_dir": str(pd),
        "warnings": [],
        "blocking_reasons": [],
        "steps": {},
        "paths": {"preview_with_subtitles": str(missing)},
    }
    out = preview_mod.colocate_local_preview_video(r)
    assert "preview_colocation_source_missing" in out["warnings"]
    assert out["paths"]["preview_with_subtitles"] == str(missing)


def test_colocate_source_equals_dest_sets_keys_only(preview_mod, tmp_path):
    pd = tmp_path / "local_preview_coloc3"
    pd.mkdir()
    f = pd / "preview_with_subtitles.mp4"
    f.write_bytes(b"a")
    r: Dict[str, Any] = {
        "ok": True,
        "pipeline_dir": str(pd),
        "warnings": [],
        "blocking_reasons": [],
        "paths": {"preview_with_subtitles": str(f)},
        "steps": {},
    }
    out = preview_mod.colocate_local_preview_video(r)
    assert "preview_colocation" not in " ".join(out["warnings"])
    assert out["paths"]["preview_video"] == str(f.resolve())
    assert out["paths"]["preview_with_subtitles"] == str(f.resolve())
    assert "burnin_preview_source" not in out["paths"]


def test_finalize_operator_artifacts_open_me_uses_central_preview(preview_mod, tmp_path):
    pd = tmp_path / "local_preview_coloc4"
    pd.mkdir(parents=True)
    ext_burn = tmp_path / "subtitle_burnin_rid" / "preview_with_subtitles.mp4"
    ext_burn.parent.mkdir(parents=True)
    ext_burn.write_bytes(b"x")
    r: Dict[str, Any] = {
        "ok": True,
        "run_id": "coloc4",
        "pipeline_dir": str(pd),
        "warnings": [],
        "blocking_reasons": [],
        "steps": {
            "burnin_preview": {"ok": True, "skipped": False, "output_video_path": str(ext_burn), "warnings": []},
            "build_subtitles": {"ok": True, "subtitle_manifest_path": "/m.json", "warnings": []},
            "render_clean": {"video_created": True, "output_path": str(pd / "clean_video.mp4"), "warnings": []},
        },
        "paths": {
            "clean_video": str(pd / "clean_video.mp4"),
            "preview_with_subtitles": str(ext_burn),
        },
    }
    r2 = preview_mod.colocate_local_preview_video(r)
    r3 = preview_mod.finalize_local_preview_operator_artifacts(r2)
    central = (pd / "preview_with_subtitles.mp4").resolve()
    om = (pd / "OPEN_ME.md").read_text(encoding="utf-8")
    open_first = om.split("## Open First", 1)[1].split("## What This Is", 1)[0]
    assert str(central) in open_first
    assert str(ext_burn.resolve()) not in open_first
    rep = (pd / "local_preview_report.md").read_text(encoding="utf-8")
    preview_block = rep.split("## Preview", 1)[1].split("## Run", 1)[0]
    assert str(central) in preview_block
    assert str(ext_burn.resolve()) not in preview_block
    assert r3["paths"]["preview_with_subtitles"] == str(central)


def test_smoke_summary_shows_central_preview_path(smoke_mod, preview_mod, tmp_path):
    pd = tmp_path / "local_preview_coloc5"
    pd.mkdir()
    src = tmp_path / "ext.mp4"
    src.write_bytes(b"p")
    r: Dict[str, Any] = {
        "ok": True,
        "run_id": "c5",
        "pipeline_dir": str(pd),
        "warnings": [],
        "blocking_reasons": [],
        "steps": {"burnin_preview": {"ok": True, "skipped": False, "output_video_path": str(src), "warnings": []}},
        "paths": {"preview_with_subtitles": str(src), "clean_video": str(pd / "c.mp4")},
    }
    r2 = preview_mod.colocate_local_preview_video(r)
    summary = smoke_mod.build_local_preview_smoke_summary(r2)
    central = (pd / "preview_with_subtitles.mp4").resolve()
    assert "Preview öffnen:" in summary
    assert str(central) in summary
    assert str(src.resolve()) not in summary.split("Preview öffnen:")[1].split("\n")[0]


def test_resolve_prefers_preview_video_over_preview_with_subtitles(smoke_mod):
    assert smoke_mod.resolve_local_preview_smoke_video_path(
        {"preview_video": "/a.mp4", "preview_with_subtitles": "/p.mp4", "clean_video": "/c.mp4"}
    ) == "/a.mp4"

