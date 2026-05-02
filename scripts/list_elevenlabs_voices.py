"""List ElevenLabs voices and print safe JSON only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.production_connectors.elevenlabs_voices_list import list_elevenlabs_voices


def main() -> int:
    result = list_elevenlabs_voices()
    print(json.dumps(result.safe_output(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
