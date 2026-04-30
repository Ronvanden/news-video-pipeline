"""BA 8.5 — Transkript- und Eingangsqualität: Klassifikation ohne harte Pipeline-Brüche.

Keine externen Calls. Rein deterministische Heuristik aus Fehlercodes, Skip-Gründen und Warntexten.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

InputQualityStatusLiteral = Literal[
    "ok",
    "transcript_missing",
    "transcript_blocked",
    "transcript_partial",
    "source_low_quality",
    "unknown",
]

LEGACY_TRANSCRIPT_MISSING = "transcript_not_available"
LEGACY_TRANSCRIPT_BLOCKED = "transcript_check_failed"


def classify_transcript_failure(
    *,
    error_code: str = "",
    warnings: Optional[Sequence[str]] = None,
    joined_warnings: str = "",
) -> InputQualityStatusLiteral:
    """Ordnet Transkript-/Eingangsfehler der operativen Qualitätskategorie zu."""
    ws = list(warnings or [])
    blob = joined_warnings or " ".join(x or "" for x in ws)
    ec = (error_code or "").strip().lower()

    if ec == LEGACY_TRANSCRIPT_MISSING.lower():
        return "transcript_missing"
    if ec == LEGACY_TRANSCRIPT_BLOCKED.lower():
        return "transcript_blocked"

    if "transcript not available" in blob.lower():
        return "transcript_missing"
    if "blocked" in blob.lower() and "transcript" in blob.lower():
        return "transcript_blocked"
    if "could not parse a youtube video id" in blob.lower():
        return "source_low_quality"
    if "partial" in blob.lower() and "transcript" in blob.lower():
        return "transcript_partial"
    if "transcript" in blob.lower() and (
        "unvollständig" in blob.lower() or "incomplete" in blob.lower()
    ):
        return "transcript_partial"

    if ec in ("script_generation_empty",):
        return "source_low_quality"
    return "unknown"


def normalize_input_quality_status(
    raw: str,
) -> Tuple[InputQualityStatusLiteral, str]:
    """Mappt Legacy-Codes auf kanonische Status und optionalen normalisierten Skip-Reason-Text.

    Der zweite Wert ist der empfohlene ``skip_reason`` / Kurzcode für neue Schreibvorgänge
    (rückwärtskompatibel mit älteren Aggregationen, wenn Legacy beibehalten wird).
    """
    s = (raw or "").strip().lower()
    mapping = {
        "": ("unknown", ""),
        LEGACY_TRANSCRIPT_MISSING: ("transcript_missing", "transcript_missing"),
        LEGACY_TRANSCRIPT_BLOCKED: ("transcript_blocked", "transcript_blocked"),
        "transcript_missing": ("transcript_missing", "transcript_missing"),
        "transcript_blocked": ("transcript_blocked", "transcript_blocked"),
        "transcript_partial": ("transcript_partial", "transcript_partial"),
        "source_low_quality": ("source_low_quality", "source_low_quality"),
        "ok": ("ok", ""),
    }
    if s in mapping:
        return mapping[s]  # type: ignore[return-value]
    if "transcript" in s and "fail" in s:
        return "transcript_blocked", "transcript_blocked"
    return "unknown", raw


def build_input_quality_decision(
    *,
    error_code: str = "",
    skip_reason: str = "",
    warnings: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Operative Entscheidung: Eskalation, Hinweise, Platzhalter für spätere Fallback-Hooks."""
    ws = list(warnings or [])
    blob = " ".join(warnings or [])
    from_code = classify_transcript_failure(
        error_code=error_code,
        warnings=ws,
        joined_warnings=blob,
    )
    canon_sr, norm_skip = normalize_input_quality_status(
        skip_reason or error_code or ""
    )
    if from_code != "unknown":
        status: InputQualityStatusLiteral = from_code
    elif canon_sr != "unknown":
        status = canon_sr
    else:
        status = "unknown"

    should_escalate = status == "transcript_blocked"

    warnings_append: List[str] = []
    if status == "transcript_missing":
        warnings_append.append(
            "input_quality: transcript_missing — kein Job-Erfolg erwartbar ohne andere Quelle."
        )
    elif status == "transcript_blocked":
        warnings_append.append(
            "input_quality: transcript_blocked — technisch/Plattform; Ops prüfen und ggf. Retry."
        )
    elif status == "transcript_partial":
        warnings_append.append(
            "input_quality: transcript_partial — Ausgabe kann unvollständig sein."
        )
    elif status == "source_low_quality":
        warnings_append.append(
            "input_quality: source_low_quality — Eingang zu dünn oder nicht nutzbar."
        )

    fallback_hooks: List[str] = [
        "alt_transcript_source:youtube_captions_v2",
        "alt_transcript_source:manual_upload_future",
    ]
    if status == "transcript_missing":
        fallback_hooks.append("escalation:queue_manual_source")

    return {
        "input_quality_status": status,
        "normalized_skip_reason": norm_skip or skip_reason,
        "should_escalate": should_escalate,
        "warnings_append": warnings_append,
        "fallback_hooks": fallback_hooks,
    }


