"""BA 25.3 — URL-to-Script Bridge.

Lokale CLI-Brücke: nimmt eine Artikel- oder YouTube-URL und erzeugt eine
``GenerateScriptResponse``-kompatible JSON-Datei unter
``output/url_script_<run_id>/generate_script_response.json``.

Strikte Grenzen (BA 25.3):

- **Kein** Render, **kein** Final Render, **kein** Dashboard.
- **Kein** YouTube Upload / Publishing.
- **Kein** Scene-Asset-Pack-Build (das macht BA 25.2 Adapter).
- **Kein** Orchestrator-Aufruf (das macht BA 25.4).
- **Keine** neuen Provider-Calls — die bestehende ``app.utils``-Logik wird
  nur lokal wiederverwendet (Article + YouTube). Kein ``.env``-Lesen.

Nur die Adapter-Kompatibilität zu BA 25.2 wird sichergestellt.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.utils import (
    build_script_response_from_extracted_text,
    extract_text_from_url,
    generate_script_from_youtube_video,
)

URL_SCRIPT_RESULT_FILENAME = "generate_script_response.json"
URL_SCRIPT_OPEN_ME_FILENAME = "URL_SCRIPT_OPEN_ME.md"

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
_YOUTUBE_HOST_HINTS = (
    "youtube.com",
    "youtu.be",
    "m.youtube.com",
    "music.youtube.com",
    "www.youtube.com",
)

_VALID_SOURCE_TYPES = ("auto", "article", "youtube")

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_INVALID_INPUT = 3


# ----------------------------
# Validation / detection
# ----------------------------


def _validate_run_id(run_id: str) -> bool:
    s = (run_id or "").strip()
    if not s or ".." in s or "/" in s or "\\" in s:
        return False
    return bool(_RUN_ID_RE.fullmatch(s))


def _is_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url or "")
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    if not (parsed.netloc or "").strip():
        return False
    return True


def detect_source_type(url: str, requested: str = "auto") -> str:
    """Return ``"youtube"`` or ``"article"``.

    ``requested`` may be ``auto`` (default), ``article`` or ``youtube``.
    Auto detection: hosts wie ``youtube.com`` / ``youtu.be`` → youtube,
    sonst article.
    """
    requested = (requested or "auto").strip().lower() or "auto"
    if requested not in _VALID_SOURCE_TYPES:
        requested = "auto"
    if requested in ("article", "youtube"):
        return requested

    try:
        host = (urlparse(url or "").hostname or "").lower()
    except Exception:
        host = ""
    if not host:
        return "article"
    for hint in _YOUTUBE_HOST_HINTS:
        if host == hint or host.endswith("." + hint):
            return "youtube"
    return "article"


# ----------------------------
# Output helpers
# ----------------------------


def _list_str(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x if i is not None and str(i).strip() != ""]
    if isinstance(x, (str, int, float, bool)):
        t = str(x).strip()
        return [t] if t else []
    return [str(x)]


def _chapter_to_dict(ch: Any) -> Dict[str, str]:
    if isinstance(ch, dict):
        title = str(ch.get("title") or "").strip()
        content = str(ch.get("content") or ch.get("text") or ch.get("summary") or "").strip()
        return {"title": title, "content": content}
    title = str(getattr(ch, "title", "") or "").strip()
    content = str(getattr(ch, "content", "") or "").strip()
    return {"title": title, "content": content}


def _normalize_chapters(chapters: Any) -> List[Dict[str, str]]:
    if not isinstance(chapters, list):
        return []
    out: List[Dict[str, str]] = []
    for ch in chapters:
        norm = _chapter_to_dict(ch)
        if norm.get("title") or norm.get("content"):
            out.append(norm)
    return out


def _build_payload(
    *,
    title: str,
    hook: str,
    chapters: Sequence[Any],
    full_script: str,
    sources: Sequence[Any],
    warnings: Sequence[Any],
    run_id: str,
    source_url: str,
    source_type: str,
    target_language: str,
    duration_minutes: int,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        # GenerateScriptResponse-Kern (Vertrag bleibt unverändert):
        "title": str(title or ""),
        "hook": str(hook or ""),
        "chapters": _normalize_chapters(chapters),
        "full_script": str(full_script or ""),
        "sources": _list_str(sources),
        "warnings": _list_str(warnings),
        # Bridge-Metadaten (zusätzlich, brechen Adapter-Kompatibilität nicht):
        "run_id": run_id,
        "source_url": source_url,
        "source_type": source_type,
        "target_language": target_language,
        "duration_minutes": int(duration_minutes),
        "created_at_epoch": int(time.time()),
    }
    return payload


# ----------------------------
# Generation paths
# ----------------------------


def _generate_article_payload(
    *,
    url: str,
    target_language: str,
    duration_minutes: int,
) -> Tuple[Dict[str, Any], List[str]]:
    """Return (response_dict, blocking_reasons). response_dict is None-equivalent if blocked."""
    try:
        text, extraction_warnings = extract_text_from_url(url)
    except Exception as exc:  # pragma: no cover — defensive
        return ({}, [f"article_extraction_exception:{type(exc).__name__}"])

    if not (text or "").strip():
        ws = list(extraction_warnings or [])
        ws.append("article_extraction_empty")
        return ({"warnings": ws}, ["article_extraction_empty"])

    try:
        title, hook, chapters, full_script, sources, warnings = (
            build_script_response_from_extracted_text(
                extracted_text=text,
                source_url=url,
                target_language=target_language,
                duration_minutes=duration_minutes,
                extraction_warnings=list(extraction_warnings or []),
                video_template="generic",
                template_conformance_level="warn",
            )
        )
    except Exception as exc:  # pragma: no cover — defensive
        return ({}, [f"article_generation_exception:{type(exc).__name__}"])

    return (
        {
            "title": title,
            "hook": hook,
            "chapters": chapters,
            "full_script": full_script,
            "sources": sources,
            "warnings": warnings,
        },
        [],
    )


def _generate_youtube_payload(
    *,
    url: str,
    target_language: str,
    duration_minutes: int,
) -> Tuple[Dict[str, Any], List[str]]:
    try:
        result = generate_script_from_youtube_video(
            url,
            target_language=target_language,
            duration_minutes=duration_minutes,
            video_template="generic",
            template_conformance_level="warn",
        )
    except Exception as exc:  # pragma: no cover — defensive
        return ({}, [f"youtube_generation_exception:{type(exc).__name__}"])

    # ``GenerateScriptResponse`` (pydantic) oder dict-ähnlich
    if hasattr(result, "model_dump"):
        data = result.model_dump()
    elif isinstance(result, dict):
        data = dict(result)
    else:
        data = {
            "title": getattr(result, "title", "") or "",
            "hook": getattr(result, "hook", "") or "",
            "chapters": getattr(result, "chapters", []) or [],
            "full_script": getattr(result, "full_script", "") or "",
            "sources": getattr(result, "sources", []) or [],
            "warnings": getattr(result, "warnings", []) or [],
        }

    title = data.get("title") or ""
    full_script = data.get("full_script") or ""
    chapters = data.get("chapters") or []
    if not (title or full_script or chapters):
        ws = _list_str(data.get("warnings"))
        if not ws:
            ws = ["youtube_generation_empty"]
        return ({"warnings": ws, "sources": _list_str(data.get("sources"))}, ["youtube_generation_empty"])

    return (data, [])


# ----------------------------
# Orchestration
# ----------------------------


def _run_dir(out_root: Path, run_id: str) -> Path:
    return Path(out_root).resolve() / f"url_script_{run_id}"


def _write_open_me(run_dir: Path, *, run_id: str, source_url: str, source_type: str) -> Path:
    md = (
        f"# URL-to-Script Bridge — {run_id}\n\n"
        f"BA 25.3 hat aus einer URL ein lokales `generate_script_response.json` erzeugt.\n\n"
        f"- **Source URL**: {source_url}\n"
        f"- **Source Type**: {source_type}\n"
        f"- **Datei**: `{URL_SCRIPT_RESULT_FILENAME}`\n\n"
        "Nächster Schritt (BA 25.4): Diese Datei mit "
        "`scripts/adapt_script_to_scene_asset_pack.py` in ein "
        "`scene_asset_pack.json` überführen und anschließend optional mit "
        "`scripts/run_real_video_build.py` lokal bauen.\n\n"
        "BA 25.3 selbst macht **keinen** Render, **keinen** Final Render, "
        "**keinen** Upload und **keinen** Orchestrator-Lauf.\n"
    )
    p = run_dir / URL_SCRIPT_OPEN_ME_FILENAME
    p.write_text(md, encoding="utf-8")
    return p


def run_bridge(
    *,
    url: str,
    run_id: str,
    target_language: str = "de",
    duration_minutes: int = 10,
    source_type: str = "auto",
    out_root: str = "output",
    write_open_me: bool = True,
) -> Dict[str, Any]:
    """Programmatische Eintrittsfunktion (für Tests).

    Liefert ein strukturiertes Result-Dict (kein Exception-Pfad bei
    erwartbaren Fehlern). Schreibt bei Erfolg ``generate_script_response.json``.
    """
    if not _validate_run_id(run_id):
        return {
            "ok": False,
            "status": "failed",
            "run_id": run_id,
            "error_code": "invalid_run_id",
            "blocking_reasons": ["invalid_run_id"],
            "warnings": [
                "run_id must match ^[A-Za-z0-9_-]{1,80}$ and contain no path separators."
            ],
            "exit_code": EXIT_INVALID_INPUT,
        }

    if not _is_http_url(url):
        return {
            "ok": False,
            "status": "failed",
            "run_id": run_id,
            "error_code": "invalid_url",
            "blocking_reasons": ["invalid_url"],
            "warnings": ["url must be an absolute http(s) URL."],
            "exit_code": EXIT_INVALID_INPUT,
        }

    requested_type = (source_type or "auto").strip().lower()
    if requested_type not in _VALID_SOURCE_TYPES:
        return {
            "ok": False,
            "status": "failed",
            "run_id": run_id,
            "error_code": "invalid_source_type",
            "blocking_reasons": ["invalid_source_type"],
            "warnings": [f"source_type must be one of {list(_VALID_SOURCE_TYPES)}."],
            "exit_code": EXIT_INVALID_INPUT,
        }

    if duration_minutes is None or int(duration_minutes) < 1:
        return {
            "ok": False,
            "status": "failed",
            "run_id": run_id,
            "error_code": "invalid_duration",
            "blocking_reasons": ["invalid_duration"],
            "warnings": ["duration_minutes must be a positive integer."],
            "exit_code": EXIT_INVALID_INPUT,
        }

    detected_type = detect_source_type(url, requested_type)

    run_dir = _run_dir(Path(out_root), run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    if detected_type == "youtube":
        gen, blocking = _generate_youtube_payload(
            url=url, target_language=target_language, duration_minutes=int(duration_minutes)
        )
    else:
        gen, blocking = _generate_article_payload(
            url=url, target_language=target_language, duration_minutes=int(duration_minutes)
        )

    if blocking:
        warnings = _list_str(gen.get("warnings"))
        return {
            "ok": False,
            "status": "failed",
            "run_id": run_id,
            "source_url": url,
            "source_type": detected_type,
            "build_dir": str(run_dir),
            "error_code": (blocking[0] if blocking else "generation_failed"),
            "blocking_reasons": list(blocking),
            "warnings": warnings,
            "exit_code": EXIT_FAILED,
        }

    payload = _build_payload(
        title=gen.get("title", ""),
        hook=gen.get("hook", ""),
        chapters=gen.get("chapters", []),
        full_script=gen.get("full_script", ""),
        sources=gen.get("sources", []),
        warnings=gen.get("warnings", []),
        run_id=run_id,
        source_url=url,
        source_type=detected_type,
        target_language=target_language,
        duration_minutes=int(duration_minutes),
    )

    out_path = run_dir / URL_SCRIPT_RESULT_FILENAME
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    open_me_path: Optional[Path] = None
    if write_open_me:
        try:
            open_me_path = _write_open_me(
                run_dir, run_id=run_id, source_url=url, source_type=detected_type
            )
        except OSError:
            open_me_path = None

    return {
        "ok": True,
        "status": "completed",
        "run_id": run_id,
        "source_url": url,
        "source_type": detected_type,
        "target_language": target_language,
        "duration_minutes": int(duration_minutes),
        "build_dir": str(run_dir),
        "generate_script_response_path": str(out_path),
        "open_me_path": str(open_me_path) if open_me_path else "",
        "warnings": payload.get("warnings", []),
        "blocking_reasons": [],
        "exit_code": EXIT_OK,
    }


# ----------------------------
# CLI
# ----------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "BA 25.3 — URL-to-Script Bridge. Erzeugt aus einer Artikel-/YouTube-URL "
            "ein lokales generate_script_response.json (kompatibel mit BA 25.2 Adapter)."
        )
    )
    p.add_argument("--url", required=True, dest="url")
    p.add_argument("--run-id", required=True, dest="run_id")
    p.add_argument("--target-language", default="de", dest="target_language")
    p.add_argument("--duration-minutes", type=int, default=10, dest="duration_minutes")
    p.add_argument(
        "--source-type",
        choices=list(_VALID_SOURCE_TYPES),
        default="auto",
        dest="source_type",
    )
    p.add_argument("--out-root", default="output", dest="out_root")
    p.add_argument("--print-json", action="store_true", dest="print_json")
    p.add_argument(
        "--no-open-me",
        action="store_true",
        dest="no_open_me",
        help="Optional: kein URL_SCRIPT_OPEN_ME.md schreiben.",
    )
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    result = run_bridge(
        url=args.url,
        run_id=args.run_id,
        target_language=args.target_language,
        duration_minutes=int(args.duration_minutes),
        source_type=args.source_type,
        out_root=args.out_root,
        write_open_me=not args.no_open_me,
    )

    exit_code = int(result.get("exit_code", EXIT_FAILED))
    printable = {k: v for k, v in result.items() if k != "exit_code"}
    if args.print_json:
        print(json.dumps(printable, ensure_ascii=False, indent=2))
    else:
        compact = {
            "ok": printable.get("ok"),
            "status": printable.get("status"),
            "run_id": printable.get("run_id"),
            "source_type": printable.get("source_type"),
            "build_dir": printable.get("build_dir"),
            "generate_script_response_path": printable.get("generate_script_response_path"),
            "blocking_reasons": printable.get("blocking_reasons", []),
        }
        if not printable.get("ok"):
            compact["error_code"] = printable.get("error_code", "")
            compact["warnings"] = printable.get("warnings", [])
        print(json.dumps(compact, ensure_ascii=False, indent=2))

    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
