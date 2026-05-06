"""Orchestrierung: Topic → Klassifikation → Narrativ → Hook (9.2) → Kapitel → Szenen."""

from __future__ import annotations

from typing import List

from app.prompt_engine.chapter_planner import build_chapter_outline
from app.prompt_engine.hook_generator import planned_hook
from app.prompt_engine.loader import load_all_prompt_templates
from app.prompt_engine.narrative_selector import select_archetype
from app.prompt_engine.scene_builder import build_scene_prompts
from app.prompt_engine.narrative_scoring import evaluate_narrative_score
from app.prompt_engine.performance_learning import build_performance_record_from_prompt_plan
from app.prompt_engine.quality_check import evaluate_prompt_plan_quality
from app.prompt_engine.human_approval import build_human_approval_state
from app.prompt_engine.cost_projection import build_cost_projection
from app.prompt_engine.final_readiness_gate import evaluate_final_production_readiness
from app.prompt_engine.master_orchestrator import build_master_orchestration_summary
from app.prompt_engine.package_validation import validate_provider_export_bundle
from app.production_connectors.auth_contract import build_connector_auth_contracts_result
from app.production_connectors.dry_run_executor import dry_run_provider_bundle
from app.production_connectors.execution_queue import build_provider_execution_queue
from app.prompt_engine.production_export_contract import build_production_export_contract
from app.prompt_engine.provider_export_bundle import build_provider_export_bundle
from app.prompt_engine.provider_packaging import build_provider_packages
from app.prompt_engine.production_handoff import build_production_handoff
from app.prompt_engine.production_os_dashboard import build_production_os_dashboard
from app.prompt_engine.provider_strategy_optimizer import optimize_provider_strategy
from app.prompt_engine.template_performance_comparison import compare_template_performance
from app.prompt_engine.template_recommendation import recommend_best_template
from app.prompt_engine.timeline_builder import build_production_timeline
from app.prompt_engine.repair_preview import build_repair_preview
from app.prompt_engine.repair_suggestions import build_prompt_repair_suggestions
from app.prompt_engine.review_gate import evaluate_prompt_plan_review_gate
from app.prompt_engine.schema import PerformanceRecord, ProductionPromptPlan, PromptPlanRequest
from app.prompt_engine.topic_classifier import TopicClassification, classify_topic
from app.manual_url_story.demo_execution import build_manual_url_demo_execution_result
from app.manual_url_story.engine import (
    finalize_manual_url_story_execution_result,
    run_manual_url_rewrite_phase,
)
from app.manual_url_story.rewrite_mode import prompt_template_for_rewrite_mode
from app.story_engine.hook_engine import HookEngineResult


