"""BA 13.1 — Metadata Optimizer."""

from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest
from app.publishing.metadata_optimizer import build_metadata_optimizer


def test_metadata_optimizer_builds_seo_variants():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    opt = plan.metadata_optimizer_result
    assert opt is not None
    assert len(opt.optimized_titles) >= 3
    assert opt.optimized_descriptions
    assert len(opt.optimized_tags) >= len(plan.metadata_master_package_result.canonical_tags)
    assert opt.seo_score > 0
    assert opt.click_potential_score > 0


def test_metadata_optimizer_limited_when_metadata_blocked():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    blocked_meta = plan.metadata_master_package_result.model_copy(update={"metadata_status": "blocked"})
    opt = build_metadata_optimizer(plan.model_copy(update={"metadata_master_package_result": blocked_meta}))
    assert opt.seo_score <= 35
    assert "metadata_blocked_optimizer_limited" in opt.warnings
