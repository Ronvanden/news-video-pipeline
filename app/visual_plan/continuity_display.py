"""BA 27.3 — Continuity Display (operator-friendly strings, no provider calls)."""

from __future__ import annotations

from typing import Any, Dict, List, Literal


def _s(v: Any) -> str:
    return str(v or "").strip()


def _list_str(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [t for t in (_s(x) for x in v) if t]
    t = _s(v)
    return [t] if t else []


def _short(s: str, *, max_len: int = 140) -> str:
    t = _s(s)
    if len(t) <= max_len:
        return t
    return t[: max(0, max_len - 1)].rstrip() + "…"


Language = Literal["de", "en"]


def _map_strength(strength: str, *, language: Language) -> str:
    s = _s(strength).lower()
    if language == "de":
        if s == "low":
            return "niedrig"
        if s == "medium":
            return "mittel"
        if s == "high":
            return "hoch"
    return s


def _map_status(st: str, *, language: Language) -> str:
    s = _s(st).lower()
    if language == "de":
        if s == "prepared":
            return "vorbereitet"
        if s == "missing_reference":
            return "Referenz fehlt"
        if s == "needs_review":
            return "Prüfung nötig"
        if s == "none":
            return "keine"
    return s


def build_continuity_display_line(asset: Dict[str, Any], *, language: Language = "de") -> str:
    a = asset if isinstance(asset, dict) else {}
    st = _s(a.get("continuity_provider_preparation_status") or "").lower()
    ids = _list_str(a.get("reference_asset_ids"))
    strength = _s(a.get("continuity_strength") or "").lower()

    if not st:
        st = "none" if not ids else "prepared"
    st_de = _map_status(st, language=language)
    strength_de = _map_strength(strength, language=language) if strength else ""
    lbl_cont = "Kontinuität" if language == "de" else "Continuity"
    lbl_refs = "Referenzen" if language == "de" else "References"
    lbl_strength = "Stärke" if language == "de" else "Strength"
    if st == "prepared":
        return f"{lbl_cont}: {st_de} · {lbl_refs}: {len(ids)}" + (f" · {lbl_strength}: {strength_de}" if strength_de else "")
    if st == "missing_reference":
        return f"{lbl_cont}: {st_de} · {lbl_refs}: {len(ids)}"
    if st == "needs_review":
        return f"{lbl_cont}: {st_de} · {lbl_refs}: {len(ids)}"
    return f"{lbl_cont}: {st_de}"


def build_continuity_display_block(asset: Dict[str, Any], *, language: Language = "de") -> Dict[str, Any]:
    a = asset if isinstance(asset, dict) else {}
    ids = _list_str(a.get("reference_asset_ids"))
    hint = _short(_s(a.get("continuity_prompt_hint") or ""))
    stub = a.get("continuity_provider_payload_stub") if isinstance(a.get("continuity_provider_payload_stub"), dict) else {}
    no_live = bool(stub.get("no_live_upload") is True) if isinstance(stub, dict) else True

    line = build_continuity_display_line(a, language=language)
    st = _s(a.get("continuity_provider_preparation_status") or "").lower() or ("none" if not ids else "prepared")

    return {
        "continuity_display_status": st,
        "continuity_display_line": line,
        "continuity_reference_ids": ids,
        "continuity_reference_count": int(len(ids)),
        "continuity_hint_short": hint or None,
        "continuity_no_live_upload": bool(no_live),
        "continuity_display_version": "ba27_3_v1",
    }


def build_continuity_export_summary(assets: List[Dict[str, Any]]) -> Dict[str, Any]:
    prepared = 0
    missing = 0
    needs_review = 0
    none = 0
    for a in assets or []:
        if not isinstance(a, dict):
            continue
        st = _s(a.get("continuity_provider_preparation_status") or "").lower()
        if st == "prepared":
            prepared += 1
        elif st == "missing_reference":
            missing += 1
        elif st == "needs_review":
            needs_review += 1
        else:
            none += 1
    return {
        "prepared_count": int(prepared),
        "missing_reference_count": int(missing),
        "needs_review_count": int(needs_review),
        "none_count": int(none),
        "continuity_display_version": "ba27_3_v1",
    }

