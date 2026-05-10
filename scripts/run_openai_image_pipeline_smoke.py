"""BA 32.71 — OpenAI Image über den echten Asset-Runner (1–2 Szenen, Live)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.production_connectors.openai_image_pipeline_smoke import (
    run_openai_image_pipeline_smoke_v1,
    trim_scene_asset_pack,
    write_builtin_minimal_scene_pack,
)

RESULT_NAME = "openai_image_pipeline_smoke_result.json"


def main() -> int:
    p = argparse.ArgumentParser(
        description="BA 32.71 — Pipeline-Mini-Smoke: IMAGE_PROVIDER=openai_image + Asset Runner, "
        "max. 2 Szenen. Keine Response-Bodies; keine Secrets in der Ausgabe."
    )
    p.add_argument(
        "--confirm-live-openai-image",
        action="store_true",
        dest="confirm",
        help="Pflicht: ein oder mehrere echte OpenAI Images API Calls + Produktionspfad.",
    )
    p.add_argument("--run-id", default="", dest="run_id")
    p.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    p.add_argument(
        "--scene-asset-pack",
        type=Path,
        default=None,
        dest="scene_asset_pack",
        help="Optional scene_asset_pack.json; wird auf --max-scenes gekürzt. Ohne Angabe: eingebautes Mini-Pack.",
    )
    p.add_argument(
        "--max-scenes",
        type=int,
        default=1,
        dest="max_scenes",
        help="1 oder 2 (hart begrenzt).",
    )
    p.add_argument(
        "--model",
        default=None,
        dest="model",
        help="OpenAI-Bildmodell für diesen Lauf (Default: OPENAI_IMAGE_MODEL oder gpt-image-2). Kein automatischer Fallback.",
    )
    p.add_argument("--size", default="1024x1024", dest="size")
    p.add_argument("--timeout-seconds", type=float, default=120.0, dest="timeout_seconds")

    args = p.parse_args()

    if not args.confirm:
        print(
            json.dumps(
                {
                    "ok": False,
                    "blocking_reason": "confirm_live_openai_image_required",
                    "hint": "Wiederholen mit --confirm-live-openai-image.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 3

    ms = int(args.max_scenes)
    if ms < 1 or ms > 2:
        print(
            json.dumps(
                {"ok": False, "blocking_reason": "max_scenes_out_of_range", "allowed": [1, 2]},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 3

    rid = (args.run_id or "").strip() or f"pl_{uuid.uuid4().hex[:12]}"
    work_parent = Path(args.out_root).resolve() / f"openai_image_pipeline_smoke_{rid}"
    work_parent.mkdir(parents=True, exist_ok=True)

    env_model = (os.environ.get("OPENAI_IMAGE_MODEL") or "").strip()
    cli_model = (args.model or "").strip()
    effective_model = cli_model or env_model or "gpt-image-2"

    if args.scene_asset_pack is not None:
        src = Path(args.scene_asset_pack).resolve()
        pack_eff = trim_scene_asset_pack(src, ms, work_parent / "trimmed_scene_asset_pack.json")
    else:
        pack_eff = write_builtin_minimal_scene_pack(work_parent / "builtin_scene_asset_pack.json", ms)

    saved_ip = os.environ.get("IMAGE_PROVIDER")
    try:
        os.environ["IMAGE_PROVIDER"] = "openai_image"
        body = run_openai_image_pipeline_smoke_v1(
            pack_path=pack_eff,
            out_root=Path(args.out_root).resolve(),
            run_id=rid,
            max_scenes=ms,
            openai_image_model=effective_model,
            openai_image_size=str(args.size).strip() or "1024x1024",
            openai_image_timeout_seconds=float(args.timeout_seconds),
        )
    finally:
        if saved_ip is None:
            os.environ.pop("IMAGE_PROVIDER", None)
        else:
            os.environ["IMAGE_PROVIDER"] = saved_ip

    result_path = work_parent / RESULT_NAME
    payload = {
        **body,
        "run_id": rid,
        "pack_path": str(pack_eff.resolve()),
        "result_path": str(result_path.resolve()),
    }
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if body.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
