"""BA 22.0 — Dashboard Local Preview Panel (JSON + Scan-Helfer)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.founder_dashboard.local_preview_panel import (
    build_local_preview_panel_payload,
    default_local_preview_out_root,
)
from app.main import app


def test_default_out_root_points_to_repo_output():
    p = default_local_preview_out_root()
    assert p.name == "output"


def test_build_panel_lists_run_and_artifacts(tmp_path: Path):
    run_dir = tmp_path / "local_preview_demo_run"
    run_dir.mkdir(parents=True)
    (run_dir / "OPEN_ME.md").write_text("# x", encoding="utf-8")
    (run_dir / "local_preview_report.md").write_text("# r", encoding="utf-8")

    payload = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=10)
    assert payload["panel_version"] == "ba22_local_preview_panel_v3"
    assert payload["result_contract"]["id"] == "local_preview_result_v1"
    assert payload["out_root_exists"] is True
    assert len(payload["runs"]) == 1
    r0 = payload["runs"][0]
    assert r0["run_id"] == "demo_run"
    assert r0["artifacts"]["open_me"] is True
    assert r0["artifacts"]["founder_report"] is True
    assert r0["artifacts"]["preview_with_subtitles"] is False
    assert "status_cards" in r0
    assert r0["status_cards"]["verdict"] == "UNKNOWN"
    ids = [a["id"] for a in payload["actions"]]
    assert "cli_mini_fixture" in ids and "doc_runbook" in ids


def test_get_panel_endpoint_uses_injected_builder(monkeypatch, tmp_path: Path):
    run_dir = tmp_path / "local_preview_api_test"
    run_dir.mkdir(parents=True)
    (run_dir / "preview_with_subtitles.mp4").write_bytes(b"\0\0")

    import app.routes.founder_dashboard as fd_mod

    monkeypatch.setattr(
        fd_mod,
        "build_local_preview_panel_payload",
        lambda: build_local_preview_panel_payload(out_root=tmp_path),
    )

    client = TestClient(app)
    res = client.get("/founder/dashboard/local-preview/panel")
    assert res.status_code == 200
    data = res.json()
    assert data["out_root_exists"] is True
    assert any(x.get("run_id") == "api_test" for x in data.get("runs", []))


def test_dashboard_config_lists_local_preview_panel_path():
    client = TestClient(app)
    r = client.get("/founder/dashboard/config")
    assert r.status_code == 200
    cfg = r.json()
    rel = cfg.get("local_preview_panel_relative") or {}
    assert rel.get("path") == "/founder/dashboard/local-preview/panel"
    assert rel.get("method") == "GET"
