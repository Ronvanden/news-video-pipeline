"""Heuristische Cash-Optimization — reuse nur UrlQualityGate + Textblob."""

from __future__ import annotations

import re
from typing import List, Tuple

from app.cash_optimization.schema import (
    CashOptimizationLayerResult,
    CandidateRoiScoreResult,
    ComplexityLabel,
    ConfidenceLevel,
    EstimatedRpmResult,
    FactRiskLabel,
    PriorityLevel,
    ProductionCostSnapshotResult,
    ProductionCostTier,
    VisualDifficultyLabel,
    ViralHookScoreResult,
    WinnerRepeatResult,
)
from app.manual_url_story.schema import UrlQualityGateResult, UrlQualityStatus

_RPM_HIGH = (
    "finance",
    "finanz",
    "aktien",
    "etf",
    "crypto",
    "bitcoin",
    "immobilie",
    "immobilien",
    "real estate",
    "hypothek",
    "business",
    "startup",
    "unternehmen",
    "legal",
    "anwalt",
    "recht",
    "klage",
    "luxury",
    "luxus",
    "milliard",
    "million",
    "ceo",
    "bank",
)
_RPM_MEDIUM = (
    "dokumentation",
    "documentary",
    "geschichte",
    "histor",
    "geopolit",
    "bildung",
    "educat",
    "erklär",
    "analysis",
    "analyse",
)
_RPM_LOW = (
    "meme",
    "lustig",
    "tiktok",
    "gossip",
    "promi",
    "skandal trash",
    "random",
    "kurzwitz",
)

_VIRAL_DIMS: dict[str, Tuple[str, ...]] = {
    "shock": ("schock", "ungeheuerlich", "enthüll", "skandal", "erschütter"),
    "secrecy": ("geheim", "verborgen", "klassifi", "niemand weiß", "cover-up"),
    "controversy": ("kontrovers", "hitze", "polarisier", "debatte", "skandal"),
    "transformation": ("von arm zu", "vorher nachher", "wendepunkt", "karrierehoch"),
    "money": ("million", "milliard", "gehalt", "lohn", "deal", "gewinn"),
    "danger": ("tod", "gefahr", "überleb", "krieg", "attentat", "verbrechen"),
    "exclusivity": ("exklusiv", "insider", "elite", "vip", "nur hier"),
}

_WINNER_CLUSTERS: dict[str, Tuple[str, ...]] = {
    "abandoned_wealth": ("verlassenes herrenhaus", "lost place", "verfall", "milliarden verlassen"),
    "hidden_truth": ("die wahrheit über", "enthüllt", "geheimakte", "unterdrückt"),
    "rise_fall": ("aufstieg und fall", "sturz des", "vom millionär", "bankrott"),
    "scandal": ("skandal", "affäre", "korruption", "bestech"),
    "elite_luxury": ("luxus", "elite", "superyacht", "privatjet"),
    "war_secret": ("krieg", "geheimdienst", "nato", "ukraine", "konflikt"),
    "survival": ("überleb", "rettung", "schlimmste", "dramatisch überleb"),
}


def _blob(title: str, summary: str, mode: str) -> str:
    return f"{title}\n{summary}\n{mode}".lower()


def _word_count(text: str) -> int:
    return len(re.findall(r"\w+", text or "", flags=re.UNICODE))


def estimate_rpm(blob: str) -> EstimatedRpmResult:
    hits_high = sum(1 for k in _RPM_HIGH if k in blob)
    hits_med = sum(1 for k in _RPM_MEDIUM if k in blob)
    hits_low = sum(1 for k in _RPM_LOW if k in blob)

    if hits_high >= 2 or (hits_high >= 1 and hits_low == 0):
        cat = "high"
        conf = min(95, 55 + hits_high * 15)
        reason = f"high_intent_keywords={hits_high}"
    elif hits_low >= 2 and hits_high == 0:
        cat = "low"
        conf = min(90, 50 + hits_low * 12)
        reason = f"low_intent_or_meme_signals={hits_low}"
    elif hits_med >= 1:
        cat = "medium"
        conf = min(85, 48 + hits_med * 14)
        reason = f"authority_documentary_signals={hits_med}"
    else:
        cat = "medium"
        conf = 40
        reason = "no_strong_niche_match_default_medium"

    return EstimatedRpmResult(
        estimated_rpm_category=cat,
        estimated_rpm_confidence=conf,
        niche_reasoning=reason,
    )


