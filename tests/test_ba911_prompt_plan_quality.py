"""BA 9.11 — Prompt Plan Quality Check V1."""

from fastapi.testclient import TestClient

from app.main import app
from app.prompt_engine.quality_check import evaluate_prompt_plan_quality
from app.prompt_engine.schema import ChapterOutlineItem, ProductionPromptPlan


def _plan_passing() -> ProductionPromptPlan:
    ch = [ChapterOutlineItem(title=f"Kapitel {i}", summary="Zusammenfassung.") for i in range(1, 6)]
    sc = [f"Szenenprompt {i} mit genug Text." for i in range(1, 6)]
    return ProductionPromptPlan(
        template_type="true_crime",
        tone="ernst, dokumentarisch",
        hook="Ein ausreichend langer Hook für die Qualitätsprüfung hier.",
        chapter_outline=ch,
        scene_prompts=sc,
        voice_style="neutral dokumentarisch",
        thumbnail_angle="Kontrast, Silhouette",
        warnings=[],
        narrative_archetype_id="cold_case_arc",
        hook_type="shock_reveal",
        hook_score=7.5,
    )


def test_good_plan_status_pass():
    q = evaluate_prompt_plan_quality(_plan_passing())
    assert q.status == "pass"
    assert q.score >= 80
    assert not q.blocking_issues
    assert "template_type" in q.checked_fields


def test_missing_hook_fails():
    p = _plan_passing().model_copy(update={"hook": ""})
    q = evaluate_prompt_plan_quality(p)
    assert q.status == "fail"
    assert "hook_empty" in q.blocking_issues


def test_too_few_chapters_warning():
    ch = [ChapterOutlineItem(title="A", summary="a"), ChapterOutlineItem(title="B", summary="b")]
    p = _plan_passing().model_copy(
        update={
            "chapter_outline": ch,
            "scene_prompts": ["s1", "s2"],
        }
    )
    q = evaluate_prompt_plan_quality(p)
    assert q.status == "warning"
    assert any("kapitel_unter" in w for w in q.warnings)


def test_missing_voice_style_warning():
    p = _plan_passing().model_copy(update={"voice_style": ""})
    q = evaluate_prompt_plan_quality(p)
    assert q.status == "warning"
    assert any("voice_style_leer" in w for w in q.warnings)


def test_prompt_plan_api_includes_quality_result():
    client = TestClient(app)
    r = client.post(
        "/story-engine/prompt-plan",
        json={"topic": "Polizei und Ermittlung im Mordfall"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "quality_result" in data
    qr = data["quality_result"]
    assert qr["status"] in ("pass", "warning", "fail")
    assert "score" in qr
    assert "warnings" in qr
    assert "blocking_issues" in qr
    assert "checked_fields" in qr


def test_default_pipeline_plan_has_quality_warning_or_pass():
    """BA 9.10 Templates haben typisch <5 Kapitel → eher warning; Quality-Feld immer da."""
    import app.prompt_engine.loader as pe_loader

    from app.prompt_engine.pipeline import build_production_prompt_plan
    from app.prompt_engine.schema import PromptPlanRequest

    pe_loader.list_prompt_template_keys.cache_clear()
    pe_loader.load_prompt_template.cache_clear()
    try:
        plan = build_production_prompt_plan(
            PromptPlanRequest(topic="Mordfall und Forensik", title="", source_summary="")
        )
        assert plan.quality_result is not None
        assert plan.quality_result.status in ("pass", "warning", "fail")
    finally:
        pe_loader.list_prompt_template_keys.cache_clear()
        pe_loader.load_prompt_template.cache_clear()
