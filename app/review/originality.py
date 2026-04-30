"""
Local heuristics for script originality vs. source text. No external ML libraries.
"""

from __future__ import annotations

import re
import unicodedata
from typing import List, Tuple

from app.models import (
    ReviewIssue,
    ReviewRecommendation,
    ReviewScriptRequest,
    ReviewScriptResponse,
    SimilarityFlag,
)
from app.story_engine.templates import normalize_story_template_id

# Tunable V1 thresholds
NGRAM_N = 5
LONG_RUN_MIN_WORDS = 12
SENTENCE_JACCARD_HIGH = 0.75
SHORT_SOURCE_MAX_WORDS = 30
YOUTUBE_NGRAM_STRICT_FACTOR = 1.12
YOUTUBE_RUN_STRICT = 10  # flag runs >= this many words (stricter than 12 for news)

_FRAMING_TERMS = (
    "einordnung",
    "kontext",
    "bedeutet",
    "warum",
    "kritisch",
    "offen bleibt",
    "zusammenhang",
    "ausblick",
    "entscheidend",
    "praktisch heißt",
    "hintergrund",
    "fazit",
)

_WARN_SHORT_SOURCE = "Source text is short; originality review is limited."
_WARN_YOUTUBE_STRICT = "YouTube transcript source: stricter originality review applied."
_WARN_LLM_V1 = "LLM qualitative review is not enabled in V1; heuristic review only."


def normalize_text(text: str) -> str:
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)
    t = t.lower()
    t = re.sub(r"[^\w\säöüß]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def tokenize_words(text: str) -> List[str]:
    if not text:
        return []
    return [w for w in normalize_text(text).split() if w]


def split_sentences(text: str) -> List[str]:
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p and p.strip()]


def corpus_token_jaccard(source_text: str, generated_script: str) -> float:
    """Share of distinct tokens overlapping between whole source and whole script (0–1)."""
    a = set(tokenize_words(source_text))
    b = set(tokenize_words(generated_script))
    if not a and not b:
        return 0.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def calculate_ngram_overlap(
    source_text: str, generated_script: str, n: int = NGRAM_N
) -> float:
    sw = tokenize_words(source_text)
    gw = tokenize_words(generated_script)
    if len(gw) < n:
        return 0.0
    source_ngrams: set[tuple[str, ...]] = set()
    for i in range(max(0, len(sw) - n + 1)):
        source_ngrams.add(tuple(sw[i : i + n]))
    if not source_ngrams:
        return 0.0
    hits = 0
    total = 0
    for i in range(len(gw) - n + 1):
        total += 1
        if tuple(gw[i : i + n]) in source_ngrams:
            hits += 1
    return hits / total if total else 0.0


def find_long_common_runs(
    source_text: str, generated_script: str
) -> Tuple[int, str]:
    """
    Longest common contiguous word run between source and generated.
    Returns (max_length, short evidence_hint or "").
    """
    sw = tokenize_words(source_text)
    gw = tokenize_words(generated_script)
    max_run = 0
    best_i = 0
    for i in range(len(gw)):
        for j in range(len(sw)):
            k = 0
            while (
                i + k < len(gw)
                and j + k < len(sw)
                and gw[i + k] == sw[j + k]
            ):
                k += 1
            if k > max_run:
                max_run = k
                best_i = i
    hint = ""
    if max_run >= LONG_RUN_MIN_WORDS:
        snippet_words = gw[best_i : best_i + min(6, max_run)]
        snippet = " ".join(snippet_words)
        if len(snippet) > 70:
            snippet = snippet[:67].rstrip() + "…"
        hint = f"~{max_run} consecutive words overlap source; excerpt: {snippet!r}"
    return max_run, hint


def sentence_similarity_flags(
    source_text: str,
    generated_script: str,
    threshold: float = SENTENCE_JACCARD_HIGH,
) -> Tuple[List[SimilarityFlag], int]:
    src_sents = [s for s in split_sentences(source_text) if s.strip()]
    gen_sents = [s for s in split_sentences(generated_script) if s.strip()]
    flags: List[SimilarityFlag] = []
    high_count = 0
    for gi, g in enumerate(gen_sents):
        gw_set = set(tokenize_words(g))
        if not gw_set:
            continue
        best = 0.0
        for s in src_sents:
            sw_set = set(tokenize_words(s))
            if not sw_set:
                continue
            inter = len(gw_set & sw_set)
            union = len(gw_set | sw_set)
            jacc = inter / union if union else 0.0
            best = max(best, jacc)
        if best >= threshold:
            high_count += 1
            flags.append(
                SimilarityFlag(
                    flag_type="high_sentence_similarity",
                    severity="warning",
                    detail=(
                        f"Generated sentence #{gi + 1} has high token overlap "
                        f"with source (Jaccard ~{best:.2f})."
                    ),
                    evidence_hint=None,
                )
            )
    return flags, high_count


