from app.visual_plan.engine_v1 import VisualPromptEngineContext, build_visual_prompt_v1
from app.visual_plan.prompt_anatomy import VisualPromptAnatomy
from app.visual_plan.prompt_formatters import anatomy_to_generic_prompt, anatomy_to_openai_image_prompt
from app.visual_plan.presets import VISUAL_PROMPT_CONTROL_DEFAULTS


def test_hook_title_is_sanitized_in_visual_prompts():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Hook",
            narration="A quiet opening line introduces the investigation without showing text.",
            beat_role="opening hook",
        )
    )
    prompt_blob = f"{result.visual_prompt_raw}\n{result.visual_prompt_effective}"
    assert "Hook" not in prompt_blob
    assert "hook" not in prompt_blob.lower()
    assert "cinematic opening beat" in result.visual_prompt_raw
    assert "internal_term_sanitized:hook" in result.visual_policy_warnings
    anatomy = result.visual_prompt_anatomy
    assert anatomy["subject_description"] == "cinematic opening beat"
    assert "Hook" not in anatomy["subject_description"]
    assert "internal_term_sanitized:hook" in anatomy["sanitized_terms"]


def test_hook_negative_prompt_contains_fishing_hook_guard():
    result = build_visual_prompt_v1(VisualPromptEngineContext(scene_title="Aufhänger", narration="Intro."))
    neg = result.negative_prompt.lower()
    assert "no fishing hook" in neg
    assert "no metal hook" in neg
    assert "no literal hook object" in neg
    assert "no hook-shaped object" in neg
    constraints = [x.lower() for x in result.visual_prompt_anatomy["negative_constraints"]]
    assert "no fishing hook" in constraints
    assert "no literal hook object" in constraints


def test_normalized_controls_use_defaults_when_unset():
    result = build_visual_prompt_v1(VisualPromptEngineContext(scene_title="Scene One", narration="A city at dawn."))
    assert result.normalized_controls == VISUAL_PROMPT_CONTROL_DEFAULTS
    assert result.visual_style_profile == "documentary_realism"


def test_visual_prompt_anatomy_contains_core_fields():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Chapter One",
            narration="A grounded documentary scene follows workers entering a public building at sunrise.",
        )
    )
    anatomy = result.visual_prompt_anatomy
    assert anatomy["subject_description"] == "Chapter One"
    assert anatomy["environment"]
    assert anatomy["camera"]
    assert anatomy["lighting"]
    assert anatomy["composition"]
    assert anatomy["source_summary"]
    assert "grounded_realism" in anatomy["style_tags"]


def test_visual_prompt_anatomy_derives_subject_environment_and_action_from_headline():
    title = "Warum Vertrauen in Experten plÃ¶tzlich brÃ¶ckelt"
    narration = (
        "Ein neuer Gesundheitsfall sorgt fÃ¼r Ã¶ffentliche Unsicherheit. "
        "Experten versuchen ruhig zu erklÃ¤ren, wÃ¤hrend BÃ¼rger zwischen Fakten, "
        "Angst und Misstrauen schwanken."
    )
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title=title,
            narration=narration,
            provider_target="openai_image",
        )
    )
    anatomy = result.visual_prompt_anatomy
    subject = anatomy["subject_description"].lower()
    assert anatomy["subject_description"] != title
    assert any(term in subject for term in ["expert", "citizens", "public health", "documentary subject"])
    assert anatomy["environment"] != "grounded documentary environment / editorial real-world setting"
    assert "public information" in anatomy["environment"].lower() or "municipal hallway" in anatomy["environment"].lower()
    assert anatomy["action"] != narration
    assert len(anatomy["action"]) < len(narration)
    assert "visual_subject_derived" in result.prompt_risk_flags
    assert "subject_was_headline" in result.prompt_risk_flags
    assert "visual_action_derived" in result.prompt_risk_flags
    assert 0 <= result.prompt_quality_score <= 100
    assert "Subject: " + anatomy["subject_description"] in result.visual_prompt_raw


