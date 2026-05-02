"""Build the first local demo MP4 from one image and one MP3."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.production_assembly.first_demo_video import build_first_demo_video


def main() -> int:
    image_source = sys.argv[1] if len(sys.argv) > 1 else ""
    result = build_first_demo_video(image_source)
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
