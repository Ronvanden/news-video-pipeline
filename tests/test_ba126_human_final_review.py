"""BA 12.6 — Human Final Review Package."""

from app.production_assembly.human_final_review import build_human_final_review_package
from app.prompt_engine.pipeline import build_production_prompt_plan
from app.prompt_engine.schema import PromptPlanRequest


def test_human_final_review_package_default_needs_revision_not_publish():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    review = plan.human_final_review_package_result
    assert review is not None
    assert review.review_status in ("ready_for_human_review", "needs_revision", "blocked")
    assert review.release_recommendation in ("approve_for_render", "revise_before_render", "hold")
    assert review.final_checklist
    assert review.final_summary


def test_human_final_review_blocks_when_manifest_blocked():
    plan = build_production_prompt_plan(PromptPlanRequest(topic="Polizei und Mord", title="", source_summary=""))
    blocked_manifest = plan.master_asset_manifest_result.model_copy(update={"manifest_status": "blocked"})
    review = build_human_final_review_package(plan.model_copy(update={"master_asset_manifest_result": blocked_manifest}))
    assert review.review_status == "blocked"
    assert review.release_recommendation == "hold"
    assert "asset_manifest_blocked_or_missing" in review.critical_risks
