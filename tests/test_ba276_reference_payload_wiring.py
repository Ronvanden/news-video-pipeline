"""BA 27.6 — Reference payload export/pack wiring (mirror helpers)."""

from __future__ import annotations

import json
from pathlib import Path

from app.real_video_build.production_pack import build_production_pack
from app.visual_plan.reference_payload_mirror import (
    build_reference_payload_mirror_summary,
    extract_reference_payload_fields,
    merge_reference_payload_fields,
    mirror_reference_payloads_by_scene,
)


def test_extract_reference_payload_fields_subset():
    a = {"scene_number": 1, "reference_provider_payload_status": "prepared", "x": 1}
    out = extract_reference_payload_fields(a)
    assert out["reference_provider_payload_status"] == "prepared"
    assert "x" not in out


def test_merge_does_not_overwrite_existing_non_empty():
    t = {"reference_provider_payload_status": "prepared"}
    s = {"reference_provider_payload_status": "missing_reference"}
    out = merge_reference_payload_fields(t, s)
    assert out["reference_provider_payload_status"] == "prepared"


def test_mirror_by_scene_number_matches():
    targets = [{"scene_number": 1}, {"scene_number": 2}]
    assets = [{"scene_number": 2, "reference_provider_payload_status": "prepared"}]
    mirrored, summ = mirror_reference_payloads_by_scene(targets, assets)
    assert summ["matched_count"] == 1
    assert mirrored[1]["reference_provider_payload_status"] == "prepared"


def test_unmatched_does_not_crash_and_summary_present():
    targets = [{"scene_number": 1}]
    assets = [{"scene_number": 2, "reference_provider_payload_status": "prepared"}]
    mirrored, summ = mirror_reference_payloads_by_scene(targets, assets)
    assert isinstance(mirrored, list)
    assert summ["matched_count"] == 0


def test_build_reference_payload_mirror_summary_counts():
    items = [{"reference_provider_payload_status": "prepared"}, {"reference_provider_payload_status": "none"}]
    s = build_reference_payload_mirror_summary(items)
    assert s["prepared_count"] == 1


def test_production_pack_summary_includes_reference_payload_mirror_summary(tmp_path: Path):
    out_root = tmp_path / "output"
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)
    asset_manifest = {
        "run_id": "r1",
        "assets": [{"scene_number": 1, "reference_provider_payload_status": "prepared"}],
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
    }
    scene_asset_pack = {
        "scene_expansion": {"expanded_scene_assets": [{"scene_number": 1, "visual_prompt": "x"}]}
    }
    (src / "asset_manifest.json").write_text(json.dumps(asset_manifest), encoding="utf-8")
    (src / "scene_asset_pack.json").write_text(json.dumps(scene_asset_pack), encoding="utf-8")

    res = build_production_pack(
        run_id="r1",
        output_root=out_root,
        source_paths={"asset_manifest": src / "asset_manifest.json", "scene_asset_pack": src / "scene_asset_pack.json"},
        dry_run=False,
    )
    pack = Path(res["pack_dir"])
    summary = json.loads((pack / "production_summary.json").read_text(encoding="utf-8"))
    assert "reference_payload_mirror_summary" in summary
    assert summary["reference_payload_mirror_summary"]["mirror"]["matched_count"] == 1