def test_visual_prompt_anatomy_derives_subject_from_headline_without_narration():
    title = "Warum Vertrauen in Experten plÃ¶tzlich brÃ¶ckelt"
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title=title,
            provider_target="openai_image",
        )
    )
    anatomy = result.visual_prompt_anatomy
    assert anatomy["subject_description"] != title
    assert "expert" in anatomy["subject_description"].lower() or "citizens" in anatomy["subject_description"].lower()
    assert "visual_subject_derived" in result.prompt_risk_flags
    assert "cinematic opening beat" not in anatomy["subject_description"]


def test_youtube_political_commentary_chapter_derives_concrete_visual_anatomy():
    title = "Kapitel 1: Die Demokratie in Deutschland"
    narration = (
        "Sarah Bosetti aeussert in ihrer neuesten Folge, dass menschliches Handeln zu dumm "
        "fuer die Demokratie sei. Doch wie steht es wirklich um die Demokratie in Deutschland?"
    )
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title=title,
            narration=narration,
            provider_target="openai_image",
            prompt_detail_level="deep",
            text_safety_mode="strict_no_text",
        )
    )
    anatomy = result.visual_prompt_anatomy
    subject = anatomy["subject_description"].lower()
    environment = anatomy["environment"].lower()
    action = anatomy["action"].lower()
    assert anatomy["subject_description"] != title
    assert any(term in subject for term in ["political commentator", "documentary host", "public political debate"])
    assert "grounded documentary environment / editorial real-world setting" not in environment
    assert any(
        term in environment
        for term in ["editorial studio", "newsroom desk", "political talk", "public media analysis"]
    )
    assert anatomy["action"] != narration
    assert len(anatomy["action"]) < len(narration)
    assert any(term in action for term in ["explains", "reviews", "public debate", "public reactions"])
    assert "[visual_no_text_guard_v26_4]" in result.visual_prompt_effective
    assert "environment_generic" not in result.prompt_risk_flags
    assert "visual_action_derived" in result.prompt_risk_flags
    assert "action_from_summary" not in result.prompt_risk_flags
    assert "Subject: " + anatomy["subject_description"] in result.visual_prompt_raw


def test_documentary_realism_derives_concrete_subjects_and_environments_for_lab_topics():
    cases = [
        (
            "Regierung verliert Vertrauen der Bevoelkerung",
            "Eine Regierungserklaerung trifft auf skeptische Buerger und Pressefragen.",
            ["government spokesperson", "skeptical citizens"],
            ["press briefing room", "municipal hallway"],
            ["spokesperson addresses", "reporters listen"],
            ["public scrutiny", "quiet civic tension"],
        ),
        (
            "Steigende Preise verunsichern Familien",
            "Eine Familie prueft Rechnungen und Einkaeufe, waehrend die Stimmung angespannt bleibt.",
            ["worried parent", "blank unreadable grocery receipts", "family"],
            ["modest family kitchen", "small apartment dining table"],
            ["compares blank receipts", "unbranded groceries"],
            ["financial uncertainty", "family stress"],
        ),
        (
            "Eine Ermittlerin rekonstruiert den letzten Abend",
            "Eine Ermittlerin ordnet Hinweise und versucht den Ablauf eines Abends nachzuvollziehen.",
            ["focused investigator", "blank unmarked evidence cards"],
            ["quiet investigation office", "out-of-focus evidence photos", "blank notes"],
            ["studies blank unmarked evidence cards", "sequence of events"],
            ["investigative", "tense but grounded"],
        ),
        (
            "Ein verlassenes Dorf in den Bergen sorgt fuer Fragen",
            "Ein leeres Bergdorf wirkt real und still, ohne uebernatuerliche Zeichen.",
            ["abandoned mountain village street", "shuttered houses"],
            ["weathered houses", "alpine slopes"],
            ["empty street holds still", "quiet unease"],
            ["restrained mystery", "quiet unease"],
        ),
        (
            "Ein Vater erklaert seiner Tochter die Krise",
            "Ein Vater spricht ruhig mit seiner Tochter am Kuechentisch ueber schwierige Nachrichten.",
            ["father and daughter", "modest kitchen table"],
            ["modest family kitchen", "household details"],
            ["restrained emotion", "daughter listens"],
            ["emotional restraint", "family intimacy"],
        ),
    ]
    for title, narration, subject_terms, environment_terms, action_terms, mood_terms in cases:
        result = build_visual_prompt_v1(
            VisualPromptEngineContext(
                scene_title=title,
                narration=narration,
                provider_target="openai_image",
                prompt_detail_level="deep",
            )
        )
        anatomy = result.visual_prompt_anatomy
        subject = anatomy["subject_description"].lower()
        environment = anatomy["environment"].lower()
        action = anatomy["action"].lower()
        mood = anatomy["mood"].lower()
        assert anatomy["subject_description"] != title
        assert any(term in subject for term in subject_terms)
        assert any(term in environment for term in environment_terms)
        assert any(term in action for term in action_terms)
        assert any(term in mood for term in mood_terms)
        assert "grounded documentary environment / editorial real-world setting" not in environment


