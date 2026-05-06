"""BA 9.12 — Narrative Scoring V1."""

from fastapi.testclient import TestClient

from app.main import app
from app.prompt_engine.narrative_scoring import evaluate_narrative_score
from app.prompt_engine.schema import ChapterOutlineItem, ProductionPromptPlan


def _base_plan(**kwargs) -> ProductionPromptPlan:
    defaults = dict(
        template_type="true_crime",
        tone="ernst dokumentarisch mit tragischer Spannung",
        hook="",
        chapter_outline=[],
        scene_prompts=[],
        voice_style="neutral",
        thumbnail_angle="",
        warnings=[],
        narrative_archetype_id="cold_case_arc",
        hook_type="shock_reveal",
        hook_score=8.0,
        video_template="true_crime",
        quality_result=None,
        narrative_score_result=None,
    )
    defaults.update(kwargs)
    return ProductionPromptPlan(**defaults)


def test_strong_mystery_hook_strong_status():
    hook = (
        "Warum niemand bis heute die Akten öffnete — plötzlich wurde ein "
        "geheimes Detail ungeklärt enthüllt, das alle überraschte."
    )
    ch = [
        ChapterOutlineItem(
            title="Einordnung: Was wir über den Fall wissen",
            summary="Kontext und Überblick ohne Spekulation.",
        ),
        ChapterOutlineItem(
            title="Wendung — plötzlich eine neue Spur",
            summary="Ein Hypothese bricht auf und ein Risiko wird sichtbar.",
        ),
        ChapterOutlineItem(
            title="Offene Fragen und tragisches Fazit",
            summary="Verlust und Angst bleiben; Hoffnung ist fragil.",
        ),
    ]
    plan = _base_plan(
        hook=hook,
        chapter_outline=ch,
        scene_prompts=["s1", "s2", "s3"],
        thumbnail_angle="dramatisch finster — verschwunden in der Nacht",
    )
    r = evaluate_narrative_score(plan)
    assert r.status == "strong"
    assert r.score >= 80
    assert r.subscores.hook_curiosity_score >= 70


def test_weak_generic_hook_moderate_or_weak():
    plan = _base_plan(
        hook="Ein kurzes Video über ein allgemeines Sachthema ohne besondere Wendung.",
        chapter_outline=[
            ChapterOutlineItem(title="Teil A", summary="Text."),
            ChapterOutlineItem(title="Teil B", summary="Mehr Text."),
        ],
        scene_prompts=["a", "b"],
        thumbnail_angle="neutral",
        hook_score=4.0,
    )
    r = evaluate_narrative_score(plan)
    assert r.status in ("weak", "moderate")
    assert r.score < 65


def test_escalation_weakness_emitted():
    plan = _base_plan(
        hook="Niemand weiß mehr als einen kurzen Satz über das Thema.",
        chapter_outline=[
            ChapterOutlineItem(title="X", summary="a"),
            ChapterOutlineItem(title="Y", summary="b"),
            ChapterOutlineItem(title="Z", summary="c"),
        ],
        scene_prompts=["1", "2", "3"],
        thumbnail_angle="ok",
    )
    r = evaluate_narrative_score(plan)
    assert r.subscores.escalation_score < 55
    assert any("Eskalationsbogen" in w for w in r.weaknesses)


def test_good_chapter_progression_subscore():
    ch = [
        ChapterOutlineItem(title="Einordnung der mysteriösen Vorgeschichte", summary="s1"),
        ChapterOutlineItem(title="Analyse der überraschenden Wendung", summary="s2"),
        ChapterOutlineItem(title="Fazit mit offenen sicherheitsrelevanten Fragen", summary="s3"),
    ]
    plan = _base_plan(
        hook="Warum verschwand die Spur plötzlich und blieb ungeklärt?",
        chapter_outline=ch,
        scene_prompts=["a", "b", "c"],
        thumbnail_angle="kontrastreich dramatisch",
    )
    r = evaluate_narrative_score(plan)
    assert r.subscores.chapter_progression_score >= 60


def test_api_contains_narrative_score_result():
    client = TestClient(app)
    r = client.post(
        "/story-engine/prompt-plan",
        json={"topic": "Geheimnis und ungeklärter Fall der Polizei"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "narrative_score_result" in data
    ns = data["narrative_score_result"]
    assert ns["status"] in ("strong", "moderate", "weak")
    assert "subscores" in ns
    assert "hook_curiosity_score" in ns["subscores"]
    assert "checked_dimensions" in ns


def test_checked_dimensions_complete():
    plan = _base_plan(
        hook="Warum blieb alles geheim?",
        chapter_outline=[ChapterOutlineItem(title="T1", summary="s")],
        scene_prompts=["p"],
        thumbnail_angle="finster",
    )
    r = evaluate_narrative_score(plan)
    assert set(r.checked_dimensions) == {
        "hook_curiosity",
        "emotional_pull",
        "escalation_structure",
        "chapter_progression",
        "thumbnail_potential",
    }
