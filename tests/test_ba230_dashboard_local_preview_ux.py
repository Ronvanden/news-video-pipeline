"""BA 23.0 — Dashboard Local Preview UX Polish / Control Review."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_local_preview_ux_sections_and_controls_present():
    client = TestClient(app)
    t = client.get("/founder/dashboard").text

    # Section labels (founder/operator readability)
    assert "Founder Summary" in t
    assert "Preview Actions" in t
    assert "Quality & Diagnostics" in t
    assert "Human Approval" in t
    assert "Final Render" in t
    assert "Recent Runs" in t or "Letzte Läufe" in t

    # Key button/link texts still present
    assert "Preview erstellen" in t
    assert "Preview öffnen" in t  # BA 22.2 link label
    assert "Report öffnen" in t
    assert "OPEN_ME öffnen" in t
    assert "JSON öffnen" in t
    assert "Preview freigeben" in t
    assert "Freigabe zurückziehen" in t
    assert "Finales Video erstellen" in t

    # Keep past JS robustness check anchored
    assert 'innerHTML = "<p class="' not in t