def test_generic_formatter_contains_core_anatomy_parts():
    anatomy = VisualPromptAnatomy(
        subject_description="public building at sunrise",
        environment="grounded documentary environment",
        composition="clean editorial frame",
    )
    prompt = anatomy_to_generic_prompt(anatomy, {"prompt_detail_level": "basic"})
    assert "public building at sunrise" in prompt
    assert "grounded documentary environment" in prompt
    assert "clean editorial frame" in prompt


def test_generic_formatter_detail_levels_change_prompt_depth():
    anatomy = VisualPromptAnatomy(
        subject_description="public building at sunrise",
        action="workers enter through the main doors",
        environment="grounded documentary environment",
        camera="documentary medium-wide frame",
        lighting="natural morning light",
        mood="grounded documentary realism",
        composition="clean editorial frame",
        style_tags=["grounded_realism", "natural_light"],
        continuity="use one consistent visual style across the video",
        source_summary="workers enter a public building at sunrise",
        negative_constraints=["no readable text"],
    )
    basic = anatomy_to_generic_prompt(anatomy, {"prompt_detail_level": "basic"})
    deep = anatomy_to_generic_prompt(
        anatomy,
        {
            "prompt_detail_level": "deep",
            "visual_preset": "documentary_realism",
            "provider_target": "generic",
            "visual_consistency_mode": "one_style_per_video",
        },
    )
    assert len(basic) < len(deep)
    assert "use one consistent visual style" in deep
    assert "grounded_realism" in deep
    assert "workers enter a public building" in deep


def test_openai_image_formatter_contains_image_anatomy_sections():
    anatomy = VisualPromptAnatomy(
        subject_description="public building at sunrise",
        action="workers enter through the main doors",
        environment="grounded documentary environment",
        camera="documentary medium-wide frame",
        lighting="natural morning light",
        mood="grounded documentary realism",
        composition="clean editorial frame",
        negative_constraints=["no readable text"],
    )
    prompt = anatomy_to_openai_image_prompt(
        anatomy,
        {
            "prompt_detail_level": "enhanced",
            "visual_preset": "documentary_realism",
        },
    )
    assert prompt.startswith("Create a realistic documentary-style image")
    assert "Subject: public building at sunrise" in prompt
    assert "Environment: grounded documentary environment" in prompt
    assert "Composition: clean editorial frame" in prompt
    assert "Lighting and color: natural morning light" in prompt
    assert "Important constraints: no readable text" in prompt
    assert "Motion direction" not in prompt
    assert "camera move" not in prompt.lower()


def test_openai_image_formatter_basic_is_shorter_than_deep():
    anatomy = VisualPromptAnatomy(
        subject_description="public building at sunrise",
        action="workers enter through the main doors",
        environment="grounded documentary environment",
        camera="documentary medium-wide frame",
        lighting="natural morning light",
        mood="grounded documentary realism",
        composition="clean editorial frame",
        style_tags=["grounded_realism", "natural_light"],
        continuity="use one consistent visual style across the video",
        source_summary="workers enter a public building at sunrise",
        negative_constraints=["no readable text", "no logo"],
    )
    basic = anatomy_to_openai_image_prompt(anatomy, {"prompt_detail_level": "basic"})
    deep = anatomy_to_openai_image_prompt(
        anatomy,
        {
            "prompt_detail_level": "deep",
            "visual_preset": "documentary_realism",
        },
    )
    assert len(basic) < len(deep)
    assert "Style consistency" in deep
    assert "Source context" in deep
    assert "grounded_realism" in deep


