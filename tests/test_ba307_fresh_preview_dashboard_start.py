"""BA 30.7 — Fresh Preview Dry-Run start from Founder Dashboard."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.founder_dashboard.html import get_founder_dashboard_html
from app.main import app


def test_start_dry_run_422_missing_input():
    client = TestClient(app)
    r = client.post("/founder/dashboard/fresh-preview/start-dry-run", json={})
    assert r.status_code == 422


def test_start_dry_run_422_both_topic_and_url():
    client = TestClient(app)
    r = client.post(
        "/founder/dashboard/fresh-preview/start-dry-run",
        json={"topic": "a", "url": "https://example.com"},
    )
    assert r.status_code == 422


def test_start_dry_run_422_whitespace_only():
    client = TestClient(app)
    r = client.post(
        "/founder/dashboard/fresh-preview/start-dry-run",
        json={"topic": "   ", "url": "  "},
    )
    assert r.status_code == 422


def _ok_result(**kwargs):
    rid = kwargs.get("run_id", "")
    return {
        "ok": True,
        "run_id": rid,
        "fresh_work_dir": str(Path("output") / "fresh_topic_preview" / rid),
        "warnings": ["ba302_dry_run:no_preview_smoke_executed"],
        "blocking_reasons": [],
    }


def test_start_dry_run_invokes_library_with_dry_run_and_placeholder():
    client = TestClient(app)
    captured: dict = {}

    def _fake(**kwargs):
        captured.update(kwargs)
        return _ok_result(**kwargs)

    with patch("app.routes.founder_dashboard.run_fresh_topic_preview_smoke", side_effect=_fake):
        r = client.post(
            "/founder/dashboard/fresh-preview/start-dry-run",
            json={"topic": "Klimapolitik heute", "max_scenes": 4, "duration_target_seconds": 60},
        )

    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["snapshot_hint"] == "Refresh Fresh Preview Snapshot"
    assert data["fresh_preview_start_dry_run_version"] == "ba30_8_v1"
    assert "handoff_cli_command_powershell" in data
    assert "handoff_cli_command" in data
    assert "_full" in data["handoff_cli_command"]
    assert "--topic" in data["handoff_cli_command"]
    assert "--dry-run" not in data["handoff_cli_command"]
    assert "--allow-live-assets" not in data["handoff_cli_command"]
    assert captured["dry_run"] is True
    assert captured["asset_runner_mode"] == "placeholder"
    assert captured["provider"] == "placeholder"
    assert captured["topic"] == "Klimapolitik heute"
    assert captured["url"] is None
    assert captured["max_scenes"] == 4
    assert captured["duration_target_seconds"] == 60
    assert str(captured["run_id"]).startswith("fresh_dash_")


def test_start_dry_run_url_branch():
    client = TestClient(app)
    captured: dict = {}

    def _fake(**kwargs):
        captured.update(kwargs)
        return _ok_result(**kwargs)

    with patch("app.routes.founder_dashboard.run_fresh_topic_preview_smoke", side_effect=_fake):
        r = client.post(
            "/founder/dashboard/fresh-preview/start-dry-run",
            json={"url": "https://example.com/a"},
        )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert captured["url"] == "https://example.com/a"
    assert captured["topic"] is None


def test_start_dry_run_request_provider_overridden_to_placeholder():
    client = TestClient(app)
    captured: dict = {}

    def _fake(**kwargs):
        captured.update(kwargs)
        return _ok_result(**kwargs)

    with patch("app.routes.founder_dashboard.run_fresh_topic_preview_smoke", side_effect=_fake):
        r = client.post(
            "/founder/dashboard/fresh-preview/start-dry-run",
            json={"topic": "x", "provider": "openai"},
        )
    assert r.status_code == 200
    assert captured["provider"] == "placeholder"


def test_config_includes_start_dry_run_relative():
    client = TestClient(app)
    r = client.get("/founder/dashboard/config")
    assert r.status_code == 200
    cfg = r.json()
    assert "fresh_preview_start_dry_run_relative" in cfg
    assert cfg["fresh_preview_start_dry_run_relative"]["path"] == "/founder/dashboard/fresh-preview/start-dry-run"
    assert cfg["fresh_preview_start_dry_run_relative"]["method"] == "POST"


def test_dashboard_html_contains_dry_run_ui():
    html = get_founder_dashboard_html()
    assert "Struktur-Test starten" in html
    assert "fp-btn-start-dry-run" in html
    assert "fresh-preview/start-dry-run" in html
    assert "data-ba307-start-dry-run" in html
