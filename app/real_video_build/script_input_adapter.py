from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


def build_scene_asset_pack_from_generate_script_response(
    data: dict,
    *,
    run_id: str = "",
) -> dict:
    """
    BA 25.2 — Adapter: GenerateScriptResponse-ähnliches Dict → scene_asset_pack.json (BA 18.2-kompatibel).

    Keine Provider-/LLM-Calls. Nutzt nur vorhandenen Text (hook/chapters/full_script).
    """
    if not isinstance(data, dict):
        raise ValueError("GenerateScriptResponse input must be a JSON object (dict).")

    title = _s(data.get("title"))
    hook = _s(data.get("hook"))
    full_script = _s(data.get("full_script"))
    chapters_raw = data.get("chapters")
    sources = _list_str(data.get("sources"))
    warnings = _list_str(data.get("warnings"))

    scenes = _scenes_from_chapters_like(chapters_raw)
    if not scenes:
        scenes = _scenes_from_full_script(full_script)

    if not scenes:
        raise ValueError(
            "GenerateScriptResponse contains no usable content: expected non-empty chapters or full_script."
        )

    return _build_scene_asset_pack(
        run_id=run_id,
        title=title,
        hook=hook,
        scenes=scenes,
        metadata={
            "adapter": "ba_25_2_generate_script_response",
            "sources": sources,
            "input_warnings": warnings,
        },
    )


def build_scene_asset_pack_from_story_pack(
    data: dict,
    *,
    run_id: str = "",
) -> dict:
    """
    BA 25.2 — Adapter: einfacher Story-Pack (lokales JSON) → scene_asset_pack.json.

    Erwartet grob:
    - title / hook optional
    - scenes[] oder beats[]: list[dict] oder list[str]
    - oder full_script als Text
    """
    if not isinstance(data, dict):
        raise ValueError("Story pack input must be a JSON object (dict).")

    title = _s(data.get("title"))
    hook = _s(data.get("hook"))
    full_script = _s(data.get("full_script") or data.get("script") or data.get("text"))

    scenes_raw = data.get("scenes")
    if scenes_raw is None:
        scenes_raw = data.get("beats")

    scenes = _scenes_from_story_pack_scenes(scenes_raw)
    if not scenes:
        scenes = _scenes_from_full_script(full_script)

    if not scenes:
        raise ValueError("Story pack contains no usable content: expected scenes/beats or full_script.")

    return _build_scene_asset_pack(
        run_id=run_id,
        title=title,
        hook=hook,
        scenes=scenes,
        metadata={"adapter": "ba_25_2_story_pack"},
    )


def write_scene_asset_pack(pack: dict, output_path: Path) -> Path:
    if not isinstance(pack, dict):
        raise ValueError("pack must be a dict")
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


# ----------------------------
# Internal helpers
# ----------------------------


