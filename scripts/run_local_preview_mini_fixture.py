"""BA 21.0 — Shortcut: Local Preview Smoke mit fixtures/local_preview_mini (keine Logik-Duplikation)."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_FIXTURE_DIR = ROOT / "fixtures" / "local_preview_mini"
_TIMELINE = _FIXTURE_DIR / "mini_timeline_manifest.json"
_NARRATION = _FIXTURE_DIR / "mini_narration.txt"
_SMOKE_SCRIPT = ROOT / "scripts" / "run_local_preview_smoke.py"


def build_mini_fixture_argv(
    *,
    out_root: Path,
    run_id: str,
    print_json: bool,
    motion_mode: str = "static",
    subtitle_style: str = "typewriter",
    extra: Optional[List[str]] = None,
) -> List[str]:
    """Argv nur mit Optionen (ohne argv[0]) für `run_local_preview_smoke.main(argv)`."""
    argv: List[str] = [
        "--timeline-manifest",
        str(_TIMELINE),
        "--narration-script",
        str(_NARRATION),
        "--out-root",
        str(out_root),
        "--run-id",
        run_id,
        "--motion-mode",
        motion_mode,
        "--subtitle-style",
        subtitle_style,
    ]
    if print_json:
        argv.append("--print-json")
    if extra:
        argv.extend(extra)
    return argv


def _load_smoke_main():
    spec = importlib.util.spec_from_file_location("run_local_preview_smoke", _SMOKE_SCRIPT)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {_SMOKE_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="BA 21.0 — Ruft run_local_preview_smoke mit fixtures/local_preview_mini auf."
    )
    parser.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    parser.add_argument("--run-id", default="mini_e2e", dest="run_id")
    parser.add_argument("--print-json", action="store_true", dest="print_json")
    parser.add_argument(
        "--motion-mode",
        choices=("static", "basic"),
        default="static",
        dest="motion_mode",
    )
    parser.add_argument(
        "--subtitle-style",
        choices=("classic", "word_by_word", "typewriter", "karaoke", "none"),
        default="typewriter",
        dest="subtitle_style",
    )
    parser.add_argument(
        "passthrough",
        nargs="*",
        help="Zusätzliche Argumente für run_local_preview_smoke (nach --)",
    )
    args, unknown = parser.parse_known_args(argv)
    extra = list(args.passthrough or []) + list(unknown or [])
    smoke_main = _load_smoke_main()
    built = build_mini_fixture_argv(
        out_root=args.out_root,
        run_id=(args.run_id or "").strip() or "mini_e2e",
        print_json=bool(args.print_json),
        motion_mode=args.motion_mode,
        subtitle_style=args.subtitle_style,
        extra=extra if extra else None,
    )
    return int(smoke_main(built))


if __name__ == "__main__":
    raise SystemExit(main())
