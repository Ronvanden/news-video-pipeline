"""Feststehende Video-Story-Templates — Metadaten und Prompt-Zusätze."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.watchlist.models import SceneAssetStyleProfileLiteral, VoiceProfileLiteral

# Kanonische IDs (u. a. abgestimmt auf ``templates/template_registry.json`` / ``documentary.json``).
STORY_TEMPLATE_IDS = frozenset(
    {
        "generic",
        "true_crime",
        "mystery_explainer",
        "history_deep_dive",
        "documentary",
        "real_estate_story",
    }
)

# Eingabe-Aliase → kanonische ID (keine Warnung bei Alias-Treffer).
VIDEO_TEMPLATE_ALIASES: Dict[str, str] = {
    "documentary_story": "documentary",
    "real_estate": "real_estate_story",
}


def normalize_story_template_id(raw: str | None) -> Tuple[str, List[str]]:
    """Liefert kanonischen Template-Key und optionale Hinweise."""
    ws: List[str] = []
    s = (raw or "").strip().lower().replace("-", "_")
    if not s or s == "default":
        return "generic", ws
    s = VIDEO_TEMPLATE_ALIASES.get(s, s)
    if s in STORY_TEMPLATE_IDS:
        return s, ws
    ws.append(
        f"Unbekanntes video_template '{raw}'; verwende 'generic'. "
        f"Erlaubt: {', '.join(sorted(STORY_TEMPLATE_IDS))}."
    )
    return "generic", ws


def chapter_band_for_template_duration(
    template_id: str, duration_minutes: int
) -> Tuple[int, int]:
    """Erlaubtes Zielband Kapitelanzahl (min, max) für Template und Dauer."""
    tid, _ = normalize_story_template_id(template_id)
    d = max(1, int(duration_minutes))
    if tid == "generic":
        if d <= 6:
            return (2, 6)
        if d <= 10:
            return (3, 8)
        return (4, 10)
    if tid == "true_crime":
        if d <= 6:
            return (3, 5)
        if d <= 10:
            return (4, 7)
        return (5, 9)
    if tid == "mystery_explainer":
        if d <= 6:
            return (3, 5)
        if d <= 10:
            return (4, 6)
        return (5, 8)
    if tid == "history_deep_dive":
        if d <= 6:
            return (3, 5)
        if d <= 10:
            return (4, 7)
        return (6, 10)
    if tid == "documentary":
        if d <= 6:
            return (3, 5)
        if d <= 10:
            return (4, 7)
        return (6, 10)
    if tid == "real_estate_story":
        if d <= 6:
            return (3, 6)
        if d <= 10:
            return (4, 8)
        return (5, 10)
    return (3, 8)


def min_hook_words_for_template(template_id: str) -> int:
    tid, _ = normalize_story_template_id(template_id)
    if tid == "generic":
        return 8
    return 18


def chapter_title_style_hint_de(template_id: str) -> str:
    tid, _ = normalize_story_template_id(template_id)
    if tid == "true_crime":
        return (
            "präzise, sachlich; Zeitmarker oder Orte möglich; keine reißerischen "
            "ungeprüften Behauptungen in der Überschrift."
        )
    if tid == "mystery_explainer":
        return (
            "häufig Fragestellung oder klare These; keine Grusel-Klischees in jedem Titel."
        )
    if tid == "history_deep_dive":
        return (
            "Epoche/Kontext oder Wendepunkt im Titel; kein reißerischer "
            "Anachronismus."
        )
    if tid == "documentary":
        return (
            "Dokumentarisch: Fokus, Wendepunkt oder These im Titel; "
            "seriös und erklärend, ohne reißerische Übertreibung."
        )
    return "klar und informativ; kein abgeschnittener Titel."


def story_template_blueprint_prompt_de(
    template_id: str, duration_minutes: int
) -> str:
    """Strukturhinweise für LLM/Fallback-Prompt (kein Secret-Inhalt)."""
    tid, _ = normalize_story_template_id(template_id)
    if tid == "generic":
        return ""
    lo, hi = chapter_band_for_template_duration(tid, duration_minutes)
    mw = min_hook_words_for_template(tid)
    style = chapter_title_style_hint_de(tid)
    return (
        f"- Ziel: etwa {lo}–{hi} inhaltliche Kapitel (materialabhängig flexibel).\n"
        f"- Hook: mindestens ca. {mw} Wörter; klar, einordnend, ohne Übertreibung.\n"
        f"- Kapiteltitel: {style}"
    ).strip()


def public_story_template_catalog() -> List[Dict[str, Any]]:
    """Lesbare Meta-Infos für GET /story-engine/templates (ohne Prompt-Rohlinge)."""
    examples = [5, 10, 15]

    def bands_for(tid: str) -> List[Dict[str, int]]:
        out: List[Dict[str, int]] = []
        for dm in examples:
            lo, hi = chapter_band_for_template_duration(tid, dm)
            out.append(
                {
                    "duration_minutes": dm,
                    "chapters_min": lo,
                    "chapters_max": hi,
                }
            )
        return out

    return [
        {
            "id": "generic",
            "label": "Allgemein",
            "description": (
                "Standard-Erzählstruktur für Nachrichten und Erklärer; "
                "keine feste Format-Fessel."
            ),
            "duration_examples": bands_for("generic"),
            "min_hook_words": min_hook_words_for_template("generic"),
            "chapter_title_style": chapter_title_style_hint_de("generic"),
        },
        {
            "id": "true_crime",
            "label": "True Crime",
            "description": (
                "Sachlich-respektvolle True-Crime-Erzählung mit Zeitlinie "
                "und Einordnung; keine erfundenen Details."
            ),
            "duration_examples": bands_for("true_crime"),
            "min_hook_words": min_hook_words_for_template("true_crime"),
            "chapter_title_style": chapter_title_style_hint_de("true_crime"),
        },
        {
            "id": "mystery_explainer",
            "label": "Mystery / Rätsel-Erklärer",
            "description": (
                "Spannung über Fragen und dokumentierte Lücken; "
                "keine Verschwörungsverkäufe als Fakten."
            ),
            "duration_examples": bands_for("mystery_explainer"),
            "min_hook_words": min_hook_words_for_template("mystery_explainer"),
            "chapter_title_style": chapter_title_style_hint_de("mystery_explainer"),
        },
        {
            "id": "history_deep_dive",
            "label": "History Deep Dive",
            "description": (
                "Historischer Kontext, Wendepunkte, Folgen; "
                "reflektierte Sprache ohne neue Fakten zu erfinden."
            ),
            "duration_examples": bands_for("history_deep_dive"),
            "min_hook_words": min_hook_words_for_template("history_deep_dive"),
            "chapter_title_style": chapter_title_style_hint_de("history_deep_dive"),
        },
        {
            "id": "documentary",
            "label": "Documentary Story",
            "description": (
                "Seriöse, emotionale dokumentarische Erzählung aus realen Ereignissen (``templates/documentary.json``); "
                "Ton: sachlich, cineastisch, ernst, geerdet, emotional zugänglich — ohne Sensationsjournalismus. "
                "Struktur: Hook → Kontext → Ereignis → Folgen → Erklärung → Abschlussreflexion. "
                "API-Alias ohne Extra-Warnung: ``documentary_story`` → ``documentary``."
            ),
            "duration_examples": bands_for("documentary"),
            "min_hook_words": min_hook_words_for_template("documentary"),
            "chapter_title_style": chapter_title_style_hint_de("documentary"),
        },
        {
            "id": "real_estate_story",
            "label": "Real Estate Story",
            "description": (
                "Immobilien, Umbau, Marktverlauf — sachlich-erklärend; "
                "orientiert an ``templates/real_estate_story.json``. "
                "API-Alias ohne Extra-Warnung: ``real_estate`` → ``real_estate_story``."
            ),
            "duration_examples": bands_for("real_estate_story"),
            "min_hook_words": min_hook_words_for_template("real_estate_story"),
            "chapter_title_style": chapter_title_style_hint_de("real_estate_story"),
        },
    ]


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
    if tid == "documentary":
        return """
