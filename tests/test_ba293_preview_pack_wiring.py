"""BA 29.3 — Production pack wiring for local preview artefacts."""

from __future__ import annotations

import json
from pathlib import Path

from app.real_video_build.production_pack import build_production_pack


def test_pack_copies_preview_result_and_video_paths_in_summary(tmp_path: Path):
    out_root = tmp_path / "out"
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)
    asset_manifest = {
        "assets": [{"scene_number": 1}],
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
    }
    (src / "asset_manifest.json").write_text(json.dumps(asset_manifest), encoding="utf-8")
    preview_json = {
        "ok": True,
        "preview_render_version": "ba29_2_v1",
        "output_video_path": str(src / "pv.mp4"),
        "ffmpeg_available": True,
    }
    (src / "lpr.json").write_text(json.dumps(preview_json), encoding="utf-8")
    (src / "pv.mp4").write_bytes(b"not-really-mp4")

    res = build_production_pack(
        run_id="p1",
        output_root=out_root,
        source_paths={
            "asset_manifest": src / "asset_manifest.json",
            "local_preview_render_result": src / "lpr.json",
            "preview_video": src / "pv.mp4",
        },
        dry_run=False,
        copy_assets=False,
    )
    pack = Path(res["pack_dir"])
    assert (pack / "local_preview_render_result.json").is_file()
    assert (pack / "local_preview.mp4").is_file()
    summary = json.loads((pack / "production_summary.json").read_text(encoding="utf-8"))
    assert summary.get("local_preview_status") == "available"
    assert summary.get("local_preview_video_path")
    assert isinstance(summary.get("local_preview_render_result"), dict)
