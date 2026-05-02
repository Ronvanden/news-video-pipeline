"""BA 15.7 — Heuristisches URL-Quality-Gate (ohne externe API)."""

from __future__ import annotations

import re
from typing import List

from app.manual_url_story.schema import RecommendedRewriteMode, UrlQualityGateResult, UrlQualityStatus

_EMOTIONAL_DE = (
    "tragisch",
    "schock",
    "emotion",
    "tränen",
    "familie",
    "liebe",
    "verlust",
    "angst",
    "dramatisch",
    "hart",
    "unvergesslich",
)

_MYSTERY_DE = (
    "warum",
    "wieso",
    "rätsel",
    "geheimnis",
    "unklar",
    "spur",
    "niemand weiß",
    "verschwunden",
)

_VIRAL_DE = (
    "jetzt",
    "nie",
    "das musst",
    "ungeheuerlich",
    "skandal",
    "breaking",
)


def _word_count(text: str) -> int:
    if not (text or "").strip():
        return 0
    return len(re.findall(r"\w+", text, flags=re.UNICODE))


def _sentence_count(text: str) -> int:
    parts = [p.strip() for p in re.split(r"[.!?]+", text) if p.strip()]
    return max(1, len(parts))


def build_url_quality_gate_result(
    *,
    extraction_ok: bool,
    extracted_text: str,
    narrative_ok: bool,
    script_title: str,
    full_script: str,
    chapter_count: int,
) -> UrlQualityGateResult:
    blocking: List[str] = []
    warnings: List[str] = []

    if not extraction_ok:
        return UrlQualityGateResult(
            gate_version="15.7-v1",
            url_quality_status="blocked",
            hook_potential_score=0,
            narrative_density_score=0,
            emotional_weight_score=0,
            recommended_mode="documentary",
            warnings=[],
            blocking_reasons=["extraction_failed_or_empty"],
        )

    blob = (extracted_text or "").lower()
    ew = _word_count(extracted_text)
    sc = _sentence_count(extracted_text)
    wps = ew / float(sc)

    # Narrativdichte 0–100 (Wörter/Satz + Rohertrag)
    density_raw = min(100.0, (wps / 25.0) * 55.0 + min(45.0, ew / 80.0))
    narrative_density_score = int(max(0, min(100, round(density_raw))))

    hook_potential = 38
    if "?" in extracted_text:
        hook_potential += 18
    if re.search(r"\d", extracted_text):
        hook_potential += 10
    if 400 <= ew <= 4000:
        hook_potential += 18
    elif ew < 250:
        hook_potential -= 28
    if (script_title or "").strip():
        hook_potential += 8
    if narrative_ok and chapter_count >= 3:
        hook_potential += 12
    hook_potential_score = int(max(0, min(100, hook_potential)))

    emotional_weight_score = int(
        min(100, sum(14 for k in _EMOTIONAL_DE if k in blob))
    )

    recommended_mode: RecommendedRewriteMode = "documentary"
    if any(k in blob for k in _MYSTERY_DE):
        recommended_mode = "mystery"
    elif emotional_weight_score >= 42:
        recommended_mode = "emotional"
    elif any(k in blob for k in _VIRAL_DE) or ew < 900:
        recommended_mode = "viral"

    # Gesamtstatus
    url_quality_status: UrlQualityStatus
    if ew < 120:
        url_quality_status = "blocked"
        blocking.append("extract_word_count_too_low")
    elif ew < 280 or sc < 3:
        url_quality_status = "weak"
        warnings.append("url_quality_weak_extract_short_or_few_sentences")
    elif narrative_density_score < 38 or hook_potential_score < 35:
        url_quality_status = "moderate"
        warnings.append("url_quality_moderate_density_or_hook_signal")
    else:
        url_quality_status = "strong"

    if url_quality_status in ("weak", "moderate"):
        warnings.append(
            f"url_quality_recommended_rewrite_mode={recommended_mode} "
            "(heuristisch, keine Pflicht)"
        )

    return UrlQualityGateResult(
        gate_version="15.7-v1",
        url_quality_status=url_quality_status,
        hook_potential_score=hook_potential_score,
        narrative_density_score=narrative_density_score,
        emotional_weight_score=emotional_weight_score,
        recommended_mode=recommended_mode,
        warnings=warnings,
        blocking_reasons=blocking,
    )
