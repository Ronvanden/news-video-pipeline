"""BA 9.19 — Versionierter Export-Vertrag aus Prompt-Plan und Handoff (ohne Produktionsstart)."""

from __future__ import annotations

import hashlib
import re
from typing import List, Optional

from app.prompt_engine.schema import (
    ProductionExportContractResult,
    ProductionExportPayload,
    ProductionPromptPlan,
)

EXPORT_CONTRACT_VERSION = "9.19-v1"
WARN_HANDOFF_MISSING = "Production handoff result missing."


def _sanitize_job_fragment(job_id: str) -> str:
    s = (job_id or "").strip()
    if not s:
        return ""
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", s)
    return safe[:120]


def build_handoff_package_id(plan: ProductionPromptPlan) -> str:
    """Deterministische Paket-ID: bevorzugt Production-Job aus PerformanceRecord, sonst Content-Hash."""
    pr = plan.performance_record
    if pr is not None:
        jid = _sanitize_job_fragment(pr.production_job_id)
        if jid:
            return f"handoff_job_{jid}"
    seed_parts = [
        plan.template_type,
        plan.video_template,
        plan.hook[:120],
        str(len(plan.chapter_outline)),
        str(len(plan.scene_prompts)),
        plan.narrative_archetype_id,
    ]
    seed = "|".join(seed_parts)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    tt = (plan.template_type or "unknown").replace(" ", "_")
    return f"handoff_{tt}_{digest}"


def _build_export_payload(plan: ProductionPromptPlan) -> ProductionExportPayload:
    prompt_plan_id: Optional[str] = None
    if plan.performance_record is not None and (plan.performance_record.id or "").strip():
        prompt_plan_id = plan.performance_record.id.strip()
    ho = plan.production_handoff_result
    return ProductionExportPayload(
        prompt_plan_id=prompt_plan_id,
        template_type=plan.template_type,
        video_template=plan.video_template,
        narrative_archetype_id=plan.narrative_archetype_id,
        hook_type=plan.hook_type,
        hook_score=plan.hook_score,
        hook=plan.hook,
        chapter_outline=list(plan.chapter_outline or []),
        scene_prompts=list(plan.scene_prompts or []),
        voice_style=plan.voice_style,
        thumbnail_angle=plan.thumbnail_angle,
        quality_result=plan.quality_result,
        narrative_score_result=plan.narrative_score_result,
        review_gate_result=plan.review_gate_result,
        human_approval_state=plan.human_approval_state,
        production_handoff_result=ho,
    )


def build_production_export_contract(plan: ProductionPromptPlan) -> ProductionExportContractResult:
    checked_sources: List[str] = [
        "production_prompt_plan",
        "production_export_contract",
    ]
    ho = plan.production_handoff_result
    package_id = build_handoff_package_id(plan)
    payload = _build_export_payload(plan)

    if ho is None:
        checked_sources.append("production_handoff_result:missing")
        return ProductionExportContractResult(
            export_contract_version=EXPORT_CONTRACT_VERSION,
            handoff_package_id=package_id,
            export_ready=False,
            export_status="blocked",
            summary="Production handoff unavailable; export blocked.",
            export_payload=payload,
            warnings=[WARN_HANDOFF_MISSING],
            blocking_reasons=[WARN_HANDOFF_MISSING],
            checked_sources=checked_sources,
        )

    checked_sources.extend(ho.checked_sources or [])
    checked_sources = list(dict.fromkeys(checked_sources))

    export_status = ho.handoff_status
    export_ready = export_status == "ready"
    warnings = list(ho.warnings or [])
    blocking_reasons = list(ho.blocking_reasons or []) if not export_ready else []

    return ProductionExportContractResult(
        export_contract_version=EXPORT_CONTRACT_VERSION,
        handoff_package_id=package_id,
        export_ready=export_ready,
        export_status=export_status,
        summary=ho.summary,
        export_payload=payload,
        warnings=warnings,
        blocking_reasons=blocking_reasons,
        checked_sources=checked_sources,
    )
