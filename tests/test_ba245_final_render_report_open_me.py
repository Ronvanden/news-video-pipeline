"""BA 24.5 — Final Render Report / OPEN_ME Update."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.run_final_render import main as run_final_render_main


def _mk_preview_run(out_root: Path, run_id: str) -> None:
    d = out_root / f"local_preview_{run_id}"
    d.mkdir(parents=True)
    (d / "preview_with_subtitles.mp4").write_bytes(b"\0\0\0\x20ftypisom")
    snap = {
        "verdict": "PASS",
        "quality_checklist": {"status": "pass"},
        "founder_quality_decision": {"decision_code": "GO_PREVIEW", "top_issue": "", "next_step": ""},
        "production_costs": {"estimated_total_cost": 1.0, "over_budget_flag": False},
        "warnings": ["Cost status unknown; review recommended."],
    }
    (d / "local_preview_result.json").write_text(json.dumps(snap), encoding="utf-8")
    appr = {
        "schema_version": "local_preview_human_approval_v1",
        "run_id": run_id,
        "status": "approved",
        "approved_at": "2026-01-01T00:00:00+00:00",
        "approved_by": "local_operator",
        "note": "",
        "source": "test",
    }
    (d / "human_approval.json").write_text(json.dumps(appr), encoding="utf-8")


def test_completed_writes_open_me_and_report_and_sets_contract_path(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    _mk_preview_run(out_root, "r1")
    code = run_final_render_main(["--run-id", "r1", "--out-root", str(out_root)])
    assert code == 0
    final_dir = out_root / "final_render_r1"
    open_me = final_dir / "FINAL_OPEN_ME.md"
    report = final_dir / "final_render_report.md"
    res = final_dir / "final_render_result.json"
    assert open_me.is_file()
    assert report.is_file()
    assert res.is_file()
    txt = open_me.read_text(encoding="utf-8")
    assert "# Final Render Package" in txt
    assert "## Open First" in txt
    assert "## Gates" in txt
    assert "## Next Step" in txt
    rtxt = report.read_text(encoding="utf-8")
    assert "# Final Render Report" in rtxt
    assert "## Summary" in rtxt
    assert "## Gates" in rtxt
    assert "Warnings" in rtxt
    j = json.loads(res.read_text(encoding="utf-8"))
    assert j["output"]["final_report_path"].endswith("final_render_report.md")


def test_skipped_existing_updates_open_me_and_report(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    _mk_preview_run(out_root, "r2")
    final_dir = out_root / "final_render_r2"
    final_dir.mkdir()
    (final_dir / "final_video.mp4").write_bytes(b"existing")
    code = run_final_render_main(["--run-id", "r2", "--out-root", str(out_root)])
    assert code == 0
    assert (final_dir / "FINAL_OPEN_ME.md").is_file()
    assert (final_dir / "final_render_report.md").is_file()
    j = json.loads((final_dir / "final_render_result.json").read_text(encoding="utf-8"))
    assert j["status"] == "skipped_existing"

