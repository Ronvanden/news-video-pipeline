"""Run ElevenLabs voice smoke test and save MP3 output."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.production_connectors.voice_smoke_file_save import run_voice_smoke_test_and_save


def main() -> int:
    result = run_voice_smoke_test_and_save()
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
