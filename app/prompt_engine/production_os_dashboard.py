"""BA 9.29 — Production OS Dashboard Summary (read-only JSON, kein UI)."""

from __future__ import annotations

from typing import List, Optional

from app.prompt_engine.schema import (
    PerformanceRecord,
    ProductionOSDashboardResult,
    ProductionOSDashboardStatus,
    ProductionPromptPlan,
)


def build_production_os_dashboard(
    plan: ProductionPromptPlan,
    *,
    performance_records: Optional[List[PerformanceRecord]] = None,
) -> ProductionOSDashboardResult:
    q = plan.quality_result
    n = plan.narrative_score_result
    fr = plan.final_readiness_gate_result
    cost = plan.cost_projection_result
    tr = plan.template_recommendation_result
    po = plan.provider_strategy_optimizer_result

    prompt_health = int(q.score) if q else 0
    readiness = int(fr.readiness_score) if fr else 0
    est = float(cost.total_estimated_cost_eur) if cost else 0.0

    top_risks: List[str] = []
    top_strengths: List[str] = []
    if fr:
        top_risks.extend(fr.production_blockers[:5])
        top_risks.extend(fr.review_flags[:3])
        top_strengths.extend(fr.strengths[:5])
    if q and q.status != "pass":
        top_risks.append(f"Qualität: {q.status}")
    if n and n.status == "weak":
        top_risks.append("Narrativ schwach (Heuristik).")

    status: ProductionOSDashboardStatus = "ready"
    if po and po.optimization_status == "blocked":
        status = "blocked"
    elif (fr and fr.readiness_decision == "not_ready") or (po and po.optimization_status == "partial"):
        status = "degraded"
    elif fr and fr.readiness_decision == "ready_for_review":
        status = "degraded"

    rec_t = tr.recommended_template if tr else plan.template_type
    strat = ""
    if po:
        strat = (
            f"image={po.recommended_image_provider}; video={po.recommended_video_provider}; "
            f"voice={po.recommended_voice_provider}; thumb={po.recommended_thumbnail_provider}; "
            f"priority={po.cost_priority}"
        )

    extra = ""
    if performance_records:
        extra = f" {len(performance_records)} PerformanceRecord(s) für Kontext."
    summary = (
        f"Plan {plan.template_type}: Prompt-Gesundheit ~{prompt_health}/100, "
        f"Readiness-Score {readiness}/100, geschätzte Kosten {est:.2f} EUR.{extra}"
    )

    return ProductionOSDashboardResult(
        dashboard_status=status,
        prompt_health_score=prompt_health,
        production_readiness_score=readiness,
        estimated_cost=round(est, 4),
        recommended_template=rec_t,
        recommended_provider_strategy=strat,
        top_risks=list(dict.fromkeys([x for x in top_risks if x]))[:8],
        top_strengths=list(dict.fromkeys([x for x in top_strengths if x]))[:8],
        executive_summary=summary.strip(),
    )
