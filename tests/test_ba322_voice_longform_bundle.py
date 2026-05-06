"""BA 32.2 — Voice paths in controlled production run / render bundle."""

from __future__ import annotations

import json
from pathlib import Path

from app.production_assembly.controlled_production_run import run_controlled_production_run


def test_voice_manifest_paths_merge_into_render_bundle(tmp_path: Path):
    work = tmp_path / "w"
    work.mkdir(parents=True)
    img = work / "s0.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    mp3 = tmp_path / "voice_track.mp3"
    mp3.write_bytes(b"ID3fake")

    vm = {
        "run_id": "v1",
        "full_voiceover_path": str(mp3.resolve()),
        "real_tts_generated": True,
        "warnings": ["voice_test_warning"],
        "blocking_reasons": [],
    }
    vm_path = tmp_path / "voice_manifest.json"
    vm_path.write_text(json.dumps(vm), encoding="utf-8")

    am = {
        "assets": [
            {
                "scene_number": 1,
                "visual_asset_kind": "still",
                "selected_asset_path": str(img.resolve()),
            }
        ],
        "production_asset_approval_result": {"approval_status": "approved", "blocking_reasons": [], "warnings": []},
        "visual_cost_summary": {"total_units": 1.0, "by_kind": {}},
    }
    am_path = work / "asset_manifest.json"
    am_path.write_text(json.dumps(am), encoding="utf-8")

    out_root = tmp_path / "out"
    out_root.mkdir()
    r = run_controlled_production_run(
        run_id="voice_bundle_t",
        output_root=out_root,
        asset_manifest_path=am_path,
        voice_manifest_path=vm_path,
    )
    bundle_path = Path(r["bundle_path"])
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    vps = bundle.get("voice_paths") or []
    assert any(str(mp3.resolve()) in str(p) for p in vps)
    summ = r.get("first_real_production_run_summary") or {}
    assert summ.get("used_real_voice") is True
    assert "voice_test_warning" in " ".join(bundle.get("warnings") or [])
