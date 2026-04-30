"""BA 9.4 — deterministische Pacing-/Rhythmik-Hinweise (Nebenkanal)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from app.story_engine.templates import normalize_story_template_id


def _word_count(text: str) -> int:
    if not (text or "").strip():
        return 0
    return len(re.findall(r"\w+", text, flags=re.UNICODE))


def _chapter_body(ch: Any) -> str:
    if isinstance(ch, dict):
        return str(ch.get("content") or "") + str(ch.get("title") or "")
    return str(getattr(ch, "content", "") or "") + str(getattr(ch, "title", "") or "")


def rhythm_hints_v1(
    *,
    video_template: str,
    duration_minutes: int,
    chapters: List[Any],
    hook: str,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Liefert strukturierten Nebenkanal + optionale konsumierbare warnings (nicht automatisch angehängt).
    """
    tid, ws_norm = normalize_story_template_id(video_template)
    warns = list(ws_norm)
    dm = max(1, int(duration_minutes))
    secs_total = float(dm * 60)
    chap = chapters or []
    wc_hook = _word_count(hook or "")
    n = len(chap)
    if n == 0:
        warns.append("[rhythm_engine] Keine Kapitel — Rhythmik nur Minimalhinweis.")
        return (
            {
                "schema_version": "1",
                "video_template": tid,
                "duration_minutes": dm,
                "beats": [],
                "hook_open_seconds_budget": round(min(42.0, secs_total * 0.09), 1),
                "transition_style_hint": "",
                "reveal_timing_hint": "",
            },
            warns,
        )

    beats: List[Dict[str, Any]] = []
    total_w = 0
    for ch in chap:
        total_w += max(1, _word_count(_chapter_body(ch)))

    for i, ch in enumerate(chap):
        if isinstance(ch, dict):
            title = str(ch.get("title") or f"Kap {i + 1}")
        else:
            title = str(getattr(ch, "title", "") or f"Kap {i + 1}")
        bw = max(1, _word_count(_chapter_body(ch)))
        share = bw / max(1, total_w)
        sec_est = max(48.0, secs_total * share)
        label = (
            "open"
            if i == 0
            else ("close" if i == n - 1 else f"middle_{i}")
        )
        beats.append(
            {
                "index": i,
                "label": label,
                "chapter_title_preview": title[:120],
                "seconds_estimate_band": (
                    round(sec_est * 0.92, 1),
                    round(sec_est * 1.08, 1),
                ),
                "word_share": round(share, 3),
                "density_note": ("hoch" if share > (1.25 / n) else "moderat"),
            }
        )

    trans = ""
    if tid == "mystery_explainer":
        trans = "Zwischen drei und fünf Sekunden Luft vor jeder Hypothesenwendung einplanen."
    elif tid == "true_crime":
        trans = "Bei Datumssprüngen eine kurze Orientierungsklammer sprechen, dann Fade."
    elif tid == "history_deep_dive":
        trans = "Epochenwechsel mit zwei Satz-Anker verkitten, keine harten Schnitt-Sprünge."
    else:
        trans = "Abschnitte mit einer Satz-Brücke falten — kein stumpfer Topic-Sprung."

    reveal_hint = ""
    if tid == "mystery_explainer" and n >= 3:
        reveal_hint = "Kernaufklärung idealerweise im vorletzten Block; letztes Kapitel nur Einordnung/CTA."
    elif tid == "true_crime" and n >= 4:
        reveal_hint = "Zweite Hälfte: Ermittlungswendungen stärker dosieren als zu Beginn."
    elif wc_hook < 10 and wc_hook > 0:
        reveal_hint = "Hook ist kurz — ersten Beat max. 75–110 Wörter, dann erste Fragestellung."
    else:
        reveal_hint = "Pattern: Problem → Kontext → vertiefende Belege → zusammengefasstes Urteil."

    out: Dict[str, Any] = {
        "schema_version": "1",
        "video_template": tid,
        "duration_minutes": dm,
        "beats": beats,
        "hook_open_seconds_budget": round(min(40.0, secs_total * 0.092), 1),
        "transition_style_hint": trans,
        "reveal_timing_hint": reveal_hint,
    }
    return out, warns
