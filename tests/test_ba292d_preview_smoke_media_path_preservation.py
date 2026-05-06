"""BA 29.2d — Media path preservation when preparing asset_manifest for preview smoke."""

from __future__ import annotations

import json
from pathlib import Path

from app.production_assembly.preview_smoke_auto import (
    preserve_or_absolutize_asset_media_paths,
    prepare_asset_manifest_for_smoke,
)
from app.production_assembly.render_input_bundle import build_render_input_bundle


def _minimal_manifest(assets: list, **extra) -> dict:
    base = {
        "assets": assets,
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
        "visual_cost_summary": {"total_units": 0.0, "by_kind": {}},
    }
    base.update(extra)
    return base


def test_relative_image_path_becomes_absolute(tmp_path: Path):
    pack = tmp_path / "generated_assets_pack"
    pack.mkdir()
    img = pack / "scene_001.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    src = pack / "asset_manifest.json"
    doc = _minimal_manifest(
        [{"scene_number": 1, "image_path": "scene_001.png", "visual_asset_kind": "still", "extra_field": 42}],
    )
    src.write_text(json.dumps(doc), encoding="utf-8")

    out = preserve_or_absolutize_asset_media_paths(json.loads(src.read_text()), source_manifest_path=src.resolve())
    assert out["assets"][0]["image_path"] == str(img.resolve())
    assert out["assets"][0]["extra_field"] == 42
    summ = out["media_path_preservation_summary"]
    assert summ["media_path_preservation_version"] == "ba29_2d_v1"
    assert summ["media_paths_absolutized_count"] == 1
    assert summ["media_paths_missing_count"] == 0


def test_resolve_against_source_dir_not_work_dir(tmp_path: Path):
    pack = tmp_path / "real_pack"
    pack.mkdir()
    work = tmp_path / "output" / ".preview_smoke_work" / "run_x"
    work.mkdir(parents=True)
    img = pack / "deep.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    src = pack / "asset_manifest.json"
    src.write_text(json.dumps(_minimal_manifest([{"image_path": "deep.png"}])), encoding="utf-8")

    prepared = work / "asset_manifest_prepared_run_x.json"
    prepared.write_text("{}", encoding="utf-8")

    out = preserve_or_absolutize_asset_media_paths(json.loads(src.read_text()), source_manifest_path=src.resolve())
    assert Path(out["assets"][0]["image_path"]).resolve() == img.resolve()
    assert not (work / "deep.png").is_file()


def test_missing_relative_warns_and_no_crash(tmp_path: Path):
    pack = tmp_path / "pack2"
    pack.mkdir()
    src = pack / "asset_manifest.json"
    src.write_text(json.dumps(_minimal_manifest([{"image_path": "ghost.png"}])), encoding="utf-8")

    out = preserve_or_absolutize_asset_media_paths(json.loads(src.read_text()), source_manifest_path=src.resolve())
    assert out["assets"][0]["image_path"] == "ghost.png"
    summ = out["media_path_preservation_summary"]
    assert summ["media_paths_missing_count"] == 1
    assert summ["media_paths_absolutized_count"] == 0
    assert any("missing_relative" in w for w in summ["warnings"])


def test_absolute_existing_unchanged_string(tmp_path: Path):
    pack = tmp_path / "pack3"
    pack.mkdir()
    img = pack / "x.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    abs_s = str(img.resolve())
    src = pack / "asset_manifest.json"
    src.write_text(json.dumps(_minimal_manifest([{"image_path": abs_s}])), encoding="utf-8")

    out = preserve_or_absolutize_asset_media_paths(json.loads(src.read_text()), source_manifest_path=src.resolve())
    assert Path(out["assets"][0]["image_path"]).resolve() == img.resolve()
    assert out["media_path_preservation_summary"]["media_paths_absolutized_count"] == 0
    assert out["media_path_preservation_summary"]["media_paths_missing_count"] == 0


def test_prepare_smoke_writes_absolute_paths_for_bundle_hydration(tmp_path: Path):
    pack = tmp_path / "gen_assets"
    pack.mkdir()
    img = pack / "scene_001.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    clip = pack / "scene_001.mp4"
    clip.write_bytes(b"\x00\x00\x00\x20ftypisom")
    src = pack / "asset_manifest.json"
    src.write_text(
        json.dumps(
            _minimal_manifest(
                [
                    {
                        "scene_number": 1,
                        "visual_asset_kind": "motion_clip",
                        "selected_asset_path": "scene_001.png",
                        "video_path": "scene_001.mp4",
                    }
                ]
            )
        ),
        encoding="utf-8",
    )
    work = tmp_path / "w"
    prepared_path, report = prepare_asset_manifest_for_smoke(src, work, run_id="hydr")
    assert report.get("media_path_preservation_summary") is not None
    doc = json.loads(prepared_path.read_text(encoding="utf-8"))
    assert Path(doc["assets"][0]["selected_asset_path"]).is_file()
    assert Path(doc["assets"][0]["video_path"]).is_file()

    bundle = build_render_input_bundle(
        run_id="hydr",
        asset_manifest_path=str(prepared_path.resolve()),
        asset_manifest=doc,
        ready_for_render=True,
    )
    hyd = bundle.get("media_path_hydration_summary") or {}
    assert int(hyd.get("images_found", 0)) >= 1
    assert int(hyd.get("clips_found", 0)) >= 1