def _s(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _list_str(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        out: List[str] = []
        for i in v:
            t = _s(i)
            if t:
                out.append(t)
        return out
    t = _s(v)
    return [t] if t else []


def _collapse_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _scene(title: str, narration: str) -> Dict[str, str]:
    return {"title": _s(title), "narration": _s(narration)}


def _scenes_from_chapters_like(chapters: Any) -> List[Dict[str, str]]:
    """
    Akzeptiert:
    - list[str]
    - list[dict] mit title/text/content/summary
    - list[pydantic-like] (mit .get oder attr-Zugriff wird nicht garantiert; wir bleiben bei dict/str)
    """
    if chapters is None:
        return []
    if not isinstance(chapters, list) or not chapters:
        return []

    out: List[Dict[str, str]] = []
    for idx, ch in enumerate(chapters, start=1):
        if isinstance(ch, str):
            text = ch.strip()
            if text:
                out.append(_scene(f"Kapitel {idx}", text))
            continue
        if isinstance(ch, dict):
            title = _s(ch.get("title")) or f"Kapitel {idx}"
            # Accept multiple common keys
            body = _s(ch.get("content")) or _s(ch.get("text")) or _s(ch.get("summary"))
            if not body:
                # last resort: if dict has any stringy fields, keep it minimal but not invented
                body = _s(ch.get("narration")) or _s(ch.get("voiceover_text")) or _s(ch.get("script_text"))
            if body:
                out.append(_scene(title, body))
            continue
        # ignore unknown chapter types
    return out


def _scenes_from_story_pack_scenes(scenes_raw: Any) -> List[Dict[str, str]]:
    if scenes_raw is None:
        return []
    if not isinstance(scenes_raw, list) or not scenes_raw:
        return []
    out: List[Dict[str, str]] = []
    for idx, s in enumerate(scenes_raw, start=1):
        if isinstance(s, str):
            t = s.strip()
            if t:
                out.append(_scene(f"Szene {idx}", t))
            continue
        if isinstance(s, dict):
            title = _s(s.get("title")) or _s(s.get("scene_title")) or f"Szene {idx}"
            narration = (
                _s(s.get("narration"))
                or _s(s.get("voiceover_text"))
                or _s(s.get("script_text"))
                or _s(s.get("text"))
                or _s(s.get("content"))
                or _s(s.get("summary"))
            )
            if narration:
                out.append(_scene(title, narration))
            continue
    return out


def _scenes_from_full_script(full_script: str) -> List[Dict[str, str]]:
    t = (full_script or "").strip()
    if not t:
        return []

    # Prefer paragraph-based chunking (German-friendly, deterministic)
    paras = [p.strip() for p in re.split(r"\n\s*\n+", t) if p.strip()]
    if not paras:
        paras = [t]

    # If there are enough paragraphs, use them (bounded to 3–8)
    if len(paras) >= 3:
        chunks = paras
    else:
        chunks = _chunk_by_sentences(t)

    chunks = [c.strip() for c in chunks if c.strip()]
    if not chunks:
        return []

    target_min, target_max = 3, 8
    chunks = _coerce_chunk_count(chunks, target_min=target_min, target_max=target_max)
    return [_scene(f"Szene {i+1}", chunk) for i, chunk in enumerate(chunks)]


def _chunk_by_sentences(text: str) -> List[str]:
    t = _collapse_ws(text)
    if not t:
        return []
    # Simple sentence split: keep punctuation, avoid empty fragments
    parts = re.split(r"(?<=[.!?])\s+", t)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) <= 2:
        return [t]
    # Wenn wir schon eine gute Anzahl Sätze haben, lieber direkt nutzen
    # (deterministisch, und erfüllt BA 25.2: 3–8 Chunks bei vorhandenem full_script).
    if 3 <= len(parts) <= 8:
        return parts

    # Group sentences into roughly medium chunks
    groups: List[str] = []
    cur: List[str] = []
    cur_len = 0
    target_chars = 550  # ~80–110 words in DE depending on whitespace
    for s in parts:
        cur.append(s)
        cur_len += len(s) + 1
        if cur_len >= target_chars:
            groups.append(" ".join(cur).strip())
            cur = []
            cur_len = 0
    if cur:
        groups.append(" ".join(cur).strip())
    return groups or [t]


def _coerce_chunk_count(chunks: Sequence[str], *, target_min: int, target_max: int) -> List[str]:
    ch = [c for c in chunks if (c or "").strip()]
    if not ch:
        return []

    # Merge if too many
    while len(ch) > target_max:
        # merge the shortest adjacent pair for minimal damage
        best_i = 0
        best_len = None
        for i in range(len(ch) - 1):
            l = len(ch[i]) + len(ch[i + 1])
            if best_len is None or l < best_len:
                best_len = l
                best_i = i
        merged = (ch[best_i].rstrip() + "\n\n" + ch[best_i + 1].lstrip()).strip()
        ch = list(ch[:best_i]) + [merged] + list(ch[best_i + 2 :])

    # Split if too few (only if a chunk is large enough)
    while len(ch) < target_min and any(len(x) >= 900 for x in ch):
        # split the largest chunk in half (by nearest whitespace)
        i = max(range(len(ch)), key=lambda k: len(ch[k]))
        s = ch[i]
        mid = len(s) // 2
        left = s[:mid].rsplit(" ", 1)[0].strip()
        right = s[len(left) :].strip() if left else s[mid:].strip()
        if not left or not right:
            break
        ch = list(ch[:i]) + [left, right] + list(ch[i + 1 :])

    return list(ch)


def _estimate_duration_seconds(text: str) -> int:
    # Project rule of thumb: 1 minute ≈ 140 words.
    words = re.findall(r"\b\w+\b", text or "")
    wc = len(words)
    sec = int(round((wc / 140.0) * 60.0)) if wc > 0 else 0
    return max(4, min(25, sec)) if sec else 4


def _visual_prompt_from_text(title: str, narration: str) -> str:
    """
    Deterministischer Placeholder-Visual-Prompt, ohne neue Fakten zu erfinden:
    nur „Textkarte/Abstrakt“ + kurze Stichworte aus vorhandenem Text.
    """
    base = (title or "").strip()
    snippet = _collapse_ws(narration)[:160]
    if base and snippet:
        return f"Textkarte, neutrale dokumentarische Bildsprache. Kapitel: {base}. Textauszug: {snippet}"
    if snippet:
        return f"Textkarte, neutrale dokumentarische Bildsprache. Textauszug: {snippet}"
    return "Textkarte, neutrale dokumentarische Bildsprache."


def _build_scene_asset_pack(
    *,
    run_id: str,
    title: str,
    hook: str,
    scenes: Sequence[Dict[str, str]],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    rid = _s(run_id)
    expanded: List[Dict[str, Any]] = []

    # Optional: hook as first beat if present (keeps orchestration narration useful)
    beat_index = 0
    if hook:
        expanded.append(
            {
                "chapter_index": 0,
                "beat_index": beat_index,
                "visual_prompt": _visual_prompt_from_text("Hook", hook),
                "camera_motion_hint": "static",
                "duration_seconds": _estimate_duration_seconds(hook),
                "asset_type": "hook_text",
                "continuity_note": "",
                "safety_notes": [],
                # preferred narration fields (BA 25.2)
                "narration": hook,
                "voiceover_text": hook,
                "scene_title": "Hook",
            }
        )
        beat_index += 1

    for i, sc in enumerate(scenes, start=1):
        narration = _s((sc or {}).get("narration"))
        if not narration:
            continue
        sc_title = _s((sc or {}).get("title")) or f"Szene {i}"
        expanded.append(
            {
                "chapter_index": 0,
                "beat_index": beat_index,
                "visual_prompt": _visual_prompt_from_text(sc_title, narration),
                "camera_motion_hint": "static",
                "duration_seconds": _estimate_duration_seconds(narration),
                "asset_type": "story_text",
                "continuity_note": "match prior" if i > 1 else "",
                "safety_notes": [],
                # preferred narration fields (BA 25.2)
                "narration": narration,
                "voiceover_text": narration,
                "scene_title": sc_title,
                "estimated_duration_seconds": _estimate_duration_seconds(narration),
            }
        )
        beat_index += 1

    if not expanded:
        raise ValueError("No usable scenes after normalization (all narration empty).")

    pack: Dict[str, Any] = {
        "export_version": "25.2-v1",
        "source_label": "adapter:script_input_adapter",
        "title": title,
        "hook": hook,
        "run_id": rid,
        "metadata": dict(metadata or {}),
        # Keep BA 18.2 compatibility for downstream scripts (asset runner)
        "scene_expansion": {"expanded_scene_assets": expanded},
    }
    return pack

