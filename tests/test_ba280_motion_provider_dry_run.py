"""BA 28.0 — Motion provider dry-run tests."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from app.production_connectors.motion_provider_adapter import build_motion_clip_result


def test_motion_clip_dry_run_ready_when_input_exists(tmp_path: Path):
    img = tmp_path / "scene_001.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")  # minimal stub bytes
    asset = {
        "scene_number": 1,
        "visual_asset_kind": "motion_clip",
        "selected_asset_path": str(img),
        "visual_prompt_effective": "prompt",
        "recommended_reference_provider_payload": {"provider": "runway", "supported_mode": "image_to_video_reference_prepared"},
    }
    res = build_motion_clip_result(asset, base_dir=tmp_path, provider="auto", duration_seconds=5, dry_run=True)
    assert res["ok"] is True
    assert res["provider_status"] == "dry_run_ready"
    assert res["no_live_upload"] is True


def test_missing_input_image_is_controlled(tmp_path: Path):
    asset = {"scene_number": 1, "visual_asset_kind": "motion_clip"}
    res = build_motion_clip_result(asset, base_dir=tmp_path, provider="runway", duration_seconds=5, dry_run=True)
    assert res["ok"] is False
    assert res["error_code"] == "missing_input_image"


def _import_cli():
    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "run_motion_provider_dry_run.py"
    spec = importlib.util.spec_from_file_location("run_motion_provider_dry_run", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cli_writes_motion_clip_manifest(tmp_path: Path, monkeypatch):
    mod = _import_cli()
    img = tmp_path / "scene_001.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    man = tmp_path / "asset_manifest.json"
    man.write_text(
        json.dumps({"assets": [{"scene_number": 1, "visual_asset_kind": "motion_clip", "selected_asset_path": str(img)}]}),
        encoding="utf-8",
    )
    outp = tmp_path / "motion_clip_manifest.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_motion_provider_dry_run.py",
            "--manifest",
            str(man),
            "--output",
            str(outp),
            "--provider",
            "runway",
            "--duration-seconds",
            "5",
            "--dry-run",
        ],
    )
    assert mod.main() == 0
    obj = json.loads(outp.read_text(encoding="utf-8"))
    assert obj["motion_clip_manifest_version"] == "ba28_0_v1"
    assert obj["summary"]["clips_planned"] == 1

