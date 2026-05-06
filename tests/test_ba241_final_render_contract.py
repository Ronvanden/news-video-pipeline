"""BA 24.1 — Final Render Contract (final_render_result.json)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.final_render_contract import (
    FINAL_RENDER_ALLOWED_STATUSES,
    FINAL_RENDER_RESULT_CONTRACT_ID,
    FINAL_RENDER_RESULT_FILENAME,
    FINAL_RENDER_RESULT_SCHEMA_VERSION,
    apply_final_render_result_contract,
    build_final_render_result_contract,
    load_final_render_result_json,
    write_final_render_result_json,
)


def test_build_contract_includes_required_fields(tmp_path: Path):
    c = build_final_render_result_contract(
        run_id="mini_e2e",
        source_preview_package_dir=tmp_path / "output" / "local_preview_mini_e2e",
        output_dir=tmp_path / "output" / "final_render_mini_e2e",
        status="ready",
    )
    assert c["contract_id"] == FINAL_RENDER_RESULT_CONTRACT_ID
    assert c["schema_version"] == FINAL_RENDER_RESULT_SCHEMA_VERSION
    assert c["run_id"] == "mini_e2e"
    assert c["status"] == "ready"
    assert "created_at" in c and "updated_at" in c
    assert isinstance(c["source"], dict)
    assert isinstance(c["output"], dict)
    assert isinstance(c["gates"], dict)
    assert isinstance(c["warnings"], list)
    assert isinstance(c["blocking_reasons"], list)
    assert isinstance(c["metadata"], dict)
    assert c["output"]["final_video_path"].endswith("final_video.mp4")
    assert c["output"]["final_open_me_path"].endswith("FINAL_OPEN_ME.md")


def test_build_contract_invalid_status_raises(tmp_path: Path):
    with pytest.raises(ValueError):
        build_final_render_result_contract(
            run_id="x",
            source_preview_package_dir=tmp_path,
            output_dir=tmp_path,
            status="nope",
        )


def test_apply_contract_on_minimal_dict_adds_defaults():
    raw: dict = {}
    out = apply_final_render_result_contract(raw)
    assert out is raw
    assert out["contract_id"] == FINAL_RENDER_RESULT_CONTRACT_ID
    assert out["schema_version"] == FINAL_RENDER_RESULT_SCHEMA_VERSION
    assert out["status"] in FINAL_RENDER_ALLOWED_STATUSES
    assert isinstance(out["source"], dict)
    assert isinstance(out["output"], dict)
    assert isinstance(out["gates"], dict)
    assert isinstance(out["warnings"], list)
    assert isinstance(out["blocking_reasons"], list)
    assert isinstance(out["metadata"], dict)


def test_write_and_load_roundtrip(tmp_path: Path):
    out_dir = tmp_path / "final_render_x"
    c = build_final_render_result_contract(
        run_id="x",
        source_preview_package_dir=tmp_path / "local_preview_x",
        output_dir=out_dir,
        status="running",
        warnings=["w1"],
        blocking_reasons=["b1"],
    )
    p = write_final_render_result_json(c, out_dir)
    assert p.name == FINAL_RENDER_RESULT_FILENAME
    assert p.is_file()
    j = json.loads(p.read_text(encoding="utf-8"))
    assert j["schema_version"] == FINAL_RENDER_RESULT_SCHEMA_VERSION
    loaded = load_final_render_result_json(p)
    assert loaded["contract_id"] == FINAL_RENDER_RESULT_CONTRACT_ID
    assert loaded["status"] == "running"
    assert loaded["warnings"] == ["w1"]
    assert loaded["blocking_reasons"] == ["b1"]


def test_apply_normalizes_warnings_and_gate_states():
    raw = {
        "warnings": "one",
        "blocking_reasons": [None, "x", "  "],
        "gates": {"preview_available": "PASS", "quality_not_fail": "fail"},
        "status": "completed",
    }
    apply_final_render_result_contract(raw)
    assert raw["warnings"] == ["one"]
    assert raw["blocking_reasons"] == ["x"]
    assert raw["gates"]["preview_available"] == "pass"
    assert raw["gates"]["quality_not_fail"] == "fail"

