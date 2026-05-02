"""BA 9.12 — Narrative Scoring: erzählerische Zugkraft, regelbasiert (kein LLM)."""

from __future__ import annotations

import re
from typing import List, Literal, Sequence, Set, Tuple

from app.prompt_engine.schema import (
    ChapterOutlineItem,
    NarrativeScoreResult,
    NarrativeSubscores,
    ProductionPromptPlan,
)

# A) Hook Curiosity / Mystery
CURIOSITY_MARKERS = (
    "niemand",
    "bis heute",
    "geheim",
    "warum",
    "wieso",
    "plötzlich",
    "ungeklärt",
    "doch dann",
    "entdeckte",
    "entdeckt",
    "rätsel",
    "unklar",
    "verborgen",
    "was wenn",
    "wie kann",
    "jahrelang",
    "spurlos",
    "verschwand",
    "verschwunden",
    "mysteri",
)

# B) Emotional Pull
EMOTIONAL_MARKERS = (
    "verlust",
    "angst",
    "schock",
    "hoffnung",
    "tragik",
    "risiko",
    "schmerz",
    "tragödie",
    "gebrochen",
    "alarmierend",
    "bedroh",
    "hoffnungslos",
    "ängst",
    "verzweiflung",
)

# E) Thumbnail / visuelle Spannung (Blob Hook + Thumbnail + Kontext)
THUMBNAIL_MARKERS = (
    "verlassen",
    "geheim",
    "tot",
    "verschwunden",
    "luxus",
    "absturz",
    "verboten",
    "verbotene",
    "finster",
    "nacht",
    "silhouette",
    "dramatisch",
    "kontrast",
    "schatten",
)

# C) Eskalation — grobe Aktmarker je Kapitelposition
EARLY_MARKERS = (
    "einordnung",
    "kontext",
    "überblick",
    "was wir",
    "stand der",
    "rahmen",
)
MID_MARKERS = (
    "wendung",
    "jedoch",
    "plötzlich",
    "enthüll",
    "widerspruch",
    "überrasch",
    "hypothese",
    "wendepunkt",
)
LATE_MARKERS = (
    "fazit",
    "offen",
    "urteil",
    "aufklärung",
    "finale",
    "offene fragen",
    "nächste schritte",
)


def _lower(s: str) -> str:
    return (s or "").lower()


def _hit_count(blob: str, markers: Sequence[str]) -> int:
    b = _lower(blob)
    return sum(1 for m in markers if m.lower() in b)


def _tier_from_hits(hits: int, *, zero_floor: int = 15) -> int:
    """Mehr Treffer → höherer Score (gesättigt)."""
    if hits <= 0:
        return zero_floor
    if hits == 1:
        return 44
    if hits == 2:
        return 58
    if hits == 3:
        return 72
    return min(100, 72 + (hits - 3) * 9)


def _chapter_blob(ch: ChapterOutlineItem) -> str:
    return _lower(f"{ch.title} {ch.summary}")


def _token_set(text: str) -> Set[str]:
    return set(re.findall(r"\w+", _lower(text)))


def _score_hook_curiosity(plan: ProductionPromptPlan) -> int:
    hb = _lower(plan.hook or "")
    hits = _hit_count(hb, CURIOSITY_MARKERS)
    base = _tier_from_hits(hits, zero_floor=12)
    # leichte Kopplung an Hook-Engine-Score (BA 9.2), transparent eingemischt
    blend = min(10.0, max(0.0, float(plan.hook_score or 0.0)))
    adj = int(round(base * 0.82 + blend * 1.8))
    return max(0, min(100, adj))


def _score_emotional_pull(plan: ProductionPromptPlan) -> int:
    blob = _lower(plan.hook or "")
    for ch in plan.chapter_outline or []:
        blob += " " + _chapter_blob(ch)
    hits = _hit_count(blob, EMOTIONAL_MARKERS)
    return _tier_from_hits(hits, zero_floor=18)