def build_production_prompt_plan(req: PromptPlanRequest) -> ProductionPromptPlan:
    templates = load_all_prompt_templates()
    if not templates:
        raise ValueError("Keine Templates unter app/templates/prompt_planning/ gefunden.")

    mu_outcome, url_quality_gate = run_manual_url_rewrite_phase(req)
    effective_topic = mu_outcome.effective_topic if mu_outcome else req.topic
    effective_title = mu_outcome.effective_title if mu_outcome else req.title
    effective_summary = mu_outcome.effective_source_summary if mu_outcome else req.source_summary

    override = (req.template_override or "").strip()
    forced_mode_template: str | None = None
    if (req.manual_source_url or "").strip() and not override:
        forced_mode_template = prompt_template_for_rewrite_mode(
            req.manual_url_rewrite_mode or "",
            templates,
        )

    if override:
        if override not in templates:
            raise ValueError(f"Unbekanntes template_override: {override!r}")
        classification = TopicClassification(
            template_type=override,
            scores=((override, -1),),
            rationale="template_override gesetzt — Klassifikator übersprungen.",
        )
    elif forced_mode_template:
        classification = TopicClassification(
            template_type=forced_mode_template,
            scores=((forced_mode_template, -1),),
            rationale=(
                f"manual_url_rewrite_mode='{(req.manual_url_rewrite_mode or '').strip()}' — "
                "Prompt-Template an Preset angeglichen (ohne template_override)."
            ),
        )
    else:
        classification = classify_topic(effective_topic, templates)

    doc = templates[classification.template_type]
    arc = select_archetype(effective_topic, doc)
    if mu_outcome and mu_outcome.chapter_outline_override is not None:
        chapters = mu_outcome.chapter_outline_override
    else:
        chapters = build_chapter_outline(arc, effective_topic)

    vid = str(doc.get("video_template") or "generic")
    if mu_outcome and mu_outcome.hook_override:
        hook_res = HookEngineResult(
            hook_text=mu_outcome.hook_override,
            hook_type="manual_url_story_rewrite",
            hook_score=7.5,
            rationale="Hook aus URL-Skriptpfad (shared mit /generate-script).",
            template_match=classification.template_type,
            warnings=[],
        )
    else:
        hook_res = planned_hook(
            video_template=vid,
            topic=effective_topic,
            title=effective_title,
            source_summary=effective_summary,
            manual_url_rewrite_mode=req.manual_url_rewrite_mode or "",
        )
    scenes = build_scene_prompts(chapters, doc, effective_topic)

    warnings = list(hook_res.warnings)
    if mu_outcome:
        warnings.extend(mu_outcome.hook_extra_warnings)
        warnings.extend(mu_outcome.extraction_warnings)
        warnings.extend(mu_outcome.narrative_warnings)
    if url_quality_gate:
        warnings.extend(url_quality_gate.warnings)
        if url_quality_gate.blocking_reasons:
            warnings.append(f"[url_quality_gate] blocking={','.join(url_quality_gate.blocking_reasons)}")
    warnings.append(f"[prompt_plan] {classification.rationale}")

    manual_url_story_execution_result = (
        finalize_manual_url_story_execution_result(mu_outcome, scene_prompt_count=len(scenes))
        if mu_outcome
        else None
    )
    manual_url_quality_gate_result = (
        url_quality_gate if (req.manual_source_url or "").strip() else None
    )
    manual_url_demo_execution_result = None
    if mu_outcome and manual_url_story_execution_result:
        manual_url_demo_execution_result = build_manual_url_demo_execution_result(
            mu_outcome,
            narrative_ok=mu_outcome.narrative_ok,
            scene_prompt_count=len(scenes),
            first_demo_video_hint=list(
                manual_url_story_execution_result.demo_video_execution.command_hint
            ),
        )

    cash_optimization_layer_result = None
    if url_quality_gate and (req.manual_source_url or "").strip():
        from app.cash_optimization.layer import build_cash_optimization_layer

        summary_text = ""
        cc = len(chapters)
        if mu_outcome:
            summary_text = (
                mu_outcome.full_script_preview or mu_outcome.effective_source_summary or ""
            )[:2400]
            cc = max(cc, mu_outcome.chapter_count or 0)
        cash_optimization_layer_result = build_cash_optimization_layer(
            url_quality_gate,
            title=effective_title,
            rewrite_summary=summary_text,
            chapter_count=cc,
            recommended_mode=str(req.manual_url_rewrite_mode or url_quality_gate.recommended_mode),
        )

    plan = ProductionPromptPlan(
        template_type=classification.template_type,
        tone=str(doc.get("tone") or ""),
        hook=hook_res.hook_text,
        chapter_outline=chapters,
        scene_prompts=scenes,
        voice_style=str(doc.get("voice_style") or ""),
        thumbnail_angle=str(doc.get("thumbnail_angle") or ""),
        warnings=warnings,
        video_template=vid,
        narrative_archetype_id=str(arc.get("id") or ""),
        hook_type=hook_res.hook_type,
        hook_score=hook_res.hook_score,
        allow_live_provider_execution=req.allow_live_provider_execution,
        kpi_source_type=req.kpi_source_type,
        external_kpi_metrics=dict(req.external_kpi_metrics or {}),
        manual_url_story_execution_result=manual_url_story_execution_result,
        manual_url_quality_gate_result=manual_url_quality_gate_result,
        manual_url_demo_execution_result=manual_url_demo_execution_result,
        cash_optimization_layer_result=cash_optimization_layer_result,
        quality_result=None,
        narrative_score_result=None,
        performance_record=None,
        review_gate_result=None,
        repair_suggestions_result=None,
        repair_preview_result=None,
        human_approval_state=None,
        production_handoff_result=None,
        production_export_contract_result=None,
        provider_packaging_result=None,
        provider_export_bundle_result=None,
        package_validation_result=None,
    )
    plan_final = plan.model_copy(
        update={
            "quality_result": evaluate_prompt_plan_quality(plan),
            "narrative_score_result": evaluate_narrative_score(plan),
        }
    )
    extra: dict = {}
    if req.include_performance_record:
        extra["performance_record"] = build_performance_record_from_prompt_plan(
            plan_final,
            production_job_id=req.production_job_id,
            script_job_id=req.script_job_id,
            video_id=req.video_id,
            record_id=req.performance_record_id,
        )
    plan_ready = plan_final.model_copy(update=extra) if extra else plan_final
    plan_gated = plan_ready.model_copy(
        update={"review_gate_result": evaluate_prompt_plan_review_gate(plan_ready)}
    )
    plan_with_repairs = plan_gated.model_copy(
        update={"repair_suggestions_result": build_prompt_repair_suggestions(plan_gated)}
    )
    plan_with_preview = plan_with_repairs.model_copy(
        update={"repair_preview_result": build_repair_preview(plan_with_repairs)}
    )
    plan_with_human = plan_with_preview.model_copy(
        update={"human_approval_state": build_human_approval_state(plan_with_preview)}
    )
    plan_with_handoff = plan_with_human.model_copy(
        update={"production_handoff_result": build_production_handoff(plan_with_human)}
    )
    plan_contract = plan_with_handoff.model_copy(
        update={
            "production_export_contract_result": build_production_export_contract(
                plan_with_handoff
            )
        }
    )
    plan_pkg = plan_contract.model_copy(
        update={"provider_packaging_result": build_provider_packages(plan_contract)}
    )
    plan_bundle = plan_pkg.model_copy(
        update={"provider_export_bundle_result": build_provider_export_bundle(plan_pkg)}
    )
    plan_validated = plan_bundle.model_copy(
        update={
            "package_validation_result": validate_provider_export_bundle(plan_bundle),
        }
    )
    suite = dry_run_provider_bundle(plan_validated)
    auth_res = build_connector_auth_contracts_result(plan_validated)
    queue_res = build_provider_execution_queue(plan_validated)
    suite_enriched = suite.model_copy(
        update={
            "auth_contracts": auth_res.contracts if auth_res.contracts else None,
            "execution_queue_result": queue_res,
            "suite_version": "10.2-v1",
        }
    )
    plan_connectors = plan_validated.model_copy(
        update={
            "production_connector_suite_result": suite_enriched,
            "connector_auth_contracts_result": auth_res,
            "provider_execution_queue_result": queue_res,
        }
    )
    plan_timeline = plan_connectors.model_copy(
        update={"production_timeline_result": build_production_timeline(plan_connectors)}
    )
    plan_cost = plan_timeline.model_copy(
        update={"cost_projection_result": build_cost_projection(plan_timeline)}
    )
    plan_readiness = plan_cost.model_copy(
        update={
            "final_readiness_gate_result": evaluate_final_production_readiness(plan_cost),
        }
    )

    from app.production_connectors.run_core_bundle import apply_run_core_suite

    plan_run_core = apply_run_core_suite(plan_readiness)

    from app.production_connectors.live_provider_suite import apply_live_provider_suite

    plan_after_live = apply_live_provider_suite(plan_run_core)

    from app.viral_upgrade.layer import build_viral_upgrade_layer

    plan_viral = plan_after_live.model_copy(
        update={"viral_upgrade_layer_result": build_viral_upgrade_layer(plan_after_live)}
    )

    from app.scene_expansion.layer import build_scene_expansion_layer

    plan_scene = plan_viral.model_copy(
        update={"scene_expansion_result": build_scene_expansion_layer(plan_viral)}
    )

    from app.production_assembly.assembly_suite import apply_production_assembly_suite

    plan_assembled = apply_production_assembly_suite(plan_scene)

    from app.publishing.publishing_suite import apply_publishing_preparation_suite

    plan_publish = apply_publishing_preparation_suite(plan_assembled)

    from app.performance_feedback.feedback_suite import apply_performance_feedback_suite

    plan_feedback = apply_performance_feedback_suite(plan_publish)

    from app.production_acceleration.acceleration_suite import apply_production_acceleration_suite

    plan_acceleration = apply_production_acceleration_suite(plan_feedback)

    from app.monetization_scale.scale_suite import apply_monetization_scale_suite

    plan_scale = apply_monetization_scale_suite(plan_acceleration)

    records_for_compare: List[PerformanceRecord] = []
    if plan_scale.performance_record is not None:
        records_for_compare.append(plan_scale.performance_record)

    tpc = compare_template_performance(records_for_compare)
    plan_tpc = plan_scale.model_copy(
        update={"template_performance_comparison_result": tpc}
    )

    template_keys = sorted(templates.keys())
    rec_tpl = recommend_best_template(
        req.topic,
        template_keys,
        records_for_compare if records_for_compare else None,
        template_docs=templates,
        current_narrative_archetype_id=plan_tpc.narrative_archetype_id,
    )
    plan_rec = plan_tpc.model_copy(update={"template_recommendation_result": rec_tpl})

    opt = optimize_provider_strategy(plan_rec)
    plan_opt = plan_rec.model_copy(update={"provider_strategy_optimizer_result": opt})

    dash = build_production_os_dashboard(
        plan_opt,
        performance_records=records_for_compare if records_for_compare else None,
    )
    plan_dash = plan_opt.model_copy(update={"production_os_dashboard_result": dash})

    master = build_master_orchestration_summary(plan_dash)
    return plan_dash.model_copy(update={"master_orchestration_result": master})
