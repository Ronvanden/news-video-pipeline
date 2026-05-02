"""Real KPI Feedback CF 16.5–16.9 — Kernfälle."""

import json
from pathlib import Path

from app.cash_feedback.loop import capture_real_kpi, run_real_kpi_feedback_loop
from app.cash_optimization.schema import (
    CashOptimizationLayerResult,
    CandidateRoiScoreResult,
    EstimatedRpmResult,
    ProductionCostSnapshotResult,
    ViralHookScoreResult,
    WinnerRepeatResult,
)


def _cash_layer(roi: int) -> CashOptimizationLayerResult:
    roi_res = CandidateRoiScoreResult(
        candidate_roi_score=roi,
        hook_power_score=70,
        narrative_strength_score=70,
        niche_value_score=70,
        production_efficiency_score=70,
        confidence_level="high",
        recommended_priority="high",
    )
    rpm = EstimatedRpmResult(estimated_rpm_category="medium", estimated_rpm_confidence=60)
    cost = ProductionCostSnapshotResult()
    viral = ViralHookScoreResult(viral_hook_score=40, dominant_hook_type="money")
    win = WinnerRepeatResult(winner_cluster="hidden_truth", repeatability_score=40)
    return CashOptimizationLayerResult(
        roi=roi_res,
        estimated_rpm=rpm,
        production_cost=cost,
        viral_hook=viral,
        winner_repeat=win,
    )


def test_good_kpi_classifies_winner():
    raw = {
        "source_url": "https://example.com/article",
        "views": 12000,
        "impressions": 400000,
        "ctr": 0.045,
        "watch_time_minutes": 900,
        "subscribers_gained": 80,
    }
    out = run_real_kpi_feedback_loop(raw)
    assert out.classification.performance_label == "winner"
    assert out.capture.capture_status in ("ok", "partial")


def test_weak_kpi_classifies_loser():
    raw = {
        "source_url": "https://example.com/x",
        "views": 120,
        "impressions": 8000,
        "ctr": 0.008,
        "watch_time_minutes": 40,
        "subscribers_gained": 0,
    }
    out = run_real_kpi_feedback_loop(raw)
    assert out.classification.performance_label == "loser"


def test_high_prediction_weak_reality_overestimated():
    raw = {
        "source_url": "https://example.com/y",
        "views": 300,
        "impressions": 10000,
        "ctr": 0.01,
        "watch_time_minutes": 50,
        "subscribers_gained": 0,
    }
    cash = _cash_layer(92)
    out = run_real_kpi_feedback_loop(raw, cash_layer=cash)
    assert out.prediction_reality is not None
    assert out.prediction_reality.overestimated_signals


def test_low_prediction_strong_reality_underestimated():
    raw = {
        "source_url": "https://example.com/z",
        "views": 4200,
        "impressions": 120000,
        "ctr": 0.038,
        "watch_time_minutes": 520,
        "subscribers_gained": 45,
        "revenue_eur": 95,
    }
    cash = _cash_layer(28)
    out = run_real_kpi_feedback_loop(raw, cash_layer=cash)
    assert out.prediction_reality is not None
    assert out.prediction_reality.underestimated_signals


def test_repeat_vs_kill_decision():
    strong = run_real_kpi_feedback_loop(
        {
            "source_url": "https://ex.com/a",
            "views": 15000,
            "ctr": 0.05,
            "watch_time_minutes": 800,
        }
    )
    assert strong.decision.decision == "repeat_format"

    weak = run_real_kpi_feedback_loop(
        {
            "source_url": "https://ex.com/b",
            "views": 80,
            "ctr": 0.008,
            "watch_time_minutes": 30,
        }
    )
    assert weak.decision.decision == "kill_topic"


def test_capture_ctr_percent_input():
    cap = capture_real_kpi({"source_url": "https://a.de/x", "views": 100, "ctr": 4.5})
    assert cap.capture_status != "invalid"
    assert abs(cap.normalized_metrics["ctr"] - 0.045) < 1e-6


def test_cli_json_roundtrip_tmp(tmp_path: Path):
    metrics = {
        "source_url": "https://cli.example/video",
        "views": 5000,
        "ctr": 0.032,
        "watch_time_minutes": 300,
        "subscribers_gained": 12,
    }
    p = tmp_path / "m.json"
    p.write_text(json.dumps(metrics), encoding="utf-8")
    out = run_real_kpi_feedback_loop(metrics)
    assert out.summary.feedback_status in ("ok", "partial")
