"""BA 27.4 — Reference provider payload stubs tests (no live calls)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from app.real_video_build.production_pack import build_production_pack
from app.visual_plan.reference_provider_payloads import (
    apply_reference_provider_payload_to_asset,
    apply_reference_provider_payloads_to_manifest,
    build_reference_provider_payload,
)


def test_asset_without_reference_ids_status_none():
    a = {"scene_number": 1}
    out = apply_reference_provider_payload_to_asset(a)
    assert out["reference_provider_payload_status"] == "none"


def test_openai_with_reference_paths_prepared_image_reference():
    a = {
        "scene_number": 1,
        "reference_asset_ids": ["r1"],
        "continuity_reference_paths": ["ref.png"],
        "continuity_provider_preparation_status": "prepared",
        "routed_visual_provider": "openai_images",
    }
    p = build_reference_provider_payload(a, provider="openai_images")
    assert p["supported_mode"] == "image_reference_prepared"
    assert p["status"] == "prepared"
    assert p["no_live_upload"] is True
    assert p.get("payload_format") == "openai_images_reference_stub_v1"
    payload = p.get("payload")
    assert isinstance(payload, dict)
    assert payload.get("no_live_upload") is True
    ref_imgs = payload.get("reference_images")
    assert isinstance(ref_imgs, list)
    assert [r.get("path") for r in ref_imgs] == ["ref.png"]


def test_runway_motion_clip_with_reference_paths_image_to_video_prepared():
    a = {
        "scene_number": 1,
        "visual_asset_kind": "motion_clip",
        "reference_asset_ids": ["r1"],
        "continuity_reference_paths": ["ref.png"],
        "continuity_provider_preparation_status": "prepared",
    }
    p = build_reference_provider_payload(a, provider="runway")
    assert p["supported_mode"] == "image_to_video_reference_prepared"
    assert p.get("payload_format") == "runway_reference_stub_v1"
    payload = p.get("payload")
    assert isinstance(payload, dict)
    assert payload.get("no_live_upload") is True
    init_imgs = payload.get("init_images")
    assert isinstance(init_imgs, list)
    assert [r.get("path") for r in init_imgs] == ["ref.png"]


def test_seedance_motion_clip_with_reference_paths_image_to_video_prepared():
    a = {
        "scene_number": 1,
        "visual_asset_kind": "motion_clip",
        "reference_asset_ids": ["r1"],
        "continuity_reference_paths": ["ref.png"],
        "continuity_provider_preparation_status": "prepared",
    }
    p = build_reference_provider_payload(a, provider="seedance")
    assert p["supported_mode"] == "image_to_video_reference_prepared"
    assert p.get("payload_format") == "seedance_reference_stub_v1"
    payload = p.get("payload")
    assert isinstance(payload, dict)
    assert payload.get("no_live_upload") is True
    ref_imgs = payload.get("reference_images")
    assert isinstance(ref_imgs, list)
    assert [r.get("path") for r in ref_imgs] == ["ref.png"]


def test_leonardo_payload_is_prompt_hint_only():
    a = {
        "scene_number": 1,
        "reference_asset_ids": ["r1"],
        "continuity_reference_paths": ["ref.png"],
        "continuity_provider_preparation_status": "prepared",
    }
    p = build_reference_provider_payload(a, provider="leonardo")
    assert p.get("payload_format") == "leonardo_reference_stub_v1"
    payload = p.get("payload")
    assert isinstance(payload, dict)
    assert payload.get("mode") == "prompt_hint_only"
    assert payload.get("no_live_upload") is True


def test_missing_reference_is_propagated():
    a = {
        "scene_number": 1,
        "reference_asset_ids": ["missing"],
        "continuity_provider_preparation_status": "missing_reference",
    }
    out = apply_reference_provider_payload_to_asset(a)
    assert out["reference_provider_payload_status"] == "missing_reference"


def test_needs_review_is_propagated():
    a = {
        "scene_number": 1,
        "reference_asset_ids": ["r1"],
        "continuity_provider_preparation_status": "needs_review",
    }
    out = apply_reference_provider_payload_to_asset(a)
    assert out["reference_provider_payload_status"] == "needs_review"


def test_recommended_payload_follows_priority_provider_used():
    a = {
        "scene_number": 1,
        "reference_asset_ids": ["r1"],
        "continuity_reference_paths": ["ref.png"],
        "continuity_provider_preparation_status": "prepared",
        "provider_used": "runway",
        "visual_asset_kind": "motion_clip",
    }
    out = apply_reference_provider_payload_to_asset(a)
    rec = out["recommended_reference_provider_payload"]
    assert rec["provider"] == "runway"
    assert rec["supported_mode"] == "image_to_video_reference_prepared"


def _import_cli():
    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "run_reference_provider_payloads.py"
    spec = importlib.util.spec_from_file_location("run_reference_provider_payloads", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cli_dry_run_writes_nothing(tmp_path: Path, monkeypatch):
    mod = _import_cli()
    man = tmp_path / "asset_manifest.json"
    man.write_text(json.dumps({"assets": [{"scene_number": 1}]}), encoding="utf-8")
    outp = tmp_path / "out.json"
    monkeypatch.setattr(sys, "argv", ["run_reference_provider_payloads.py", "--manifest", str(man), "--output", str(outp), "--dry-run"])
    assert mod.main() == 0
    assert outp.exists() is False


def test_cli_output_writes_payload_fields(tmp_path: Path, monkeypatch):
    mod = _import_cli()
    man = tmp_path / "asset_manifest.json"
    man.write_text(
        json.dumps({"assets": [{"scene_number": 1, "reference_asset_ids": ["r1"], "continuity_reference_paths": ["ref.png"], "continuity_provider_preparation_status": "prepared"}]}),
        encoding="utf-8",
    )
    outp = tmp_path / "out.json"
    monkeypatch.setattr(sys, "argv", ["run_reference_provider_payloads.py", "--manifest", str(man), "--output", str(outp)])
    assert mod.main() == 0
    patched = json.loads(outp.read_text(encoding="utf-8"))
    a = patched["assets"][0]
    assert "reference_provider_payloads" in a
    assert a["reference_provider_payload_status"] in ("prepared", "none", "missing_reference", "needs_review", "not_supported")


def test_production_pack_summary_includes_reference_provider_payload_summary(tmp_path: Path):
    out_root = tmp_path / "output"
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)
    am = {
        "run_id": "r1",
        "assets": [{"scene_number": 1}],
        "reference_provider_payload_summary": {"assets_checked": 1, "prepared_count": 1},
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
    }
    (src / "asset_manifest.json").write_text(json.dumps(am), encoding="utf-8")
    res = build_production_pack(run_id="r1", output_root=out_root, source_paths={"asset_manifest": src / "asset_manifest.json"}, dry_run=False)
    pack = Path(res["pack_dir"])
    summary = json.loads((pack / "production_summary.json").read_text(encoding="utf-8"))
    assert summary["reference_provider_payload_summary"]["assets_checked"] == 1


def test_real_provider_smoke_includes_reference_payload_status(tmp_path: Path):
    # We test the helper path by calling run_real_provider_smoke with a minimal scene_asset_pack containing the fields.
    root = Path(__file__).resolve().parents[1]
    p = root / "app" / "production_connectors" / "real_provider_smoke.py"
    spec = importlib.util.spec_from_file_location("real_provider_smoke_mod", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    pack = {
        "scene_expansion": {
            "expanded_scene_assets": [
                {
                    "chapter_index": 0,
                    "beat_index": 0,
                    "visual_prompt": "x",
                    "visual_asset_kind": "motion_clip",
                    "reference_provider_payloads": {"openai_images": {"no_live_upload": True}},
                    "reference_provider_payload_status": "prepared",
                    "recommended_reference_provider_payload": {"provider": "openai_images", "supported_mode": "prompt_hint_only", "no_live_upload": True, "status": "prepared"},
                }
            ]
        }
    }
    pack_path = tmp_path / "scene_asset_pack.json"
    pack_path.write_text(json.dumps(pack), encoding="utf-8")
    out = mod.run_real_provider_smoke(
        pack_path,
        out_root=tmp_path,
        run_id="r1",
        selected_provider="runway",
        dry_run=True,
        real_provider_enabled=False,
        max_real_scenes=0,
        force_provider=False,
        assets_directory=None,
    )
    assert out["scenes"][0].get("reference_provider_payload_status") == "prepared"

