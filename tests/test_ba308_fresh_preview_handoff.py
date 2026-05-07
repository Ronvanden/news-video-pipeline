"""BA 30.8 — Full Preview Smoke CLI handoff after dashboard dry-run."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.founder_dashboard.html import get_founder_dashboard_html
from app.main import app


def _fail_result(**kwargs):
    return {
        "ok": False,
        "run_id": kwargs.get("run_id", ""),
        "fresh_work_dir": "",
        "warnings": [],
        "blocking_reasons": ["test_blocker"],
    }


def test_handoff_not_included_when_dry_run_fails():
    client = TestClient(app)

    def _fake(**kwargs):
        return _fail_result(**kwargs)

    with patch("app.routes.founder_dashboard.run_fresh_topic_preview_smoke", side_effect=_fake):
        r = client.post(
            "/founder/dashboard/fresh-preview/start-dry-run",
            json={"topic": "nur test"},
        )
    assert r.status_code == 200
    d = r.json()
    assert d.get("ok") is False
    assert "handoff_cli_command_powershell" not in d
    assert "handoff_cli_command" not in d


def test_handoff_url_branch_powershell():
    client = TestClient(app)

    def _fake(**kwargs):
        rid = kwargs["run_id"]
        return {
            "ok": True,
            "run_id": rid,
            "fresh_work_dir": str(Path("output") / "fresh_topic_preview" / rid),
            "warnings": [],
            "blocking_reasons": [],
        }

    with patch("app.routes.founder_dashboard.run_fresh_topic_preview_smoke", side_effect=_fake):
        r = client.post(
            "/founder/dashboard/fresh-preview/start-dry-run",
            json={"url": "https://example.com/news/a", "duration_target_seconds": 50, "max_scenes": 3},
        )
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    ps = d["handoff_cli_command_powershell"]
    assert "--url" in ps
    assert "https://example.com/news/a" in ps
    assert "--topic" not in ps
    assert "--dry-run" not in ps
    assert "--allow-live-assets" not in ps
    assert d["run_id"] + "_full" in ps.replace("\n", " ")
    cmd = d["handoff_cli_command"]
    assert "--url" in cmd
    assert "--dry-run" not in cmd


def test_dashboard_html_handoff_strings():
    html = get_founder_dashboard_html()
    assert "Nächster Schritt: vollen Vorschau-Prüflauf lokal starten" in html
    assert "Befehl zum Kopieren" in html
    assert "fp-btn-copy-handoff-cli" in html
