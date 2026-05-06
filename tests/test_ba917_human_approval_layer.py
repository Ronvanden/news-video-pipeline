"""BA 9.17 — Human Approval Layer V1."""

from fastapi.testclient import TestClient

from app.main import app
from app.prompt_engine.human_approval import GO_CHECKLIST, build_human_approval_state
from app.prompt_engine.schema import (
    ChapterOutlineItem,
    NarrativeScoreResult,
    NarrativeSubscores,
    ProductionPromptPlan,
    PromptPlanQualityResult,
    PromptPlanReviewGateResult,
    PromptRepairSuggestionsResult,
)


def _sub() -> NarrativeSubscores:
    return NarrativeSubscores(
        hook_curiosity_score=65,
        emotional_pull_score=65,
        escalation_score=65,
        chapter_progression_score=65,
        thumbnail_potential_score=65,
    )


def _base_plan(**kwargs) -> ProductionPromptPlan:
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
        hook="Ein ausreichend langer Hook für Human-Approval-Tests.",
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
        review_gate_result=PromptPlanReviewGateResult(
            decision="go",
            confidence=90,
            reasons=[],
            required_actions=[],
            checked_signals=[],
        ),
        repair_suggestions_result=None,
        repair_preview_result=None,
        human_approval_state=None,
    )
    defaults.update(kwargs)
    return ProductionPromptPlan(**defaults)


def test_go_pending_review_and_recommend_approve():
    h = build_human_approval_state(_base_plan())
    assert h.status == "pending_review"
    assert h.recommended_action == "approve"
    assert h.approval_required is True


def test_revise_needs_revision():
    rg = PromptPlanReviewGateResult(
        decision="revise",
        confidence=55,
        reasons=["Quality-Status warning."],
        required_actions=[],
        checked_signals=[],
    )
    rs = PromptRepairSuggestionsResult(
        status="suggestions_available",
        suggestions=[],
        summary="Zwei Hinweise aus Quality und Narrative.",
        checked_sources=[],
    )
    h = build_human_approval_state(_base_plan(review_gate_result=rg, repair_suggestions_result=rs))
    assert h.status == "needs_revision"
    assert h.recommended_action == "revise"
    assert any("Quality" in r for r in h.reasons)
    assert any("Zwei Hinweise" in r for r in h.reasons)


def test_stop_rejected():
    rg = PromptPlanReviewGateResult(
        decision="stop",
        confidence=35,
        reasons=["Hook leer."],
        required_actions=[],
        checked_signals=[],
    )
    q = PromptPlanQualityResult(
        score=20,
        status="fail",
        warnings=[],
        blocking_issues=["hook_empty"],
        checked_fields=[],
    )
    h = build_human_approval_state(_base_plan(review_gate_result=rg, quality_result=q))
    assert h.status == "rejected"
    assert h.recommended_action == "reject"
    assert h.rejected_reason == "Plan failed automated review gate."
    assert any("Blocker" in r for r in h.reasons)


def test_missing_gate_pending_review_recommend_review():
    h = build_human_approval_state(_base_plan(review_gate_result=None))
    assert h.status == "pending_review"
    assert h.recommended_action == "review"
    assert "Review gate result missing." in h.reasons


def test_go_checklist_includes_source_fact_risk():
    h = build_human_approval_state(_base_plan())
    assert any("Quellen" in item and "Fakten" in item for item in h.checklist)
    assert h.checklist == GO_CHECKLIST


def test_approved_fields_none_in_v1():
    h = build_human_approval_state(_base_plan())
    assert h.approved_by is None
    assert h.approved_at is None


def test_prompt_plan_api_includes_human_approval_state():
    client = TestClient(app)
    r = client.post("/story-engine/prompt-plan", json={"topic": "Polizei und Mord"})
    assert r.status_code == 200
    body = r.json()
    assert "human_approval_state" in body
    assert body["human_approval_state"] is not None
    assert body["human_approval_state"]["approved_by"] is None
    assert body["human_approval_state"]["approved_at"] is None
