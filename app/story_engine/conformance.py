"""BA 9.2-light — Template-Conformance nur als warnings."""

from __future__ import annotations

import re
from typing import Any, List

from app.story_engine.templates import normalize_story_template_id


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
    h = (hook or "").strip()
    if len(h) < 16:
        ws.append(
            f"template_conformance({tid}): Hook sehr kurz — für narrative Wirkung eher ausführlicher."
        )

    n_ch = len(chapters or [])
    if duration_minutes <= 6 and n_ch < 3:
        ws.append(
            f"template_conformance({tid}): Nur {n_ch} Kapitel bei {duration_minutes} Min. — Format erwartet typ. mehr Struktur."
        )
    elif duration_minutes <= 10 and n_ch < 4:
        ws.append(
            f"template_conformance({tid}): {n_ch} Kapitel bei ~10 Min. — optional mehr Kapitel für {tid}."
        )
    elif duration_minutes > 10 and n_ch < 5:
        ws.append(
            f"template_conformance({tid}): {n_ch} Kapitel bei längerer Dauer — Struktur ggf. ausbauen."
        )

    wc = _count_words(full_script or "")
    target = max(1, int(duration_minutes * 140 * 0.35))
    if wc < target:
        ws.append(
            f"template_conformance({tid}): Volltext eher kurz ({wc} Wörter) für gewähltes Format — prüfen ob ausbaubar."
        )

    return ws
