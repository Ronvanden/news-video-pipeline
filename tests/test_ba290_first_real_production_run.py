"""BA 29.0 — First real 30–60s production run tests (controlled, placeholder motion)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _import_cli():
    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "run_first_real_production_30_60.py"
    spec = importlib.util.spec_from_file_location("run_first_real_production_30_60", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_production_run_writes_summary(tmp_path: Path, monkeypatch):
    mod = _import_cli()
    out_root = tmp_path / "output"
    out_root.mkdir(parents=True, exist_ok=True)

    # minimal image input for motion clip result to be ok
    img = tmp_path / "scene_001.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")

    asset_manifest = {
        "run_id": "r1",
        "assets": [
            {
                "scene_number": 1,
                "visual_asset_kind": "motion_clip",
                "selected_asset_path": str(img),
                "visual_prompt_effective": "p",
            }
        ],
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
    }
    am_path = tmp_path / "asset_manifest.json"
    am_path.write_text(json.dumps(asset_manifest), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_first_real_production_30_60.py",
            "--run-id",
            "r1",
            "--output-root",
            str(out_root),
            "--asset-manifest",
            str(am_path),
            "--dry-run",
        ],
    )
    assert mod.main() == 0
    summ = out_root / "first_real_production_run_summary_r1.json"
    assert summ.is_file()
    data = json.loads(summ.read_text(encoding="utf-8"))
    assert data["production_run_version"] == "ba29_0_v1"

