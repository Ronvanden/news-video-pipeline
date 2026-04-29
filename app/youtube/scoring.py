"""Heuristische Bewertung der RSS-Einträge (kein Transkript, keine API)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Tuple

_FILLER_WORDS = frozenset(
    {
        "official",
        "video",
        "trailer",
        "live",
        "stream",
        "hd",
        "4k",
        "new",
        "neu",
        "full",
        "episode",
        "part",
        "teaser",
        "clip",
    }
)


def _parse_published_iso(published_at: str) -> datetime | None:
    if not published_at:
        return None
    s = published_at.strip()
    try:
        if s.endswith("Z"):
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _recency_points(published_at: str) -> Tuple[int, str]:
    dt = _parse_published_iso(published_at)
    if dt is None:
        return 5, "Veröffentlichungszeit nicht parsebar"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = now - dt
    days = max(0.0, delta.total_seconds() / 86400.0)
    if days <= 1:
        return 35, "sehr aktuell (≤1 Tag)"
    if days <= 7:
        return 28, "aktuell (≤7 Tage)"
    if days <= 30:
        return 20, "relativ aktuell (≤30 Tage)"
    if days <= 90:
        return 12, "älter (≤90 Tage)"
    return 5, "nicht mehr frisch (>90 Tage)"


def _title_word_tokens(title: str) -> list[str]:
    return [w for w in re.findall(r"[\wäöüÄÖÜß]+", title, flags=re.UNICODE) if len(w) > 1]


def _topic_clarity_points(title: str) -> Tuple[int, str]:
    t = (title or "").strip()
    if not t:
        return 0, "leerer Titel"
    words = _title_word_tokens(t)
    n = len(words)
    if n <= 2:
        return 8, "sehr kurzer Titel, Thema wenig erklärbar"
    if n <= 4:
        return 18, "kurzer Titel"
    if n <= 12:
        substantive = sum(1 for w in words if w.lower() not in _FILLER_WORDS)
        if substantive >= 3:
            return 30, "klarer, erklärbarer Titel"
        return 22, "mittlere Titelqualität"
    return 24, "langer Titel, Fokus evtl. diffus"


def _shorts_and_noise_penalty(title: str, duration_seconds: int | None) -> Tuple[int, str]:
    reasons: list[str] = []
    penalty = 0
    low = (title or "").lower()
    if "#shorts" in low or "shorts" == low.strip():
        penalty += 25
        reasons.append("Shorts-Hinweis im Titel")
    if duration_seconds is not None and duration_seconds > 0 and duration_seconds < 60:
        penalty += 20
        reasons.append("sehr kurze Laufzeit (<60s)")
    if len((title or "").strip()) < 8:
        penalty += 12
        reasons.append("Titel sehr knapp")
    if re.search(r"^[^a-zA-ZäöüÄÖÜß0-9]+", (title or "").strip()):
        penalty += 5
        reasons.append("Titel beginnt mit Symbolen")
    detail = "; ".join(reasons) if reasons else "keine Shorts-/Kürze-Abzüge"
    return penalty, detail


def build_summary_from_title(title: str) -> str:
    """Kurzbeschreibung aus Metadaten (Titel), ohne 1:1-Wiedergabe."""
    words = _title_word_tokens(title)
    if not words:
        return "Keine ausreichenden Wörter im Titel für eine thematische Kurzbeschreibung."
    seen: set[str] = set()
    keywords: list[str] = []
    for w in words:
        wl = w.lower()
        if wl in _FILLER_WORDS:
            continue
        if wl in seen:
            continue
        seen.add(wl)
        keywords.append(w)
        if len(keywords) >= 5:
            break
    if not keywords:
        keywords = words[:4]
    return "Schwerpunkt laut Metadaten (Stichworte): " + ", ".join(keywords) + "."


def score_video(
    title: str,
    published_at: str,
    duration_seconds: int | None,
) -> Tuple[int, str]:
    r_pts, r_note = _recency_points(published_at)
    t_pts, t_note = _topic_clarity_points(title)
    pen, p_note = _shorts_and_noise_penalty(title, duration_seconds)
    raw = r_pts + t_pts - pen
    score = max(0, min(100, raw))
    reason = (
        f"Aktualität: {r_note} ({r_pts} Punkte). "
        f"Thema: {t_note} ({t_pts} Punkte). "
        f"Anpassungen: {p_note} (−{pen}). "
        f"Gesamt {score}/100."
    )
    return score, reason
