"""BA 9.15 — Prompt Repair Suggestions V1."""

from fastapi.testclient import TestClient

from app.main import app
from app.prompt_engine.performance_learning import evaluate_performance_snapshot
from app.prompt_engine.repair_suggestions import build_prompt_repair_suggestions
from app.prompt_engine.schema import (
    ChapterOutlineItem,
    NarrativeScoreResult,
    NarrativeSubscores,
    PerformanceRecord,
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


def _plan(**kwargs) -> ProductionPromptPlan:
    sub = NarrativeSubscores(
        hook_curiosity_score=65,
        emotional_pull_score=65,
        escalation_score=65,
        chapter_progression_score=65,
        thumbnail_potential_score=65,
    )
    n = NarrativeScoreResult(
        score=72,
        status="moderate",
        subscores=sub,
        strengths=[],
        weaknesses=[],
        checked_dimensions=[],
    )
    defaults: dict = dict(
        template_type="true_crime",
        tone="ernst",
        hook="Ein ausreichend langer Hook für die Repair-Tests hier.",
        chapter_outline=[
            ChapterOutlineItem(title=f"K{i}", summary="s") for i in range(1, 6)
        ],
        scene_prompts=[f"p{i}" for i in range(1, 6)],
        voice_style="dokumentarisch ruhig",
        thumbnail_angle="Kontrast, Silhouette",
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
    )
    defaults.update(kwargs)
    return ProductionPromptPlan(**defaults)


def test_go_yields_not_needed_and_empty_suggestions():
    r = build_prompt_repair_suggestions(_plan())
    assert r.status == "not_needed"
    assert r.suggestions == []
    assert "production-ready" in r.summary.lower()


def test_empty_hook_high_priority_hook_suggestion():
    p = _plan(
        hook="",
        review_gate_result=PromptPlanReviewGateResult(
            decision="stop",
            confidence=35,
            reasons=[],
            required_actions=[],
            checked_signals=[],
        ),
    )
    r = build_prompt_repair_suggestions(p)
    assert r.status == "suggestions_available"
    hook_high = [s for s in r.suggestions if s.category == "hook" and s.priority == "high"]
    assert any("leer" in s.issue.lower() for s in hook_high)


def test_too_few_chapters_chapters_suggestion():
    ch = [
        ChapterOutlineItem(title="A", summary="a"),
        ChapterOutlineItem(title="B", summary="b"),
    ]
    p = _plan(
        chapter_outline=ch,
        scene_prompts=["s1", "s2"],
        review_gate_result=PromptPlanReviewGateResult(
            decision="revise",
            confidence=55,
            reasons=[],
            required_actions=[],
            checked_signals=[],
        ),
    )
    r = build_prompt_repair_suggestions(p)
    assert any(s.category == "chapters" for s in r.suggestions)


def test_scene_count_mismatch_scenes_suggestion():
    p = _plan(
        chapter_outline=[
            ChapterOutlineItem(title="A", summary="a"),
            ChapterOutlineItem(title="B", summary="b"),
            ChapterOutlineItem(title="C", summary="c"),
        ],
        scene_prompts=["only_one"],
        review_gate_result=PromptPlanReviewGateResult(
            decision="revise",
            confidence=50,
            reasons=[],
            required_actions=[],
            checked_signals=[],
        ),
    )
    r = build_prompt_repair_suggestions(p)
    assert any(s.category == "scenes" for s in r.suggestions)


def test_narrative_weakness_yields_narrative_suggestion():
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
        weaknesses=["Emotionaler Zug fehlt"],
        checked_dimensions=[],
    )
    p = _plan(
        narrative_score_result=n,
        review_gate_result=PromptPlanReviewGateResult(
            decision="revise",
            confidence=55,
            reasons=[],
            required_actions=[],
            checked_signals=[],
        ),
    )
    r = build_prompt_repair_suggestions(p)
    assert any(s.category == "narrative" for s in r.suggestions)


def test_performance_pending_low_priority_hint():
    rec = PerformanceRecord(id="x", created_at="t", updated_at="t")
    assert evaluate_performance_snapshot(rec).status == "pending_data"
    p = _plan(
        performance_record=rec,
        review_gate_result=PromptPlanReviewGateResult(
            decision="revise",
            confidence=60,
            reasons=[],
            required_actions=[],
            checked_signals=[],
        ),
    )
    r = build_prompt_repair_suggestions(p)
    perf = [s for s in r.suggestions if s.category == "performance"]
    assert perf and all(s.priority == "low" for s in perf)


def test_prompt_plan_api_includes_repair_suggestions_result():
    client = TestClient(app)
    r = client.post("/story-engine/prompt-plan", json={"topic": "Polizei und Mord"})
    assert r.status_code == 200
    body = r.json()
    assert "repair_suggestions_result" in body
    assert body["repair_suggestions_result"] is not None
    assert body["repair_suggestions_result"]["status"] in (
        "not_needed",
        "suggestions_available",
    )
