"""BA 26.4 — CLI für kontrollierten Video-Provider-Smoke (Runway/Veo).

Default: dry_run (keine API-Calls). Für Live: --live --real-provider-enabled und ENV-Key.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.production_connectors.real_provider_smoke import RESULT_SCHEMA, run_real_provider_smoke

RESULT_FILENAME = "real_provider_smoke_result.json"


def main() -> int:
    p = argparse.ArgumentParser(description="BA 26.4 — Real Provider Smoke (dry_run default, max. 1 Live-Szene).")
    p.add_argument("--scene-asset-pack", type=Path, required=True, dest="scene_asset_pack")
    p.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    p.add_argument("--run-id", required=True, dest="run_id")
    p.add_argument(
        "--selected-provider",
        required=True,
        choices=("runway", "veo"),
        dest="selected_provider",
    )
    p.add_argument(
        "--live",
        action="store_true",
        dest="live",
        help="dry_run=false — nur mit --real-provider-enabled und API-Key in ENV.",
    )
    p.add_argument(
        "--real-provider-enabled",
        action="store_true",
        dest="real_provider_enabled",
        help="Explizite Freigabe für echte Provider-Aufrufe (Sicherheitsflag).",
    )
    p.add_argument(
        "--max-real-scenes",
        type=int,
        default=1,
        dest="max_real_scenes",
        help="Max. Anzahl Szenen mit echtem Aufruf (Default 1).",
    )
    p.add_argument(
        "--force-provider",
        action="store_true",
        dest="force_provider",
        help="Lokales Video im Beat ignorieren und Provider-Pfad ausführen.",
    )
    p.add_argument(
        "--assets-directory",
        type=Path,
        default=None,
        dest="assets_directory",
        help="Ordner mit scene_001.png … für Runway image-to-video (nach Asset Runner).",
    )
    args = p.parse_args()

    dry_run = not bool(args.live)
    body = run_real_provider_smoke(
        args.scene_asset_pack,
        out_root=args.out_root,
        run_id=args.run_id,
        selected_provider=args.selected_provider,
        dry_run=dry_run,
        real_provider_enabled=bool(args.real_provider_enabled),
        max_real_scenes=args.max_real_scenes,
        force_provider=bool(args.force_provider),
        assets_directory=args.assets_directory,
    )

    out_dir = Path(args.out_root).resolve() / f"real_provider_smoke_{(args.run_id or '').strip()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / RESULT_FILENAME
    out_payload = dict(body)
    out_payload["result_path"] = str(result_path)
    result_path.write_text(json.dumps(out_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({**body, "result_path": str(result_path)}, ensure_ascii=False, indent=2))
    return 0 if body.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
