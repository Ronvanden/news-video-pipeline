"""BA 29.2c — Preview smoke auto-runner (path discovery, orchestration hooks, summary)."""

from __future__ import annotations

import json
from pathlib import Path

from app.production_assembly.preview_smoke_auto import (
    execute_preview_smoke_auto,
    find_newest_usable_asset_manifest,
    is_usable_asset_manifest,
)


def test_find_newest_usable_asset_manifest_picks_highest_mtime(tmp_path: Path):
    root = tmp_path / "output"
    old_dir = root / "pack_old"
    new_dir = root / "pack_new"
    old_dir.mkdir(parents=True)
    new_dir.mkdir(parents=True)

    doc = {"assets": [{"scene_number": 1, "visual_asset_kind": "still", "selected_asset_path": "x.png"}]}
    p_old = old_dir / "asset_manifest.json"
    p_new = new_dir / "asset_manifest.json"
    p_old.write_text(json.dumps(doc), encoding="utf-8")
    p_new.write_text(json.dumps(doc), encoding="utf-8")

    import os
    import time

    t_base = time.time() - 100
    os.utime(p_old, (t_base, t_base))
    os.utime(p_new, (t_base + 50, t_base + 50))

    picked = find_newest_usable_asset_manifest(root)
    assert picked is not None
    assert picked.resolve() == p_new.resolve()


def test_find_newest_skips_preview_smoke_work_tree(tmp_path: Path):
    root = tmp_path / "output"
    hidden = root / ".preview_smoke_work" / "x"
    vis = root / "visible"
    hidden.mkdir(parents=True)
    vis.mkdir(parents=True)
    doc = {"assets": [{"k": 1}]}
    (hidden / "asset_manifest.json").write_text(json.dumps(doc), encoding="utf-8")
    p_vis = vis / "asset_manifest.json"
    p_vis.write_text(json.dumps(doc), encoding="utf-8")
    assert find_newest_usable_asset_manifest(root).resolve() == p_vis.resolve()


def test_execute_fails_without_usable_manifest(tmp_path: Path):
    out = tmp_path / "output"
    out.mkdir()
    summ, code = execute_preview_smoke_auto(run_id="nom", output_root=out)
    assert code == 2
    assert summ["ok"] is False
    assert "no_usable_asset_manifest" in str(summ.get("operator_blocking_reasons", []))


def test_is_usable_asset_manifest_requires_assets(tmp_path: Path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps({"assets": []}), encoding="utf-8")
    assert is_usable_asset_manifest(p) is False
    p.write_text(json.dumps({"assets": [{"a": 1}]}), encoding="utf-8")
    assert is_usable_asset_manifest(p) is True


def test_execute_passes_bundle_to_preview_mock(tmp_path: Path, monkeypatch):
    out = tmp_path / "output"
    out.mkdir(parents=True)
    work = out / "w"
    work.mkdir()
    img = work / "scene.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    am = {
        "assets": [
            {
                "scene_number": 1,
                "visual_asset_kind": "motion_clip",
                "selected_asset_path": str(img),
                "visual_prompt_effective": "p",
            }
        ],
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
        "visual_cost_summary": {"total_units": 1.0, "by_kind": {}},
    }
    am_path = work / "asset_manifest.json"
    am_path.write_text(json.dumps(am), encoding="utf-8")

    captured: dict = {}

    def fake_prev(**kwargs):
        captured.update(kwargs)
        return {
            "ok": True,
            "output_video_path": str((Path(kwargs["output_dir"]) / "local_preview_x.mp4").resolve()),
            "scenes_rendered": 1,
            "used_images_count": 0,
            "used_clips_count": 1,
            "blocking_reasons": [],
            "warnings": [],
            "ffmpeg_available": True,
        }

    summ, code = execute_preview_smoke_auto(
        run_id="t1",
        output_root=out,
        asset_manifest=am_path,
        run_local_preview_from_bundle_fn=fake_prev,
    )
    assert code == 0
    assert summ["ok"] is True
    assert captured["bundle"].get("run_id") == "t1" or "image_paths" in captured["bundle"]
    assert str(captured["bundle_path"]).endswith("render_input_bundle_t1.json")


def test_execute_no_media_preview(tmp_path: Path):
    out = tmp_path / "output"
    out.mkdir(parents=True)
    work = out / "w"
    work.mkdir()
    am = {
        "assets": [{"scene_number": 1, "visual_asset_kind": "still"}],
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
        "visual_cost_summary": {"total_units": 0.0, "by_kind": {}},
    }
    am_path = work / "asset_manifest.json"
    am_path.write_text(json.dumps(am), encoding="utf-8")

    def fake_prev(**kwargs):
        return {
            "ok": False,
            "error_code": "no_media",
            "blocking_reasons": ["no_media_segments_built"],
            "warnings": [],
            "scenes_rendered": 0,
            "used_images_count": 0,
            "used_clips_count": 0,
            "ffmpeg_available": True,
        }

    def fake_prod(**kwargs):
        bp = out / f"render_input_bundle_{kwargs['run_id']}.json"
        bundle = {
            "run_id": kwargs["run_id"],
            "ready_for_render": True,
            "image_paths": [],
            "clip_paths": [],
            "motion_timeline_manifest_path": "",
            "media_path_hydration_summary": {"images_found": 0, "clips_found": 0},
        }
        bp.write_text(json.dumps(bundle), encoding="utf-8")
        return {
            "bundle_path": bp.resolve(),
            "bundle": bundle,
            "timeline": {"scenes": [{"scene_number": 1, "duration_seconds": 5}]},
            "first_real_production_run_summary_path": str(out / f"first_real_production_run_summary_{kwargs['run_id']}.json"),
        }

    summ, code = execute_preview_smoke_auto(
        run_id="t2",
        output_root=out,
        asset_manifest=am_path,
        run_controlled_production_run_fn=fake_prod,
        run_local_preview_from_bundle_fn=fake_prev,
    )
    assert code == 3
    assert summ["ok"] is False
    assert summ["failure_class"] == "asset_media"
    assert "no_media" in str(summ.get("preview_result", {}).get("error_code", ""))


def test_run_preview_smoke_cli_writes_summary(tmp_path: Path, monkeypatch):
    import importlib.util
    import sys

    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "run_preview_smoke_auto.py"
    spec = importlib.util.spec_from_file_location("run_preview_smoke_auto", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    out = tmp_path / "output"
    out.mkdir()
    work = out / "w"
    work.mkdir()
    img = work / "scene.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    am = {
        "assets": [
            {
                "scene_number": 1,
                "visual_asset_kind": "motion_clip",
                "selected_asset_path": str(img),
                "visual_prompt_effective": "p",
            }
        ],
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
        "visual_cost_summary": {"total_units": 1.0, "by_kind": {}},
    }
    am_path = work / "asset_manifest.json"
    am_path.write_text(json.dumps(am), encoding="utf-8")

    def fake_exec(**kwargs):
        return (
            {
                "ok": True,
                "run_id": kwargs["run_id"],
                "failure_class": None,
                "preview_result": {"ok": True, "blocking_reasons": []},
            },
            0,
        )

    monkeypatch.setattr(mod, "execute_preview_smoke_auto", fake_exec)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_preview_smoke_auto.py",
            "--run-id",
            "cli_r1",
            "--output-root",
            str(out),
            "--asset-manifest",
            str(am_path),
        ],
    )
    assert mod.main() == 0
    sp = out / "preview_smoke_auto_summary_cli_r1.json"
    assert sp.is_file()
    data = json.loads(sp.read_text(encoding="utf-8"))
    assert data["ok"] is True
