"""BA 9.x — Template-Conformance nur als warnings."""

from __future__ import annotations

import re
from typing import Any, List

from app.story_engine.templates import (
    chapter_band_for_template_duration,
    min_hook_words_for_template,
    normalize_story_template_id,
)


def template_conformance_warning(code: str, detail: str) -> str:
    """Einheitliches Präfix für Log und UI (nur String in warnings)."""
    c = (code or "general").strip().replace("]", "").replace("[", "")
    return f"[template_conformance:{c}] {detail.strip()}"


def _count_words(text: str) -> int:
    if not (text or "").strip():
        return 0
    return len(re.findall(r"\w+", text, flags=re.UNICODE))


def conformance_warnings_for_template(
    *,
    template_id: str,
    hook: str,
    chapters: List[Any],
    full_script: str,
    duration_minutes: int,
) -> List[str]:
    tid, _ = normalize_story_template_id(template_id)
    if tid == "generic":
        return []

    ws: List[str] = []
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

    return ws
