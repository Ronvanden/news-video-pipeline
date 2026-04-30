"""BA 9.x — Template-Conformance als warnings (+ BA 9.3 strict Gate für Persistenz)."""

from __future__ import annotations

import re
from typing import Any, List, Literal, Optional, Tuple

from app.models import TemplateConformanceLevelLiteral
from app.story_engine.templates import (
    chapter_band_for_template_duration,
    min_hook_words_for_template,
    normalize_story_template_id,
)


def template_conformance_warning(code: str, detail: str) -> str:
    """Einheitliches Präfix für Log und UI (nur String in warnings)."""
    c = (code or "general").strip().replace("]", "").replace("[", "")
    return f"[template_conformance:{c}] {detail.strip()}"


def template_strict_gate_warning_failed() -> str:
    """Sichtbare Markierung bei strict Gate failed ( weiterhin nur List[str] in warnings)."""
    return (
        "[template_strict:gate_failed] Template conformance gate failed "
        "(schwere Blueprint-Abweichung siehe template_conformance-Hinweise oben)."
    )


def _count_words(text: str) -> int:
    if not (text or "").strip():
        return 0
    return len(re.findall(r"\w+", text, flags=re.UNICODE))


ConformanceGateLiteral = Literal["passed", "failed"]


def _collect_conformance_issues(
    *,
    template_id: str,
    hook: str,
    chapters: List[Any],
    full_script: str,
    duration_minutes: int,
) -> Tuple[List[str], List[str]]:
    """Liefert (warning_strings, severe_codes)."""
    tid, _ = normalize_story_template_id(template_id)
    if tid == "generic":
        return [], []

    ws: List[str] = []
    severe_codes: List[str] = []

    lo, hi = chapter_band_for_template_duration(tid, duration_minutes)
    n_ch = len(chapters or [])
    if n_ch < lo:
        ws.append(
            template_conformance_warning(
                "chapter_count",
                f"Nur {n_ch} Kapitel — für „{tid}“ bei {duration_minutes} Min. "
                f"Ziel typischerweise {lo}–{hi}.",
            )
        )
        severe_codes.append("chapter_count")
    elif n_ch > hi:
        ws.append(
            template_conformance_warning(
                "chapter_count",
                f"{n_ch} Kapitel — für „{tid}“ bei {duration_minutes} Min. "
                f"Obergrenze oft {hi}; prüfen ob Inhalt nicht zerstückelt wirkt.",
            )
        )

    hw = _count_words(hook or "")
    min_hw = min_hook_words_for_template(tid)
    if hw < min_hw:
        ws.append(
            template_conformance_warning(
                "hook_length",
                f"Hook kurz ({hw} Wörter) — für „{tid}“ eher mindestens ca. {min_hw} Wörter.",
            )
        )
        severe_codes.append("hook_length")

    wc = _count_words(full_script or "")
    target = max(1, int(duration_minutes * 140 * 0.35))
    if wc < target:
        ws.append(
            template_conformance_warning(
                "full_script_length",
                f"Volltext eher kurz ({wc} Wörter) für gewähltes Format — "
                f"prüfen ob ausbaubar (heuristisch ab Ziel ~{target} Wörter).",
            )
        )
        severe_codes.append("full_script_length")

    return ws, severe_codes


def apply_template_conformance(
    *,
    template_conformance_level: TemplateConformanceLevelLiteral | str,
    template_id: str,
    hook: str,
    chapters: List[Any],
    full_script: str,
    duration_minutes: int,
) -> Tuple[List[str], Optional[ConformanceGateLiteral]]:
    """Warnings für die Live-Antwort; Gate nur bei level==strict."""
    lvl = str(template_conformance_level or "warn").strip().lower()
    if lvl not in ("off", "warn", "strict"):
        lvl = "warn"

    if lvl == "off":
        return [], None

    ws, severe_codes = _collect_conformance_issues(
        template_id=template_id,
        hook=hook,
        chapters=chapters,
        full_script=full_script,
        duration_minutes=duration_minutes,
    )
    if lvl == "warn":
        return list(ws), None

    gate: ConformanceGateLiteral = "passed" if not severe_codes else "failed"
    out = list(ws)
    if gate == "failed":
        out.append(template_strict_gate_warning_failed())
    return out, gate


def conformance_persistence_gate(
    *,
    template_conformance_level: TemplateConformanceLevelLiteral | str,
    template_id: str,
    hook: str,
    chapters: List[Any],
    full_script: str,
    duration_minutes: int,
) -> str:
    """Für Persistenz Felder ohne erneuten Generate-Lauf — '' wenn kein strict-Gate."""
    _, g = apply_template_conformance(
        template_conformance_level=template_conformance_level,
        template_id=template_id,
        hook=hook,
        chapters=chapters,
        full_script=full_script,
        duration_minutes=duration_minutes,
    )
    if g is None:
        return ""
    return g


def conformance_warnings_for_template(
    *,
    template_id: str,
    hook: str,
    chapters: List[Any],
    full_script: str,
    duration_minutes: int,
) -> List[str]:
    """Rückwärtskompatibel: entspricht früherem warn-Verhalten ohne strict-Zusatz."""
    w, _ = apply_template_conformance(
        template_conformance_level="warn",
        template_id=template_id,
        hook=hook,
        chapters=chapters,
        full_script=full_script,
        duration_minutes=duration_minutes,
    )
    return w
