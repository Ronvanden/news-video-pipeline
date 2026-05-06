"""BA 19.1 — Asset-Manifest + Audio → timeline_manifest.json (kein Render)."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _zoom_from_camera_hint(hint: str) -> str:
    h = (hint or "").lower()
    if "pull" in h or "zoom out" in h:
        return "slow_pull"
    if "push" in h or "zoom in" in h or "push-in" in h:
        return "slow_push"
    return "static"


def _pan_from_camera_hint(hint: str) -> str:
    h = (hint or "").lower()
    if "pan" in h and "left" in h:
        return "left"
    if "pan" in h and "right" in h:
        return "right"
    return "none"


def load_asset_manifest(path: Path) -> Dict[str, Any]:
    p = path.resolve()
    if not p.is_file():
        raise FileNotFoundError(f"asset_manifest not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def build_timeline_manifest_data(
    manifest: Dict[str, Any],
    *,
    asset_manifest_path: Path,
    audio_path: Path | None,
    run_id: str,
    scene_duration_seconds: int,
) -> Dict[str, Any]:
    """Baut das timeline_manifest-Objekt (ohne Schreiben)."""
    assets_dir = asset_manifest_path.resolve().parent
    raw_assets = manifest.get("assets") or []
    if not isinstance(raw_assets, list) or not raw_assets:
        raise ValueError("asset_manifest.assets empty or missing")

    scenes: List[Dict[str, Any]] = []
    t = 0.0
    default_dur = max(1, int(scene_duration_seconds))

    for a in sorted(raw_assets, key=lambda x: int(x.get("scene_number", 0))):
        sn = int(a.get("scene_number", len(scenes) + 1))
        img = str(a.get("image_path") or "").strip()
        vid_rel = str(a.get("video_path") or "").strip()
        ch = int(a.get("chapter_index", 0))
        bi = int(a.get("beat_index", 0))
        cam = str(a.get("camera_motion_hint") or "")
        adur = a.get("duration_seconds")
        if adur is None:
            adur = a.get("estimated_duration_seconds")
        try:
            dur = max(1, int(adur)) if adur is not None else default_dur
        except (TypeError, ValueError):
            dur = default_dur
        start = round(t, 3)
        end = round(t + dur, 3)

        use_video = False
        if vid_rel:
            vfull = assets_dir / vid_rel
            if vfull.is_file():
                use_video = True
            elif img:
                pass
            else:
                raise ValueError(f"asset video_path not found for scene_number={sn}: {vid_rel}")

        if not use_video and not img:
            raise ValueError(f"asset missing image_path for scene_number={sn}")

        row: Dict[str, Any] = {
            "scene_number": sn,
            "start_time": start,
            "end_time": end,
            "duration_seconds": dur,
            "transition": "fade",
            "camera_motion_hint": cam,
            "zoom_type": _zoom_from_camera_hint(cam),
            "pan_direction": _pan_from_camera_hint(cam),
            "chapter_index": ch,
            "beat_index": bi,
        }
        if use_video:
            row["media_type"] = "video"
            row["video_path"] = vid_rel
            if img:
                row["image_path"] = img
        else:
            row["media_type"] = "image"
            row["image_path"] = img
        scenes.append(row)
        t += dur

    audio_resolved = str(audio_path.resolve()) if audio_path else ""
    total = len(scenes)
    return {
        "run_id": run_id,
        "asset_manifest_path": str(asset_manifest_path.resolve()),
        "assets_directory": str(assets_dir),
        "audio_path": audio_resolved,
        "total_scenes": total,
        "estimated_duration_seconds": int(round(t)),
        "scene_duration_default_seconds": default_dur,
        "scenes": scenes,
    }


def write_timeline_manifest(
    manifest: Dict[str, Any],
    *,
    asset_manifest_path: Path,
    audio_path: Path | None,
    run_id: str,
    scene_duration_seconds: int,
    out_root: Path,
) -> Tuple[Path, Dict[str, Any]]:
    body = build_timeline_manifest_data(
        manifest,
        asset_manifest_path=asset_manifest_path,
        audio_path=audio_path,
        run_id=run_id,
        scene_duration_seconds=scene_duration_seconds,
    )
    out_dir = Path(out_root).resolve() / f"timeline_{run_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "timeline_manifest.json"
    out_file.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_file, body


def main() -> int:
    parser = argparse.ArgumentParser(description="BA 19.1 — asset_manifest.json → timeline_manifest.json")
    parser.add_argument("--asset-manifest", type=Path, required=True, dest="asset_manifest")
    parser.add_argument(
        "--audio-path",
        type=Path,
        default=None,
        dest="audio_path",
        help="Optional; z. B. output/voice_smoke_test_output.mp3",
    )
    parser.add_argument("--out-root", type=Path, default=ROOT / "output", dest="out_root")
    parser.add_argument("--run-id", default="", dest="run_id")
    parser.add_argument("--scene-duration-seconds", type=int, default=6, dest="scene_duration_seconds")
    args = parser.parse_args()

    run_id = (args.run_id or "").strip() or str(uuid.uuid4())
    try:
        am = load_asset_manifest(args.asset_manifest)
        out_file, body = write_timeline_manifest(
            am,
            asset_manifest_path=args.asset_manifest,
            audio_path=args.audio_path,
            run_id=run_id,
            scene_duration_seconds=args.scene_duration_seconds,
            out_root=args.out_root,
        )
    except (OSError, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)}, ensure_ascii=False, indent=2))
        return 2

    print(
        json.dumps(
            {"ok": True, "run_id": run_id, "timeline_manifest": str(out_file), "total_scenes": body["total_scenes"]},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
