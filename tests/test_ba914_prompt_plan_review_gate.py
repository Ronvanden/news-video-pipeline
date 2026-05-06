"""BA 9.14 — Prompt Plan Review Gate V1."""

from fastapi.testclient import TestClient

from app.main import app
from app.prompt_engine.review_gate import evaluate_prompt_plan_review_gate
from app.prompt_engine.schema import (
    ChapterOutlineItem,
    NarrativeScoreResult,
    NarrativeSubscores,
    ProductionPromptPlan,
    PromptPlanQualityResult,
)


def _plan(
    *,
    q: PromptPlanQualityResult,
    n: NarrativeScoreResult | None,
    hook: str = "Ausreichend langer Hook für den Gate-Check.",
    warnings=None,
) -> ProductionPromptPlan:
    return ProductionPromptPlan(
        template_type="true_crime",
        tone="ernst",
        hook=hook,
        chapter_outline=[
            ChapterOutlineItem(title="Einordnung der Fakten", summary="Kontext."),
            ChapterOutlineItem(title="Wendung in der Spur", summary="Mitte."),
            ChapterOutlineItem(title="Offenes Fazit", summary="Ende."),
        ],
        scene_prompts=["s1", "s2", "s3"],
        voice_style="neutral dokumentarisch",
        thumbnail_angle="kontrastreich dramatisch",
        warnings=warnings or [],
        video_template="true_crime",
        narrative_archetype_id="cold_case_arc",
        hook_type="shock_reveal",
        hook_score=7.5,
        quality_result=q,
        narrative_score_result=n,
        performance_record=None,
        review_gate_result=None,
    )


def test_good_plan_decision_go():
    q = PromptPlanQualityResult(score=88, status="pass", warnings=[], blocking_issues=[], checked_fields=[])
    sub = NarrativeSubscores(
        hook_curiosity_score=70,
        emotional_pull_score=65,
        escalation_score=68,
        chapter_progression_score=72,
        thumbnail_potential_score=66,
    )
    n = NarrativeScoreResult(score=68, status="moderate", subscores=sub, strengths=[], weaknesses=[], checked_dimensions=[])
    g = evaluate_prompt_plan_review_gate(_plan(q=q, n=n))
    assert g.decision == "go"
    assert g.confidence >= 80


def test_quality_fail_stop():
    q = PromptPlanQualityResult(score=20, status="fail", warnings=["x"], blocking_issues=[], checked_fields=[])
    sub = NarrativeSubscores(
        hook_curiosity_score=50,
        emotional_pull_score=50,
        escalation_score=50,
        chapter_progression_score=50,
        thumbnail_potential_score=50,
    )
    n = NarrativeScoreResult(score=55, status="moderate", subscores=sub, strengths=[], weaknesses=[], checked_dimensions=[])
    g = evaluate_prompt_plan_review_gate(_plan(q=q, n=n))
    assert g.decision == "stop"
    assert g.confidence <= 40


def test_narrative_weak_quality_pass_revise():
    q = PromptPlanQualityResult(score=90, status="pass", warnings=[], blocking_issues=[], checked_fields=[])
    sub = NarrativeSubscores(
        hook_curiosity_score=30,
        emotional_pull_score=30,
        escalation_score=30,
        chapter_progression_score=30,
        thumbnail_potential_score=30,
    )
    n = NarrativeScoreResult(score=35, status="weak", subscores=sub, strengths=[], weaknesses=[], checked_dimensions=[])
    g = evaluate_prompt_plan_review_gate(_plan(q=q, n=n))
    assert g.decision == "revise"


def test_narrative_weak_quality_warning_stop():
    q = PromptPlanQualityResult(score=70, status="warning", warnings=["warn"], blocking_issues=[], checked_fields=[])
    sub = NarrativeSubscores(
        hook_curiosity_score=30,
        emotional_pull_score=30,
        escalation_score=30,
        chapter_progression_score=30,
        thumbnail_potential_score=30,
    )
    n = NarrativeScoreResult(score=35, status="weak", subscores=sub, strengths=[], weaknesses=[], checked_dimensions=[])
    g = evaluate_prompt_plan_review_gate(_plan(q=q, n=n))
    assert g.decision == "stop"


def test_quality_warning_revise():
    q = PromptPlanQualityResult(score=72, status="warning", warnings=["kapitel_unter"], blocking_issues=[], checked_fields=[])
    sub = NarrativeSubscores(
        hook_curiosity_score=70,
        emotional_pull_score=65,
        escalation_score=60,
        chapter_progression_score=70,
        thumbnail_potential_score=65,
    )
    n = NarrativeScoreResult(score=68, status="moderate", subscores=sub, strengths=[], weaknesses=[], checked_dimensions=[])
    g = evaluate_prompt_plan_review_gate(_plan(q=q, n=n))
    assert g.decision == "revise"
    assert 40 <= g.confidence <= 79


def test_blocking_issues_stop_even_if_status_pass():
    q = PromptPlanQualityResult(
        score=90,
        status="pass",
        warnings=[],
        blocking_issues=["schema_inconsistent"],
        checked_fields=[],
    )
    sub = NarrativeSubscores(
        hook_curiosity_score=70,
        emotional_pull_score=70,
        escalation_score=70,
        chapter_progression_score=70,
        thumbnail_potential_score=70,
    )
    n = NarrativeScoreResult(score=75, status="moderate", subscores=sub, strengths=[], weaknesses=[], checked_dimensions=[])
    g = evaluate_prompt_plan_review_gate(_plan(q=q, n=n))
    assert g.decision == "stop"


def test_empty_hook_stop():
    q = PromptPlanQualityResult(score=90, status="pass", warnings=[], blocking_issues=[], checked_fields=[])
    sub = NarrativeSubscores(
        hook_curiosity_score=70,
        emotional_pull_score=70,
        escalation_score=70,
        chapter_progression_score=70,
        thumbnail_potential_score=70,
    )
    n = NarrativeScoreResult(score=75, status="moderate", subscores=sub, strengths=[], weaknesses=[], checked_dimensions=[])
    g = evaluate_prompt_plan_review_gate(_plan(q=q, n=n, hook=""))
    assert g.decision == "stop"


def test_api_contains_review_gate_result():
    client = TestClient(app)
    r = client.post("/story-engine/prompt-plan", json={"topic": "Mordfall und Ermittlung"})
    assert r.status_code == 200
    data = r.json()
    assert "review_gate_result" in data
    rg = data["review_gate_result"]
    assert rg["decision"] in ("go", "revise", "stop")
    assert "confidence" in rg
    assert "reasons" in rg
    assert "required_actions" in rg
    assert "checked_signals" in rg
