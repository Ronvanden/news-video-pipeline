"""BA 32.75 — Thumbnail Text Overlay Smoke (local only).

- No API keys required
- No provider calls
- Reads existing PNG/JPG and writes 1280x720 thumbnail_final.png + JSON report
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.production_connectors.thumbnail_overlay import run_thumbnail_overlay_v1


def main() -> int:
    p = argparse.ArgumentParser(description="BA 32.75 — Local Thumbnail Text Overlay (no providers).")
    p.add_argument("--image-path", required=True, dest="image_path")
    p.add_argument("--run-id", default="", dest="run_id")
    p.add_argument("--title", required=True, dest="title")
    p.add_argument("--summary", default="", dest="summary")
    p.add_argument(
        "--text",
        default="",
        dest="text",
        help='Optional override: "LINE1|LINE2" oder "LINE1".',
    )
    p.add_argument("--position", default="auto_right", dest="position", choices=("auto_right", "right", "left"))
    p.add_argument(
        "--style-preset",
        default="impact_youtube",
        dest="style_preset",
        choices=("clean_bold", "impact_youtube", "urgent_mystery", "documentary_poster"),
    )
    p.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    args = p.parse_args()

    rid = (args.run_id or "").strip() or f"ov_{uuid.uuid4().hex[:12]}"
    out_dir = Path(args.out_root).resolve() / f"thumbnail_overlay_smoke_{rid}"
    out_dir.mkdir(parents=True, exist_ok=True)

    body = run_thumbnail_overlay_v1(
        image_path=Path(args.image_path).resolve(),
        title=str(args.title or "").strip(),
        summary=str(args.summary or "").strip() or None,
        text_variant=str(args.text or "").strip() or None,
        output_dir=out_dir,
        position=str(args.position or "auto_right"),
        language="de",
        style_preset=str(args.style_preset or "impact_youtube"),
    )
    print(json.dumps(body, ensure_ascii=False, indent=2))
    return 0 if body.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())

