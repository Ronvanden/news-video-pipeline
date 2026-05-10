"""BA 32.39 — Manuelles Listing öffentlicher Leonardo-Plattform-Modelle (kein CI).

Liest ``LEONARDO_API_KEY`` aus der Prozess-Umgebung (keine .env-Datei).
Gibt nur sichere Modell-Metadaten auf stdout aus (JSON). Diagnose-Codes auf stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.production_connectors.leonardo_platform_models import (
    fetch_leonardo_platform_models_public,
)


def main() -> int:
    p = argparse.ArgumentParser(description="List Leonardo platform models (safe metadata only).")
    p.add_argument(
        "--url",
        default=os.environ.get("LEONARDO_PLATFORM_MODELS_URL", "").strip() or None,
        help="Override platform models URL (optional; default from connector).",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=45.0,
        help="HTTP timeout seconds (default 45).",
    )
    args = p.parse_args()

    api_key = (os.environ.get("LEONARDO_API_KEY") or "").strip()
    ok, models, warns = fetch_leonardo_platform_models_public(
        api_key=api_key,
        url=args.url,
        timeout_seconds=float(args.timeout),
    )
    for w in warns:
        print(w, file=sys.stderr)
    if not ok:
        return 2
    out = {"model_count": len(models), "models": models}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
