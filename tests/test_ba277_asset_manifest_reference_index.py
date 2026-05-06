"""BA 27.7 — Asset manifest reference index tests."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from app.visual_plan.asset_manifest_reference_index import build_asset_manifest_reference_index


def test_build_index_by_scene_number_and_summary_counts():
    man = {
        "assets": [
            {"scene_number": 1, "reference_provider_payload_status": "prepared", "reference_asset_ids": ["r1"]},
            {"scene_number": 2, "reference_provider_payload_status": "missing_reference"},
            {"scene_number": 3},
        ]
    }
    idx = build_asset_manifest_reference_index(man)
    assert idx["asset_manifest_reference_index_version"] == "ba27_7_v1"
    by = idx["by_scene_number"]
    assert "1" in by and "2" in by and "3" in by
    assert idx["summary"]["prepared_count"] == 1
    assert idx["summary"]["missing_reference_count"] == 1


def _import_cli():
    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "build_asset_manifest_reference_index.py"
    spec = importlib.util.spec_from_file_location("build_asset_manifest_reference_index", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cli_dry_run_writes_nothing(tmp_path: Path, monkeypatch):
    mod = _import_cli()
    man = tmp_path / "asset_manifest.json"
    man.write_text(json.dumps({"assets": [{"scene_number": 1}]}), encoding="utf-8")
    outp = tmp_path / "idx.json"
    monkeypatch.setattr(sys, "argv", ["build_asset_manifest_reference_index.py", "--manifest", str(man), "--output", str(outp), "--dry-run"])
    assert mod.main() == 0
    assert outp.exists() is False

