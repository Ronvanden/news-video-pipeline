"""BA 27.1 — Reference library V1 tests (file-based, no provider calls)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from app.real_video_build.production_pack import build_production_pack
from app.visual_plan.reference_library import (
    attach_reference_ids_to_asset,
    build_reference_library,
    build_reference_library_summary,
    normalize_reference_asset,
    read_reference_library,
    write_reference_library,
)

def _import_cli_module():
    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "build_reference_library_v1.py"
    spec = importlib.util.spec_from_file_location("build_reference_library_v1", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_normalize_reference_asset_sets_defaults():
    r = normalize_reference_asset({"type": "character", "path": "x.png"})
    assert r["id"]
    assert r["type"] == "character"
    assert r["created_by"] == "ba27_1_reference_library_v1"
    assert r["reference_strength"] in ("low", "medium", "high")


def test_duplicate_ids_create_warning(tmp_path: Path):
    (tmp_path / "a.png").write_bytes(b"x")
    lib = build_reference_library(
        [
            {"id": "dup", "type": "character", "path": str(tmp_path / "a.png")},
            {"id": "dup", "type": "character", "path": str(tmp_path / "a.png")},
        ],
        run_id="r",
    )
    assert any("reference_asset_duplicate_ids" in w for w in lib["warnings"])


def test_missing_path_warns_but_no_crash():
    lib = build_reference_library([{"id": "x", "type": "style", "path": ""}], run_id="r")
    assert any("reference_asset_path_missing:x" in w for w in lib["warnings"])


def test_attach_reference_ids_additive_and_unique():
    a = {"scene_number": 1, "reference_asset_ids": ["r1"]}
    out = attach_reference_ids_to_asset(
        a,
        ["r1", "r2"],
        continuity_strength="high",
        continuity_prompt_hint="Keep the same face as r1.",
        reference_provider_status="prepared",
    )
    assert out["reference_asset_ids"] == ["r1", "r2"]
    assert out["continuity_strength"] == "high"
    assert out["reference_policy_status"] == "attached"
    assert out["continuity_prompt_hint"]
    assert out["reference_provider_status"] == "prepared"


def test_unknown_reference_id_counts_as_missing_in_summary():
    lib = build_reference_library([{"id": "known", "type": "character", "path": "x.png"}], run_id="r")
    assets = [{"scene_number": 1, "reference_asset_ids": ["unknown"], "continuity_strength": "medium"}]
    s = build_reference_library_summary(lib, assets=assets)
    assert s["missing_references_count"] == 1


def test_read_write_reference_library(tmp_path: Path):
    lib = build_reference_library([{"id": "a", "type": "object", "path": "p.png"}], run_id="r")
    p = write_reference_library(tmp_path / "reference_library.json", lib)
    loaded = read_reference_library(p)
    assert loaded["reference_library_version"] == "ba27_1_v1"


def test_production_pack_copies_reference_library_and_adds_summary(tmp_path: Path):
    out_root = tmp_path / "output"
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)
    # minimal asset manifest
    am = {
        "run_id": "r1",
        "assets": [{"scene_number": 1, "image_path": "scene_001.png", "generated_image_path": "scene_001.png"}],
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
    }
    (src / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (src / "asset_manifest.json").write_text(json.dumps(am), encoding="utf-8")

    ref = build_reference_library([{"id": "c1", "type": "character", "path": str(src / "scene_001.png")}], run_id="r1")
    (src / "reference_library.json").write_text(json.dumps(ref), encoding="utf-8")

    res = build_production_pack(
        run_id="r1",
        output_root=out_root,
        source_paths={"asset_manifest": src / "asset_manifest.json", "reference_library": src / "reference_library.json"},
        dry_run=False,
    )
    pack = Path(res["pack_dir"])
    assert (pack / "reference_library.json").is_file()
    summary = json.loads((pack / "production_summary.json").read_text(encoding="utf-8"))
    assert summary["reference_library_path"]
    assert summary["reference_library_summary"]["reference_assets_count"] == 1


def test_cli_build_reference_library_import_smoke():
    mod = _import_cli_module()
    assert hasattr(mod, "main")


def test_cli_attach_supports_prompt_hint_and_provider_status(tmp_path: Path, monkeypatch):
    mod = _import_cli_module()
    out = tmp_path / "reference_library.json"
    am = tmp_path / "asset_manifest.json"
    am.write_text(
        json.dumps({"run_id": "r", "assets": [{"scene_number": 3}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_reference_library_v1.py",
            "--run-id",
            "run123",
            "--output",
            str(out),
            "--reference",
            "id=main_character_ref_01,type=character,path=references/main_character.png,strength=high",
            "--asset-manifest",
            str(am),
            "--attach",
            "scene_number=3,reference_id=main_character_ref_01,strength=high,prompt_hint=Keep same face,provider_status=prepared",
        ],
    )
    rc = mod.main()
    assert rc == 0
    patched = json.loads(am.read_text(encoding="utf-8"))
    a = patched["assets"][0]
    assert a["reference_asset_ids"] == ["main_character_ref_01"]
    assert a["continuity_prompt_hint"] == "Keep same face"
    assert a["reference_provider_status"] == "prepared"

