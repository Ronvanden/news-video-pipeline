"""Cash Optimization CO 16.0–16.4 — Kernfälle (heuristisch)."""

from app.cash_optimization.layer import (
    build_cash_optimization_layer,
    detect_winner_repeat,
    estimate_rpm,
    score_viral_hook,
)
from app.manual_url_story.schema import UrlQualityGateResult


def _gate(**kwargs) -> UrlQualityGateResult:
    base = dict(
        url_quality_status="strong",
        hook_potential_score=70,
        narrative_density_score=65,
        emotional_weight_score=40,
        recommended_mode="documentary",
        warnings=[],
        blocking_reasons=[],
    )
    base.update(kwargs)
    return UrlQualityGateResult(**base)


def test_rpm_high_real_estate():
    blob_title = "Luxus Immobilie und Millionen Deal am Finanzmarkt"
    r = estimate_rpm(blob_title.lower())
    assert r.estimated_rpm_category == "high"


def test_rpm_medium_documentary():
    blob_title = "Historische Dokumentation Bildung geopolitische Einordnung"
    r = estimate_rpm(blob_title.lower())
    assert r.estimated_rpm_category == "medium"


def test_rpm_low_meme_signal():
    blob_title = "lustiger meme tiktok viral gossip promi trash"
    r = estimate_rpm(blob_title.lower())
    assert r.estimated_rpm_category == "low"


def test_viral_hook_mystery_money():
    blob = "geheim exclusiv million deal enthüllt niemand weiß die wahrheit"
    v = score_viral_hook(blob)
    assert v.viral_hook_score >= 40
    assert v.dominant_hook_type != "none"


def test_weak_roi_blocked_gate():
    gate = _gate(url_quality_status="blocked", hook_potential_score=5, narrative_density_score=10)
    layer = build_cash_optimization_layer(
        gate,
        title="",
        rewrite_summary="",
        chapter_count=0,
        recommended_mode="documentary",
    )
    assert layer.roi.candidate_roi_score <= 25
    assert layer.roi.recommended_priority == "low"


def test_winner_cluster_hidden_truth():
    blob = "die wahrheit über die geheimakte wurde enthüllt und unterdrückt"
    w = detect_winner_repeat(blob)
    assert w.winner_cluster == "hidden_truth"
    assert w.repeatability_score >= 28


def test_full_layer_prioritizes_strong_gate():
    gate = _gate(url_quality_status="strong", hook_potential_score=85, narrative_density_score=80)
    layer = build_cash_optimization_layer(
        gate,
        title="Milliarden Immobilien und CEO Strategie",
        rewrite_summary="Bank und Aktienmarkt Analyse mit hohem Bildungsanspruch.",
        chapter_count=6,
        recommended_mode="mystery",
    )
    assert layer.roi.recommended_priority in ("high", "medium")
    assert layer.estimated_rpm.estimated_rpm_category == "high"
