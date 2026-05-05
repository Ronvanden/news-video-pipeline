"""BA 22.3 — Dashboard Preview Start Button (Route + HTML/JS)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_html_has_preview_create_button():
    client = TestClient(app)
    t = client.get("/founder/dashboard").text
    assert "Preview erstellen" in t
    assert "/founder/dashboard/local-preview/run-mini-fixture" in t
    # BA 22.3b — Refresh-State: finale Statusmeldungen + robustes Re-Enable via finally
    assert "Panel aktualisiert" in t
    assert "aber Panel konnte nicht aktualisiert werden" in t
    assert "finally" in t


def test_config_lists_run_mini_fixture_route():
    client = TestClient(app)
    j = client.get("/founder/dashboard/config").json()
    rel = j.get("local_preview_run_mini_fixture_relative") or {}
    assert rel.get("method") == "POST"
    assert rel.get("path") == "/founder/dashboard/local-preview/run-mini-fixture"


def test_run_mini_fixture_route_success(monkeypatch):
    import app.routes.founder_dashboard as fd

    monkeypatch.setattr(fd, "_ba223_preflight_check", lambda: {"ok": True, "warnings": []})
    monkeypatch.setattr(
        fd,
        "_ba223_run_mini_fixture",
        lambda *, out_root, run_id, force_burn: {
            "verdict": "PASS",
            "warnings": [],
            "blocking_reasons": [],
            "paths": {"preview_with_subtitles": "output/local_preview_" + run_id + "/preview_with_subtitles.mp4"},
            "result_contract": {"id": "local_preview_result_v1", "schema_version": 1},
        },
    )

    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/run-mini-fixture", json={})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["run_id"] == "mini_e2e"
    assert (j.get("result") or {}).get("verdict") == "PASS"
    assert "panel" in j


def test_run_mini_fixture_route_rejects_bad_run_id():
    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/run-mini-fixture", json={"run_id": "../x"})
    assert r.status_code == 422


def test_run_mini_fixture_route_preflight_fail_returns_ok_false(monkeypatch):
    import app.routes.founder_dashboard as fd

    monkeypatch.setattr(
        fd,
        "_ba223_preflight_check",
        lambda: {"ok": False, "missing_tools": ["ffmpeg"], "setup_hint": "Install FFmpeg.", "warnings": ["x"]},
    )

    # ensure pipeline won't run if preflight fails
    monkeypatch.setattr(fd, "_ba223_run_mini_fixture", lambda **_: (_ for _ in ()).throw(RuntimeError("should not run")))

    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/run-mini-fixture", json={})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is False
    assert "preflight" in j
    assert "setup_hint" in (j["preflight"] or {})


def test_run_mini_fixture_skip_preflight_does_not_call_preflight(monkeypatch):
    import app.routes.founder_dashboard as fd

    def _boom():
        raise RuntimeError("preflight should be skipped")

    monkeypatch.setattr(fd, "_ba223_preflight_check", _boom)
    monkeypatch.setattr(
        fd,
        "_ba223_run_mini_fixture",
        lambda *, out_root, run_id, force_burn: {"verdict": "WARNING", "warnings": [], "blocking_reasons": [], "paths": {}},
    )

    client = TestClient(app)
    r = client.post("/founder/dashboard/local-preview/run-mini-fixture", json={"skip_preflight": True})
    assert r.status_code == 200
    assert r.json()["ok"] is True

