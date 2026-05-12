from fastapi.testclient import TestClient

from app.main import app
from app.visual_plan.presets import VISUAL_PROMPT_CONTROL_DEFAULTS


def _ids(entries):
    return {entry["id"] for entry in entries}


def test_visual_plan_presets_endpoint_returns_defaults_and_controls():
    client = TestClient(app)
    r = client.get("/visual-plan/presets")

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["defaults"] == VISUAL_PROMPT_CONTROL_DEFAULTS
    controls = data["controls"]
    assert set(controls.keys()) == {
        "visual_presets",
        "prompt_detail_levels",
        "provider_targets",
        "text_safety_modes",
        "visual_consistency_modes",
    }
    assert "documentary_realism" in _ids(controls["visual_presets"])
    assert _ids(controls["provider_targets"]) == {"generic", "openai_image", "runway", "kling"}
