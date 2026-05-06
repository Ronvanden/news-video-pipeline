"""BA 13.0–13.6 — Publishing Preparation Suite."""

from __future__ import annotations

from app.publishing.founder_publishing_summary import build_founder_publishing_summary
from app.publishing.metadata_master_package import build_metadata_master_package
from app.publishing.metadata_optimizer import build_metadata_optimizer
from app.publishing.publishing_readiness_gate import evaluate_publishing_readiness
from app.publishing.schedule_plan import build_schedule_plan
from app.publishing.thumbnail_variant_pack import build_thumbnail_variant_pack
from app.publishing.upload_checklist import build_upload_checklist


def apply_publishing_preparation_suite(plan: object) -> object:
    """Metadata → Optimizer → Thumbnail → Checklist → Schedule → Readiness → Summary."""
    p = plan.model_copy(update={"metadata_master_package_result": build_metadata_master_package(plan)})
    p = p.model_copy(update={"metadata_optimizer_result": build_metadata_optimizer(p)})
    p = p.model_copy(update={"thumbnail_variant_pack_result": build_thumbnail_variant_pack(p)})
    p = p.model_copy(update={"upload_checklist_result": build_upload_checklist(p)})
    p = p.model_copy(update={"schedule_plan_result": build_schedule_plan(p)})
    p = p.model_copy(update={"publishing_readiness_gate_result": evaluate_publishing_readiness(p)})
    p = p.model_copy(update={"founder_publishing_summary_result": build_founder_publishing_summary(p)})
    return p