def test_openai_image_provider_target_routes_engine_prompt_formatter():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Documents",
            narration="Files are reviewed on a desk in natural light.",
            provider_target="openai_image",
        )
    )
    assert result.normalized_controls["provider_target"] == "openai_image"
    assert result.visual_prompt_raw.startswith("Create a realistic documentary-style image")
    assert "Subject: Documents" in result.visual_prompt_raw
    assert "Environment:" in result.visual_prompt_raw
    assert "Composition:" in result.visual_prompt_raw
    assert "Lighting and color:" in result.visual_prompt_raw
    assert "[visual_no_text_guard_v26_4]" in result.visual_prompt_effective


def test_openai_image_provider_target_keeps_hook_sanitizing_and_negative_guards():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Hook",
            narration="A quiet opening line introduces the investigation.",
            beat_role="opening hook",
            provider_target="openai_image",
        )
    )
    prompt_blob = f"{result.visual_prompt_raw}\n{result.visual_prompt_effective}"
    assert "Hook" not in prompt_blob
    assert "hook" not in prompt_blob.lower()
    assert "cinematic opening beat" in result.visual_prompt_raw
    assert "no fishing hook" in result.negative_prompt.lower()


def test_unknown_controls_warn_and_fall_back_to_defaults():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Scene One",
            narration="A city at dawn.",
            visual_preset="unknown_style",
            prompt_detail_level="maximum",
            provider_target="openai_image",
        )
    )
    assert result.normalized_controls["visual_preset"] == "documentary_realism"
    assert result.normalized_controls["prompt_detail_level"] == "enhanced"
    assert result.normalized_controls["provider_target"] == "openai_image"
    assert "visual_prompt_control_unknown:visual_preset:unknown_style" in result.visual_policy_warnings
    assert "visual_prompt_control_unknown:prompt_detail_level:maximum" in result.visual_policy_warnings


def test_visual_prompt_effective_contains_no_text_guard():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(scene_title="Documents", narration="Files are reviewed on a desk.")
    )
    assert "[visual_no_text_guard_v26_4]" in result.visual_prompt_effective
    assert "No readable text" in result.visual_prompt_effective


def test_strict_no_text_sets_anatomy_text_safety_and_composition():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(scene_title="Documents", narration="Files are reviewed on a desk.")
    )
    anatomy = result.visual_prompt_anatomy
    assert "no readable text" in anatomy["text_safety"]
    assert "no documents with legible writing" in anatomy["text_safety"]
    assert "no generated text" in anatomy["composition"]


def test_lab_topics_harden_document_props_against_text_artifacts():
    economy = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Steigende Preise verunsichern Familien",
            narration=(
                "Immer mehr Familien muessen beim Einkaufen sparen. Eltern vergleichen Preise, "
                "streichen Produkte von der Einkaufsliste und sprechen zuhause ueber finanzielle Unsicherheit."
            ),
            provider_target="openai_image",
            prompt_detail_level="deep",
            text_safety_mode="strict_no_text",
        )
    )
    economy_raw = economy.visual_prompt_raw.lower()
    assert "blank unreadable grocery receipts" in economy_raw
    assert "unbranded groceries" in economy_raw
    assert "no documents with legible writing" in economy.negative_prompt.lower()

    true_crime = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Eine Ermittlerin rekonstruiert den letzten Abend",
            narration=(
                "Eine Ermittlerin steht in einem ruhigen Buero vor unbeschrifteten Fotos und Notizen. "
                "Sie versucht, den Ablauf des letzten bekannten Abends sachlich nachzuvollziehen."
            ),
            visual_preset="dark_mystery",
            provider_target="openai_image",
            prompt_detail_level="deep",
            text_safety_mode="strict_no_text",
        )
    )
    crime_raw = true_crime.visual_prompt_raw.lower()
    assert "blank unmarked evidence cards" in crime_raw
    assert "blank notes" in crime_raw
    assert "no readable labels" in true_crime.negative_prompt.lower()


