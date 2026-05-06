"""BA 29.1 — Legacy asset_manifest upgrade helper + CLI."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from app.visual_plan.asset_approval_gate import evaluate_production_asset_approval
from app.visual_plan.legacy_manifest_upgrade import (
    build_legacy_manifest_upgrade_summary,
    detect_legacy_asset_manifest_issues,
    upgrade_legacy_asset_manifest,
)


def _import_cli():
    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "upgrade_legacy_asset_manifest.py"
    spec = importlib.util.spec_from_file_location("upgrade_legacy_asset_manifest", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_detect_legacy_issues_minimal_manifest():
    man = {
        "assets": [
            {
                "scene_number": 1,
                "visual_prompt": "cinematic wide shot",
                "provider_used": "leonardo",
                "image_path": "scene_001.png",
            }
        ]
    }
    det = detect_legacy_asset_manifest_issues(man)
    assert "visual_cost_summary_missing" in det["manifest_issues"]
    assert "production_asset_approval_result_missing" in det["manifest_issues"]
    row = det["assets"][0]
    assert "visual_prompt_effective_missing" in row["issues"]
    assert "visual_text_guard_missing" in row["issues"]
    assert "visual_policy_status_missing" in row["issues"]
    assert "visual_policy_warnings_missing" in row["issues"]
    assert "asset_override_fields_missing" in row["issues"]


def test_upgrade_derives_effective_appends_guard_and_defaults():
    man = {
        "run_id": "legacy1",
        "assets": [
            {
                "scene_number": 1,
                "visual_prompt": "office interior",
                "provider_used": "leonardo",
                "image_path": "scene_001.png",
                "visual_policy_status": "needs_review",
            }
        ],
    }
    out = upgrade_legacy_asset_manifest(man, mode="smoke_safe")
    a = out["assets"][0]
    assert a["visual_prompt_effective"]
    assert "[visual_no_text_guard_v26_4]" in a["visual_prompt_effective"]
    assert a["visual_text_guard_applied"] is True
    assert a["visual_policy_status"] == "needs_review"
    assert "legacy_manifest_guard_patched_for_smoke" in (a.get("visual_policy_warnings") or [])
    assert out["legacy_manifest_upgrade_version"] == "ba29_1_v1"
    assert out["legacy_manifest_upgrade_mode"] == "smoke_safe"
    summ = out["legacy_manifest_upgrade_summary"]
    assert summ["summary_version"] == "ba29_1_v1"
    assert "issues_before" in summ


def test_upgrade_does_not_mutate_input():
    man = {"assets": [{"scene_number": 1, "visual_prompt": "x"}]}
    _ = upgrade_legacy_asset_manifest(man)
    assert "visual_prompt_effective" not in man["assets"][0]


def test_detect_after_upgrade_clears_asset_issue_counts_for_guard():
    man = {
        "assets": [
            {
                "scene_number": 1,
                "visual_prompt": "test",
                "provider_used": "leonardo",
                "image_path": "a.png",
            }
        ]
    }
    out = upgrade_legacy_asset_manifest(man)
    det = detect_legacy_asset_manifest_issues(out)
    row = det["assets"][0]
    assert "visual_text_guard_missing" not in row["issues"]
    assert "visual_prompt_effective_missing" not in row["issues"]


def test_build_summary_includes_detect():
    man = {"assets": [], "legacy_manifest_upgrade_version": "ba29_1_v1"}
    s = build_legacy_manifest_upgrade_summary(man)
    assert s["detect"]["detector_version"] == "ba29_1_v1"


def test_upgrade_enables_approval_when_accepted_and_paths_present():
    man = {
        "assets": [
            {
                "scene_number": 1,
                "visual_prompt": "wide",
                "provider_used": "leonardo",
                "image_path": "scene_001.png",
                "asset_decision_status": "accepted",
            }
        ]
    }
    out = upgrade_legacy_asset_manifest(man)
    res = evaluate_production_asset_approval(out)
    assert res["approval_status"] in ("approved", "needs_review")
    assert res["ok"] is True


def test_cli_writes_upgraded_file(tmp_path: Path, monkeypatch):
    mod = _import_cli()
    man = {
        "assets": [
            {
                "scene_number": 1,
                "visual_prompt": "city skyline",
                "provider_used": "leonardo",
                "image_path": "scene_001.png",
                "asset_decision_status": "accepted",
            }
        ]
    }
    src = tmp_path / "in.json"
    dst = tmp_path / "out.json"
    src.write_text(json.dumps(man), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "upgrade_legacy_asset_manifest.py",
            "--manifest",
            str(src),
            "--output",
            str(dst),
            "--run-cost-tracking",
            "--run-approval-gate",
        ],
    )
    assert mod.main() == 0
    assert dst.is_file()
    data = json.loads(dst.read_text(encoding="utf-8"))
    assert data["legacy_manifest_upgrade_version"] == "ba29_1_v1"
    assert isinstance(data.get("visual_cost_summary"), dict)
    assert isinstance(data.get("production_asset_approval_result"), dict)


def test_cli_dry_run_skips_write(tmp_path: Path, monkeypatch):
    mod = _import_cli()
    src = tmp_path / "in.json"
    dst = tmp_path / "out.json"
    src.write_text(json.dumps({"assets": [{"scene_number": 1, "visual_prompt": "p", "image_path": "a.png", "provider_used": "leonardo"}]}), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "upgrade_legacy_asset_manifest.py",
            "--manifest",
            str(src),
            "--output",
            str(dst),
            "--dry-run",
        ],
    )
    assert mod.main() == 0
    assert not dst.exists()
