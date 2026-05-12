from app.visual_plan.prompt_anatomy import (
    VisualPromptAnatomy,
    build_motion_prompt_anatomy,
)
from app.visual_plan.prompt_formatters import anatomy_to_runway_motion_prompt


def _visual_anatomy() -> VisualPromptAnatomy:
    return VisualPromptAnatomy(
        subject_description="public building entrance",
        action="workers enter through the front doors",
        environment="grounded documentary environment",
        camera="documentary medium-wide frame",
        lighting="natural morning light",
        mood="grounded documentary realism",
        composition="clean editorial frame",
        continuity="use one consistent visual style across the video",
        source_summary="workers enter a public building at sunrise",
    )


def test_build_motion_prompt_anatomy_contains_expected_fields():
    motion = build_motion_prompt_anatomy(
        _visual_anatomy(),
        motion_hint="subtle pan left-to-right, hold on subject anchor",
        duration_seconds=10,
    )
    assert motion.camera_motion
    assert motion.subject_motion == "minimal natural subject movement"
    assert motion.background_motion == "subtle ambient background movement only"
    assert motion.scene_evolution == "no scene change, attention evolves within the provided image"
    assert "preserve subject identity" in motion.stability_constraints
    assert "preserve composition" in motion.stability_constraints
    assert "preserve lighting" in motion.stability_constraints
    assert "no scene cut" in motion.motion_negative_constraints
    assert "no new objects" in motion.motion_negative_constraints
    assert motion.duration_hint == "10 seconds"


def test_runway_motion_prompt_contains_expected_sections_and_constraints():
    visual = _visual_anatomy()
    motion = build_motion_prompt_anatomy(
        visual,
        motion_hint="static lock-off, slight handheld micro-movement",
    )
    prompt = anatomy_to_runway_motion_prompt(visual, motion, {"prompt_detail_level": "enhanced"})
    assert "Animate the provided image" in prompt
    assert "Camera movement:" in prompt
    assert "Scene evolution:" in prompt
    assert "Subject motion:" in prompt
    assert "Background motion:" in prompt
    assert "Stability constraints:" in prompt
    assert "Avoid:" in prompt
    assert "preserve subject identity" in prompt
    assert "preserve composition" in prompt
    assert "preserve lighting" in prompt
    assert "no scene cut" in prompt
    assert "no new objects" in prompt
    assert "no text morphing" in prompt


def test_runway_motion_prompt_does_not_redescribe_image_heavily():
    visual = _visual_anatomy()
    motion = build_motion_prompt_anatomy(visual)
    prompt = anatomy_to_runway_motion_prompt(visual, motion, {"prompt_detail_level": "basic"})
    assert "Subject:" not in prompt
    assert "Environment:" not in prompt
    assert "Lighting and color:" not in prompt
    assert "provided image" in prompt.lower()
