"""BA 32.1 — Runway Live Readiness (Pipeline Stub, klare Gates)."""

from __future__ import annotations

import json
from pathlib import Path

from app.production_assembly.controlled_production_run import run_controlled_production_run
from app.production_connectors.motion_provider_adapter import build_motion_clip_result
from app.production_connectors.runway_live_readiness import (
    RUNWAY_LIVE_CONNECTOR_IMPLEMENTED,
    augment_motion_clip_manifest_summary,
    controlled_run_blocking_reasons_for_live_motion,
)


def test_runway_live_connector_flag_false():
    assert RUNWAY_LIVE_CONNECTOR_IMPLEMENTED is False


def test_augment_summary_default_no_global_warnings_spam():
    s = augment_motion_clip_manifest_summary(
        {"clips_planned": 1, "dry_run": True},
        allow_live_motion=False,
        max_live_motion_clips=0,
    )
    assert s["runway_live_available"] is False
    assert s["runway_live_reason"] == "runway_live_connector_not_implemented"
    assert s["pipeline_motion_mode"] == "dry_run_stub_only"
    assert s.get("global_warnings") in (None, [])


def test_augment_summary_when_live_requested():
    s = augment_motion_clip_manifest_summary(
        {"clips_planned": 1, "dry_run": True},
        allow_live_motion=True,
        max_live_motion_clips=3,
    )
    gw = s.get("global_warnings") or []
    assert "runway_live_motion_requested_but_connector_not_implemented" in gw
    assert s.get("runway_live_motion_clip_budget") == 3


def test_controlled_blocking_when_live_motion_requested():
    assert controlled_run_blocking_reasons_for_live_motion(allow_live_motion=False) == []
    br = controlled_run_blocking_reasons_for_live_motion(allow_live_motion=True)
    assert "runway_live_motion_requested_but_connector_not_implemented" in br


def test_motion_clip_dry_run_default_no_live_request(tmp_path: Path):
    img = tmp_path / "scene_001.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    asset = {
        "scene_number": 1,
        "visual_asset_kind": "motion_clip",
        "selected_asset_path": str(img),
        "visual_prompt_effective": "p",
    }
    res = build_motion_clip_result(asset, base_dir=tmp_path, provider="runway", dry_run=True)
    assert res["runway_live_requested"] is False
    assert res["provider_status"] == "dry_run_ready"


def test_motion_clip_live_request_adds_stub_warnings(tmp_path: Path):
    img = tmp_path / "scene_001.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    asset = {
        "scene_number": 1,
        "visual_asset_kind": "motion_clip",
        "selected_asset_path": str(img),
        "visual_prompt_effective": "p",
    }
    res = build_motion_clip_result(
        asset,
        base_dir=tmp_path,
        provider="runway",
        dry_run=True,
        allow_live_motion=True,
    )
    assert res["runway_live_requested"] is True
    assert res["runway_live_connector_implemented"] is False
    w = " ".join(str(x) for x in (res.get("warnings") or []))
    assert "runway_live_connector_not_implemented" in w
    assert "motion_provider_dry_run_only_no_clip_generated" in w


def test_controlled_run_manifest_summary_runway_fields(tmp_path: Path):
    work = tmp_path / "w"
    work.mkdir(parents=True)
    img = work / "s0.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    am = {
        "assets": [
            {
                "scene_number": 1,
                "visual_asset_kind": "motion_clip",
                "selected_asset_path": str(img.resolve()),
            }
        ],
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
        "visual_cost_summary": {"total_units": 1.0, "by_kind": {}},
    }
    am_path = work / "asset_manifest.json"
    am_path.write_text(json.dumps(am), encoding="utf-8")
    out_root = tmp_path / "out"
    out_root.mkdir()
    r = run_controlled_production_run(
        run_id="rw_stub",
        output_root=out_root,
        asset_manifest_path=am_path,
        allow_live_motion=True,
        max_live_motion_clips=2,
    )
    mm_path = Path(r["timeline_path"]).resolve().parent / f"motion_clip_manifest_rw_stub.json"
    # timeline_path is motion_timeline_manifest — manifest is sibling under out_root
    mcp = out_root / "motion_clip_manifest_rw_stub.json"
    doc = json.loads(mcp.read_text(encoding="utf-8"))
    summ = doc.get("summary") or {}
    assert summ.get("runway_live_available") is False
    assert summ.get("pipeline_motion_mode") == "dry_run_stub_only"
    fs = r.get("first_real_production_run_summary") or {}
    br = fs.get("blocking_reasons") or []
    assert "runway_live_motion_requested_but_connector_not_implemented" in br
