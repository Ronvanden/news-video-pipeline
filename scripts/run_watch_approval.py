"""BA 15.9 — Watch/Radar aus lokaler JSON-Config (kein Publish, kein Auto-Video)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.manual_url_story.watch_approval import (
    load_watch_config_path,
    load_watch_items_from_json,
    run_watch_approval_scan,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Watch sources JSON → Approval-Queues.")
    parser.add_argument("config_json", help="JSON mit items[] und/oder sources[]")
    args = parser.parse_args()

    data = load_watch_config_path(Path(args.config_json))
    items = load_watch_items_from_json(data)
    result = run_watch_approval_scan(items)
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