Story-Format DOCUMENTARY (reale Ereignisse, dokumentarisch):
- Zweck: seriöse, emotionale, dokumentarische Erzählung — factual, cinematic, serious, grounded, emotionally engaging.
- Ton: erklärend und spannend, aber nicht reißerisch; keine Tabloid-Übertreibung.
- Struktur (orientierend): Hook → Kontext → Ereignis/Vorfall → Folgen → Erklärung/Einordnung → Abschlussreflexion.
- Hook: Relevanz und echte Spannung aus Faktenlage, keine erfundenen Schocks.
- Keine neuen Fakten erfinden; Unsicherheiten und Quellenlage transparent halten.
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
    if tid == "documentary":
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
    if tid == "documentary":
        return "documentary"
    return "documentary"


# BA 9.3.4 — Blueprint-/Conformance-Stände je Template (bump bei inhaltlicher Änderung).
TEMPLATE_DEFINITION_VERSION: Dict[str, str] = {
    "generic": "1",
    "true_crime": "1",
    "mystery_explainer": "1",
    "history_deep_dive": "1",
    "documentary": "3",
    "real_estate_story": "1",
}


def definition_version_for_template(template_id: str) -> str:
    tid, _ = normalize_story_template_id(template_id)
    return TEMPLATE_DEFINITION_VERSION.get(tid, "1")
