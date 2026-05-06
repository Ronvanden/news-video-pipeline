"""BA 9.13 — Performance Learning Loop V1."""

from fastapi.testclient import TestClient

from app.main import app
import app.prompt_engine.loader as pe_loader
from app.prompt_engine.performance_learning import (
    build_performance_record_from_prompt_plan,
    evaluate_performance_snapshot,
    summarize_template_performance,
)
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import (
    NarrativeScoreResult,
    NarrativeSubscores,
    PerformanceRecord,
    ProductionPromptPlan,
    PromptPlanQualityResult,
    PromptPlanRequest,
)


def _sample_plan() -> ProductionPromptPlan:
    from app.prompt_engine.schema import ChapterOutlineItem

    q = PromptPlanQualityResult(score=82, status="pass", warnings=[], blocking_issues=[], checked_fields=[])
    sub = NarrativeSubscores(
        hook_curiosity_score=70,
        emotional_pull_score=60,
        escalation_score=55,
        chapter_progression_score=72,
        thumbnail_potential_score=65,
    )
    n = NarrativeScoreResult(
        score=64,
        status="moderate",
        subscores=sub,
        strengths=[],
        weaknesses=[],
        checked_dimensions=[],
    )
    return ProductionPromptPlan(
        template_type="true_crime",
        tone="ernst",
        hook="Hook text lang genug.",
        chapter_outline=[ChapterOutlineItem(title="A", summary="s")],
        scene_prompts=["p1"],
        voice_style="v",
        thumbnail_angle="t",
        warnings=[],
        video_template="true_crime",
        narrative_archetype_id="cold_case_arc",
        hook_type="shock_reveal",
        hook_score=7.2,
        quality_result=q,
        narrative_score_result=n,
        performance_record=None,
    )


def test_build_record_from_plan():
    plan = _sample_plan()
    rec = build_performance_record_from_prompt_plan(
        plan,
        production_job_id="job-1",
        script_job_id="sj-9",
        video_id="vid-x",
        record_id="rec-fixed",
    )
    assert rec.id == "rec-fixed"
    assert rec.production_job_id == "job-1"
    assert rec.script_job_id == "sj-9"
    assert rec.video_id == "vid-x"
    assert rec.template_type == "true_crime"
    assert rec.video_template == "true_crime"
    assert rec.narrative_archetype_id == "cold_case_arc"
    assert rec.hook_type == "shock_reveal"
    assert rec.hook_score == 7.2
    assert rec.quality_score == 82
    assert rec.quality_status == "pass"
    assert rec.narrative_score == 64
    assert rec.narrative_status == "moderate"


def test_snapshot_pending_without_kpis():
    r = PerformanceRecord(
        id="1",
        template_type="true_crime",
        quality_score=80,
        narrative_score=70,
        created_at="t",
        updated_at="t",
    )
    snap = evaluate_performance_snapshot(r)
    assert snap.status == "pending_data"
    assert snap.learning_score is None


def test_snapshot_ready_with_core_kpis():
    r = PerformanceRecord(
        id="2",
        template_type="true_crime",
        created_at="t",
        updated_at="t",
        views=50_000.0,
        ctr=0.08,
        retention_percent=35.0,
    )
    snap = evaluate_performance_snapshot(r)
    assert snap.status == "ready"
    assert snap.learning_score is not None
    assert 0 <= snap.learning_score <= 100


def test_summarize_by_template_type():
    r1 = PerformanceRecord(
        id="a",
        template_type="true_crime",
        quality_score=80,
        narrative_score=60,
        created_at="t",
        updated_at="t",
    )
    r2 = PerformanceRecord(
        id="b",
        template_type="true_crime",
        quality_score=60,
        narrative_score=40,
        created_at="t",
        updated_at="t",
    )
    r3 = PerformanceRecord(
        id="c",
        template_type="mystery_history",
        quality_score=90,
        narrative_score=85,
        created_at="t",
        updated_at="t",
    )
    sums = summarize_template_performance([r1, r2, r3])
    assert len(sums) == 2
    by_tt = {s.template_type: s for s in sums}
    assert by_tt["true_crime"].record_count == 2
    assert by_tt["true_crime"].avg_quality_score == 70.0
    assert by_tt["true_crime"].pending_kpi_count == 2
    assert by_tt["mystery_history"].record_count == 1


def test_pipeline_optional_performance_record():
    pe_loader.list_prompt_template_keys.cache_clear()
    pe_loader.load_prompt_template.cache_clear()
    try:
        plan = build_production_prompt_plan(
            PromptPlanRequest(
                topic="Polizei und Mordfall",
                include_performance_record=True,
                production_job_id="pj-1",
                script_job_id="sj-2",
            )
        )
        assert plan.performance_record is not None
        assert plan.performance_record.template_type == plan.template_type
        assert plan.performance_record.quality_score == plan.quality_result.score
        assert plan.performance_record.narrative_score == plan.narrative_score_result.score
        snap = evaluate_performance_snapshot(plan.performance_record)
        assert snap.status == "pending_data"
    finally:
        pe_loader.list_prompt_template_keys.cache_clear()
        pe_loader.load_prompt_template.cache_clear()


def test_api_includes_performance_record_when_requested():
    client = TestClient(app)
    r = client.post(
        "/story-engine/prompt-plan",
        json={
            "topic": "Ermittlung und Gericht",
            "include_performance_record": True,
            "production_job_id": "api-job",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("performance_record") is not None
    assert data["performance_record"]["production_job_id"] == "api-job"
