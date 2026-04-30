"""BA 9.2 — Regelbasierte Hook-Line-Engine (Opening, kein LLM in V1)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple

from app.story_engine.hook_library import (
    ALLOWED_HOOK_TYPES,
    HOOK_TEMPLATES_DE,
    opening_style_label,
)
from app.story_engine.templates import normalize_story_template_id


def _focus_snippet(title: str, topic: str, source_summary: str, max_len: int = 72) -> str:
    for part in (title.strip(), topic.strip(), (source_summary or "").strip()):
        if len(part) >= 8:
            s = part.replace("\n", " ")
            if len(s) > max_len:
                s = s[: max_len - 1].rsplit(" ", 1)[0] + "…"
            return s
    return "diesem Fall"


def _word_count(text: str) -> int:
    if not (text or "").strip():
        return 0
    return len(re.findall(r"\w+", text, flags=re.UNICODE))


def _pick_hook_type(tid: str, blob: str) -> str:
    """Wählt Hook-Typ aus Stichworten (blob = topic+title+summary lowercase)."""
    if tid == "true_crime":
        if any(
            k in blob
            for k in (
                "vermisst",
                "verschwunden",
                "spurlos",
                "nicht gesehen",
                "14 jahr",
                "jahrelang",
                "leiche",
                "fund",
            )
        ):
            return "shock_reveal"
        if any(
            k in blob for k in ("enthüll", "wahrheit", "geheim", "akten", "überrasch")
        ):
            return "hidden_truth"
        return "shock_reveal"
    if tid == "history_deep_dive":
        if any(
            k in blob
            for k in (
                "haus",
                "gebäude",
                "potsdam",
                "palast",
                "denkmal",
                "rot",
                "fassade",
            )
        ):
            return "forgotten_power"
        if any(
            k in blob for k in ("chronik", "zeitlinie", "geschichte", "jahrhundert")
        ):
            return "timeline_twist"
        return "forgotten_power"
    if tid == "mystery_explainer":
        if "warum" in blob or "wieso" in blob:
            return "question_gap"
        if any(
            k in blob
            for k in ("niemand", "unklär", "rätsel", "straße", "nichts", "leer")
        ):
            return "unexplained_event"
        return "unexplained_event"
    return "generic_curiosity"


def _score_hook(hook_text: str, tid: str, hook_type: str) -> float:
    allowed = ALLOWED_HOOK_TYPES.get(tid, ALLOWED_HOOK_TYPES["generic"])
    score = 6.0
    wc = _word_count(hook_text)
    if 14 <= wc <= 44:
        score += 1.3
    elif 10 <= wc <= 50:
        score += 0.7
    if "?" in hook_text or "warum" in hook_text.lower():
        score += 0.4
    if hook_type in allowed:
        score += 1.2
    if "—" in hook_text or ";" in hook_text:
        score += 0.2
    return min(10.0, round(score, 1))


@dataclass
class HookEngineResult:
    hook_text: str
    hook_type: str
    hook_score: float
    rationale: str
    template_match: str
    warnings: List[str]


def infer_hook_type_from_blob(template_id: str, blob: str) -> str:
    """Öffentliche Heuristik für Review-Abgleich (gleiche Regeln wie Hook-Engine)."""
    tid, _ = normalize_story_template_id(template_id)
    return _pick_hook_type(tid, blob.lower())


def generate_hook_v1(
    *,
    video_template: str,
    topic: str = "",
    title: str = "",
    source_summary: str = "",
) -> HookEngineResult:
    """
    Regelbasierte Hook-Zeile + Score. Entwirft keine neuen Fakten — Nutzung des
    gegebenen Titels/Themas/Zusammenfassung als Anker.
    """
    ws: List[str] = []
    tid, nws = normalize_story_template_id(video_template)
    ws.extend(nws)

    blob = f"{topic} {title} {source_summary}".lower()
    focus = _focus_snippet(title, topic, source_summary)
    hook_type = _pick_hook_type(tid, blob)
    allowed = ALLOWED_HOOK_TYPES.get(tid, ALLOWED_HOOK_TYPES["generic"])
    if hook_type not in allowed:
        hook_type = next(iter(allowed))
        ws.append(
            f"[hook_engine] Hook-Typ angepasst auf '{hook_type}' für Template '{tid}'."
        )

    template_de = HOOK_TEMPLATES_DE.get(
        hook_type, HOOK_TEMPLATES_DE["generic_curiosity"]
    )
    hook_text = template_de.format(focus=focus).strip()
    rationale = (
        f"V1-Regelwerk: Template '{tid}', Typ '{hook_type}', "
        f"Anker aus Titel/Thema/Zusammenfassung (kein LLM)."
    )
    score = _score_hook(hook_text, tid, hook_type)
    return HookEngineResult(
        hook_text=hook_text,
        hook_type=hook_type,
        hook_score=score,
        rationale=rationale,
        template_match=tid,
        warnings=ws,
    )


def hook_meta_for_persist(result: HookEngineResult) -> Tuple[str, float, str]:
    """Felder für `GeneratedScript`: hook_type, hook_score, opening_style."""
    return (
        result.hook_type,
        result.hook_score,
        opening_style_label(result.hook_type),
    )
