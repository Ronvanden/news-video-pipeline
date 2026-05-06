"""BA 12.0–12.6 — Production Asset Assembly Suite."""

from __future__ import annotations

from app.production_assembly.downloadable_bundle import build_downloadable_production_bundle
from app.production_assembly.human_final_review import build_human_final_review_package
from app.production_assembly.master_asset_manifest import build_master_asset_manifest
from app.production_assembly.multi_asset_assembly import build_multi_asset_assembly
from app.production_assembly.render_instruction_package import build_render_instruction_package
from app.production_assembly.timeline_finalizer import build_final_timeline
from app.production_assembly.voice_scene_alignment import build_voice_scene_alignment


def apply_production_assembly_suite(plan: object) -> object:
    """Manifest → Assembly → Timeline → Alignment → Render → Bundle → Human Review."""
    p = plan.model_copy(update={"master_asset_manifest_result": build_master_asset_manifest(plan)})
    p = p.model_copy(update={"multi_asset_assembly_result": build_multi_asset_assembly(p)})
    p = p.model_copy(update={"final_timeline_result": build_final_timeline(p)})
    p = p.model_copy(update={"voice_scene_alignment_result": build_voice_scene_alignment(p)})
    p = p.model_copy(update={"render_instruction_package_result": build_render_instruction_package(p)})
    p = p.model_copy(update={"downloadable_production_bundle_result": build_downloadable_production_bundle(p)})
    p = p.model_copy(update={"human_final_review_package_result": build_human_final_review_package(p)})
    return p