def snapshot_production_cost(
    blob: str,
    *,
    chapter_count: int,
    gate_status: UrlQualityStatus,
) -> ProductionCostSnapshotResult:
    wc = _word_count(blob)
    try:
        cc_in = int(chapter_count or 0)
    except (TypeError, ValueError):
        cc_in = 0
    scenes = max(3, min(24, cc_in or max(3, wc // 380)))

    legal = any(k in blob for k in ("gericht", "urteil", "anwalt", "klage", "straf"))
    war = any(k in blob for k in ("krieg", "front", "militär"))
    luxury_vis = any(k in blob for k in ("drohne", "luftaufnahme", "rekonstruktion"))

    fc_risk: FactRiskLabel = "high" if legal or war else ("medium" if wc > 900 else "low")
    vis: VisualDifficultyLabel = "high" if luxury_vis or war else ("medium" if wc > 1200 else "low")
    complexity: ComplexityLabel
    if scenes > 12 or fc_risk == "high":
        complexity = "high"
    elif scenes <= 5 and vis == "low":
        complexity = "low"
    else:
        complexity = "medium"

    tier: ProductionCostTier = "lean"
    if complexity == "high" or vis == "high" or fc_risk == "high":
        tier = "heavy"
    elif complexity == "medium" or vis == "medium":
        tier = "standard"

    if gate_status == "blocked":
        tier = "lean"
        scenes = min(scenes, 4)

    return ProductionCostSnapshotResult(
        estimated_asset_complexity=complexity,
        likely_scene_count=scenes,
        likely_fact_check_risk=fc_risk,
        likely_visual_difficulty=vis,
        production_cost_tier=tier,
    )


def score_viral_hook(blob: str) -> ViralHookScoreResult:
    scores: dict[str, int] = {}
    for dim, kws in _VIRAL_DIMS.items():
        scores[dim] = sum(10 for kw in kws if kw in blob)
    if not scores or max(scores.values()) == 0:
        return ViralHookScoreResult(
            viral_hook_score=15,
            dominant_hook_type="none",
            hook_risk_warning="",
        )
    dominant = max(scores, key=lambda k: scores[k])
    raw = min(100, sum(scores.values()))
    viral = max(20, raw)

    risk = ""
    if scores.get("controversy", 0) >= 20 or scores.get("shock", 0) >= 20:
        risk = "high_emotional_or_legal_sensitivity_review_facts"

    return ViralHookScoreResult(
        viral_hook_score=int(viral),
        dominant_hook_type=dominant,
        hook_risk_warning=risk,
    )


def detect_winner_repeat(blob: str) -> WinnerRepeatResult:
    best_cluster = "none"
    best_hits = 0
    for cluster, kws in _WINNER_CLUSTERS.items():
        h = sum(1 for kw in kws if kw in blob)
        if h > best_hits:
            best_hits = h
            best_cluster = cluster

    repeat = min(100, best_hits * 28 + (10 if best_hits else 0))
    scaling = (
        "strong_if_template_match"
        if best_hits >= 2
        else ("moderate_series_potential" if best_hits == 1 else "weak_series_signal")
    )

    return WinnerRepeatResult(
        winner_cluster=best_cluster,
        repeatability_score=repeat,
        format_scaling_potential=scaling,
    )


def _niche_value_from_rpm(rpm: EstimatedRpmResult) -> int:
    base = {"high": 82, "medium": 58, "low": 32}[rpm.estimated_rpm_category]
    adj = int((rpm.estimated_rpm_confidence - 50) * 0.2)
    return max(0, min(100, base + adj))


def _efficiency_from_cost(cost: ProductionCostSnapshotResult) -> int:
    tier_scores = {"lean": 88, "standard": 62, "heavy": 38}
    return tier_scores[cost.production_cost_tier]


def _confidence(gate: UrlQualityGateResult, wc: int) -> ConfidenceLevel:
    if gate.url_quality_status == "blocked" or wc < 80:
        return "low"
    if gate.url_quality_status == "strong" and wc >= 400:
        return "high"
    return "medium"


def _priority(roi: int) -> PriorityLevel:
    if roi >= 72:
        return "high"
    if roi >= 48:
        return "medium"
    return "low"


def build_cash_optimization_layer(
    gate: UrlQualityGateResult,
    *,
    title: str,
    rewrite_summary: str,
    chapter_count: int,
    recommended_mode: str = "",
) -> CashOptimizationLayerResult:
    """Single URL / Batch-Zeile / Watch: ein konsistenter Profit-Stack."""
    blob = _blob(title, rewrite_summary, str(recommended_mode or ""))
    rpm = estimate_rpm(blob)
    cost = snapshot_production_cost(blob, chapter_count=chapter_count, gate_status=gate.url_quality_status)
    viral = score_viral_hook(blob)
    winner = detect_winner_repeat(blob)

    hook_power = min(
        100,
        int(round(0.55 * gate.hook_potential_score + 0.45 * viral.viral_hook_score)),
    )
    narrative_strength = min(
        100,
        int(round(0.6 * gate.narrative_density_score + 0.4 * gate.emotional_weight_score)),
    )
    niche_val = _niche_value_from_rpm(rpm)
    prod_eff = _efficiency_from_cost(cost)

    value_core = 0.32 * hook_power + 0.38 * narrative_strength + 0.30 * niche_val
    cost_drag = 1.0 - (100 - prod_eff) / 150.0
    roi_raw = value_core * max(0.55, cost_drag)
    repeat_boost = min(12, winner.repeatability_score // 10)
    roi_int = int(max(0, min(100, round(roi_raw + repeat_boost * 0.35))))

    if gate.url_quality_status == "blocked":
        roi_int = min(roi_int, 22)

    ws: List[str] = []
    if gate.url_quality_status in ("weak", "moderate"):
        ws.append("url_quality_not_strong_roi_discount_possible")
    if viral.hook_risk_warning:
        ws.append(viral.hook_risk_warning)
    if rpm.estimated_rpm_category == "low":
        ws.append("low_rpm_category_time_may_exceed_yield")

    cand = CandidateRoiScoreResult(
        candidate_roi_score=roi_int,
        hook_power_score=hook_power,
        narrative_strength_score=narrative_strength,
        niche_value_score=niche_val,
        production_efficiency_score=prod_eff,
        confidence_level=_confidence(gate, _word_count(blob)),
        recommended_priority=_priority(roi_int),
        warnings=ws,
    )

    return CashOptimizationLayerResult(
        roi=cand,
        estimated_rpm=rpm,
        production_cost=cost,
        viral_hook=viral,
        winner_repeat=winner,
    )
