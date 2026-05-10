"""Phase 8.1 — Policy‑Konstanten (keine Secrets, keine Rechtsberatung)."""

# Profilstring für Contract-Ausgaben (Doku/Versionierung).
VISUAL_POLICY_PROFILE_V1 = "visual_policy_v8_1_20260430"

# Kurztexte nur als redaktioneller Hinweis (keine Garantien).
LICENSING_NOTE_V1 = (
    "Platzhalter-Visual; keine automatische Lizenz- oder Nutzungszusage durch die Pipeline."
)

NEGATIVE_HINTS_DEFAULT_V1 = "avoid_text_watermark_claims_without_source"

# Phase 8.2 — Safety-Negative (segmentierte Tokens, deterministischer Merge im Prompt-Engine).
SAFETY_NEGATIVE_SEGMENTS_V1: tuple[str, ...] = (
    "no_gore",
    "no_explicit_nudity",
    "no_legible_trademarks_without_rights",
    "no_identifiable_real_person_likeness_claims",
    "no_fake_journalistic_on_screen_text",
)

# BA 32.60 — Zusatz-Negative für dokumentarisches Template ``documentary`` (Merge in Scene-Blueprint ``negative_hints``).
DOCUMENTARY_STORY_NEGATIVE_SEGMENTS_V1: tuple[str, ...] = (
    "no_fantasy",
    "no_surreal",
    "no_horror_monster",
    "no_gore",
    "no_exaggerated_blood",
    "no_apocalyptic_dramatic_lighting",
    "no_cartoonish",
    "no_fake_news_tabloid_aesthetic",
    "no_exaggerated_disaster_imagery",
    "no_giant_creature_unless_source_supported",
)

VISUAL_PROMPT_ENGINE_POLICY_V1 = "visual_prompt_engine_v8_2_20260501"
