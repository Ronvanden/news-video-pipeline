"""Ingest an existing Leonardo image URL and print safe JSON only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.production_connectors.leonardo_image_asset_ingest import ingest_leonardo_image_asset


def main() -> int:
    generation_id = sys.argv[1] if len(sys.argv) > 1 else ""
    image_url = sys.argv[2] if len(sys.argv) > 2 else ""
    result = ingest_leonardo_image_asset(generation_id, image_url)
    print(json.dumps(result.safe_output(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
