"""BA 15.8 — Batch-URL-Analyse (Ranking, keine Provider-Ausführung)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.manual_url_story.batch_engine import parse_urls_file_lines, run_batch_url_demo


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch URLs → Rewrite + Quality-Gate + Ranking.")
    parser.add_argument(
        "input_path",
        nargs="?",
        help="Textdatei: eine URL pro Zeile (# Kommentare erlaubt)",
    )
    parser.add_argument(
        "--json-file",
        dest="json_file",
        help='JSON: ["url", …] oder {"urls": […]}',
    )
    parser.add_argument("--rewrite-mode", default="", dest="rewrite_mode")
    parser.add_argument("--top-n", type=int, default=5, dest="top_n")
    parser.add_argument("--duration-minutes", type=int, default=10, dest="duration_minutes")
    args = parser.parse_args()

    urls: list[str] = []
    if args.json_file:
        raw = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
        if isinstance(raw, list):
            urls = [str(u).strip() for u in raw if str(u).strip()]
        elif isinstance(raw, dict) and isinstance(raw.get("urls"), list):
            urls = [str(u).strip() for u in raw["urls"] if str(u).strip()]
        else:
            print("JSON muss eine URL-Liste oder {\"urls\": [...]} sein.", file=sys.stderr)
            return 2
    elif args.input_path:
        text = Path(args.input_path).read_text(encoding="utf-8")
        urls = parse_urls_file_lines(text)
    else:
        parser.error("input_path oder --json-file angeben")

    result = run_batch_url_demo(
        urls,
        manual_url_rewrite_mode=args.rewrite_mode,
        manual_url_duration_minutes=args.duration_minutes,
        top_n=args.top_n,
    )
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
