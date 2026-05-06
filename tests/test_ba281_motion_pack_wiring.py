"""BA 28.1 — Motion manifest pack wiring tests."""

from __future__ import annotations

import json
from pathlib import Path

from app.real_video_build.production_pack import build_production_pack


def test_pack_copies_motion_clip_manifest_and_summary_contains_motion_clip_summary(tmp_path: Path):
    out_root = tmp_path / "output"
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)

    # minimal required approval for pack summary
    asset_manifest = {
        "run_id": "r1",
        "assets": [{"scene_number": 1}],
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
    }
    motion_manifest = {
        "motion_clip_manifest_version": "ba28_0_v1",
        "clips": [],
        "summary": {"clips_planned": 2, "provider_counts": {"runway": 2}, "missing_input_count": 0, "dry_run": True},
    }

    (src / "asset_manifest.json").write_text(json.dumps(asset_manifest), encoding="utf-8")
    (src / "motion_clip_manifest.json").write_text(json.dumps(motion_manifest), encoding="utf-8")

    res = build_production_pack(
        run_id="r1",
        output_root=out_root,
        source_paths={"asset_manifest": src / "asset_manifest.json", "motion_clip_manifest": src / "motion_clip_manifest.json"},
        dry_run=False,
        copy_assets=False,
    )
    pack = Path(res["pack_dir"])
    assert (pack / "motion_clip_manifest.json").is_file()
    summary = json.loads((pack / "production_summary.json").read_text(encoding="utf-8"))
    assert summary["motion_clip_summary"]["clips_planned"] == 2

