"""Orchestrierung Real KPI → Klassifikation → Kalibrierung → Founder-Decision → Summary."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from app.cash_feedback.schema import (
    CaptureStatus,
    FeedbackStatus,
    FounderDecision,
    FounderPerformanceDecisionResult,
    KpiFeedbackSummaryResult,
    PerformanceClassificationResult,
    PerformanceLabel,
    PredictionRealityResult,
    RealKpiCaptureInput,
    RealKpiCaptureResult,
    RealKpiFeedbackLoopResult,
)
from app.cash_optimization.schema import CashOptimizationLayerResult


def _normalize_ctr(raw: float) -> float:
    if raw <= 0:
        return 0.0
    if raw > 1.0:
        return min(1.0, raw / 100.0)
    return raw


def capture_real_kpi(raw: Dict[str, Any]) -> RealKpiCaptureResult:
    """BA 16.5 — Parsen, CTR normalisieren, Lücken markieren."""
    warnings: List[str] = []
    missing: List[str] = []
    try:
        inp = RealKpiCaptureInput.model_validate(raw)
    except Exception as e:
        return RealKpiCaptureResult(
            capture_status="invalid",
            normalized_metrics={},
            missing_metrics=["input_validation_failed"],
            warnings=[f"kpi_input_invalid:{type(e).__name__}"],
        )

    ctr_n = _normalize_ctr(inp.ctr)
    if inp.ctr > 1.0:
        warnings.append("ctr_assumed_percent_converted_to_fraction")

    norm: Dict[str, Any] = {
        "video_id": inp.video_id or "",
        "source_url": inp.source_url.strip(),
        "views": float(inp.views),
        "impressions": float(inp.impressions),
        "ctr": ctr_n,
        "watch_time_minutes": float(inp.watch_time_minutes),
        "avg_view_duration_seconds": float(inp.avg_view_duration_seconds),
        "subscribers_gained": float(inp.subscribers_gained),
        "revenue_eur": float(inp.revenue_eur) if inp.revenue_eur is not None else None,
        "upload_date": inp.upload_date or "",
    }

    if inp.impressions <= 0 and ctr_n > 0:
        missing.append("impressions_ctr_only_partial_confidence")
    if inp.views <= 0:
        missing.append("views_zero_or_missing")
    if inp.watch_time_minutes <= 0 and inp.avg_view_duration_seconds <= 0:
        missing.append("watch_time_signals_weak")

    status: CaptureStatus = "ok"
    if missing:
        status = "partial"
        warnings.append("some_metrics_missing_heuristic_confidence_reduced")

    return RealKpiCaptureResult(
        capture_status=status,
        normalized_metrics=norm,
        missing_metrics=missing,
        warnings=warnings,
    )


def compute_reality_performance_score(norm: Dict[str, Any]) -> int:
    """0–100 Komposit aus Views/CTR/Watchtime/Revenue/Subs (heuristisch)."""
    v = float(norm.get("views") or 0)
    ctr = float(norm.get("ctr") or 0)
    wt = float(norm.get("watch_time_minutes") or 0)
    rev = norm.get("revenue_eur")
    rev_f = float(rev) if rev is not None else 0.0
    sub = float(norm.get("subscribers_gained") or 0)
    avgd = float(norm.get("avg_view_duration_seconds") or 0)

    v_part = min(38.0, 38.0 * math.log10(v + 10.0) / math.log10(100_001.0))
    ctr_part = min(28.0, ctr * 560.0)
    wt_part = min(22.0, wt / 45.0)
    rev_part = min(12.0, rev_f / 8.0)
    sub_part = min(10.0, sub * 1.8)
    ret_part = min(10.0, avgd / 180.0 * 10.0) if avgd > 0 else 0.0

    return int(max(0, min(100, round(v_part + ctr_part + wt_part + rev_part + sub_part + ret_part))))


def classify_performance(norm: Dict[str, Any], capture: RealKpiCaptureResult) -> PerformanceClassificationResult:
    """BA 16.6"""
    views = int(float(norm.get("views") or 0))
    ctr = float(norm.get("ctr") or 0)
    wt = float(norm.get("watch_time_minutes") or 0)
    rev = norm.get("revenue_eur")
    rev_f = float(rev) if rev is not None else 0.0
    sub = int(float(norm.get("subscribers_gained") or 0))

    strengths: List[str] = []
    weaknesses: List[str] = []
    label: PerformanceLabel = "neutral"
    conf = 52

    if views >= 8000 and ctr >= 0.04 and wt >= 400:
        label = "winner"
        conf = 88
        strengths.extend(["strong_views", "healthy_ctr", "meaningful_watch_time"])
    elif rev_f >= 120 or (views >= 5000 and rev_f >= 40):
        label = "winner"
        conf = min(90, conf + 12)
        strengths.append("revenue_signal_strong_for_sample_size")
    elif views < 400 and ctr < 0.012 and wt < 80 and sub <= 1:
        label = "loser"
        conf = 78
        weaknesses.extend(["low_views", "weak_ctr", "thin_engagement"])
    elif views >= 1500 and (ctr >= 0.025 or wt >= 180):
        label = "promising"
        conf = 68
        strengths.extend(["early_positive_ctr_or_watch"])
    else:
        label = "neutral"
        conf = 55

    if capture.capture_status == "partial":
        conf = max(30, conf - 12)
        weaknesses.append("incomplete_metrics_snapshot")

    repeat_rec = {
        "winner": "repeat_format_with_similar_angle",
        "promising": "iterate_one_variable_then_scale",
        "neutral": "adjust_packaging_or_niche_test",
        "loser": "deprioritize_or_kill_similar_hooks",
    }[label]

    return PerformanceClassificationResult(
        performance_label=label,
        confidence=conf,
        strengths=strengths,
        weaknesses=weaknesses,
        repeat_recommendation=repeat_rec,
    )


def compare_prediction_reality(
    *,
    cash_layer: Optional[CashOptimizationLayerResult],
    reality_score: int,
) -> Optional[PredictionRealityResult]:
    """BA 16.7"""
    if cash_layer is None:
        return None

    predicted = int(cash_layer.roi.candidate_roi_score)
    delta = predicted - reality_score
    accuracy = max(0, 100 - abs(delta))

    over: List[str] = []
    under: List[str] = []
    notes: List[str] = []

    if delta >= 18:
        over.append("candidate_roi_above_observed_performance")
        if cash_layer.viral_hook.viral_hook_score >= 70:
            over.append("viral_hook_score_may_have_overweighted_short_term_clickbait")
        if cash_layer.estimated_rpm.estimated_rpm_category == "high":
            over.append("rpm_category_high_vs_actual_yield")
    elif delta <= -18:
        under.append("candidate_roi_below_observed_performance")
        if predicted < 45:
            under.append("conservative_pre_publish_score")
    else:
        notes.append("prediction_within_tolerance_band")

    notes.append(f"predicted_roi={predicted}_reality_heuristic={reality_score}")

    return PredictionRealityResult(
        prediction_accuracy=accuracy,
        overestimated_signals=over,
        underestimated_signals=under,
        calibration_notes=notes,
    )


def founder_performance_decision(
    *,
    label: PerformanceLabel,
    compare: Optional[PredictionRealityResult],
    capture: RealKpiCaptureResult,
) -> FounderPerformanceDecisionResult:
    """BA 16.8"""
    decision: FounderDecision = "test_again"
    reason = "default_iterate_with_controlled_change"
    nxt = "run_one_more_test_with_documented_hypothesis"
    priority = "medium"

    if capture.capture_status == "invalid":
        return FounderPerformanceDecisionResult(
            decision="test_again",
            reason="kpi_capture_invalid_retry_with_complete_metrics",
            next_action="fix_json_fields_then_record_video_kpi",
            priority="high",
        )

    over = bool(compare and compare.overestimated_signals)
    under = bool(compare and compare.underestimated_signals)

    if label == "winner":
        decision = "repeat_format"
        reason = "observed_performance_supports_format_repeat"
        nxt = "clone_structure_adjust_hook_10_percent_only"
        priority = "high"
    elif label == "loser":
        decision = "kill_topic"
        reason = "weak_engagement_across_core_signals"
        nxt = "stop_similar_topics_review_niche_and_thumb"
        priority = "high"
    elif label == "promising":
        if over:
            decision = "modify_hook"
            reason = "had_high_pre_score_but_moderate_delivery"
            nxt = "tighten_hook_and_first_30s_retention"
            priority = "medium"
        elif under:
            decision = "test_again"
            reason = "undersold_heuristic_double_down_with_controls"
            nxt = "repeat_with_same_topic_clearer_packaging"
            priority = "medium"
        else:
            decision = "test_again"
            reason = "promising_but_not_proven"
            nxt = "single_variable_ab_test"
            priority = "medium"
    else:
        decision = "change_niche" if over else "test_again"
        reason = "neutral_band_needs_positioning_or_niche_shift"
        nxt = "try_adjacent_subniche_or_packaging_refresh"
        priority = "low"

    return FounderPerformanceDecisionResult(
        decision=decision,
        reason=reason,
        next_action=nxt,
        priority=priority,
    )


def build_kpi_feedback_summary(
    *,
    capture: RealKpiCaptureResult,
    classification: PerformanceClassificationResult,
    compare: Optional[PredictionRealityResult],
    decision: FounderPerformanceDecisionResult,
    cash_layer: Optional[CashOptimizationLayerResult],
) -> KpiFeedbackSummaryResult:
    """BA 16.9"""
    fb: FeedbackStatus = "ok" if capture.capture_status == "ok" else "partial"
    if capture.capture_status == "invalid":
        fb = "blocked"

    cash_sum = "no_pre_publish_cash_layer_provided"
    if cash_layer:
        cash_sum = (
            f"pre_roi={cash_layer.roi.candidate_roi_score};"
            f"rpm_cat={cash_layer.estimated_rpm.estimated_rpm_category};"
            f"priority={cash_layer.roi.recommended_priority}"
        )

    perf_sum = (
        f"label={classification.performance_label};"
        f"confidence={classification.confidence};"
        f"views={capture.normalized_metrics.get('views')}"
    )

    learn_parts: List[str] = []
    if compare:
        learn_parts.append(f"prediction_accuracy={compare.prediction_accuracy}")
        if compare.overestimated_signals:
            learn_parts.append("calibrate_down:" + ",".join(compare.overestimated_signals[:2]))
        if compare.underestimated_signals:
            learn_parts.append("calibrate_up:" + ",".join(compare.underestimated_signals[:2]))
    else:
        learn_parts.append("no_pre_publish_compare_store_cash_layer_next_time")

    return KpiFeedbackSummaryResult(
        feedback_status=fb,
        cash_result_summary=cash_sum,
        performance_summary=perf_sum,
        learning_summary=" | ".join(learn_parts),
        next_best_action=f"{decision.decision}:{decision.next_action}",
    )


def run_real_kpi_feedback_loop(
    metrics: Dict[str, Any],
    *,
    cash_layer: Optional[CashOptimizationLayerResult] = None,
) -> RealKpiFeedbackLoopResult:
    """Öffentlicher Einstieg: JSON-Dict → vollständiger Feedback-Loop."""
    capture = capture_real_kpi(metrics)
    if capture.capture_status == "invalid":
        stub_pc = PerformanceClassificationResult(
            performance_label="neutral",
            confidence=0,
            weaknesses=["invalid_input"],
            repeat_recommendation="fix_metrics_json",
        )
        stub_dec = founder_performance_decision(
            label="neutral",
            compare=None,
            capture=capture,
        )
        stub_sum = build_kpi_feedback_summary(
            capture=capture,
            classification=stub_pc,
            compare=None,
            decision=stub_dec,
            cash_layer=cash_layer,
        )
        return RealKpiFeedbackLoopResult(
            capture=capture,
            classification=stub_pc,
            prediction_reality=None,
            decision=stub_dec,
            summary=stub_sum,
        )

    norm = capture.normalized_metrics
    reality = compute_reality_performance_score(norm)
    classification = classify_performance(norm, capture)
    compare = compare_prediction_reality(cash_layer=cash_layer, reality_score=reality)
    decision = founder_performance_decision(
        label=classification.performance_label,
        compare=compare,
        capture=capture,
    )
    summary = build_kpi_feedback_summary(
        capture=capture,
        classification=classification,
        compare=compare,
        decision=decision,
        cash_layer=cash_layer,
    )

    return RealKpiFeedbackLoopResult(
        capture=capture,
        classification=classification,
        prediction_reality=compare,
        decision=decision,
        summary=summary,
    )
