"""BA 10.5 — deterministische Thumbnail-CTR-Heuristik und Textvarianten (kein Bild-API)."""

from __future__ import annotations

import re
from typing import List, Tuple

from app.models import ThumbnailCTRRequest, ThumbnailCTRResponse, ThumbnailVariantSpec


def _dedupe_warnings(ws: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for w in ws or []:
        key = (w or "").strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _norm_space(s: str) -> str:
    return " ".join((s or "").split())


def _truncate(s: str, cap: int) -> str:
    t = _norm_space(s)
    if len(t) <= cap:
        return t
    return t[: cap - 1].rsplit(" ", 1)[0].strip() + "…"


def build_thumbnail_variants(
    *,
    title: str,
    hook: str,
    video_template: str,
) -> List[ThumbnailVariantSpec]:
    """Drei feste Varianten für Packaging / optimize-Response."""
    t = _truncate(title or "Video", 72)
    h = _truncate(hook or "", 96)
    tid = (video_template or "generic").strip() or "generic"
    return [
        ThumbnailVariantSpec(
            headline=_truncate(f"{t} — was dahintersteckt", 80),
            overlay_text=h or _truncate(f"Template: {tid}", 64),
            emotion_type="curiosity",
        ),
        ThumbnailVariantSpec(
            headline=_truncate(f"{t}: die wichtigsten Punkte", 80),
            overlay_text=_truncate(h or "Kontext in unter 60 Sekunden", 64),
            emotion_type="authority",
        ),
        ThumbnailVariantSpec(
            headline=_truncate(f"Jetzt: {t}", 72),
            overlay_text=_truncate(h or "Direkt zum Kern", 64),
            emotion_type="urgency",
        ),
    ]


def _ctr_heuristic_score(req: ThumbnailCTRRequest) -> Tuple[int, List[str]]:
    warns: List[str] = []
    title = (req.title or "").strip()
    hook = (req.hook or "").strip()
    tp = (req.thumbnail_prompt or "").strip()

    if not title:
        warns.append("[thumbnail_ctr] Kein Titel — CTR-Schätzung nur Platzhalter.")
        return 42, warns

    score = 52
    lt = len(title)
    if lt >= 10:
        score += 6
    if lt >= 22:
        score += 4
    if "?" in title or "？" in title:
        score += 8
    if re.search(r"\b(jetzt|heute|breaking|eilmeldung|update)\b", title, re.I):
        score += 6

    if len(hook) >= 18:
        score += 6
    if any(ch in hook for ch in ("!", "?", "…")):
        score += 4

    if len(tp) >= 120:
        score += 10
    elif len(tp) >= 60:
        score += 5

    body_chars = sum(len((c.content or "") + (c.title or "")) for c in (req.chapters or []))
    if body_chars >= 400:
        score += 6
    elif body_chars > 0:
        score += 3

    if title.lower() in hook.lower() and len(hook) > len(title) + 8:
        score += 5

    synergy = min(10, max(0, min(lt, 48) // 5))
    score += synergy

    return max(40, min(100, int(score))), warns


def build_thumbnail_ctr_report(req: ThumbnailCTRRequest) -> ThumbnailCTRResponse:
    score, w1 = _ctr_heuristic_score(req)
    variants = build_thumbnail_variants(
        title=req.title,
        hook=req.hook,
        video_template=req.video_template,
    )
    merged = _dedupe_warnings(
        w1
        + [
            "[thumbnail_ctr] Heuristik V1 — keine echte Klickvorhersage, kein Bild-API.",
        ]
    )
    return ThumbnailCTRResponse(ctr_score=score, thumbnail_variants=variants, warnings=merged)
