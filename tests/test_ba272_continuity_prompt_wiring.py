"""BA 27.2 — Continuity prompt wiring tests (no live calls)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from app.real_video_build.production_pack import build_production_pack
from app.visual_plan.continuity_prompt import (
    apply_continuity_prompt_wiring_to_asset,
    apply_continuity_prompt_wiring_to_manifest,
)
from app.visual_plan.reference_library import build_reference_library


def test_asset_without_reference_ids_is_none():
    a = {"scene_number": 1}
    out = apply_continuity_prompt_wiring_to_asset(a, reference_library=None)
    assert out["continuity_provider_preparation_status"] == "none"


def test_asset_with_valid_reference_is_prepared_and_paths_types_present(tmp_path: Path):
    ref_file = tmp_path / "ref.png"
    ref_file.write_bytes(b"x")
    lib = build_reference_library([{"id": "main_character_ref_01", "type": "character", "path": str(ref_file), "continuity_notes": "same face"}], run_id="r")
    a = {"scene_number": 3, "reference_asset_ids": ["main_character_ref_01"], "continuity_strength": "high"}
    out = apply_continuity_prompt_wiring_to_asset(a, reference_library=lib)
    assert out["continuity_provider_preparation_status"] == "prepared"
    assert str(ref_file) in (out["continuity_reference_paths"] or [])
    assert "character" in (out["continuity_reference_types"] or [])
    assert out["continuity_provider_payload_stub"]["no_live_upload"] is True


def test_existing_continuity_prompt_hint_not_overwritten(tmp_path: Path):
    ref_file = tmp_path / "ref.png"
    ref_file.write_bytes(b"x")
    lib = build_reference_library([{"id": "r1", "type": "character", "path": str(ref_file), "continuity_notes": "same face"}], run_id="r")
    a = {"scene_number": 1, "reference_asset_ids": ["r1"], "continuity_prompt_hint": "KEEP THIS"}
    out = apply_continuity_prompt_wiring_to_asset(a, reference_library=lib)
    assert out["continuity_prompt_hint"] == "KEEP THIS"


def test_missing_reference_id_sets_missing_reference():
    lib = build_reference_library([], run_id="r")
    a = {"scene_number": 1, "reference_asset_ids": ["missing"]}
    out = apply_continuity_prompt_wiring_to_asset(a, reference_library=lib)
    assert out["continuity_provider_preparation_status"] == "missing_reference"


def test_reference_policy_needs_review_sets_needs_review(tmp_path: Path):
    ref_file = tmp_path / "ref.png"
    ref_file.write_bytes(b"x")
    lib = build_reference_library([{"id": "r1", "type": "character", "path": str(ref_file)}], run_id="r")
    a = {"scene_number": 1, "reference_asset_ids": ["r1"], "reference_policy_status": "needs_review"}
    out = apply_continuity_prompt_wiring_to_asset(a, reference_library=lib)
    assert out["continuity_provider_preparation_status"] == "needs_review"


def test_manifest_summary_counts_correctly(tmp_path: Path):
    ref_file = tmp_path / "ref.png"
    ref_file.write_bytes(b"x")
    lib = build_reference_library([{"id": "r1", "type": "character", "path": str(ref_file)}], run_id="r")
    m = {"assets": [{"scene_number": 1}, {"scene_number": 2, "reference_asset_ids": ["r1"]}]}
    out = apply_continuity_prompt_wiring_to_manifest(m, reference_library=lib)
    s = out["continuity_wiring_summary"]
    assert s["assets_checked"] == 2
    assert s["prepared_count"] == 1
    assert s["none_count"] == 1


def _import_cli():
    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "run_continuity_prompt_wiring.py"
    spec = importlib.util.spec_from_file_location("run_continuity_prompt_wiring", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cli_dry_run_writes_nothing(tmp_path: Path, monkeypatch):
    mod = _import_cli()
    man = tmp_path / "asset_manifest.json"
    man.write_text(json.dumps({"assets": [{"scene_number": 1}]}), encoding="utf-8")
    outp = tmp_path / "out.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_continuity_prompt_wiring.py", "--manifest", str(man), "--output", str(outp), "--dry-run"],
    )
    rc = mod.main()
    assert rc == 0
    assert outp.exists() is False


def test_cli_output_writes_fields(tmp_path: Path, monkeypatch):
    mod = _import_cli()
    ref_file = tmp_path / "ref.png"
    ref_file.write_bytes(b"x")
    lib = build_reference_library([{"id": "r1", "type": "character", "path": str(ref_file)}], run_id="r")
    refp = tmp_path / "reference_library.json"
    refp.write_text(json.dumps(lib), encoding="utf-8")
    man = tmp_path / "asset_manifest.json"
    man.write_text(json.dumps({"assets": [{"scene_number": 2, "reference_asset_ids": ["r1"]}]}), encoding="utf-8")
    outp = tmp_path / "out.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_continuity_prompt_wiring.py", "--manifest", str(man), "--reference-library", str(refp), "--output", str(outp)],
    )
    rc = mod.main()
    assert rc == 0
    patched = json.loads(outp.read_text(encoding="utf-8"))
    assert patched["assets"][0]["continuity_provider_preparation_status"] == "prepared"


def test_production_pack_summary_includes_continuity_summary(tmp_path: Path):
    out_root = tmp_path / "output"
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)
    # asset manifest already containing continuity summary
    am = {
        "run_id": "r1",
        "assets": [{"scene_number": 1, "continuity_provider_preparation_status": "prepared"}],
        "continuity_wiring_summary": {"assets_checked": 1, "prepared_count": 1, "missing_reference_count": 0, "needs_review_count": 0, "none_count": 0},
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
    }
    (src / "asset_manifest.json").write_text(json.dumps(am), encoding="utf-8")
    res = build_production_pack(run_id="r1", output_root=out_root, source_paths={"asset_manifest": src / "asset_manifest.json"}, dry_run=False)
    pack = Path(res["pack_dir"])
    summary = json.loads((pack / "production_summary.json").read_text(encoding="utf-8"))
    assert summary["continuity_wiring_summary"]["prepared_count"] == 1

