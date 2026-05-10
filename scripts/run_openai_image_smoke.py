"""BA 32.70 — Ein Call OpenAI Images API (Live); strukturiertes JSON, keine Bodies, keine Secrets."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.production_connectors.openai_image_smoke import run_openai_image_smoke_v1

RESULT_NAME = "openai_image_smoke_result.json"


def main() -> int:
    p = argparse.ArgumentParser(
        description="BA 32.70 — Minimaler OpenAI-Image-Live-Smoke (ein Generierungs-Call). "
        "Setze OPENAI_API_KEY in der Shell. Optional OPENAI_IMAGE_MODEL / --model. "
        "Keine Response-Bodies in der Ausgabe."
    )
    p.add_argument(
        "--confirm-live-openai-image",
        action="store_true",
        dest="confirm",
        help="Pflicht: bestätigt bewusste Live-Kosten für einen echten API-Call.",
    )
    p.add_argument("--run-id", default="", dest="run_id", help="Ordner openai_image_smoke_<run-id> unter --out-root")
    p.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    p.add_argument(
        "--model",
        default=None,
        dest="model",
        help="Optional; sonst OPENAI_IMAGE_MODEL → Settings → Adapter-Default (kein automatischer Fallback).",
    )
    p.add_argument("--size", default="1024x1024", dest="size", help="Bildgröße für generations (Default 1024x1024).")
    p.add_argument(
        "--timeout-seconds",
        type=float,
        default=120.0,
        dest="timeout_seconds",
    )
    args = p.parse_args()

    if not args.confirm:
        msg = {
            "ok": False,
            "blocking_reason": "confirm_live_openai_image_required",
            "hint": "Erneut mit --confirm-live-openai-image (bewusste Kostenfreigabe).",
        }
        print(json.dumps(msg, ensure_ascii=False, indent=2))
        return 3

    rid = (args.run_id or "").strip() or f"smoke_{uuid.uuid4().hex[:12]}"
    out_dir = Path(args.out_root).resolve() / f"openai_image_smoke_{rid}"
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / "openai_smoke_test.png"

    body = run_openai_image_smoke_v1(
        dest,
        model=args.model,
        size=str(args.size).strip() or "1024x1024",
        timeout_seconds=float(args.timeout_seconds),
    )
    result_path = out_dir / RESULT_NAME
    payload = {**body, "run_id": rid, "result_path": str(result_path)}
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if body.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
