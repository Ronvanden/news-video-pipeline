"""Optional YouTube packaging text layer.

V1 is intentionally deterministic and provider-free. It prepares a small
intro/CTA/outro wrapper for an already generated script without changing any
publishing or render flows.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


_VERSION = "youtube_packaging_v1"


def _clean(value: Any, *, limit: int = 500) -> str:
    text = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())
    if len(text) <= limit:
        return text.strip()
    clipped = text[:limit].rstrip()
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0].rstrip(" ,;:-")
    if clipped and clipped[-1] not in ".!?":
        clipped += "."
    return clipped.strip()


def _chapter_titles(chapters: Any, *, limit: int = 5) -> List[str]:
    out: List[str] = []
    if not isinstance(chapters, list):
        return out
    for ch in chapters:
        if not isinstance(ch, dict):
            continue
        title = _clean(ch.get("title"), limit=90)
        if title and title not in out:
            out.append(title)
        if len(out) >= limit:
            break
    return out


def _language_is_german(target_language: Optional[str]) -> bool:
    return str(target_language or "de").strip().lower().startswith("de")


def _packaging_level(duration_target_seconds: Optional[int]) -> str:
    try:
        duration = int(duration_target_seconds or 0)
    except (TypeError, ValueError):
        duration = 0
    if duration and duration <= 120:
        return "minimal"
    if duration and duration < 600:
        return "short"
    return "standard"


def build_youtube_packaging(
    *,
    title: Optional[str] = None,
    hook: Optional[str] = None,
    chapters: Any = None,
    target_language: str = "de",
    channel_name: Optional[str] = None,
    duration_target_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """Build a deterministic YouTube wrapper for script/voice usage.

    The returned object is data only. It does not call providers and does not
    assume branding beyond an optional channel name.
    """
    title_s = _clean(title, limit=140) or "diesem Thema"
    hook_s = _clean(hook, limit=220)
    channel_s = _clean(channel_name, limit=80)
    german = _language_is_german(target_language)
    warnings: List[str] = []

    packaging_level = _packaging_level(duration_target_seconds)
    included_intro = packaging_level in {"short", "standard"}
    included_cta = True
    included_outro = packaging_level == "standard"

    if german:
        if packaging_level == "standard":
            intro_text = (
                f"Willkommen zu dieser Einordnung. In diesem Video geht es um {title_s}. "
                "Wir schauen ruhig auf die wichtigsten Punkte, ordnen den Kontext ein und trennen Beobachtung von Bewertung."
            )
            if hook_s:
                intro_text += f" Ausgangspunkt ist: {hook_s}"
        elif packaging_level == "short":
            intro_text = f"Willkommen zu dieser kurzen Einordnung zu {title_s}."
        else:
            intro_text = ""
        cta_text = "Wenn du solche Einordnungen hilfreich findest, abonniere den Kanal."
        outro_text = (
            "Zum Schluss bleibt wichtig: Dieser Beitrag ersetzt keine eigene Pruefung der Quellen, "
            "sondern hilft bei einer strukturierteren Einordnung. Danke fuers Zuschauen."
        ) if included_outro else ""
    else:
        if packaging_level == "standard":
            intro_text = (
                f"Welcome to this analysis. In this video, we look at {title_s}, separate observation from evaluation, "
                "and put the key points into context."
            )
            if hook_s:
                intro_text += f" The starting point is: {hook_s}"
        elif packaging_level == "short":
            intro_text = f"Welcome to this short analysis of {title_s}."
        else:
            intro_text = ""
        cta_text = "If you find this useful, subscribe to the channel."
        outro_text = (
            "To close, this video is meant to support a clearer view of the topic, not replace your own source check. "
            "Thanks for watching."
        ) if included_outro else ""

    overlay_hooks = [{"type": "title_hook", "text": title_s}]
    for idx, chapter_title in enumerate(_chapter_titles(chapters), start=1):
        overlay_hooks.append({"type": "chapter_hook", "chapter_index": idx - 1, "text": chapter_title})

    if not _clean(title):
        warnings.append("youtube_packaging_title_missing_generic_used")
    if channel_s:
        overlay_hooks.append({"type": "channel_hint", "text": channel_s})

    return {
        "youtube_packaging_version": _VERSION,
        "packaging_applied": True,
        "packaging_level": packaging_level,
        "included_intro": bool(included_intro),
        "included_cta": bool(included_cta),
        "included_outro": bool(included_outro),
        "intro_text": intro_text,
        "cta_text": cta_text,
        "outro_text": outro_text,
        "overlay_hooks": overlay_hooks,
        "warnings": warnings,
    }


def apply_youtube_packaging_to_script(
    script: Dict[str, Any],
    *,
    target_language: str = "de",
    channel_name: Optional[str] = None,
    duration_target_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """Return a copied script with intro/CTA/outro added to ``full_script``."""
    src = dict(script or {})
    packaging = build_youtube_packaging(
        title=src.get("title"),
        hook=src.get("hook"),
        chapters=src.get("chapters"),
        target_language=target_language,
        channel_name=channel_name,
        duration_target_seconds=duration_target_seconds,
    )
    original_full = str(src.get("full_script") or "").strip()
    if not original_full:
        parts: List[str] = []
        hook = _clean(src.get("hook"), limit=2000)
        if hook:
            parts.append(hook)
        chapters = src.get("chapters")
        if isinstance(chapters, list):
            for ch in chapters:
                if not isinstance(ch, dict):
                    continue
                title = _clean(ch.get("title"), limit=180)
                content = _clean(ch.get("content") or ch.get("summary") or ch.get("narration"), limit=4000)
                if title and content:
                    parts.append(f"{title}\n{content}")
                elif content:
                    parts.append(content)
        original_full = "\n\n".join(parts).strip()

    combined_parts = [
        str(packaging["intro_text"]).strip(),
        original_full,
        str(packaging["cta_text"]).strip(),
        str(packaging["outro_text"]).strip(),
    ]
    src["full_script"] = "\n\n".join(part for part in combined_parts if part).strip()
    warnings = [str(x) for x in (src.get("warnings") or []) if str(x).strip()]
    warnings.append("youtube_packaging_v1_applied")
    for w in packaging.get("warnings") or []:
        if w not in warnings:
            warnings.append(str(w))
    src["warnings"] = warnings
    return {"script": src, "packaging": packaging, "original_full_script": original_full}
