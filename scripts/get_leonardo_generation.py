"""Fetch a Leonardo generation by ID and print safe JSON only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.production_connectors.leonardo_generation_result import fetch_leonardo_generation_result


def main() -> int:
    generation_id = sys.argv[1] if len(sys.argv) > 1 else ""
    result = fetch_leonardo_generation_result(generation_id)
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
