"""BA 32.0 — 10-minute production: Leonardo cap + timeline scene limit wiring."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

from app.production_assembly.controlled_production_run import run_controlled_production_run
from app.production_assembly.fresh_topic_preview_smoke import run_fresh_topic_preview_smoke


def test_max_live_assets_forwarded_to_asset_runner(tmp_path: Path):
    """CLI ``--max-live-assets`` flows through as ``max_assets_live`` on the Asset Runner."""
    out = tmp_path / "output"
    fake_script = {
        "title": "T",
        "hook": "H",
        "chapters": [{"title": "K1", "content": "Text für eine Szene mit ausreichend Länge."}],
        "full_script": "",
        "sources": [],
        "warnings": [],
    }
    captured: dict = {}

    def spy_runner(pack_path, out_root, *, run_id, mode, max_assets_live=None, **kw):
        captured["max_assets_live"] = max_assets_live
        gen = Path(out_root).resolve() / f"generated_assets_{run_id}"
        gen.mkdir(parents=True)
        mp = gen / "asset_manifest.json"
        (gen / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        mp.write_text(
            json.dumps(
                {
                    "assets": [
                        {
                            "scene_number": 1,
                            "image_path": "scene_001.png",
                            "visual_asset_kind": "still",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        return {"ok": True, "manifest_path": str(mp.resolve()), "warnings": []}

    from app.production_assembly import fresh_topic_preview_smoke as ft

    ft._load_module("run_asset_runner_ba302", "scripts/run_asset_runner.py")
    ar_mod = sys.modules["run_asset_runner_ba302"]

    with patch(
        "app.production_assembly.fresh_topic_preview_smoke._build_script_for_fresh_input",
        return_value=(fake_script, [], []),
    ), patch.object(ar_mod, "run_local_asset_runner", spy_runner):
        r = run_fresh_topic_preview_smoke(
            run_id="ba320_cap",
            output_root=out,
            topic="ignored",
            dry_run=True,
            max_scenes=3,
            max_live_assets=24,
            asset_runner_mode="live",
        )
    assert r.get("ok") is True
    assert captured.get("max_assets_live") == 24


def test_max_live_assets_unset_leaves_default_none(tmp_path: Path):
    """Without ``max_live_assets``, Asset Runner receives ``max_assets_live=None`` (internal default 3)."""
    out = tmp_path / "output"
    fake_script = {
        "title": "T",
        "hook": "H",
        "chapters": [{"title": "K1", "content": "Text für eine Szene mit ausreichend Länge."}],
        "full_script": "",
        "sources": [],
        "warnings": [],
    }
    captured: dict = {}

    def spy_runner(pack_path, out_root, *, run_id, mode, max_assets_live=None, **kw):
        captured["max_assets_live"] = max_assets_live
        gen = Path(out_root).resolve() / f"generated_assets_{run_id}"
        gen.mkdir(parents=True)
        mp = gen / "asset_manifest.json"
        (gen / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        mp.write_text(
            json.dumps(
                {
                    "assets": [
                        {
                            "scene_number": 1,
                            "image_path": "scene_001.png",
                            "visual_asset_kind": "still",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        return {"ok": True, "manifest_path": str(mp.resolve()), "warnings": []}

    from app.production_assembly import fresh_topic_preview_smoke as ft

    ft._load_module("run_asset_runner_ba302", "scripts/run_asset_runner.py")
    ar_mod = sys.modules["run_asset_runner_ba302"]

    with patch(
        "app.production_assembly.fresh_topic_preview_smoke._build_script_for_fresh_input",
        return_value=(fake_script, [], []),
    ), patch.object(ar_mod, "run_local_asset_runner", spy_runner):
        run_fresh_topic_preview_smoke(
            run_id="ba320_default",
            output_root=out,
            topic="ignored",
            dry_run=True,
            max_scenes=3,
            asset_runner_mode="live",
        )
    assert captured.get("max_assets_live") is None


def test_controlled_run_timeline_can_exceed_five_scenes(tmp_path: Path):
    """``max_timeline_scenes`` allows more than five manifest rows in the timeline."""
    work = tmp_path / "w"
    work.mkdir(parents=True)
    assets = []
    for i in range(8):
        img = work / f"s{i}.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n")
        assets.append(
            {
                "scene_number": i + 1,
                "visual_asset_kind": "still",
                "selected_asset_path": str(img.resolve()),
            }
        )
    am = {
        "assets": assets,
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
        "visual_cost_summary": {"total_units": 8.0, "by_kind": {}},
    }
    am_path = work / "asset_manifest.json"
    am_path.write_text(json.dumps(am), encoding="utf-8")

    out_root = tmp_path / "output"
    out_root.mkdir()
    r = run_controlled_production_run(
        run_id="tl_cap",
        output_root=out_root,
        asset_manifest_path=am_path,
        max_timeline_scenes=8,
    )
    tl = r.get("timeline") or {}
    assert len(tl.get("scenes") or []) == 8


def test_controlled_run_default_timeline_still_five(tmp_path: Path):
    """Default ``max_timeline_scenes=5`` keeps previous behaviour for many assets."""
    work = tmp_path / "w2"
    work.mkdir(parents=True)
    assets = []
    for i in range(8):
        img = work / f"s{i}.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n")
        assets.append(
            {
                "scene_number": i + 1,
                "visual_asset_kind": "still",
                "selected_asset_path": str(img.resolve()),
            }
        )
    am = {
        "assets": assets,
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
        "visual_cost_summary": {"total_units": 8.0, "by_kind": {}},
    }
    am_path = work / "asset_manifest.json"
    am_path.write_text(json.dumps(am), encoding="utf-8")

    out_root = tmp_path / "output2"
    out_root.mkdir()
    r = run_controlled_production_run(
        run_id="tl_def",
        output_root=out_root,
        asset_manifest_path=am_path,
    )
    tl = r.get("timeline") or {}
    assert len(tl.get("scenes") or []) == 5
