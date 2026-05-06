"""BA 27.0 — Production Pack V1 tests (file-based, no live calls)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from app.real_video_build.production_pack import build_production_pack


def _write(p: Path, obj) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def _asset_manifest(*, approval_status: str | None, asset_path: str, policy_status: str = "safe", decision: str = "pending"):
    man = {
        "run_id": "r1",
        "assets": [
            {
                "scene_number": 1,
                "provider_used": "leonardo",
                "image_path": asset_path,
                "generated_image_path": asset_path,
                "visual_text_guard_applied": True,
                "visual_policy_status": policy_status,
                "asset_decision_status": decision,
                "text_sensitive": False,
                "overlay_intent": [],
            }
        ],
        "visual_cost_summary": {"visual_total_estimated_cost_eur": 0.12, "visual_cost_breakdown_by_provider": {"leonardo": 0.12}},
    }
    if approval_status is not None:
        man["production_asset_approval_result"] = {
            "ok": approval_status != "blocked",
            "approval_status": approval_status,
            "blocking_reasons": ["x"] if approval_status == "blocked" else [],
            "warnings": ["w1"] if approval_status != "approved" else [],
            "assets_checked": 1,
        }
    return man


def test_pack_builds_and_writes_files_when_approved(tmp_path: Path):
    out_root = tmp_path / "output"
    src_dir = tmp_path / "src"
    asset_file = src_dir / "scene_001.png"
    asset_file.parent.mkdir(parents=True, exist_ok=True)
    asset_file.write_bytes(b"\x89PNG\r\n\x1a\n")  # tiny dummy header only

    am = _write(src_dir / "asset_manifest.json", _asset_manifest(approval_status="approved", asset_path="scene_001.png"))
    sp = _write(src_dir / "scene_asset_pack.json", {"title": "t", "scenes": [{"n": 1}]})
    sj = _write(src_dir / "script.json", {"title": "Script Title"})

    res = build_production_pack(
        run_id="r1",
        output_root=out_root,
        source_paths={"asset_manifest": am, "scene_asset_pack": sp, "script_json": sj},
        dry_run=False,
    )
    assert res["ok"] is True
    assert res["ready_for_render"] is True
    assert res["render_readiness_status"] == "ready"

    pack_dir = Path(res["pack_dir"])
    assert (pack_dir / "production_summary.json").is_file()
    assert (pack_dir / "README_PRODUCTION_PACK.md").is_file()
    assert (pack_dir / "production_asset_approval.json").is_file()
    assert (pack_dir / "production_pack_reference.json").is_file()
    assert (pack_dir / "asset_manifest.json").is_file()
    assert (pack_dir / "scene_asset_pack.json").is_file()
    assert (pack_dir / "script.json").is_file()
    # asset copied
    assert (pack_dir / "assets" / "images" / "scene_001.png").is_file()

    summary = json.loads((pack_dir / "production_summary.json").read_text(encoding="utf-8"))
    assert summary["approval_status"] == "approved"
    assert summary["ready_for_render"] is True
    assert summary["visual_cost_summary"]["visual_total_estimated_cost_eur"] == 0.12

    ref = json.loads((pack_dir / "production_pack_reference.json").read_text(encoding="utf-8"))
    assert ref["pack_dir"]
    assert "production_summary.json" in ref["production_summary_path"]
    assert ref["ready_for_render"] is True


def test_pack_not_ready_when_needs_review(tmp_path: Path):
    out_root = tmp_path / "output"
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    am = _write(src_dir / "asset_manifest.json", _asset_manifest(approval_status="needs_review", asset_path="scene_001.png"))
    res = build_production_pack(run_id="r1", output_root=out_root, source_paths={"asset_manifest": am}, dry_run=False)
    assert res["ready_for_render"] is False
    assert res["render_readiness_status"] == "needs_review"


def test_pack_not_ready_when_blocked(tmp_path: Path):
    out_root = tmp_path / "output"
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    am = _write(src_dir / "asset_manifest.json", _asset_manifest(approval_status="blocked", asset_path="scene_001.png"))
    res = build_production_pack(run_id="r1", output_root=out_root, source_paths={"asset_manifest": am}, dry_run=False)
    assert res["ready_for_render"] is False
    assert res["render_readiness_status"] == "blocked"
    assert res["approval_status"] == "blocked"
    assert "render_not_ready_due_to_approval_status" in (res["blocking_reasons"] or [])


def test_missing_approval_result_forces_not_ready_with_warning(tmp_path: Path):
    out_root = tmp_path / "output"
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    am = _write(src_dir / "asset_manifest.json", _asset_manifest(approval_status=None, asset_path="scene_001.png"))
    res = build_production_pack(run_id="r1", output_root=out_root, source_paths={"asset_manifest": am}, dry_run=False)
    assert res["ready_for_render"] is False
    assert res["approval_status"] == "blocked"
    assert "approval_result_missing" in (res["warnings"] or [])


def test_missing_asset_file_is_warning_not_crash(tmp_path: Path):
    out_root = tmp_path / "output"
    src_dir = tmp_path / "src"
    am = _write(src_dir / "asset_manifest.json", _asset_manifest(approval_status="approved", asset_path="missing.png"))
    res = build_production_pack(run_id="r1", output_root=out_root, source_paths={"asset_manifest": am}, dry_run=False)
    # approved still makes ready_for_render true, but we should record missing asset file
    assert res["ready_for_render"] is True
    summary = json.loads((Path(res["pack_dir"]) / "production_summary.json").read_text(encoding="utf-8"))
    assert any("image_path:missing.png" in x or "generated_image_path:missing.png" in x for x in summary["files"]["missing_asset_files"])


def test_dry_run_does_not_write_pack_files(tmp_path: Path):
    out_root = tmp_path / "output"
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    am = _write(src_dir / "asset_manifest.json", _asset_manifest(approval_status="approved", asset_path="scene_001.png"))
    res = build_production_pack(run_id="r1", output_root=out_root, source_paths={"asset_manifest": am}, dry_run=True)
    assert res["ok"] is True
    assert (Path(res["pack_dir"]) / "production_summary.json").is_file() is False
    assert (Path(res["pack_dir"]) / "README_PRODUCTION_PACK.md").is_file() is False
    assert (Path(res["pack_dir"]) / "production_pack_reference.json").is_file() is False


def test_cli_script_imports_and_runs_smoke(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "build_production_pack_v1.py"
    spec = importlib.util.spec_from_file_location("build_production_pack_v1", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "main")

