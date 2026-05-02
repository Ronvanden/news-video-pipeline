"""Run the isolated Voice smoke test and print safe JSON only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.production_connectors.voice_smoke_test import run_voice_connector_smoke_test


def main() -> int:
    result = run_voice_connector_smoke_test()
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
