"""BA 9.18 — Production Handoff V1."""

from fastapi.testclient import TestClient

from app.main import app
from app.prompt_engine.production_handoff import (
    SUMMARY_APPROVED,
    SUMMARY_PENDING_REVIEW,
    WARN_HUMAN_MISSING,
    build_production_handoff,
)
from app.prompt_engine.schema import (
    ChapterOutlineItem,
    HumanApprovalState,
    NarrativeScoreResult,
    NarrativeSubscores,
    ProductionPromptPlan,
    PromptPlanQualityResult,
    PromptPlanReviewGateResult,
    PromptRepairSuggestion,
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
    rg = PromptPlanReviewGateResult(
        decision="go",
        confidence=90,
        reasons=[],
        required_actions=[],
        checked_signals=[],
    )
    ha = HumanApprovalState(
        status="pending_review",
        recommended_action="approve",
        approval_required=True,
        reasons=[],
        checklist=[],
        approved_by=None,
        approved_at=None,
        rejected_reason=None,
    )
    defaults: dict = dict(
        template_type="true_crime",
        tone="ernst",
        hook="Ein ausreichend langer Hook für Production-Handoff-Tests.",
        chapter_outline=[
            ChapterOutlineItem(title=f"K{i}", summary="s") for i in range(1, 6)
        ],
        scene_prompts=[f"p{i}" for i in range(1, 6)],
        voice_style="dokumentarisch",
        thumbnail_angle="Kontrast",
        warnings=[],
        video_template="true_crime",
        narrative_archetype_id="arc_x",
        hook_type="cold_open",
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
        review_gate_result=rg,
        repair_suggestions_result=None,
        repair_preview_result=None,
        human_approval_state=ha,
        production_handoff_result=None,
    )
    defaults.update(kwargs)
    return ProductionPromptPlan(**defaults)


def test_go_and_pending_review_needs_review_not_production_ready():
    h = build_production_handoff(_base_plan())
    assert h.handoff_status == "needs_review"
    assert h.production_ready is False
    assert h.summary == SUMMARY_PENDING_REVIEW


def test_approved_ready_and_production_ready():
    ha = HumanApprovalState(
        status="approved",
        recommended_action="approve",
        approval_required=False,
        reasons=[],
        checklist=[],
        approved_by=None,
        approved_at=None,
        rejected_reason=None,
    )
    h = build_production_handoff(_base_plan(human_approval_state=ha))
    assert h.handoff_status == "ready"
    assert h.production_ready is True
    assert h.summary == SUMMARY_APPROVED


def test_needs_revision_handoff():
    rg = PromptPlanReviewGateResult(
        decision="revise",
        confidence=55,
        reasons=["Quality-Status warning."],
        required_actions=["Fix chapters"],
        checked_signals=[],
    )
    rs = PromptRepairSuggestionsResult(
        status="suggestions_available",
        suggestions=[
            PromptRepairSuggestion(
                category="chapters",
                priority="high",
                issue="Zu wenige Kapitel.",
                suggestion="Erweitern.",
            )
        ],
        summary="Ein struktureller Hinweis.",
        checked_sources=[],
    )
    ha = HumanApprovalState(
        status="needs_revision",
        recommended_action="revise",
        approval_required=True,
        reasons=["Needs work"],
        checklist=[],
        approved_by=None,
        approved_at=None,
        rejected_reason=None,
    )
    h = build_production_handoff(
        _base_plan(
            review_gate_result=rg,
            repair_suggestions_result=rs,
            human_approval_state=ha,
        )
    )
    assert h.handoff_status == "needs_revision"
    assert h.production_ready is False
    assert h.blocking_reasons


def test_rejected_blocked():
    rg = PromptPlanReviewGateResult(
        decision="stop",
        confidence=30,
        reasons=["Hook leer."],
        required_actions=[],
        checked_signals=[],
    )
    q = PromptPlanQualityResult(
        score=15,
        status="fail",
        warnings=[],
        blocking_issues=["hook_empty"],
        checked_fields=[],
    )
    ha = HumanApprovalState(
        status="rejected",
        recommended_action="reject",
        approval_required=True,
        reasons=["Rejected"],
        checklist=[],
        approved_by=None,
        approved_at=None,
        rejected_reason="Plan failed automated review gate.",
    )
    h = build_production_handoff(
        _base_plan(review_gate_result=rg, quality_result=q, human_approval_state=ha)
    )
    assert h.handoff_status == "blocked"
    assert h.production_ready is False
    assert any("Blocker" in b or "Hook" in b for b in h.blocking_reasons)


def test_missing_human_approval_warning_and_needs_review():
    h = build_production_handoff(_base_plan(human_approval_state=None))
    assert h.handoff_status == "needs_review"
    assert h.production_ready is False
    assert WARN_HUMAN_MISSING in h.warnings


def test_package_has_core_content_and_metadata():
    h = build_production_handoff(_base_plan())
    p = h.package
    assert p.hook
    assert len(p.chapter_outline) >= 1
    assert len(p.scene_prompts) == len(p.chapter_outline)
    assert p.voice_style
    assert p.thumbnail_angle
    assert p.quality_status == "pass"
    assert p.quality_score == 90
    assert p.narrative_status == "moderate"
    assert p.narrative_score == 72
    assert p.review_decision == "go"
    assert p.approval_status == "pending_review"


def test_prompt_plan_api_has_production_handoff_result():
    client = TestClient(app)
    r = client.post("/story-engine/prompt-plan", json={"topic": "Polizei und Mord"})
    assert r.status_code == 200
    body = r.json()
    assert "production_handoff_result" in body
    assert body["production_handoff_result"] is not None
    pkg = body["production_handoff_result"]["package"]
    assert "hook" in pkg and "chapter_outline" in pkg
    assert "quality_status" in pkg and "review_decision" in pkg and "approval_status" in pkg
