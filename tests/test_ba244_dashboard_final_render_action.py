"""BA 24.4 — Dashboard Final Render Action (route + minimal UI strings)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _patch_out_root(monkeypatch, tmp: Path) -> None:
    import app.routes.founder_dashboard as fd

    monkeypatch.setattr(fd, "default_local_preview_out_root", lambda: tmp)


def _mk_ready_run(tmp_path: Path, run_id: str) -> Path:
    d = tmp_path / f"local_preview_{run_id}"
    d.mkdir(parents=True)
    (d / "preview_with_subtitles.mp4").write_bytes(b"\0\0\0\x20ftypisom")
    snap = {
        "verdict": "PASS",
        "quality_checklist": {"status": "pass"},
        "founder_quality_decision": {"decision_code": "GO_PREVIEW", "top_issue": "", "next_step": ""},
        "production_costs": {"estimated_total_cost": 1.0, "over_budget_flag": False},
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
    return d


def _mk_locked_run(tmp_path: Path, run_id: str) -> Path:
    d = tmp_path / f"local_preview_{run_id}"
    d.mkdir(parents=True)
    (d / "preview_with_subtitles.mp4").write_bytes(b"\0\0")
    (d / "local_preview_result.json").write_text(
        json.dumps(
            {
                "verdict": "PASS",
                "quality_checklist": {"status": "pass"},
                "founder_quality_decision": {"decision_code": "GO_PREVIEW", "top_issue": "", "next_step": ""},
            }
        ),
        encoding="utf-8",
    )
    # no approval file -> locked
    return d


def test_final_render_route_completed(monkeypatch, tmp_path: Path):
    _patch_out_root(monkeypatch, tmp_path)
    _mk_ready_run(tmp_path, "fr1")
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/final-render/run/fr1", json={"force": False})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["status"] in ("completed", "skipped_existing")
    final_dir = tmp_path / "final_render_fr1"
    assert (final_dir / "final_video.mp4").is_file()
    assert (final_dir / "final_render_result.json").is_file()
    assert (final_dir / "FINAL_OPEN_ME.md").is_file()


def test_final_render_route_skipped_existing(monkeypatch, tmp_path: Path):
    _patch_out_root(monkeypatch, tmp_path)
    _mk_ready_run(tmp_path, "fr2")
    final_dir = tmp_path / "final_render_fr2"
    final_dir.mkdir()
    (final_dir / "final_video.mp4").write_bytes(b"existing")
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/final-render/run/fr2", json={})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["status"] == "skipped_existing"


def test_final_render_route_locked_does_not_write(monkeypatch, tmp_path: Path):
    _patch_out_root(monkeypatch, tmp_path)
    _mk_locked_run(tmp_path, "fr3")
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/final-render/run/fr3", json={})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is False
    assert j["status"] in ("locked", "blocked", "unknown")
    assert not (tmp_path / "final_render_fr3").exists()


def test_final_render_route_invalid_run_id_422():
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/final-render/run/../x", json={})
    assert r.status_code in (404, 422)


def test_dashboard_html_contains_final_render_run_route_string():
    client = TestClient(app)
    t = client.get("/founder/dashboard").text
    assert "/founder/dashboard/local-preview/final-render/run/" in t
    assert "Final Render läuft" in t
    assert "Final Render abgeschlossen" in t

