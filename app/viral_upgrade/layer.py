"""BA 17.0 — Heuristische Viral-/CTR-Verpackung aus Plan + Rewrite-Text (advisory)."""

from __future__ import annotations

import re
from typing import List, Tuple

from app.prompt_engine.schema import ProductionPromptPlan
from app.viral_upgrade.schema import AudienceMode, EmotionalDriver, ViralUpgradeLayerResult

_SENSATIONAL = (
    "schock",
    "skandal",
    "explosiv",
    "irre",
    "wahnsinn",
    "unfassbar",
    "zerstört",
    "massaker",
)
_ABSOLUTE = (
    "garantiert",
    "100%",
    "hundertprozentig",
    "beweist",
    "unbestreitbar",
    "alle wissen",
)
_URGENCY = ("jetzt", "sofort", "eilt", "breaking", "live", "update")
_CONCERN = ("krise", "warnung", "gefahr", "risiko", "absturz", "einbruch")
_HOPE = ("chance", "lösung", "hoffnung", "erfolg", "rettung", "durchbruch")
_SURPRISE = ("plötzlich", "überraschend", "niemand erwartet", "unglaublich")


def _rewrite_blob(plan: ProductionPromptPlan) -> Tuple[str, str]:
    """(lowercase blob für Keywords, basis_titel für Varianten)."""
    parts: List[str] = [plan.hook or "", plan.template_type or ""]
    base_title = ""
    mu = plan.manual_url_story_execution_result
    if mu is not None:
        nr = mu.narrative_rewrite
        if (nr.script_title or "").strip():
            base_title = nr.script_title.strip()
        prev = (nr.full_script_preview or "").strip()
        if prev:
            parts.insert(0, prev[:800])
    for ch in plan.chapter_outline[:6]:
        parts.append(ch.title or "")
        parts.append((ch.summary or "")[:240])
    if not base_title and plan.chapter_outline:
        base_title = (plan.chapter_outline[0].title or "").strip()
    if not base_title:
        base_title = "Thema"
    blob = " ".join(p for p in parts if p).lower()
    return blob, base_title[:120]


def _clip(s: str, n: int) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    cut = s[: n - 1].rsplit(" ", 1)[0]
    return (cut or s[:n]) + "…"


def _title_variants(base_title: str, template_type: str) -> List[str]:
    b = _clip(base_title, 72)
    v1 = b
    v2 = f"Was {_clip(base_title, 48)} wirklich bedeutet"
    if template_type == "true_crime":
        v3 = f"{_clip(base_title, 44)}: Fakten, die zählen"
    else:
        v3 = f"{_clip(base_title, 44)} — 3 Punkte, die ihr kennen solltet"
    return [v1, v2, v3]


def _hook_intensity(plan: ProductionPromptPlan) -> int:
    h = (plan.hook or "").strip()
    score = 38
    score += min(28, max(0, len(h) // 4))
    score += int(min(10.0, plan.hook_score) * 2)
    if "?" in h:
        score += 12
    if any(c in h for c in ("!", "—", "…")):
        score += 5
    if re.search(r"\b(du|ihr|wir)\b", h, re.I):
        score += 4
    return max(0, min(100, score))


def _thumbnail_variants(plan: ProductionPromptPlan) -> List[str]:
    base = (plan.thumbnail_angle or "").strip() or "Klarer Bildausschnitt, hohe Lesbarkeit"
    return [
        f"{base} — starkes Kontrast-Key-Visual, maximal 5 Wörter Overlay",
        "Nahaufnahme Emotion oder Symbol + kurzer Claim, YouTube-Kleinformat testen",
        "Split: Fakt/Chart links, Kontext rechts; keine explizite Gewalt",
    ]


def _emotional_driver(blob: str) -> EmotionalDriver:
    if any(w in blob for w in _URGENCY):
        return "urgency"
    if any(w in blob for w in _CONCERN):
        return "concern"
    if any(w in blob for w in _HOPE):
        return "hope"
    if any(w in blob for w in _SURPRISE):
        return "surprise"
    if any(w in blob for w in _SENSATIONAL):
        return "surprise"
    if "?" in blob or "warum" in blob or "wieso" in blob:
        return "curiosity"
    return "neutral"


def _audience_mode(template_type: str, blob: str) -> AudienceMode:
    if template_type in ("documentary", "public_interest"):
        return "news_literate" if any(w in blob for w in ("studie", "daten", "analyse", "eu", "gesetz")) else "general_public"
    if template_type == "mystery_history":
        return "niche_insider"
    return "mixed"


def _caution_flags(blob: str, hook: str) -> List[str]:
    flags: List[str] = []
    if any(w in blob for w in _SENSATIONAL):
        flags.append("sensational_language_detected")
    if any(w in blob for w in _ABSOLUTE) or any(w in hook.lower() for w in _ABSOLUTE):
        flags.append("absolute_claim_risk")
    if len(blob) < 140:
        flags.append("thin_story_signal_low_context")
    return flags


def build_viral_upgrade_layer(plan: ProductionPromptPlan) -> ViralUpgradeLayerResult:
    blob, base_title = _rewrite_blob(plan)
    titles = _title_variants(base_title, plan.template_type or "")
    thumbs = _thumbnail_variants(plan)
    driver = _emotional_driver(blob + " " + (plan.hook or "").lower())
    audience = _audience_mode(plan.template_type or "", blob)
    cautions = _caution_flags(blob, plan.hook or "")
    signals = [
        "manual_url_preview" if plan.manual_url_story_execution_result else "topic_chapters_only",
        f"template={plan.template_type or 'unknown'}",
        f"hook_len={len((plan.hook or '').strip())}",
    ]
    note = (
        "Advisory-only: Titel/Thumbnails sind Heuristiken für CTR/Retention — "
        "Fakten nicht verschärfen, redaktionell gegen Quelle prüfen."
    )
    return ViralUpgradeLayerResult(
        viral_title_variants=titles,
        hook_intensity_score=_hook_intensity(plan),
        thumbnail_angle_variants=thumbs,
        emotional_driver=driver,
        audience_mode=audience,
        caution_flags=cautions,
        founder_note=note,
        checked_signals=signals,
    )
