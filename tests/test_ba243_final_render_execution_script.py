"""BA 24.3 — Final Render Execution Script (V1 copy preview)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.run_final_render import main as run_final_render_main


def _mk_preview_run(
    out_root: Path,
    run_id: str,
    *,
    approval_status: str = "approved",
    quality_status: str = "pass",
    founder_decision: str = "GO_PREVIEW",
    over_budget: bool = False,
    with_preview: bool = True,
) -> Path:
    d = out_root / f"local_preview_{run_id}"
    d.mkdir(parents=True)
    if with_preview:
        (d / "preview_with_subtitles.mp4").write_bytes(b"\0\0\0\x20ftypisom")
    snap = {
        "verdict": "PASS",
        "quality_checklist": {"status": quality_status},
        "founder_quality_decision": {"decision_code": founder_decision, "top_issue": "", "next_step": ""},
        "production_costs": {"estimated_total_cost": 1.0, "over_budget_flag": bool(over_budget)},
    }
    (d / "local_preview_result.json").write_text(json.dumps(snap), encoding="utf-8")
    appr = {
        "schema_version": "local_preview_human_approval_v1",
        "run_id": run_id,
        "status": approval_status,
        "approved_at": "2026-01-01T00:00:00+00:00",
        "approved_by": "local_operator",
        "note": "",
        "source": "test",
    }
    (d / "human_approval.json").write_text(json.dumps(appr), encoding="utf-8")
    return d


def test_ready_run_copies_preview_and_writes_contract_and_open_me(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    _mk_preview_run(out_root, "mini_e2e", approval_status="approved", over_budget=False)
    code = run_final_render_main(["--run-id", "mini_e2e", "--out-root", str(out_root)])
    assert code == 0
    final_dir = out_root / "final_render_mini_e2e"
    assert (final_dir / "final_video.mp4").is_file()
    assert (final_dir / "final_render_result.json").is_file()
    assert (final_dir / "FINAL_OPEN_ME.md").is_file()
    j = json.loads((final_dir / "final_render_result.json").read_text(encoding="utf-8"))
    assert j["schema_version"] == "final_render_result_v1"
    assert j["status"] == "completed"


def test_skipped_existing_when_final_video_exists(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    _mk_preview_run(out_root, "rid1", approval_status="approved", over_budget=False)
    final_dir = out_root / "final_render_rid1"
    final_dir.mkdir()
    (final_dir / "final_video.mp4").write_bytes(b"existing")
    code = run_final_render_main(["--run-id", "rid1", "--out-root", str(out_root)])
    assert code == 0
    j = json.loads((final_dir / "final_render_result.json").read_text(encoding="utf-8"))
    assert j["status"] == "skipped_existing"


def test_force_overwrites_existing(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    _mk_preview_run(out_root, "rid2", approval_status="approved", over_budget=False)
    final_dir = out_root / "final_render_rid2"
    final_dir.mkdir()
    (final_dir / "final_video.mp4").write_bytes(b"old")
    code = run_final_render_main(["--run-id", "rid2", "--out-root", str(out_root), "--force"])
    assert code == 0
    assert (final_dir / "final_video.mp4").read_bytes() != b"old"


def test_locked_dry_run_exits_2_and_does_not_write(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    _mk_preview_run(out_root, "lock1", approval_status="not_approved", over_budget=False)
    code = run_final_render_main(["--run-id", "lock1", "--out-root", str(out_root)])
    assert code == 2
    assert not (out_root / "final_render_lock1").exists()


def test_invalid_run_id_exits_3(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    code = run_final_render_main(["--run-id", "../x", "--out-root", str(out_root)])
    assert code == 3


def test_missing_preview_dir_exits_1(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    code = run_final_render_main(["--run-id", "missing", "--out-root", str(out_root)])
    assert code == 1


def test_print_json_outputs_json(tmp_path: Path, capsys):
    out_root = tmp_path / "output"
    out_root.mkdir()
    _mk_preview_run(out_root, "pj1", approval_status="approved", over_budget=False)
    code = run_final_render_main(["--run-id", "pj1", "--out-root", str(out_root), "--print-json"])
    assert code == 0
    out = capsys.readouterr().out
    j = json.loads(out)
    assert j["ok"] is True
    assert j["status"] in ("completed", "skipped_existing")


def test_run_final_render_script_help_no_import_error():
    """Direkter Scriptstart darf nicht an `No module named app` scheitern."""
    cp = subprocess.run(
        [sys.executable, "scripts/run_final_render.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert cp.returncode == 0
    assert "No module named" not in (cp.stderr or "")

