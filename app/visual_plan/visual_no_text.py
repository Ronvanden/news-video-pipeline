"""BA 26.4b — No-Text Guard + deterministische Text-/Overlay-Zerlegung für Bild-/Video-Prompts."""

from __future__ import annotations

import re
from typing import List, Tuple

_GUARD_MARKER = "[visual_no_text_guard_v26_4]"

NO_TEXT_GUARD_EN = (
    "No readable text, no letters, no fake UI, no documents with legible writing, "
    "no subtitles, no watermark, no logo, no typography. "
    "Leave clean empty space for later editorial text overlay."
)

NO_TEXT_GUARD_DE = (
    "Keine lesbare Schrift, keine Buchstaben, keine Fake-UI, keine Dokumenttexte, "
    "keine Untertitel, keine Wasserzeichen, keine Logos. "
    "Freie Fläche für spätere echte Text-Overlays lassen."
)


def no_text_guard_block() -> str:
    """Kompakter zweisprachiger Sicherheitsblock (ohne Marker)."""
    return f"{NO_TEXT_GUARD_EN}\n{NO_TEXT_GUARD_DE}"


def visual_no_text_guard_overhead() -> int:
    """Zeichenbudget für Zeilenumbrüche + Marker + zweisprachigen Block (ohne Kernprompt)."""
    return len("\n\n" + _GUARD_MARKER + "\n" + no_text_guard_block())


def append_no_text_guard(prompt: str) -> str:
    """Hängt den No-Text-Guard an Generator-Prompts (idempotent)."""
    raw = prompt or ""
    if _GUARD_MARKER in raw:
        return raw.strip()
    core = " ".join(raw.split())
    if not core:
        return f"{_GUARD_MARKER}\n{no_text_guard_block()}"
    return f"{core}\n\n{_GUARD_MARKER}\n{no_text_guard_block()}"


def strip_visual_no_text_guard(prompt: str) -> str:
    """Entfernt einen bereits angehängten Guard (für Zwischenverarbeitung / Re-Optimierung)."""
    raw = prompt or ""
    if _GUARD_MARKER not in raw:
        return raw.strip()
    return raw.split(_GUARD_MARKER, 1)[0].strip()


_TEXT_HINT_RE = re.compile(
    r"(?is)\b("
    r"subtitle|untertitel|lower\s*third|logo|watermark|wasserzeichen|"
    r"headline|überschrift|tickertape|ticker|fake\s*ui|screenshot|"
    r"dokumenttext|lesbare\s+schrift|text\s+einblenden|einblendtext|"
    r"typografie|caption|beschriftung"
    r")\b"
)

_QUOTED_RE = re.compile(r"«([^»]+)»|\"([^\"]{2,120})\"|\'([^\']{2,120})\'")


def _norm_space(s: str) -> str:
    return " ".join((s or "").split())


def _split_tail_items(tail: str) -> List[str]:
    tail = tail.strip()
    if not tail:
        return []
    parts = [p.strip() for p in re.split(r"[,;]|(?:\s+und\s+)", tail) if p.strip()]
    return parts


def partition_visual_overlay_text(raw: str) -> Tuple[str, List[str], bool]:
    """
    Erkennt häufige Text-/Listenabsichten und lagert konkrete Lesetexte nach ``overlay_intent`` aus.

    Returns:
        (visual_prompt_clean, overlay_intent, text_sensitive)
    """
    s = _norm_space(raw)
    if not s:
        return "", [], False

    overlay: List[str] = []
    text_sensitive = bool(_TEXT_HINT_RE.search(s))

    # Explizite Checklisten / Aufzählung nach Doppelpunkt (ohne Uhrzeiten / URLs)
    if ":" in s and "http" not in s.lower() and not re.search(r"\b\d{1,2}:\d{2}\b", s):
        left, right = s.rsplit(":", 1)
        left = left.strip()
        right = right.strip()
        left_l = left.lower()
        # Blueprint image_primary nutzt „… detail: Kapitel. Focus:“ — nicht als Overlay-Liste lesen
        blueprint_scaffold = (
            "emphasising chapter semantics" in left_l or "aligned to template" in left_l
        )
        colon_items: List[str] = []
        if not blueprint_scaffold:
            colon_items = _split_tail_items(right)
        if (
            not blueprint_scaffold
            and len(colon_items) >= 2
            and len(right) <= 420
            and all(3 <= len(it) <= 140 for it in colon_items)
            and len(left) >= 10
        ):
            overlay.extend(colon_items)
            low_left = left.lower()
            if "checkliste" in low_left or "punkten" in low_left or "punkt:" in low_left:
                visual = (
                    "Dunkle cineastische Ermittlungswand mit leeren Checkboxen, dramatisches Licht, "
                    "Platz für spätere Text-Overlays"
                )
            else:
                visual = (
                    f"{left}. Symbolische Darstellung ohne lesbare Beschriftung; "
                    "freie Fläche für spätere Editorial-Overlays"
                )
            return visual, overlay, True

    # Anführungszeichen-Inhalte auslagern
    work = s
    for m in _QUOTED_RE.finditer(s):
        chunk = next(g for g in m.groups() if g)
        chunk = chunk.strip()
        if 2 <= len(chunk) <= 160:
            overlay.append(chunk)
            work = work.replace(m.group(0), " ", 1)
    work = _norm_space(work)
    if overlay:
        text_sensitive = True
        if work:
            return f"{work}. Keine lesbare Schrift im Bild; Editorial-Text kommt im Render-Layer.", overlay, True
        return (
            "Editorial Symbolmotiv ohne Beschriftung, großzügige Freiflächen für spätere Text-Overlays.",
            overlay,
            True,
        )

    if text_sensitive:
        return (
            f"{s}. Visual ohne lesbare Schrift oder UI-Elemente; Text nur im Render-Layer.",
            overlay,
            True,
        )

    return s, [], False
