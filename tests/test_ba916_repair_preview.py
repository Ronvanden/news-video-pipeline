"""BA 9.16 — Repair Preview / Auto-Revision V1."""

from fastapi.testclient import TestClient

from app.main import app
from app.prompt_engine.repair_preview import (
    DEFAULT_HOOK,
    NARRATIVE_WEAK_HINT,
    build_repair_preview,
)
from app.prompt_engine.schema import (
    ChapterOutlineItem,
    NarrativeScoreResult,
    NarrativeSubscores,
    ProductionPromptPlan,
    PromptPlanQualityResult,
    PromptPlanReviewGateResult,
)


def _gate_go() -> PromptPlanReviewGateResult:
    return PromptPlanReviewGateResult(
        decision="go",
        confidence=90,
        reasons=[],
        required_actions=[],
        checked_signals=[],
    )


def _gate_revise() -> PromptPlanReviewGateResult:
    return PromptPlanReviewGateResult(
        decision="revise",
        confidence=55,
        reasons=[],
        required_actions=[],
        checked_signals=[],
    )


def _sub() -> NarrativeSubscores:
    return NarrativeSubscores(
        hook_curiosity_score=65,
        emotional_pull_score=65,
        escalation_score=65,
        chapter_progression_score=65,
        thumbnail_potential_score=65,
    )


def _plan(**kwargs) -> ProductionPromptPlan:
    n = NarrativeScoreResult(
        score=72,
        status="moderate",
        subscores=_sub(),
        strengths=[],
        weaknesses=[],
        checked_dimensions=[],
    )
    defaults: dict = dict(
        template_type="true_crime",
        tone="ernst",
        hook="Ein ausreichend langer Hook für die Repair-Preview-Tests.",
        chapter_outline=[
            ChapterOutlineItem(title=f"K{i}", summary="s") for i in range(1, 6)
        ],
        scene_prompts=[f"p{i}" for i in range(1, 6)],
        voice_style="dokumentarisch",
        thumbnail_angle="Kontrast",
        warnings=[],
        video_template="true_crime",
        narrative_archetype_id="arc",
        hook_type="x",
        hook_score=7.0,
        quality_result=PromptPlanQualityResult(
            score=90,
            status="pass",
            warnings=[],
            blocking_issues=[],
            checked_fields=[],
        ),
        narrative_score_result=n,
        performance_record=None,
        review_gate_result=_gate_go(),
        repair_suggestions_result=None,
        repair_preview_result=None,
    )
    defaults.update(kwargs)
    return ProductionPromptPlan(**defaults)


def test_go_yields_not_needed():
    r = build_repair_preview(_plan())
    assert r.status == "not_needed"
    assert r.preview_plan is None
    assert r.applied_repairs == []


def test_empty_hook_preview_and_applied_repairs():
    p = _plan(hook="", review_gate_result=_gate_revise())
    r = build_repair_preview(p)
    assert r.status == "preview_available"
    assert r.preview_plan is not None
    assert r.preview_plan.hook == DEFAULT_HOOK
    assert "hook_repaired" in r.applied_repairs


def test_too_few_chapters_preview_has_at_least_five():
    ch = [
        ChapterOutlineItem(title="A", summary="a"),
        ChapterOutlineItem(title="B", summary="b"),
    ]
    p = _plan(
        chapter_outline=ch,
        scene_prompts=["s1", "s2"],
        review_gate_result=_gate_revise(),
    )
    r = build_repair_preview(p)
    assert r.preview_plan is not None
    assert len(r.preview_plan.chapter_outline) >= 5
    assert "chapters_extended" in r.applied_repairs


def test_scene_prompts_aligned_to_chapters():
    p = _plan(
        chapter_outline=[
            ChapterOutlineItem(title="A", summary="a"),
            ChapterOutlineItem(title="B", summary="b"),
            ChapterOutlineItem(title="C", summary="c"),
        ],
        scene_prompts=["only"],
        review_gate_result=_gate_revise(),
    )
    r = build_repair_preview(p)
    assert r.preview_plan is not None
    assert len(r.preview_plan.scene_prompts) == len(r.preview_plan.chapter_outline)
    assert "scene_prompts_aligned" in r.applied_repairs


def test_voice_and_thumbnail_filled_when_empty():
    p = _plan(
        template_type="mystery_history",
        voice_style="",
        thumbnail_angle="",
        review_gate_result=_gate_revise(),
    )
    r = build_repair_preview(p)
    assert r.preview_plan is not None
    assert r.preview_plan.voice_style == "cinematic historical mystery narration"
    assert "visually tense contrast" in r.preview_plan.thumbnail_angle.lower()
    assert "voice_style_added" in r.applied_repairs
    assert "thumbnail_angle_added" in r.applied_repairs


def test_weak_narrative_remaining_issues():
    sub = NarrativeSubscores(
        hook_curiosity_score=40,
        emotional_pull_score=40,
        escalation_score=40,
        chapter_progression_score=40,
        thumbnail_potential_score=40,
    )
    n = NarrativeScoreResult(
        score=40,
        status="weak",
        subscores=sub,
        strengths=[],
        weaknesses=[],
        checked_dimensions=[],
    )
    p = _plan(narrative_score_result=n, review_gate_result=_gate_revise())
    r = build_repair_preview(p)
    assert NARRATIVE_WEAK_HINT in r.remaining_issues
    assert NARRATIVE_WEAK_HINT in r.warnings


def test_preview_plan_has_no_nested_repair_preview():
    p = _plan(hook="", review_gate_result=_gate_revise())
    r = build_repair_preview(p)
    assert r.preview_plan is not None
    assert r.preview_plan.repair_preview_result is None


def test_prompt_plan_api_includes_repair_preview_result():
    client = TestClient(app)
    res = client.post("/story-engine/prompt-plan", json={"topic": "Polizei und Mord"})
    assert res.status_code == 200
    body = res.json()
    assert "repair_preview_result" in body
    assert body["repair_preview_result"] is not None
    assert body["repair_preview_result"]["status"] in (
        "not_needed",
        "preview_available",
        "not_possible",
    )
