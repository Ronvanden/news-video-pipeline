"""BA 32.74 — Thumbnail Candidates Smoke (1–3 PNGs, OpenAI Image 2).

CLI-first. Keine Provider-Calls in CI.
Sicherheit:
- Ohne --confirm-live-openai-image: Exit 3 + JSON blocking_reason.
- Keine Secrets / API-Bodies / Bearer Tokens in stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.production_connectors.thumbnail_candidates import run_thumbnail_candidates_v1


RESULT_NAME = "thumbnail_candidates_smoke_result.json"


def main() -> int:
    p = argparse.ArgumentParser(
        description="BA 32.74 — Thumbnail Candidates Smoke: 1–3 Thumbnail-Kandidaten (gpt-image-2 Preferred Path). "
        "Keine Response-Bodies; keine Secrets in der Ausgabe."
    )
    p.add_argument(
        "--confirm-live-openai-image",
        action="store_true",
        dest="confirm",
        help="Pflicht: 1–3 echte OpenAI Images API Calls (Kostenfreigabe).",
    )
    p.add_argument("--run-id", default="", dest="run_id")
    p.add_argument("--title", default="", dest="title")
    p.add_argument("--summary", default="", dest="summary")
    p.add_argument("--video-template", default="", dest="video_template")
    p.add_argument("--count", type=int, default=3, dest="count", help="1–3 (max 3).")
    p.add_argument("--model", default=None, dest="model")
    p.add_argument("--size", default="1024x1024", dest="size")
    p.add_argument("--timeout-seconds", type=float, default=120.0, dest="timeout_seconds")
    p.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")

    args = p.parse_args()

    if not args.confirm:
        print(
            json.dumps(
                {
                    "ok": False,
                    "blocking_reason": "confirm_live_openai_image_required",
                    "hint": "Erneut mit --confirm-live-openai-image (bewusste Kostenfreigabe).",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 3

    rid = (args.run_id or "").strip() or f"thumb_{uuid.uuid4().hex[:12]}"
    work_dir = Path(args.out_root).resolve() / f"thumbnail_candidates_smoke_{rid}"
    work_dir.mkdir(parents=True, exist_ok=True)

    env_model = (os.environ.get("OPENAI_IMAGE_MODEL") or "").strip()
    cli_model = (args.model or "").strip() if args.model is not None else ""
    effective_model = cli_model or env_model or "gpt-image-2"

    body = run_thumbnail_candidates_v1(
        output_dir=work_dir,
        title=str(args.title or "").strip() or None,
        summary=str(args.summary or "").strip() or None,
        video_template=str(args.video_template or "").strip() or None,
        count=int(args.count),
        target_platform="youtube",
        model=effective_model,
        size=str(args.size or "").strip() or "1024x1024",
        timeout_seconds=float(args.timeout_seconds),
        dry_run=False,
    )

    result_path = work_dir / RESULT_NAME
    payload = {
        **(body or {}),
        "run_id": rid,
        "result_path": str(result_path.resolve()),
        "output_dir": str(work_dir.resolve()),
    }
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())