def test_overlay_friendly_sets_anatomy_overlay_space():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Explainer",
            narration="A clear explainer scene.",
            text_safety_mode="overlay_friendly",
        )
    )
    anatomy = result.visual_prompt_anatomy
    assert "overlay" in anatomy["text_safety"]
    assert "clean negative space" in anatomy["composition"]


def test_documentary_realism_camera_anatomy_has_documentary_lens_feel():
    """Documentary Realism Preset: konkrete Kameraregie statt generischem Frame."""
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Briefing",
            narration="An expert calmly addresses concerned citizens.",
            prompt_detail_level="deep",
        )
    )
    camera = result.visual_prompt_anatomy["camera"].lower()
    assert "35mm" in camera
    assert "documentary lens" in camera
    assert "shallow depth of field" in camera


def test_documentary_realism_lighting_anatomy_has_directional_natural_light():
    """Documentary Realism Preset: konkrete Lichtregie."""
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Briefing",
            narration="An expert calmly addresses concerned citizens.",
        )
    )
    lighting = result.visual_prompt_anatomy["lighting"].lower()
    assert "soft directional natural light" in lighting
    assert "subtle cinematic contrast" in lighting


def test_documentary_realism_composition_anatomy_has_overlay_space_and_off_center_subject():
    """Documentary Realism Preset: Bildregie mit Off-Center-Subjekt und Negative Space, No-Text Guard bleibt."""
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Briefing",
            narration="An expert calmly addresses concerned citizens.",
        )
    )
    composition = result.visual_prompt_anatomy["composition"].lower()
    assert "slightly off-center" in composition
    assert "softly defocused" in composition
    assert "clean negative space" in composition
    assert "no generated text" in composition


def test_documentary_realism_overlay_friendly_keeps_off_center_subject_and_overlay_space():
    """Documentary Realism + overlay_friendly: Bildregie + Overlay-Space sichtbar, kein No-Text Zwang."""
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Briefing",
            narration="An expert calmly addresses concerned citizens.",
            text_safety_mode="overlay_friendly",
        )
    )
    composition = result.visual_prompt_anatomy["composition"].lower()
    assert "slightly off-center" in composition
    assert "clean negative space" in composition
    assert "softly defocused" in composition


def test_documentary_realism_openai_image_prompt_carries_documentary_camera_lighting_composition():
    """OpenAI-Image-Formatter zeigt die documentary_realism Bildregie in den labelled Sections."""
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Briefing",
            narration="An expert calmly addresses concerned citizens.",
            provider_target="openai_image",
            prompt_detail_level="deep",
        )
    )
    raw = result.visual_prompt_raw
    assert raw.startswith("Create a realistic documentary-style image")
    low = raw.lower()
    assert "framing: " in low
    assert "35mm" in low
    assert "shallow depth of field" in low
    assert "lighting and color: soft directional natural light" in low
    assert "subtle cinematic contrast" in low
    assert "composition: " in low
    assert "slightly off-center" in low
    assert "clean negative space" in low


def test_sparse_narration_sets_risk_flag_without_crash():
    result = build_visual_prompt_v1(VisualPromptEngineContext(scene_title="Scene One"))
    assert result.visual_prompt_raw
    assert result.visual_prompt_effective
    assert "sparse_narration" in result.prompt_risk_flags


def test_prompt_quality_score_is_present_and_bounded():
    result = build_visual_prompt_v1(
        VisualPromptEngineContext(
            scene_title="Chapter One",
            narration="A grounded documentary scene follows workers entering a public building at sunrise.",
        )
    )
    assert isinstance(result.prompt_quality_score, int)
    assert 0 <= result.prompt_quality_score <= 100
