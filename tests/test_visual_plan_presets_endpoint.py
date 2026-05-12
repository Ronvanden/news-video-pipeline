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


def test_visual_plan_prompt_preview_endpoint_returns_engine_output():
    client = TestClient(app)
    r = client.post(
        "/visual-plan/prompt-preview",
        json={
            "scene_title": "Opening city lab",
            "narration": "Scientists review a glowing city heat map at dawn.",
            "video_template": "documentary_short",
            "beat_role": "opening",
            "provider_target": "openai_image",
            "prompt_detail_level": "deep",
        },
    )

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["visual_prompt_raw"]
    assert data["visual_prompt_effective"]
    assert data["negative_prompt"]
    assert data["visual_prompt_anatomy"]
    assert isinstance(data["prompt_quality_score"], int)
    assert isinstance(data["prompt_risk_flags"], list)
    assert data["normalized_controls"]["provider_target"] == "openai_image"
    for label in [
        "Subject",
        "Environment",
        "Composition",
        "Lighting and color",
        "Mood",
        "Important constraints",
    ]:
        assert label in data["visual_prompt_raw"]


def test_visual_plan_prompt_preview_endpoint_derives_subject_from_headline():
    client = TestClient(app)
    title = "Warum Vertrauen in Experten plÃ¶tzlich brÃ¶ckelt"
    narration = (
        "Ein neuer Gesundheitsfall sorgt fÃ¼r Ã¶ffentliche Unsicherheit. "
        "Experten versuchen ruhig zu erklÃ¤ren, wÃ¤hrend BÃ¼rger zwischen Fakten, "
        "Angst und Misstrauen schwanken."
    )
    r = client.post(
        "/visual-plan/prompt-preview",
        json={
            "scene_title": title,
            "narration": narration,
            "provider_target": "openai_image",
        },
    )

    assert r.status_code == 200, r.text
    data = r.json()
    anatomy = data["visual_prompt_anatomy"]
    assert anatomy["subject_description"] != title
    assert any(
        term in anatomy["subject_description"].lower()
        for term in ["expert", "citizens", "public health", "documentary subject"]
    )
    assert anatomy["environment"] != "grounded documentary environment / editorial real-world setting"
    assert anatomy["action"] != narration
    assert len(anatomy["action"]) < len(narration)
    assert "Subject: " + anatomy["subject_description"] in data["visual_prompt_raw"]
    assert 0 <= data["prompt_quality_score"] <= 100


def test_visual_plan_prompt_preview_endpoint_defaults_and_normalizes_unknown_controls():
    client = TestClient(app)
    r = client.post(
        "/visual-plan/prompt-preview",
        json={
            "scene_title": "Hook",
            "visual_preset": "unknown-style",
            "provider_target": "not-a-provider",
            "text_safety_mode": "unsafe-text",
        },
    )

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["normalized_controls"]["visual_preset"] == VISUAL_PROMPT_CONTROL_DEFAULTS["visual_preset"]
    assert data["normalized_controls"]["provider_target"] == VISUAL_PROMPT_CONTROL_DEFAULTS["provider_target"]
    assert data["normalized_controls"]["text_safety_mode"] == VISUAL_PROMPT_CONTROL_DEFAULTS["text_safety_mode"]
    assert data["visual_policy_warnings"]
    assert "no readable text" in data["visual_prompt_effective"].lower()
    assert "no fishing hook" in data["negative_prompt"].lower()
