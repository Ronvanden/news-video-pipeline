"""BA 9.19 — Production Handoff Export Contract V1."""

from fastapi.testclient import TestClient

from app.main import app
from app.prompt_engine.production_export_contract import (
    EXPORT_CONTRACT_VERSION,
    WARN_HANDOFF_MISSING,
    build_handoff_package_id,
    build_production_export_contract,
)
from app.prompt_engine.schema import (
    ChapterOutlineItem,
    HumanApprovalState,
    NarrativeScoreResult,
    NarrativeSubscores,
    PerformanceRecord,
    ProductionHandoffPackage,
    ProductionHandoffResult,
    ProductionPromptPlan,
    PromptPlanQualityResult,
    PromptPlanReviewGateResult,
)


def _sub() -> NarrativeSubscores:
    return NarrativeSubscores(
        hook_curiosity_score=65,
        emotional_pull_score=65,
        escalation_score=65,
        chapter_progression_score=65,
        thumbnail_potential_score=65,
    )


def _minimal_plan(**kwargs) -> ProductionPromptPlan:
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
        status="approved",
        recommended_action="approve",
        approval_required=True,
        reasons=[],
        checklist=[],
        approved_by=None,
        approved_at=None,
        rejected_reason=None,
    )
    pkg = ProductionHandoffPackage(
        template_type="true_crime",
        video_template="true_crime",
        narrative_archetype_id="arc",
        hook_type="x",
        hook_score=7.0,
        quality_status="pass",
        quality_score=90,
        narrative_status="moderate",
        narrative_score=72,
        review_decision="go",
        approval_status="approved",
        hook="Hook text for export contract tests.",
        chapter_outline=[ChapterOutlineItem(title="K1", summary="s")],
        scene_prompts=["s1"],
        voice_style="v",
        thumbnail_angle="t",
    )
    defaults: dict = dict(
        template_type="true_crime",
        tone="ernst",
        hook="Hook text for export contract tests.",
        chapter_outline=[ChapterOutlineItem(title="K1", summary="s")],
        scene_prompts=["s1"],
        voice_style="v",
        thumbnail_angle="t",
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
        review_gate_result=rg,
        repair_suggestions_result=None,
        repair_preview_result=None,
        human_approval_state=ha,
        production_handoff_result=ProductionHandoffResult(
            handoff_status="ready",
            production_ready=True,
            summary="ok",
            package=pkg,
            warnings=[],
            blocking_reasons=[],
            checked_sources=["human_approval_state"],
        ),
        production_export_contract_result=None,
    )
    defaults.update(kwargs)
    return ProductionPromptPlan(**defaults)


def test_ready_handoff_export_ready_true():
    ex = build_production_export_contract(_minimal_plan())
    assert ex.export_ready is True
    assert ex.export_status == "ready"


def test_needs_revision_export_ready_false():
    ho = ProductionHandoffResult(
        handoff_status="needs_revision",
        production_ready=False,
        summary="revise",
        package=ProductionHandoffPackage(),
        warnings=[],
        blocking_reasons=["chapters"],
        checked_sources=[],
    )
    ex = build_production_export_contract(_minimal_plan(production_handoff_result=ho))
    assert ex.export_ready is False
    assert ex.export_status == "needs_revision"


def test_needs_review_export_ready_false():
    ho = ProductionHandoffResult(
        handoff_status="needs_review",
        production_ready=False,
        summary="pending",
        package=ProductionHandoffPackage(),
        warnings=[],
        blocking_reasons=[],
        checked_sources=[],
    )
    ex = build_production_export_contract(_minimal_plan(production_handoff_result=ho))
    assert ex.export_ready is False
    assert ex.export_status == "needs_review"


def test_blocked_export_ready_false():
    ho = ProductionHandoffResult(
        handoff_status="blocked",
        production_ready=False,
        summary="blocked",
        package=ProductionHandoffPackage(),
        warnings=[],
        blocking_reasons=["x"],
        checked_sources=[],
    )
    ex = build_production_export_contract(_minimal_plan(production_handoff_result=ho))
    assert ex.export_ready is False
    assert ex.export_status == "blocked"
    assert ex.blocking_reasons


def test_missing_handoff_blocked_and_warning():
    ex = build_production_export_contract(_minimal_plan(production_handoff_result=None))
    assert ex.export_ready is False
    assert ex.export_status == "blocked"
    assert WARN_HANDOFF_MISSING in ex.warnings


def test_export_contract_version():
    ex = build_production_export_contract(_minimal_plan())
    assert ex.export_contract_version == EXPORT_CONTRACT_VERSION == "9.19-v1"


def test_handoff_package_id_present():
    ex = build_production_export_contract(_minimal_plan())
    assert ex.handoff_package_id
    assert ex.handoff_package_id.startswith("handoff_")


def test_handoff_package_id_uses_production_job_id_when_set():
    pr = PerformanceRecord(
        id="rec-1",
        production_job_id="job-xyz",
        created_at="t",
        updated_at="t",
    )
    p = _minimal_plan(performance_record=pr)
    assert build_handoff_package_id(p) == "handoff_job_job-xyz"


def test_export_payload_core_and_metadata():
    ex = build_production_export_contract(_minimal_plan())
    pl = ex.export_payload
    assert pl.hook
    assert pl.chapter_outline
    assert pl.scene_prompts
    assert pl.quality_result is not None
    assert pl.narrative_score_result is not None
    assert pl.review_gate_result is not None
    assert pl.human_approval_state is not None
    assert pl.production_handoff_result is not None


def test_prompt_plan_api_has_production_export_contract_result():
    client = TestClient(app)
    r = client.post("/story-engine/prompt-plan", json={"topic": "Polizei und Mord"})
    assert r.status_code == 200
    body = r.json()
    assert "production_export_contract_result" in body
    assert body["production_export_contract_result"] is not None
    assert body["production_export_contract_result"]["export_contract_version"] == "9.19-v1"
    ep = body["production_export_contract_result"]["export_payload"]
    assert "hook" in ep and "chapter_outline" in ep
    assert "quality_result" in ep and "production_handoff_result" in ep
