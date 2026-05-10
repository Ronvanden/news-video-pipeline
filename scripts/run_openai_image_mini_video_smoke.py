"""BA 32.71c — Ein OpenAI-Image-2-Bild (oder vorhandenes PNG) → kurzes MP4 (1 Szene)."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.production_connectors.openai_image_mini_video_smoke import run_openai_image_mini_video_smoke_v1

RESULT_NAME = "openai_image_mini_video_smoke_result.json"


def main() -> int:
    p = argparse.ArgumentParser(
        description=(
            "BA 32.71c — Mini-Video-Smoke: 1 PNG + Timeline + render_final_story_video (static). "
            "Ohne --image-path: genau ein OpenAI-Bild via Pipeline-Smoke-Pfad. "
            "Keine Response-Bodies; keine Secrets in der Ausgabe."
        )
    )
    p.add_argument(
        "--confirm-live-openai-image",
        action="store_true",
        dest="confirm",
        help="Pflicht: Live-Smoke bestätigen (API nur wenn kein --image-path).",
    )
    p.add_argument("--run-id", default="", dest="run_id")
    p.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    p.add_argument(
        "--model",
        default=None,
        dest="model",
        help="OpenAI-Bildmodell wenn Bild generiert wird (Default: OPENAI_IMAGE_MODEL oder gpt-image-2). Kein automatischer Fallback.",
    )
    p.add_argument("--size", default="1024x1024", dest="size")
    p.add_argument(
        "--duration-seconds",
        type=int,
        default=12,
        dest="duration_seconds",
        help="Szenendauer / Timeline-Segment (Default 12, min 3, max 600).",
    )
    p.add_argument(
        "--image-path",
        type=Path,
        default=None,
        dest="image_path",
        help="Optional: bestehendes PNG; sonst wird genau ein Bild über die Pipeline erzeugt.",
    )
    p.add_argument("--timeout-seconds", type=float, default=120.0, dest="timeout_seconds")
    p.add_argument(
        "--motion-mode",
        choices=("static", "basic"),
        default="static",
        dest="motion_mode",
        help="Render-Modus (Default static — minimaler ffmpeg-Pfad).",
    )

    args = p.parse_args()

    if not args.confirm:
        print(
            json.dumps(
                {
                    "ok": False,
                    "blocking_reason": "confirm_live_openai_image_required",
                    "hint": "Wiederholen mit --confirm-live-openai-image.",
                    "smoke_version": "ba32_71c_v1",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 3

    rid = (args.run_id or "").strip() or f"mv_{uuid.uuid4().hex[:12]}"
    img_arg = Path(args.image_path).resolve() if args.image_path is not None else None

    body = run_openai_image_mini_video_smoke_v1(
        run_id=rid,
        out_root=Path(args.out_root).resolve(),
        model=args.model,
        size=str(args.size).strip() or "1024x1024",
        duration_seconds=int(args.duration_seconds),
        image_path=img_arg,
        openai_image_timeout_seconds=float(args.timeout_seconds),
        motion_mode=str(args.motion_mode),
    )

    work_parent = Path(args.out_root).resolve() / f"openai_image_mini_video_smoke_{rid}"
    result_path = work_parent / RESULT_NAME
    payload = {**body, "result_path": str(result_path.resolve())}
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if body.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
