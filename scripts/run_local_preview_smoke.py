"""BA 20.11 — Local Preview Smoke: ruft die Preview-Pipeline auf, kompakte Operator-Ausgabe + Exit Codes."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_PIPELINE_PATH = ROOT / "scripts" / "run_local_preview_pipeline.py"


def _load_pipeline() -> Any:
    spec = importlib.util.spec_from_file_location("run_local_preview_pipeline", _PIPELINE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {_PIPELINE_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_pipeline_mod: Any = None


def _pipeline() -> Any:
    global _pipeline_mod
    if _pipeline_mod is None:
        _pipeline_mod = _load_pipeline()
    return _pipeline_mod


def resolve_local_preview_smoke_video_path(paths: Any) -> str:
    """Delegiert an run_local_preview_pipeline (eine zentrale Pfad-Logik)."""
    return _pipeline().resolve_local_preview_video_path(paths)


def resolve_local_preview_smoke_report_path(result: Any) -> str:
    return _pipeline().resolve_local_preview_report_path(result)


def build_local_preview_smoke_summary(result: dict) -> str:
    """Menschenlesbare Smoke-Zusammenfassung (keine Secrets, tolerant bei fehlenden Keys)."""
    pl = _pipeline()
    verdict = pl.compute_local_preview_verdict(result if isinstance(result, dict) else {})
    paths = result.get("paths") if isinstance(result, dict) else None
    preview = resolve_local_preview_smoke_video_path(paths)
    if not preview:
        preview = "nicht verfügbar"
    report = resolve_local_preview_smoke_report_path(result if isinstance(result, dict) else {})
    if not report:
        report = "nicht verfügbar"
    open_me = pl.resolve_local_preview_open_me_path(result if isinstance(result, dict) else {})
    if not open_me:
        open_me = "nicht verfügbar"
    nxt = pl.local_preview_next_step_for_verdict(verdict)
    qc = result.get("quality_checklist") if isinstance(result, dict) else None
    q_status = ""
    if isinstance(qc, dict) and qc.get("status"):
        q_status = str(qc.get("status")).strip().upper()
    lines = [
        "Local Preview Smoke",
        "",
        f"Status: {verdict}",
    ]
    if q_status:
        lines.append(f"Quality: {q_status}")
    lines.extend(
        [
        f"Preview öffnen: {preview}",
        f"Report öffnen: {report}",
        f"Open-Me Datei: {open_me}",
        f"Nächster Schritt: {nxt}",
        "",
        ]
    )
    return "\n".join(lines)


def local_preview_exit_code(verdict: str) -> int:
    """PASS 0, WARNING 2, FAIL 1 (Smoke/Operator-Konvention BA 20.11)."""
    v = (verdict or "FAIL").strip().upper()
    if v == "PASS":
        return 0
    if v == "WARNING":
        return 2
    return 1


def main(argv: list[str] | None = None) -> int:
    pl = _pipeline()
    parser = argparse.ArgumentParser(
        description="BA 20.11 — Lokaler Preview-Smoke: Pipeline-Lauf + kompakte PASS/WARNING/FAIL-Ausgabe."
    )
    parser.add_argument("--timeline-manifest", type=Path, required=True, dest="timeline_manifest")
    parser.add_argument("--narration-script", type=Path, required=True, dest="narration_script")
    parser.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    parser.add_argument("--run-id", default="", dest="run_id")
    parser.add_argument(
        "--motion-mode",
        choices=("static", "basic"),
        default="static",
        dest="motion_mode",
    )
    parser.add_argument(
        "--subtitle-mode",
        choices=("none", "simple"),
        default="simple",
        dest="subtitle_mode",
    )
    parser.add_argument(
        "--subtitle-style",
        choices=("classic", "word_by_word", "typewriter", "karaoke", "none"),
        default="classic",
        dest="subtitle_style",
    )
    parser.add_argument(
        "--subtitle-source",
        choices=("narration", "audio"),
        default="narration",
        dest="subtitle_source",
    )
    parser.add_argument("--audio-path", type=Path, default=None, dest="audio_path")
    parser.add_argument("--force-burn", action="store_true", dest="force_burn")
    parser.add_argument(
        "--print-json",
        action="store_true",
        dest="print_json",
        help="Nach der Zusammenfassung das vollständige Pipeline-JSON ausgeben",
    )
    args = parser.parse_args(argv)

    meta = pl.run_local_preview_pipeline(
        args.timeline_manifest,
        args.narration_script,
        out_root=args.out_root,
        run_id=(args.run_id or "").strip() or str(uuid.uuid4()),
        motion_mode=args.motion_mode,
        subtitle_mode=args.subtitle_mode,
        subtitle_style=args.subtitle_style,
        subtitle_source=args.subtitle_source,
        audio_path=args.audio_path,
        force_burn=bool(args.force_burn),
    )
    summary = build_local_preview_smoke_summary(meta)
    print(summary, end="")
    if args.print_json:
        print("\n---\n")
        print(json.dumps(meta, ensure_ascii=False, indent=2))
    v = pl.compute_local_preview_verdict(meta)
    return local_preview_exit_code(v)


if __name__ == "__main__":
    raise SystemExit(main())
