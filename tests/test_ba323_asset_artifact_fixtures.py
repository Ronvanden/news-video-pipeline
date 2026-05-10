"""BA 32.23 — Regression: build_asset_artifact aus festen asset_manifest.json-Szenarien (ohne Orchestrator)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.founder_dashboard.ba323_video_generate import build_asset_artifact

_MIN_BYTES = b"\x89PNG\r\n\x1a\n"


def _write_manifest(asset_dir: Path, manifest: dict) -> Path:
    asset_dir.mkdir(parents=True, exist_ok=True)
    mp = asset_dir / "asset_manifest.json"
    mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return mp


def test_fixture_placeholder_only(tmp_path: Path) -> None:
    d = tmp_path / "placeholder_only"
    d.mkdir(parents=True, exist_ok=True)
    (d / "p1.png").write_bytes(_MIN_BYTES)
    (d / "p2.png").write_bytes(_MIN_BYTES)
    mp = _write_manifest(
        d,
        {
            "run_id": "fix_ph",
            "assets": [
                {"image_path": "p1.png", "generation_mode": "placeholder"},
                {"image_path": "p2.png", "generation_mode": "placeholder"},
            ],
        },
    )
    aa = build_asset_artifact(asset_manifest_path=str(mp))
    assert aa["real_asset_file_count"] == 0
    assert aa["placeholder_asset_count"] == 2
    assert aa["generation_modes"].get("placeholder") == 2
    gate = aa["asset_quality_gate"]
    assert gate["status"] == "placeholder_only"
    assert gate["strict_ready"] is False
    assert gate["loose_ready"] is False


def test_fixture_mixed_assets(tmp_path: Path) -> None:
    d = tmp_path / "mixed"
    d.mkdir(parents=True, exist_ok=True)
    (d / "live.png").write_bytes(_MIN_BYTES)
    (d / "ph.png").write_bytes(_MIN_BYTES)
    mp = _write_manifest(
        d,
        {
            "run_id": "fix_mx",
            "assets": [
                {"image_path": "live.png", "generation_mode": "leonardo_live"},
                {"image_path": "ph.png", "generation_mode": "placeholder"},
            ],
        },
    )
    aa = build_asset_artifact(asset_manifest_path=str(mp))
    assert aa["real_asset_file_count"] == 1
    assert aa["placeholder_asset_count"] == 1
    assert aa["generation_modes"].get("leonardo_live") == 1
    assert aa["generation_modes"].get("placeholder") == 1
    gate = aa["asset_quality_gate"]
    assert gate["status"] == "mixed_assets"
    assert gate["strict_ready"] is False
    assert gate["loose_ready"] is True


def test_fixture_production_ready(tmp_path: Path) -> None:
    d = tmp_path / "production_ready"
    d.mkdir(parents=True, exist_ok=True)
    (d / "a.png").write_bytes(_MIN_BYTES)
    (d / "b.png").write_bytes(_MIN_BYTES)
    mp = _write_manifest(
        d,
        {
            "run_id": "fix_pr",
            "assets": [
                {"image_path": "a.png", "generation_mode": "leonardo_live"},
                {"image_path": "b.png", "generation_mode": "leonardo_live"},
            ],
        },
    )
    aa = build_asset_artifact(asset_manifest_path=str(mp))
    assert aa["real_asset_file_count"] > 0
    assert aa["placeholder_asset_count"] == 0
    assert aa["generation_modes"].get("leonardo_live", 0) > 0
    gate = aa["asset_quality_gate"]
    assert gate["status"] == "production_ready"
    assert gate["strict_ready"] is True
    assert gate["loose_ready"] is True


def test_fixture_missing_empty_assets(tmp_path: Path) -> None:
    d = tmp_path / "empty"
    mp = _write_manifest(d, {"run_id": "fix_empty", "assets": []})
    aa = build_asset_artifact(asset_manifest_path=str(mp))
    assert aa["asset_manifest_file_count"] == 0
    assert aa["asset_quality_gate"]["status"] == "missing_assets"


def test_fixture_unknown_mode_fallback(tmp_path: Path) -> None:
    """Keine generation_mode/mode/provider_used/source_type: defensiv, kein Crash."""
    d_missing = tmp_path / "unknown_missing_files"
    mp1 = _write_manifest(
        d_missing,
        {
            "run_id": "fix_unk1",
            "assets": [
                {"image_path": "not_here.png"},
                {"video_path": "gone.mp4"},
            ],
        },
    )
    aa1 = build_asset_artifact(asset_manifest_path=str(mp1))
    assert aa1["generation_modes"] == {}
    assert aa1["asset_manifest_file_count"] == 0
    assert aa1["asset_quality_gate"]["status"] == "missing_assets"

    d_file = tmp_path / "unknown_with_file"
    d_file.mkdir(parents=True, exist_ok=True)
    (d_file / "opaque.png").write_bytes(_MIN_BYTES)
    mp2 = _write_manifest(
        d_file,
        {"run_id": "fix_unk2", "assets": [{"image_path": "opaque.png"}]},
    )
    aa2 = build_asset_artifact(asset_manifest_path=str(mp2))
    assert aa2["generation_modes"] == {}
    assert aa2["real_asset_file_count"] == 1
    assert aa2["placeholder_asset_count"] == 0
    assert aa2["asset_quality_gate"]["status"] == "production_ready"
    assert aa2["asset_quality_gate"]["strict_ready"] is True
