"""Feststehende Video-Story-Templates — Metadaten und Prompt-Zusätze."""

from __future__ import annotations

from typing import List, Tuple

from app.watchlist.models import SceneAssetStyleProfileLiteral, VoiceProfileLiteral

STORY_TEMPLATE_IDS = frozenset(
    {
        "generic",
        "true_crime",
        "mystery_explainer",
        "history_deep_dive",
    }
)


def normalize_story_template_id(raw: str | None) -> Tuple[str, List[str]]:
    """Liefert kanonischen Template-Key und optionale Hinweise."""
    ws: List[str] = []
    s = (raw or "").strip().lower().replace("-", "_")
    if not s or s == "default":
        return "generic", ws
    if s in STORY_TEMPLATE_IDS:
        return s, ws
    ws.append(
        f"Unbekanntes video_template '{raw}'; verwende 'generic'. "
        f"Erlaubt: {', '.join(sorted(STORY_TEMPLATE_IDS))}."
    )
    return "generic", ws


def story_template_prompt_addon_de(template_id: str) -> str:
    """Deutscher Zusatz für LLM- und Fallback-Prompts (kein JSON-Shape)."""
    tid, _ = normalize_story_template_id(template_id)
    if tid == "true_crime":
        return """
Story-Format TRUE CRIME (redaktionell):
- Ton: sachlich-dramaturgisch, respektvoll; keine Voyeurismus-Übertreibung.
- Hook: Spannung aus Faktenlage, keine zugesetzten Gewaltdetails.
- Struktur: Kontext → Zeitlinie → offene Fragen/Ermittlungsstand → Einordnung → vorsichtiges Fazit (keine Schuldsprüche).
- Keine neuen Namen, Daten oder Schuldzuweisungen erfinden; nur aus Key Points ableiten.
- Call-to-Action: Einordnung/Quellenhinweis, keine Hetze.
""".strip()
    if tid == "mystery_explainer":
        return """
Story-Format MYSTERY / RÄTSEL (Explainervideo):
- Hook: knappes Rätsel oder Paradox aus den Fakten.
- Spannung durch Fragen und bekannte Lücken, nicht durch Grusel-Klischees.
- Kapitel: Spur → Gegenargumente → plausible Einordnungen → was unklar bleibt.
- Keine Verschwörungstheorien als Fakten; Unsicherheit kennzeichnen.
""".strip()
    if tid == "history_deep_dive":
        return """
Story-Format HISTORY DEEP DIVE:
- Zeitlicher Kontext zuerst; Ursachen und Folgen sauber trennen.
- Vorsicht bei Urteilen aus heutiger Sicht (kein unreflektierter Presentismus).
- Kapitel: Setting → Wendepunkte → langfristige Wirkung → Bezug zur Gegenwart ohne neue Fakten.
""".strip()
    return ""


def style_profile_for_template(
    template_id: str,
) -> SceneAssetStyleProfileLiteral:
    tid, _ = normalize_story_template_id(template_id)
    if tid == "true_crime":
        return "true_crime"
    if tid == "mystery_explainer":
        return "cinematic"
    if tid == "history_deep_dive":
        return "documentary"
    return "documentary"


def voice_profile_for_template(template_id: str) -> VoiceProfileLiteral:
    tid, _ = normalize_story_template_id(template_id)
    if tid == "true_crime":
        return "dramatic"
    if tid == "mystery_explainer":
        return "soft"
    if tid == "history_deep_dive":
        return "documentary"
    return "documentary"
