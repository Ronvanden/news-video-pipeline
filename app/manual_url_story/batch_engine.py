"""BA 15.8 — Batch-URL-Analyse: nur run_manual_url_rewrite_phase, kein voller PromptPlan."""

from __future__ import annotations

import uuid
from typing import Iterable, List, Sequence
from urllib.parse import urlparse

from app.cash_optimization.layer import build_cash_optimization_layer
from app.manual_url_story.schema import BatchUrlItemResult, BatchUrlRunResult, UrlQualityStatus

_STATUS_RANK: dict[UrlQualityStatus, int] = {
    "blocked": 0,
    "weak": 1,
    "moderate": 2,
    "strong": 3,
}


def normalize_url_duplicate_key(url: str) -> str:
    """Light Duplicate-Guard: Schema + Host + Pfad, Query gestrichen."""
    raw = (url or "").strip()
    p = urlparse(raw.split("#", 1)[0])
    if not p.netloc:
        return raw.lower()
    path = (p.path or "").rstrip("/").lower()
    return f"{(p.scheme or 'https').lower()}://{p.netloc.lower()}{path}"


def _dedupe_urls(urls: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for raw in urls:
        u = (raw or "").strip()
        if not u:
            continue
        key = normalize_url_duplicate_key(u)
        if key in seen:
            continue
        seen.add(key)
        out.append(u)
    return out


def run_batch_url_demo(
    urls: Sequence[str],
    *,
    topic_placeholder: str = "Batch URL Run",
    manual_url_rewrite_mode: str = "",
    manual_url_duration_minutes: int = 10,
    manual_url_target_language: str = "de",
    manual_url_video_template: str = "generic",
    manual_url_template_conformance_level: str = "warn",
    top_n: int = 5,
) -> BatchUrlRunResult:
    """Pro URL nur Rewrite-Phase + Quality Gate (wie Manual URL Engine), ohne Pipeline-Suites."""
    from app.prompt_engine.schema import PromptPlanRequest

    rewrite_phase = _get_manual_url_rewrite_phase()
    clean = _dedupe_urls(urls)
    items: List[BatchUrlItemResult] = []

    for url in clean:
        rid = str(uuid.uuid4())
        req = PromptPlanRequest(
            topic=topic_placeholder[:120] or "Batch",
            title="",
            source_summary="",
            manual_source_url=url,
            manual_url_rewrite_mode=(manual_url_rewrite_mode or "").strip(),
            manual_url_duration_minutes=int(manual_url_duration_minutes),
            manual_url_target_language=manual_url_target_language,
            manual_url_video_template=manual_url_video_template,
            manual_url_template_conformance_level=manual_url_template_conformance_level,
        )
        outcome, gate = rewrite_phase(req)
        if gate is None:
            continue

        summary = ""
        title = ""
        if outcome:
            title = (outcome.script_title or outcome.effective_title or "").strip()
            summary = (outcome.full_script_preview or "").strip()
            if not summary and outcome.effective_source_summary:
                summary = outcome.effective_source_summary[:480]

        try:
            cc = int(getattr(outcome, "chapter_count", 0) or 0)
        except (TypeError, ValueError):
            cc = 0
        cash_layer = build_cash_optimization_layer(
            gate,
            title=title,
            rewrite_summary=summary,
            chapter_count=cc,
            recommended_mode=str(req.manual_url_rewrite_mode or gate.recommended_mode),
        )

        items.append(
            BatchUrlItemResult(
                source_url=url,
                title=title,
                url_quality_status=gate.url_quality_status,
                hook_potential_score=gate.hook_potential_score,
                recommended_mode=gate.recommended_mode,
                rewrite_summary=summary,
                local_run_id=rid,
                cash_layer=cash_layer,
            )
        )

    def sort_key(it: BatchUrlItemResult) -> tuple[int, int, int, str]:
        roi = it.cash_layer.roi.candidate_roi_score if it.cash_layer else 0
        return (_STATUS_RANK[it.url_quality_status], roi, it.hook_potential_score, it.source_url)

    ranked = sorted(items, key=sort_key, reverse=True)
    ranked_urls = [r.source_url for r in ranked]
    profit_ranked = sorted(
        ranked,
        key=lambda it: (
            it.cash_layer.roi.candidate_roi_score if it.cash_layer else 0,
            _STATUS_RANK[it.url_quality_status],
        ),
        reverse=True,
    )
    profit_ranked_urls = [r.source_url for r in profit_ranked]
    blocked_urls = [r.source_url for r in ranked if r.url_quality_status == "blocked"]
    top_candidates = [r.source_url for r in ranked if r.url_quality_status != "blocked"][
        : max(0, int(top_n))
    ]

    return BatchUrlRunResult(
        items=ranked,
        ranked_urls=ranked_urls,
        profit_ranked_urls=profit_ranked_urls,
        top_candidates=top_candidates,
        blocked_urls=blocked_urls,
    )


def parse_urls_file_lines(text: str) -> List[str]:
    """Eine URL pro Zeile; Leerzeilen und #‑Kommentare ignorieren."""
    out: List[str] = []
    for line in (text or "").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out


def _get_manual_url_rewrite_phase():
    """Test-Hook / lazy bound um Import-Zyklen zu vermeiden."""
    from app.manual_url_story.engine import run_manual_url_rewrite_phase

    return run_manual_url_rewrite_phase
