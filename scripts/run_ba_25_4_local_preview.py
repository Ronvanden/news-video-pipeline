"""BA 25.4 — Real Local Preview Run.

Verbindet die bereits vorhandenen BA-25.x-Bausteine zu **einem** lokalen Lauf:

    generate_script_response.json
      → (BA 25.2 Adapter)        → scene_asset_pack.json
      → (BA 25.1 Orchestrator / run_real_video_build.py)
      → preview_with_subtitles.mp4
      → real_video_build_result.json

Strikte Grenzen (BA 25.4):

- **Keine** neuen Provider-Calls (kein Live-TTS-Zwang, kein Live-Leonardo-Zwang).
- **Keine** neue Cost Engine.
- **Keine** Änderung an ``GenerateScriptResponse``, ``scene_asset_pack.json``
  oder ``real_video_build_result.json``.
- **Kein** Final Render und **kein** Publishing.

BA 25.4 erzeugt zusätzlich ein eigenes Aggregat-Artefakt unter
``output/real_local_preview_<run_id>/real_local_preview_result.json`` und
zeigt auf das vom Orchestrator gepflegte ``real_build_<run_id>``-Indexpaket.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.real_video_build.script_input_adapter import (
    build_scene_asset_pack_from_generate_script_response,
    build_scene_asset_pack_from_story_pack,
    write_scene_asset_pack,
)

_REAL_BUILD_SCRIPT = ROOT / "scripts" / "run_real_video_build.py"

REAL_LOCAL_PREVIEW_RESULT_FILENAME = "real_local_preview_result.json"
REAL_LOCAL_PREVIEW_RESULT_SCHEMA = "real_local_preview_result_v1"
REAL_LOCAL_PREVIEW_OPEN_ME_FILENAME = "REAL_LOCAL_PREVIEW_OPEN_ME.md"

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_BLOCKED = 2
EXIT_INVALID_INPUT = 3

_RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


# ----------------------------
# Helpers
# ----------------------------


def _s(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _list_str(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x if i is not None and str(i).strip() != ""]
    if isinstance(x, (str, int, float, bool)):
        t = str(x).strip()
        return [t] if t else []
    return [str(x)]


def _validate_run_id(run_id: str) -> bool:
    s = (run_id or "").strip()
    if not s or ".." in s or "/" in s or "\\" in s:
        return False
    return bool(_RUN_ID_RE.fullmatch(s))


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _looks_like_generate_script_response(d: Dict[str, Any]) -> bool:
    """Same heuristic as ``scripts/adapt_script_to_scene_asset_pack.py``."""
    if not isinstance(d, dict):
        return False
    keys = set(d.keys())
    if not ({"chapters", "full_script", "hook", "title"} & keys):
        return False
    return ("chapters" in keys) or ("full_script" in keys)


def _read_script_json(path: Path) -> Dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("script JSON must be an object (dict)")
    return raw


def _next_step_for_status(status: str) -> str:
    s = (status or "").strip().lower()
    if s == "completed":
        return (
            "Öffne preview_with_subtitles.mp4 (siehe Pfad im Result). "
            "Final Render bleibt der bestehende BA 24.x-Flow (run_final_render.py)."
        )
    if s == "blocked":
        return (
            "Blocking-Reasons im Result prüfen "
            "(z. B. invalid_run_id, generate_script_response_unusable, ffmpeg_missing)."
        )
    if s == "failed":
        return (
            "Letzten Step im Orchestrator-Manifest prüfen "
            "(real_video_build_result.json) und ggf. mit --force erneut starten."
        )
    return "Result-Datei prüfen."


def _empty_paths() -> Dict[str, str]:
    return {
        "script_json": "",
        "scene_asset_pack": "",
        "real_build_dir": "",
        "real_video_build_result": "",
        "preview_with_subtitles": "",
        "clean_video": "",
        "subtitle_manifest": "",
        "subtitle_file": "",
        "narration_script": "",
        "voiceover_audio": "",
        "local_preview_dir": "",
        "open_me": "",
    }


# ----------------------------
# Orchestrator default callable
# ----------------------------


def _default_orchestrator_fn(**kwargs: Any) -> Dict[str, Any]:
    """Lädt ``run_real_video_build`` per importlib (kein scripts/ als Package nötig)."""
    mod = _load_module("run_real_video_build_for_ba_25_4", _REAL_BUILD_SCRIPT)
    return mod.run_real_video_build(**kwargs)


# ----------------------------
# OPEN_ME helper
# ----------------------------


def _write_open_me(
    run_dir: Path,
    *,
    run_id: str,
    script_json_path: Path,
    pack_path: Path,
    real_build_result_path: str,
    preview_path: str,
    status: str,
) -> Path:
    md_lines = [
        f"# Real Local Preview Run — {run_id}",
        "",
        "BA 25.4 hat aus einem realen `generate_script_response.json` ein lokales "
        "Preview-Paket gebaut (BA 25.2 Adapter → BA 25.1 Orchestrator).",
        "",
        f"- **Status**: {status}",
        f"- **Script-Input**: `{script_json_path}`",
        f"- **Scene Asset Pack**: `{pack_path}`",
    ]
    if real_build_result_path:
        md_lines.append(f"- **Real Build Result**: `{real_build_result_path}`")
    if preview_path:
        md_lines.append(f"- **Preview Video**: `{preview_path}`")
    md_lines.extend(
        [
            "",
            "BA 25.4 ändert weder den `GenerateScriptResponse`-Vertrag noch das "
            "`scene_asset_pack.json`- oder `real_video_build_result.json`-Schema. "
            "Final Render bleibt der bestehende BA 24.x-Flow "
            "(`scripts/run_final_render.py`).",
            "",
        ]
    )
    p = run_dir / REAL_LOCAL_PREVIEW_OPEN_ME_FILENAME
    p.write_text("\n".join(md_lines), encoding="utf-8")
    return p


# ----------------------------
# Main entry: programmatic
# ----------------------------


def run_real_local_preview(
    *,
    script_json_path: Path,
    run_id: str,
    out_root: Path = Path("output"),
    asset_mode: str = "placeholder",
    voice_mode: str = "smoke",
    motion_mode: str = "static",
    subtitle_style: str = "typewriter",
    subtitle_mode: str = "simple",
    force: bool = False,
    write_open_me: bool = True,
    orchestrator_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    adapter_generate_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    adapter_story_fn: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Programmatische Eintrittsfunktion (für Tests und CLI).

    Liefert ein strukturiertes Result-Dict (kein Exception-Pfad bei
    erwartbaren Fehlern). Schreibt bei Erfolg ``scene_asset_pack.json``,
    ``real_local_preview_result.json`` und delegiert die Render-Kette an
    den BA-25.1-Orchestrator (``run_real_video_build``).
    """
    rid = _s(run_id)
    out_root_p = Path(out_root).resolve()
    paths = _empty_paths()
    warnings: List[str] = []

    if not _validate_run_id(rid):
        return {
            "schema_version": REAL_LOCAL_PREVIEW_RESULT_SCHEMA,
            "run_id": rid,
            "ok": False,
            "status": "blocked",
            "build_dir": "",
            "metadata": {},
            "paths": paths,
            "real_build_result": None,
            "warnings": [],
            "blocking_reasons": ["invalid_run_id"],
            "next_step": "run_id muss zu ^[A-Za-z0-9_-]{1,80}$ passen und keine Pfadtrenner enthalten.",
            "exit_code": EXIT_INVALID_INPUT,
            "created_at_epoch": int(time.time()),
        }

    src_path = Path(script_json_path).resolve()
    paths["script_json"] = str(src_path)
    if not src_path.is_file():
        return {
            "schema_version": REAL_LOCAL_PREVIEW_RESULT_SCHEMA,
            "run_id": rid,
            "ok": False,
            "status": "blocked",
            "build_dir": "",
            "metadata": {},
            "paths": paths,
            "real_build_result": None,
            "warnings": [],
            "blocking_reasons": ["script_json_missing"],
            "next_step": (
                "Pfad zu generate_script_response.json prüfen (z. B. Ergebnis aus BA 25.3)."
            ),
            "exit_code": EXIT_INVALID_INPUT,
            "created_at_epoch": int(time.time()),
        }

    run_dir = out_root_p / f"real_local_preview_{rid}"
    run_dir.mkdir(parents=True, exist_ok=True)
    paths["local_preview_dir"] = str(run_dir)

    # 1) Read script JSON + run BA 25.2 adapter
    try:
        script_data = _read_script_json(src_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {
            "schema_version": REAL_LOCAL_PREVIEW_RESULT_SCHEMA,
            "run_id": rid,
            "ok": False,
            "status": "blocked",
            "build_dir": str(run_dir),
            "metadata": {},
            "paths": paths,
            "real_build_result": None,
            "warnings": [],
            "blocking_reasons": ["script_json_invalid"],
            "next_step": f"Script-JSON nicht lesbar: {type(exc).__name__}",
            "exit_code": EXIT_INVALID_INPUT,
            "created_at_epoch": int(time.time()),
        }

    gen_fn = adapter_generate_fn or build_scene_asset_pack_from_generate_script_response
    story_fn = adapter_story_fn or build_scene_asset_pack_from_story_pack

    try:
        if _looks_like_generate_script_response(script_data):
            pack = gen_fn(script_data, run_id=rid)
            adapter_used = "generate_script_response"
        else:
            pack = story_fn(script_data, run_id=rid)
            adapter_used = "story_pack"
    except Exception as exc:  # pragma: no cover — defensive
        return {
            "schema_version": REAL_LOCAL_PREVIEW_RESULT_SCHEMA,
            "run_id": rid,
            "ok": False,
            "status": "blocked",
            "build_dir": str(run_dir),
            "metadata": {},
            "paths": paths,
            "real_build_result": None,
            "warnings": [],
            "blocking_reasons": ["generate_script_response_unusable"],
            "next_step": (
                "Adapter konnte aus dem Script-JSON keine Szenen ableiten "
                f"({type(exc).__name__}: {str(exc)[:160]})."
            ),
            "exit_code": EXIT_FAILED,
            "created_at_epoch": int(time.time()),
        }

    pack_path = run_dir / "scene_asset_pack.json"
    try:
        write_scene_asset_pack(pack, pack_path)
    except OSError as exc:
        return {
            "schema_version": REAL_LOCAL_PREVIEW_RESULT_SCHEMA,
            "run_id": rid,
            "ok": False,
            "status": "failed",
            "build_dir": str(run_dir),
            "metadata": {"adapter": adapter_used},
            "paths": paths,
            "real_build_result": None,
            "warnings": [f"scene_asset_pack_write_failed:{type(exc).__name__}"],
            "blocking_reasons": ["scene_asset_pack_write_failed"],
            "next_step": "Schreibrechte auf out_root prüfen.",
            "exit_code": EXIT_FAILED,
            "created_at_epoch": int(time.time()),
        }
    paths["scene_asset_pack"] = str(pack_path.resolve())

    beats = ((pack.get("scene_expansion") or {}).get("expanded_scene_assets") or [])
    if not beats:
        warnings.append("scene_asset_pack_no_beats")

    metadata: Dict[str, Any] = {
        "adapter": adapter_used,
        "asset_mode": asset_mode,
        "voice_mode": voice_mode,
        "motion_mode": motion_mode,
        "subtitle_style": subtitle_style,
        "subtitle_mode": subtitle_mode,
        "force": bool(force),
        "beat_count": len(beats),
        "title": _s(script_data.get("title")),
        "hook_present": bool(_s(script_data.get("hook"))),
    }

    # 2) Run BA 25.1 orchestrator on the freshly built pack
    orch = orchestrator_fn or _default_orchestrator_fn
    try:
        real_build_result = orch(
            run_id=rid,
            scene_asset_pack=pack_path,
            out_root=out_root_p,
            asset_mode=asset_mode,
            voice_mode=voice_mode,
            motion_mode=motion_mode,
            subtitle_style=subtitle_style,
            subtitle_mode=subtitle_mode,
            force=bool(force),
        )
    except Exception as exc:  # pragma: no cover — defensive
        return {
            "schema_version": REAL_LOCAL_PREVIEW_RESULT_SCHEMA,
            "run_id": rid,
            "ok": False,
            "status": "failed",
            "build_dir": str(run_dir),
            "metadata": metadata,
            "paths": paths,
            "real_build_result": None,
            "warnings": list(warnings),
            "blocking_reasons": [f"orchestrator_exception:{type(exc).__name__}"],
            "next_step": "BA 25.1 Orchestrator-Aufruf ist gescheitert; Logs prüfen.",
            "exit_code": EXIT_FAILED,
            "created_at_epoch": int(time.time()),
        }

    if not isinstance(real_build_result, dict):
        return {
            "schema_version": REAL_LOCAL_PREVIEW_RESULT_SCHEMA,
            "run_id": rid,
            "ok": False,
            "status": "failed",
            "build_dir": str(run_dir),
            "metadata": metadata,
            "paths": paths,
            "real_build_result": None,
            "warnings": list(warnings),
            "blocking_reasons": ["orchestrator_invalid_result"],
            "next_step": "Orchestrator hat kein dict-Result geliefert.",
            "exit_code": EXIT_FAILED,
            "created_at_epoch": int(time.time()),
        }

    # 3) Aggregate
    rb_paths = real_build_result.get("paths") if isinstance(real_build_result.get("paths"), dict) else {}
    rb_status = _s(real_build_result.get("status")).lower() or "failed"
    rb_blocking = _list_str(real_build_result.get("blocking_reasons"))
    rb_warnings = _list_str(real_build_result.get("warnings"))
    rb_build_dir = _s(real_build_result.get("build_dir"))

    paths["real_build_dir"] = rb_build_dir
    if rb_build_dir:
        result_file = Path(rb_build_dir) / "real_video_build_result.json"
        if result_file.is_file():
            paths["real_video_build_result"] = str(result_file.resolve())

    paths["preview_with_subtitles"] = _s(rb_paths.get("preview_with_subtitles"))
    paths["clean_video"] = _s(rb_paths.get("clean_video"))
    paths["subtitle_manifest"] = _s(rb_paths.get("subtitle_manifest"))
    paths["subtitle_file"] = _s(rb_paths.get("subtitle_file"))
    paths["narration_script"] = _s(rb_paths.get("narration_script"))
    paths["voiceover_audio"] = _s(rb_paths.get("voiceover_audio"))

    # Normalize aggregate status: completed only if orchestrator completed and preview exists.
    if rb_status == "completed" and paths["preview_with_subtitles"]:
        agg_status = "completed"
        exit_code = EXIT_OK
    elif rb_status == "blocked":
        agg_status = "blocked"
        exit_code = EXIT_BLOCKED
    elif rb_status == "completed" and not paths["preview_with_subtitles"]:
        agg_status = "blocked"
        exit_code = EXIT_BLOCKED
        rb_blocking = list(dict.fromkeys(rb_blocking + ["preview_with_subtitles_missing"]))
    else:
        agg_status = "failed"
        exit_code = EXIT_FAILED

    if write_open_me:
        try:
            open_me_path = _write_open_me(
                run_dir,
                run_id=rid,
                script_json_path=src_path,
                pack_path=pack_path,
                real_build_result_path=paths["real_video_build_result"],
                preview_path=paths["preview_with_subtitles"],
                status=agg_status,
            )
            paths["open_me"] = str(open_me_path.resolve())
        except OSError as exc:
            warnings.append(f"open_me_write_failed:{type(exc).__name__}")

    aggregate: Dict[str, Any] = {
        "schema_version": REAL_LOCAL_PREVIEW_RESULT_SCHEMA,
        "run_id": rid,
        "ok": agg_status == "completed",
        "status": agg_status,
        "build_dir": str(run_dir),
        "metadata": metadata,
        "paths": paths,
        "real_build_result": real_build_result,
        "warnings": list(dict.fromkeys(list(warnings) + list(rb_warnings))),
        "blocking_reasons": list(dict.fromkeys(rb_blocking)),
        "next_step": _next_step_for_status(agg_status),
        "exit_code": exit_code,
        "created_at_epoch": int(time.time()),
    }

    try:
        (run_dir / REAL_LOCAL_PREVIEW_RESULT_FILENAME).write_text(
            json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        aggregate["warnings"].append(f"real_local_preview_result_write_failed:{type(exc).__name__}")

    return aggregate


# ----------------------------
# CLI
# ----------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "BA 25.4 — Real Local Preview Run: nimmt ein generate_script_response.json "
            "(z. B. aus BA 25.3) und erzeugt lokal Scene Asset Pack + Real Video Build "
            "Preview-Paket (BA 25.2 Adapter → BA 25.1 Orchestrator). Kein Final Render, "
            "kein Publishing, keine neuen Provider-Calls."
        )
    )
    p.add_argument(
        "--script-json",
        type=Path,
        required=True,
        dest="script_json",
        help="Pfad zu generate_script_response.json (oder Story-Pack JSON).",
    )
    p.add_argument("--run-id", required=True, dest="run_id")
    p.add_argument(
        "--out-root",
        type=Path,
        default=ROOT / "output",
        dest="out_root",
    )
    p.add_argument(
        "--asset-mode",
        choices=("placeholder", "live"),
        default="placeholder",
        dest="asset_mode",
    )
    p.add_argument(
        "--voice-mode",
        choices=("smoke",),
        default="smoke",
        dest="voice_mode",
        help="BA 25.4 erzwingt smoke (TTS-Live ist BA-25.x-Folgearbeit).",
    )
    p.add_argument(
        "--motion-mode",
        choices=("static", "basic"),
        default="static",
        dest="motion_mode",
    )
    p.add_argument(
        "--subtitle-style",
        choices=("classic", "word_by_word", "typewriter", "karaoke", "none"),
        default="typewriter",
        dest="subtitle_style",
    )
    p.add_argument(
        "--subtitle-mode",
        choices=("none", "simple"),
        default="simple",
        dest="subtitle_mode",
    )
    p.add_argument("--force", action="store_true", dest="force")
    p.add_argument("--print-json", action="store_true", dest="print_json")
    p.add_argument(
        "--no-open-me",
        action="store_true",
        dest="no_open_me",
        help="Optional: kein REAL_LOCAL_PREVIEW_OPEN_ME.md schreiben.",
    )
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    result = run_real_local_preview(
        script_json_path=Path(args.script_json),
        run_id=args.run_id,
        out_root=Path(args.out_root),
        asset_mode=args.asset_mode,
        voice_mode=args.voice_mode,
        motion_mode=args.motion_mode,
        subtitle_style=args.subtitle_style,
        subtitle_mode=args.subtitle_mode,
        force=bool(args.force),
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
            "build_dir": printable.get("build_dir"),
            "scene_asset_pack": (printable.get("paths") or {}).get("scene_asset_pack", ""),
            "real_video_build_result": (printable.get("paths") or {}).get(
                "real_video_build_result", ""
            ),
            "preview_with_subtitles": (printable.get("paths") or {}).get(
                "preview_with_subtitles", ""
            ),
            "blocking_reasons": printable.get("blocking_reasons", []),
        }
        if not printable.get("ok"):
            compact["warnings"] = printable.get("warnings", [])
        print(json.dumps(compact, ensure_ascii=False, indent=2))

    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
