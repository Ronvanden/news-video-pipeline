"""BA 29.2b — Render input bundle media path hydration."""

from __future__ import annotations

import json
from pathlib import Path

from app.production_assembly.render_input_bundle import (
    build_render_input_bundle,
    extract_hydrated_media_paths_from_manifest,
)


def test_selected_asset_path_preferred_over_image_path(tmp_path: Path):
    sub = tmp_path / "proj"
    sub.mkdir()
    sel = sub / "selected.png"
    other = sub / "other.png"
    sel.write_bytes(b"x")
    other.write_bytes(b"y")
    man = {
        "assets": [
            {
                "scene_number": 1,
                "selected_asset_path": str(sel.name),
                "image_path": str(other.name),
            }
        ]
    }
    imgs, clips, summ = extract_hydrated_media_paths_from_manifest(man, manifest_dir=sub)
    assert len(imgs) == 1
    assert Path(imgs[0]).resolve() == sel.resolve()
    assert summ["images_found"] == 1
    assert summ["missing_paths"] == []


def test_relative_paths_resolved_to_manifest_dir(tmp_path: Path):
    base = tmp_path / "pack"
    base.mkdir()
    rel_dir = base / "assets"
    rel_dir.mkdir()
    img = rel_dir / "scene_001.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    man = {"assets": [{"scene_number": 1, "image_path": "assets/scene_001.png"}]}
    imgs, _, summ = extract_hydrated_media_paths_from_manifest(man, manifest_dir=base)
    assert len(imgs) == 1
    assert Path(imgs[0]).resolve() == img.resolve()
    assert summ["images_found"] == 1


def test_missing_file_lists_missing_paths_no_crash(tmp_path: Path):
    base = tmp_path / "b"
    base.mkdir()
    man = {"assets": [{"scene_number": 1, "image_path": "nope.png"}]}
    imgs, _, summ = extract_hydrated_media_paths_from_manifest(man, manifest_dir=base)
    assert len(imgs) == 1
    assert summ["images_found"] == 0
    assert len(summ["missing_paths"]) == 1


def test_build_bundle_hydrates_from_asset_manifest_path(tmp_path: Path):
    base = tmp_path / "out"
    base.mkdir()
    img = base / "a.png"
    img.write_bytes(b"x")
    man_path = base / "asset_manifest.json"
    man_path.write_text(
        json.dumps({"assets": [{"scene_number": 1, "generated_image_path": str(img.name)}]}),
        encoding="utf-8",
    )
    b = build_render_input_bundle(
        run_id="r",
        production_summary_path=str(base / "ps.json"),
        asset_manifest_path=str(man_path),
        ready_for_render=True,
    )
    assert len(b["image_paths"]) == 1
    assert Path(b["image_paths"][0]).resolve() == img.resolve()
    assert b.get("media_path_hydration_summary", {}).get("hydration_version") == "ba29_2b_v1"


def test_build_bundle_merges_explicit_before_hydrated(tmp_path: Path):
    base = tmp_path / "m"
    base.mkdir()
    h_img = base / "h.png"
    h_img.write_bytes(b"1")
    x_img = base / "x.png"
    x_img.write_bytes(b"2")
    man = {"assets": [{"scene_number": 1, "image_path": str(h_img.name)}]}
    (base / "am.json").write_text(json.dumps(man), encoding="utf-8")
    b = build_render_input_bundle(
        run_id="r",
        asset_manifest_path=str(base / "am.json"),
        asset_manifest=man,
        image_paths=[str(x_img)],
    )
    # explicit first, then hydrated
    assert b["image_paths"][0] == str(x_img.resolve())
    assert str(h_img.resolve()) in b["image_paths"]


def test_video_then_clip_both_collected(tmp_path: Path):
    base = tmp_path / "v"
    base.mkdir()
    v1 = base / "a.mp4"
    v2 = base / "b.mp4"
    v1.write_bytes(b"v1")
    v2.write_bytes(b"v2")
    man = {"assets": [{"scene_number": 1, "video_path": str(v1.name), "clip_path": str(v2.name)}]}
    _, clips, summ = extract_hydrated_media_paths_from_manifest(man, manifest_dir=base)
    assert len(clips) == 2
    assert summ["clips_found"] == 2
