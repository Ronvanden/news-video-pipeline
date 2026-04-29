"""BA 6.6: deterministische Szenenplanung ohne LLM."""

from __future__ import annotations

import hashlib
import re
from typing import List, Tuple

from app.models import Chapter
from app.utils import count_words
from app.watchlist.models import (
    GeneratedScript,
    Scene,
    SceneMoodLiteral,
    ScenePlanStatusLiteral,
)

WORDS_PER_MINUTE = 140
MAX_SCENES = 48
LONG_CHAPTER_WORDS = 220
PART_CHUNK_WORDS = 180


def scene_plan_fingerprint(gs: GeneratedScript) -> str:
    """Fingerabdruck aus full_script plus Kapitelstruktur (keine Roh-Hashes im Log)."""
    parts: List[str] = [(gs.full_script or "").strip()]
    for c in gs.chapters or []:
        parts.append(((c.title or "") + "\n" + (c.content or "")).strip())
    blob = "\f".join(parts)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _duration_seconds_for_text(text: str) -> int:
    w = count_words(text)
    if w <= 0:
        return 1
    return max(1, round(w / WORDS_PER_MINUTE * 60))


def _estimate_mood(text: str) -> SceneMoodLiteral:
    tl = text.lower()
    dramatic_kw = (
        "katastrophe",
        "trag",
        "krieg",
        "bedroh",
        "gefahr",
        "crash",
        "explosion",
    )
    explain_kw = (
        "bedeutet",
        "heißt dass",
        "also:",
        "zusammenfas",
        "erklär",
        "grundlegend",
        "definition",
        "dafür spricht",
    )
    if any(k in tl for k in dramatic_kw):
        return "dramatic"
    if sum(1 for k in explain_kw if k in tl) >= 2 and count_words(text) >= 25:
        return "explainer"
    return "neutral"


def _visual_summary(slice_text: str, max_chars: int = 220) -> str:
    t = slice_text.strip().replace("\n", " ")
    if not t:
        return ""
    if len(t) <= max_chars:
        return t
    cut = t[: max_chars - 2].rsplit(" ", 1)[0]
    suffix = cut + " …" if cut else t[:max_chars]
    return suffix.strip()


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _split_oversized_text(content: str) -> List[str]:
    """Teilt langes Kapitel in Absatz- oder Satzchunks."""
    c = content.strip()
    if count_words(c) <= LONG_CHAPTER_WORDS:
        return [c]
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", c) if p.strip()]
    chunks: List[str] = []
    if len(paragraphs) > 1:
        buf: List[str] = []
        buf_w = 0
        for p in paragraphs:
            pw = count_words(p)
            if buf_w + pw > PART_CHUNK_WORDS and buf:
                chunks.append("\n\n".join(buf))
                buf = [p]
                buf_w = pw
            else:
                buf.append(p)
                buf_w += pw
        if buf:
            chunks.append("\n\n".join(buf))
        if len(chunks) > 1:
            return chunks
    sentences = [s.strip() for s in _SENT_SPLIT.split(c) if s.strip()]
    if len(sentences) <= 1:
        words = c.split()
        out: List[str] = []
        i = 0
        while i < len(words):
            part_words = words[i : i + PART_CHUNK_WORDS]
            out.append(" ".join(part_words))
            i += PART_CHUNK_WORDS
        return out if out else [c]

    chunks2: List[str] = []
    buf_s: List[str] = []
    buf_sw = 0
    for s in sentences:
        sw = count_words(s)
        if buf_sw + sw > PART_CHUNK_WORDS and buf_s:
            chunks2.append(" ".join(buf_s))
            buf_s = [s]
            buf_sw = sw
        else:
            buf_s.append(s)
            buf_sw += sw
    if buf_s:
        chunks2.append(" ".join(buf_s))
    return chunks2 if chunks2 else [c]


