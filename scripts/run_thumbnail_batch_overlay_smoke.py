"""BA 32.76 — Thumbnail Batch Overlay + Selection Smoke (local only).

- No API keys required
- No provider calls
- Combines existing thumbnail_candidate_*.png with text variants + style presets
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

from app.production_connectors.thumbnail_batch_overlay import run_thumbnail_batch_overlay_v1


def main() -> int:
    p = argparse.ArgumentParser(description="BA 32.76 — Local Thumbnail Batch Overlay + heuristic selection.")
    p.add_argument("--candidate-dir", default="", dest="candidate_dir")
    p.add_argument("--candidate-path", action="append", default=[], dest="candidate_paths")
    p.add_argument("--title", required=True, dest="title")
    p.add_argument("--summary", default="", dest="summary")
    p.add_argument("--run-id", default="", dest="run_id")
    p.add_argument("--max-outputs", type=int, default=6, dest="max_outputs")
    p.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    args = p.parse_args()

    rid = (args.run_id or "").strip() or f"batch_{uuid.uuid4().hex[:12]}"
    out_dir = Path(args.out_root).resolve() / f"thumbnail_batch_overlay_smoke_{rid}"
    out_dir.mkdir(parents=True, exist_ok=True)

    paths: list[str] = []
    if str(args.candidate_dir or "").strip():
        cdir = Path(args.candidate_dir).resolve()
        if cdir.is_dir():
            for pth in sorted(cdir.glob("thumbnail_candidate_*.png")):
                paths.append(str(pth.resolve()))
    if args.candidate_paths:
        for x in args.candidate_paths:
            if x:
                paths.append(str(Path(x).resolve()))

    # Must have at least one candidate image.
    paths = [p for p in paths if Path(p).is_file()]
    if not paths:
        payload = {
            "ok": False,
            "blocking_reason": "thumbnail_batch_overlay_no_candidates",
            "hint": "Nutze --candidate-dir oder --candidate-path (mindestens eine PNG).",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    body = run_thumbnail_batch_overlay_v1(
        candidate_paths=paths,
        title=str(args.title or "").strip(),
        summary=str(args.summary or "").strip() or None,
        output_dir=out_dir,
        language="de",
        max_outputs=int(args.max_outputs),
        style_presets=["impact_youtube", "urgent_mystery"],
        text_variants=None,
    )
    print(json.dumps(body, ensure_ascii=False, indent=2))
    return 0 if body.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())

