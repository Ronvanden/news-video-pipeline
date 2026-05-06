from __future__ import annotations

import sys
from pathlib import Path

# Pytest unter Windows startet teils ohne Repo-Root im sys.path.
# Viele Tests importieren `app.*` und `scripts.*` direkt.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