def _enforce_max_scenes(
    drafts: List[Tuple[str, str, int, str]], max_scenes: int
) -> Tuple[List[Tuple[str, str, int, str]], List[str]]:
    """(voiceover_text, title, chapter_index, chapter_parent_title) tuples."""
    warns: List[str] = []
    if len(drafts) <= max_scenes:
        return drafts, warns
    warns.append(
        f"Szenenanzahl {len(drafts)} überschreitet Maximum {max_scenes}; "
        "Rest wird in der letzten Szene zusammengeführt."
    )
    head = drafts[: max_scenes - 1]
    tail = drafts[max_scenes - 1 :]
    combined_voice = "\n\n".join(t[0] for t in tail).strip()
    first_tit = tail[0][1]
    ext = ""
    if len(tail) > 1:
        ext = f" (+{len(tail) - 1} Teile zusammengeführt)"
    last_sci = tail[-1][2]
    last_parent = tail[-1][3]
    combined_tuple: Tuple[str, str, int, str] = (
        combined_voice,
        f"{first_tit}{ext}",
        last_sci,
        last_parent,
    )
    return head + [combined_tuple], warns


def build_scenes_from_generated_script(gs: GeneratedScript) -> Tuple[List[Scene], str, List[str]]:
    """
    Liefert Szenenliste, Fingerabdruck und Warnhinweise.

    Reihenfolge: wenn Kapitel mit Inhalt vorhanden → dort ableiten,
    sonst Fallback auf ``full_script`` in Blöcken.
    """
    warnings: List[str] = []
    fp = scene_plan_fingerprint(gs)

    chapters = gs.chapters or []
    chapter_rows: List[Tuple[int, Chapter]] = []

    for idx, ch in enumerate(chapters):
        title_raw = (ch.title or "").strip()
        raw_content = ch.content or ""
        content_stripped = raw_content.strip()
        if not content_stripped:
            if title_raw:
                warnings.append(
                    f"Leeres oder fehlendes Kapitel übersprungen: „{title_raw}“ "
                    f"(Index {idx})."
                )
            continue
        chapter_rows.append((idx, ch))

    drafts: List[Tuple[str, str, int, str]] = []

    if chapter_rows:
        for ch_idx, ch in chapter_rows:
            ctit = (ch.title or "").strip() or f"Kapitel {ch_idx + 1}"
            parts = _split_oversized_text(ch.content or "")
            if len(parts) == 1:
                drafts.append((parts[0].strip(), ctit, ch_idx, ctit))
            else:
                warnings.append(
                    f"Kapitel „{ctit}“ in mehrere Szenen geteilt (langer Inhalt)."
                )
                for n, part in enumerate(parts, start=1):
                    stitle = f"{ctit} (Teil {n})"
                    drafts.append((part.strip(), stitle, ch_idx, ctit))
    else:
        warnings.append(
            "Keine verwertbaren Kapitelinhalte — Szenen aus gesamtem Skript gebildet "
            "(Fallback)."
        )
        fs = (gs.full_script or "").strip()
        if not fs:
            return [], fp, warnings + ["Weder Kapitelinhalte noch full_script vorhanden."]

        blocks = [b.strip() for b in re.split(r"\n\s*\n+", fs) if b.strip()]
        if not blocks:
            blocks = [fs]
        drafts = [(blk, f"Szene {i + 1}", -1, "") for i, blk in enumerate(blocks)]

    drafts, wm = _enforce_max_scenes(drafts, MAX_SCENES)
    warnings.extend(wm)

    scenes: List[Scene] = []
    for n, (voice, title, sci, cht_parent) in enumerate(drafts, start=1):
        mood = _estimate_mood(voice)
        scenes.append(
            Scene(
                scene_number=n,
                title=title[:500],
                voiceover_text=voice,
                visual_summary=_visual_summary(voice),
                duration_seconds=_duration_seconds_for_text(voice),
                asset_type="generated",
                mood=mood,
                source_chapter_title=cht_parent[:500],
                source_chapter_index=sci,
            )
        )

    return scenes, fp, warnings


def decide_plan_status(scenes: List[Scene]) -> ScenePlanStatusLiteral:
    if not scenes:
        return "failed"
    return "ready"