def _score_escalation(plan: ProductionPromptPlan) -> Tuple[int, bool]:
    """Erkennt grobe Setup → Mitte → Auflösung über Marker je Positionsbereich."""
    chapters = plan.chapter_outline or []
    n = len(chapters)
    missing_arc = False
    if n == 0:
        return 5, True
    if n == 1:
        return 38, True

    first = _chapter_blob(chapters[0])
    last = _chapter_blob(chapters[-1])
    middle_parts: List[str] = []
    if n >= 3:
        for ch in chapters[1:-1]:
            middle_parts.append(_chapter_blob(ch))

    early = _hit_count(first, EARLY_MARKERS) > 0 or len(re.findall(r"\w+", first)) >= 8
    late = _hit_count(last, LATE_MARKERS) > 0 or len(re.findall(r"\w+", last)) >= 8
    mid_blob = " ".join(middle_parts)
    mid = _hit_count(mid_blob, MID_MARKERS) > 0 if middle_parts else False

    raw = 0
    if early:
        raw += 32
    if mid:
        raw += 34
    if late:
        raw += 34
    if raw == 0:
        missing_arc = True
        raw = 28 + min(22, n * 5)
    return min(100, raw), missing_arc


def _score_chapter_progression(plan: ProductionPromptPlan) -> Tuple[int, bool]:
    chapters = plan.chapter_outline or []
    if len(chapters) < 2:
        return 52, False

    titles = [c.title or "" for c in chapters]
    max_sim = 0.0
    redundant = False
    for i in range(len(titles)):
        for j in range(i + 1, len(titles)):
            a, b = _token_set(titles[i]), _token_set(titles[j])
            if not a or not b:
                continue
            sim = len(a & b) / len(a | b)
            max_sim = max(max_sim, sim)
    if max_sim >= 0.88:
        redundant = True
        return max(12, int(100 - max_sim * 95)), redundant
    if max_sim >= 0.55:
        return int(62 + (0.55 - max_sim) * 60), redundant
    return int(78 + min(22, (1.0 - max_sim) * 50)), redundant


def _score_thumbnail_potential(plan: ProductionPromptPlan) -> int:
    blob = _lower(plan.hook or "")
    blob += " " + _lower(plan.thumbnail_angle or "")
    if plan.chapter_outline:
        blob += " " + _lower(plan.chapter_outline[0].title or "")
    hits = _hit_count(blob, THUMBNAIL_MARKERS) + _hit_count(blob, CURIOSITY_MARKERS[:8])
    return _tier_from_hits(min(hits, 8), zero_floor=20)


def evaluate_narrative_score(plan: ProductionPromptPlan) -> NarrativeScoreResult:
    checked = [
        "hook_curiosity",
        "emotional_pull",
        "escalation_structure",
        "chapter_progression",
        "thumbnail_potential",
    ]

    hc = _score_hook_curiosity(plan)
    ep = _score_emotional_pull(plan)
    esc, esc_gap = _score_escalation(plan)
    prog, redundant = _score_chapter_progression(plan)
    thumb = _score_thumbnail_potential(plan)

    sub = NarrativeSubscores(
        hook_curiosity_score=hc,
        emotional_pull_score=ep,
        escalation_score=esc,
        chapter_progression_score=prog,
        thumbnail_potential_score=thumb,
    )

    overall = int(round((hc + ep + esc + prog + thumb) / 5.0))
    if overall >= 80:
        status: Literal["strong", "moderate", "weak"] = "strong"
    elif overall >= 50:
        status = "moderate"
    else:
        status = "weak"

    strengths: List[str] = []
    weaknesses: List[str] = []

    if hc >= 70:
        strengths.append("Hook transportiert Neugier-/Mystery-Signale (Keyword-Heuristik).")
    elif hc < 42:
        weaknesses.append("Hook wirkt keyword-arm für Mystery/Curiosity — Retention-Risiko.")

    if ep >= 68:
        strengths.append("Emotionale Anker (Verlust/Angst/Hoffnung etc.) erkennbar.")
    elif ep < 45:
        weaknesses.append("Emotionaler Zug gering — stärkeren menschlichen Kern einbauen.")

    if esc >= 68:
        strengths.append("Kapitelmarker deuten auf Setup/Mitte/Auflösung hin.")
    elif esc < 48 or esc_gap:
        weaknesses.append("Eskalationsbogen schwer erkennbar — klare Wendepunkte schärfen.")

    if prog >= 72:
        strengths.append("Kapiteltitel wirken differenziert (Progression).")
    elif redundant or prog < 45:
        weaknesses.append("Kapitel wirken redundant oder zu ähnlich — Titel/Summaries differenzieren.")

    if thumb >= 65:
        strengths.append("Thumbnail-Potenzial (visuelle/spannungs-Stichworte) vorhanden.")
    elif thumb < 45:
        weaknesses.append("Thumbnail-Winkel und Hook liefern wenig visuelle Spannung.")

    return NarrativeScoreResult(
        score=overall,
        status=status,
        subscores=sub,
        strengths=strengths,
        weaknesses=weaknesses,
        checked_dimensions=checked,
    )