def detect_editorial_framing(generated_script: str) -> bool:
    low = (generated_script or "").lower()
    return any(term in low for term in _FRAMING_TERMS)


def _clamp_score(x: float) -> int:
    return int(max(0, min(100, round(x))))


def analyze_originality(request: ReviewScriptRequest) -> ReviewScriptResponse:
    warnings: List[str] = list(request.prior_warnings or [])
    warnings.append(_WARN_LLM_V1)

    flags: List[SimilarityFlag] = []
    issues: List[ReviewIssue] = []
    recommendations: List[ReviewRecommendation] = []

    src_raw = request.source_text or ""
    gen_raw = request.generated_script or ""
    src_stripped = src_raw.strip()
    gen_stripped = gen_raw.strip()

    if not gen_stripped:
        warnings.append("Generated script is empty; originality risk is treated as high.")
        issues.append(
            ReviewIssue(
                severity="critical",
                code="empty_script",
                message="No generated script text to review.",
                evidence_hint=None,
            )
        )
        recommendations.append(
            ReviewRecommendation(
                priority="high",
                action="Provide non-empty generated_script before production.",
                rationale="Review cannot assess originality without script content.",
            )
        )
        return ReviewScriptResponse(
            risk_level="high",
            originality_score=0,
            similarity_flags=flags,
            issues=issues,
            recommendations=recommendations,
            warnings=warnings,
        )

    is_youtube = request.source_type == "youtube_transcript"
    if is_youtube:
        warnings.append(_WARN_YOUTUBE_STRICT)

    src_words = tokenize_words(src_raw)
    if len(src_words) < SHORT_SOURCE_MAX_WORDS and src_stripped:
        warnings.append(_WARN_SHORT_SOURCE)

    norm_src = normalize_text(src_raw)
    norm_gen = normalize_text(gen_raw)
    near_identical = bool(norm_src and norm_src == norm_gen)

    ngram_overlap = (
        calculate_ngram_overlap(src_raw, gen_raw, NGRAM_N) if src_stripped else 0.0
    )
    trigram_overlap = (
        calculate_ngram_overlap(src_raw, gen_raw, 3) if src_stripped else 0.0
    )
    token_jaccard = corpus_token_jaccard(src_raw, gen_raw) if src_stripped else 0.0
    max_run, run_hint = (
        find_long_common_runs(src_raw, gen_raw) if src_stripped else (0, "")
    )

    sent_flags, high_sent_count = (
        sentence_similarity_flags(src_raw, gen_raw) if src_stripped else ([], 0)
    )
    flags.extend(sent_flags)

    if token_jaccard >= 0.35 and src_stripped and not near_identical:
        flags.append(
            SimilarityFlag(
                flag_type="high_token_jaccard",
                severity="warning",
                detail=(
                    "Distinct-token overlap between source and script is elevated "
                    f"(Jaccard ~{token_jaccard:.2f})."
                ),
                evidence_hint=None,
            )
        )

    if run_hint:
        run_severity = "critical" if max_run >= 18 else "warning"
        flags.append(
            SimilarityFlag(
                flag_type="long_common_word_run",
                severity=run_severity,
                detail=f"Long contiguous overlap: {max_run} words.",
                evidence_hint=run_hint[:200] if run_hint else None,
            )
        )

    if near_identical:
        flags.append(
            SimilarityFlag(
                flag_type="near_identical_text",
                severity="critical",
                detail="Normalized source and generated text are identical.",
                evidence_hint=None,
            )
        )
        issues.append(
            ReviewIssue(
                severity="critical",
                code="identical_to_source",
                message="Script matches source after normalization; treat as high risk.",
                evidence_hint=None,
            )
        )

    framing = detect_editorial_framing(gen_raw)

    # Score: start 100, subtract signals
    score = 100.0
    yt_factor = YOUTUBE_NGRAM_STRICT_FACTOR if is_youtube else 1.0
    score -= ngram_overlap * 58.0 * yt_factor
    score -= trigram_overlap * 28.0 * yt_factor
    score -= token_jaccard * 82.0 * yt_factor

    run_threshold = YOUTUBE_RUN_STRICT if is_youtube else LONG_RUN_MIN_WORDS
    if max_run >= run_threshold:
        score -= min(45.0, 12.0 + (max_run - run_threshold) * 2.5)

    score -= min(40.0, high_sent_count * 9.0)

    if is_youtube and (ngram_overlap > 0.12 or max_run >= 8):
        score -= 10.0

    if framing:
        score += 7.0

    if near_identical:
        score = min(score, 8.0)

    if not src_stripped:
        warnings.append("Source text missing; overlap metrics are unavailable.")
        score = min(score, 72.0)
        issues.append(
            ReviewIssue(
                severity="info",
                code="no_source_text",
                message="Without source_text, similarity to the original cannot be computed.",
                evidence_hint=None,
            )
        )
        recommendations.append(
            ReviewRecommendation(
                priority="medium",
                action="Re-run review with the original source text.",
                rationale="Heuristic review needs source text for overlap checks.",
            )
        )

    originality_score = _clamp_score(score)

    # Risk level from score + hard overrides
    if near_identical or max_run >= 22 or (ngram_overlap >= 0.55 and src_stripped):
        risk_level = "high"
    elif token_jaccard >= 0.45 and src_stripped:
        risk_level = "high"
    elif originality_score < 38 or max_run >= LONG_RUN_MIN_WORDS:
        risk_level = "high"
    elif (
        originality_score < 62
        or ngram_overlap >= 0.28
        or high_sent_count >= 3
        or (token_jaccard >= 0.28 and src_stripped)
    ):
        risk_level = "medium"
    else:
        risk_level = "low"

    if is_youtube and risk_level == "low" and (ngram_overlap > 0.18 or max_run >= 9):
        risk_level = "medium"

    if not src_stripped:
        risk_level = "medium" if risk_level == "low" else risk_level

    # Issues for strong overlap without identical
    if (
        not near_identical
        and src_stripped
        and ngram_overlap >= 0.42
        and not any(i.code == "identical_to_source" for i in issues)
    ):
        issues.append(
            ReviewIssue(
                severity="warning",
                code="high_ngram_overlap",
                message="Large share of generated n-grams appears verbatim in the source.",
                evidence_hint=f"ngram_overlap≈{ngram_overlap:.2f}",
            )
        )

    if high_sent_count >= 2 and not near_identical:
        issues.append(
            ReviewIssue(
                severity="warning",
                code="multiple_similar_sentences",
                message="Several generated sentences closely match source sentences.",
                evidence_hint=f"count={high_sent_count}",
            )
        )

    # Recommendations
    if near_identical or ngram_overlap > 0.35 or max_run >= LONG_RUN_MIN_WORDS:
        recommendations.append(
            ReviewRecommendation(
                priority="high",
                action="Rewrite overlapping sections in new words and sentence structure.",
                rationale="Long verbatim stretches or high n-gram overlap increase republication risk.",
            )
        )
    if high_sent_count:
        recommendations.append(
            ReviewRecommendation(
                priority="medium",
                action="Paraphrase sentences flagged as highly similar to the source.",
                rationale="Per-sentence overlap suggests close copying rather than new framing.",
            )
        )
    if is_youtube and risk_level != "low":
        recommendations.append(
            ReviewRecommendation(
                priority="medium",
                action="Add distinct commentary, structure, and transitions beyond the transcript.",
                rationale="Transcript-based sources warrant extra distance from spoken wording.",
            )
        )
    if framing and risk_level == "low":
        recommendations.append(
            ReviewRecommendation(
                priority="low",
                action="Keep editorial framing visible in the final edit.",
                rationale="Explicit context/analysis signals independent editorial work.",
            )
        )
    if not recommendations:
        recommendations.append(
            ReviewRecommendation(
                priority="low",
                action="Spot-check flagged metrics before voiceover or publishing prep.",
                rationale="Heuristics can miss nuanced copying; human review remains important.",
            )
        )

    tid, tpl_ws = normalize_story_template_id(request.video_template)
    for twi in tpl_ws:
        if twi not in warnings:
            warnings.append(twi)
    if tid == "true_crime":
        recommendations.append(
            ReviewRecommendation(
                priority="medium",
                action=(
                    "True-Crime-Format: Sensibles und Betroffene respektvoll behandeln; "
                    "auf Sensationsgrad achten; keine Schuldzuweisungen ohne belastbare Fakten."
                ),
                rationale="video_template=true_crime — redaktionelle Zusatzprüfung.",
            )
        )
    elif tid == "mystery_explainer":
        recommendations.append(
            ReviewRecommendation(
                priority="low",
                action=(
                    "Mystery-/Erklärformat: Ungewissheit kennzeichnen; "
                    "keine Verschwörungsnarrative als gesicherte Fakten verkaufen."
                ),
                rationale="video_template=mystery_explainer.",
            )
        )
    elif tid == "history_deep_dive":
        recommendations.append(
            ReviewRecommendation(
                priority="low",
                action=(
                    "Geschichtsformat: zeitliche Einordnung und Quellenlage prüfen; "
                    "keine modernen Wertungen ohne Kontext als Fakten formulieren."
                ),
                rationale="video_template=history_deep_dive.",
            )
        )

    return ReviewScriptResponse(
        risk_level=risk_level,
        originality_score=originality_score,
        similarity_flags=flags,
        issues=issues,
        recommendations=recommendations,
        warnings=warnings,
    )
