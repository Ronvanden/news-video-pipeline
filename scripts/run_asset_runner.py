"""BA 19.0 — Local Asset Runner: scene_asset_pack.json → lokale Bilder + asset_manifest.json."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _sorted_beats(scene_expansion: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = scene_expansion.get("expanded_scene_assets") or []
    if not isinstance(raw, list) or not raw:
        return []
    return sorted(raw, key=lambda b: (int(b.get("chapter_index", 0)), int(b.get("beat_index", 0))))


def load_scene_asset_pack(path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if not path.is_file():
        raise FileNotFoundError(f"scene_asset_pack not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    se = data.get("scene_expansion")
    if not isinstance(se, dict):
        raise ValueError("scene_asset_pack.json missing object 'scene_expansion'")
    beats = _sorted_beats(se)
    if not beats:
        raise ValueError("scene_expansion.expanded_scene_assets empty or missing")
    return data, beats


def _live_env_ready() -> bool:
    return bool((os.environ.get("LEONARDO_API_KEY") or "").strip())


def _draw_placeholder_png(
    out_path: Path,
    *,
    scene_number: int,
    chapter_index: int,
    beat_index: int,
    snippet: str,
) -> None:
    from PIL import Image, ImageDraw, ImageFont

    w, h = 960, 540
    img = Image.new("RGB", (w, h), color=(24, 28, 36))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 22)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
        font_small = font
    title = f"PLACEHOLDER  scene {scene_number:03d}"
    meta = f"chapter_index={chapter_index}  beat_index={beat_index}"
    snip = (snippet or "")[:320].replace("\n", " ")
    draw.text((40, 40), title, fill=(230, 235, 245), font=font)
    draw.text((40, 90), meta, fill=(180, 190, 210), font=font_small)
    y = 140
    for line in _wrap_text(snip, width=52):
        draw.text((40, y), line, fill=(200, 205, 220), font=font_small)
        y += 22
        if y > h - 40:
            break
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")


def _wrap_text(text: str, width: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    cur: List[str] = []
    for w in words:
        test = (" ".join(cur + [w])) if cur else w
        if len(test) <= width:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines or [""]


def run_local_asset_runner(
    pack_path: Path,
    out_root: Path,
    *,
    run_id: str,
    mode: str,
) -> Dict[str, Any]:
    """
    Schreibt output/generated_assets_<run_id>/ und gibt Metadaten zurück.

    mode: placeholder | live — live ohne LEONARDO_API_KEY erzeugt nur Warnung, keine Bilder.
    """
    pack_path = pack_path.resolve()
    data, beats = load_scene_asset_pack(pack_path)
    out_dir = Path(out_root).resolve() / f"generated_assets_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    warnings: List[str] = []
    assets: List[Dict[str, Any]] = []
    mode_l = (mode or "placeholder").strip().lower()

    if mode_l == "live":
        if not _live_env_ready():
            warnings.append(
                "live_mode_selected_but_LEONARDO_API_KEY_missing_or_empty — "
                "no remote generation in BA 19.0 V1; use --mode placeholder or set env."
            )
            manifest = {
                "run_id": run_id,
                "source_pack": str(pack_path),
                "asset_count": 0,
                "generation_mode": "live_skipped",
                "warnings": warnings,
                "assets": [],
            }
            (out_dir / "asset_manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return {
                "ok": False,
                "output_dir": str(out_dir),
                "asset_count": 0,
                "warnings": warnings,
                "manifest_path": str(out_dir / "asset_manifest.json"),
            }

    for i, b in enumerate(beats, start=1):
        ch = int(b.get("chapter_index", 0))
        bi = int(b.get("beat_index", 0))
        vp = str(b.get("visual_prompt") or "")
        cam = str(b.get("camera_motion_hint") or "")
        atype = str(b.get("asset_type") or "image")
        fname = f"scene_{i:03d}.png"
        fpath = out_dir / fname
        snippet = vp[:180] if vp else f"{atype} beat"
        _draw_placeholder_png(
            fpath,
            scene_number=i,
            chapter_index=ch,
            beat_index=bi,
            snippet=snippet,
        )
        assets.append(
            {
                "scene_number": i,
                "chapter_index": ch,
                "beat_index": bi,
                "asset_type": atype,
                "image_path": fname,
                "visual_prompt": vp,
                "camera_motion_hint": cam,
                "generation_mode": "placeholder",
            }
        )

    manifest = {
        "run_id": run_id,
        "source_pack": str(pack_path),
        "asset_count": len(assets),
        "generation_mode": "placeholder",
        "warnings": warnings,
        "assets": assets,
    }
    (out_dir / "asset_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "ok": True,
        "output_dir": str(out_dir),
        "asset_count": len(assets),
        "warnings": warnings,
        "manifest_path": str(out_dir / "asset_manifest.json"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="BA 19.0 — Scene pack → lokale Bilder + asset_manifest.json")
    parser.add_argument(
        "--scene-asset-pack",
        type=Path,
        required=True,
        dest="scene_asset_pack",
        help="Pfad zu scene_asset_pack.json (BA 18.2 Export)",
    )
    parser.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    parser.add_argument("--run-id", default="", dest="run_id", help="Optional; sonst UUID")
    parser.add_argument(
        "--mode",
        choices=("placeholder", "live"),
        default="placeholder",
        help="placeholder (Default) oder live (benötigt LEONARDO_API_KEY für künftige Erweiterung)",
    )
    args = parser.parse_args()

    run_id = (args.run_id or "").strip() or str(uuid.uuid4())
    try:
        meta = run_local_asset_runner(
            args.scene_asset_pack,
            args.out_root,
            run_id=run_id,
            mode=args.mode,
        )
    except (OSError, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        err = {"ok": False, "error": type(e).__name__, "message": str(e), "run_id": run_id}
        print(json.dumps(err, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0 if meta.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
