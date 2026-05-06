"""BA 28.2 — Motion clip placeholder ingest tests."""

from __future__ import annotations

import json
from pathlib import Path

from app.production_connectors.motion_clip_ingest import ingest_motion_clip_results


def test_ingest_writes_placeholder_clip_path(tmp_path: Path):
    mm = {
        "motion_clip_manifest_version": "ba28_0_v1",
        "clips": [{"ok": True, "provider": "runway", "dry_run": True, "scene_number": 1, "reference_payload_used": None}],
        "summary": {"clips_planned": 1, "provider_counts": {"runway": 1}, "missing_input_count": 0, "dry_run": True},
    }
    out = ingest_motion_clip_results(mm, output_dir=tmp_path / "clips", dry_run=False)
    c = out["clips"][0]
    assert c["clip_ingest_status"] == "placeholder_ready"
    assert c["clip_artifact_type"] == "placeholder"
    assert Path(c["clip_path"]).is_file()

