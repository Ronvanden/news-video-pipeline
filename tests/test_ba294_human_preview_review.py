"""BA 29.4 — Human preview review gate."""

from __future__ import annotations

import json
from pathlib import Path

from app.production_assembly.human_preview_review import (
    apply_human_preview_review_patch,
    default_human_preview_review_result,
    normalize_human_preview_review_result,
)


def test_default_pending():
    d = default_human_preview_review_result()
    assert d["review_status"] == "pending"
    assert d["approved_for_final_render"] is False


def test_normalize_approved_sets_approval_flag():
    d = normalize_human_preview_review_result({"review_status": "approved"})
    assert d["review_status"] == "approved"
    assert d["approved_for_final_render"] is True


def test_rejected_clears_approval_flag():
    d = normalize_human_preview_review_result({"review_status": "rejected", "approved_for_final_render": True})
    assert d["review_status"] == "rejected"
    assert d["approved_for_final_render"] is False


def test_apply_patch_updates_summary():
    ps = {"run_id": "x"}
    out = apply_human_preview_review_patch(ps, review_status="approved", reviewer="op", review_notes="ok")
    assert out["human_preview_review_result"]["review_status"] == "approved"
    assert out["human_preview_review_result"]["approved_for_final_render"] is True


def test_patch_cli_writes_summary(tmp_path: Path, monkeypatch):
    import importlib.util
    import sys

    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "patch_human_preview_review.py"
    spec = importlib.util.spec_from_file_location("patch_human_preview_review", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    summ = tmp_path / "ps.json"
    summ.write_text(json.dumps({"run_id": "r"}), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["patch_human_preview_review.py", "--production-summary", str(summ), "--review-status", "needs_changes", "--review-notes", "fix"],
    )
    assert mod.main() == 0
    doc = json.loads(summ.read_text(encoding="utf-8"))
    assert doc["human_preview_review_result"]["review_status"] == "needs_changes"
