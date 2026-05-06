from __future__ import annotations

import json
from pathlib import Path

from scripts.run_ba_25_5_url_to_final_video_smoke import (
    EXIT_FAILED,
    FAILURE_BRIDGE,
    FAILURE_PREVIEW,
    FAILURE_FINAL_RENDER,
    RESULT_SCHEMA,
    run_url_to_final_video_smoke,
)


def _minimal_bridge(out_root: Path, rid: str):
    d = out_root / f"url_script_{rid}"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "generate_script_response.json"
    p.write_text(
        json.dumps(
            {
                "title": "t",
                "hook": "h",
                "chapters": [{"title": "c1", "content": "x"}],
                "full_script": "x",
                "sources": [],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    return {
        "ok": True,
        "status": "completed",
        "run_id": rid,
        "build_dir": str(d),
        "generate_script_response_path": str(p),
        "warnings": [],
        "blocking_reasons": [],
    }


def test_ba256_bridge_failure_structured(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()

    def bridge_fn(**kwargs):
        return {
            "ok": False,
            "status": "failed",
            "run_id": kwargs["run_id"],
            "blocking_reasons": ["extraction_empty"],
            "warnings": ["no content"],
        }

    res = run_url_to_final_video_smoke(
        url="https://example.com/x",
        run_id="rid_br",
        out_root=out_root,
        bridge_fn=bridge_fn,
        preview_fn=lambda **k: {},
        final_render_fn=lambda **k: {},
    )
    assert res["ok"] is False
    assert res["failure_stage"] == FAILURE_BRIDGE
    assert res["exit_code"] == EXIT_FAILED
    assert "extraction_empty" in res["blocking_reasons"]
    assert "debug_traceback" not in res
    assert "youtube_upload" not in res
    assert "publishing_package" not in res


def test_ba256_preview_failure_structured(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()

    def preview_fn(**kwargs):
        return {
            "ok": False,
            "status": "failed",
            "run_id": kwargs["run_id"],
            "build_dir": str(out_root / "rl"),
            "paths": {},
            "blocking_reasons": ["ffmpeg_missing"],
            "warnings": [],
        }

    res = run_url_to_final_video_smoke(
        url="https://example.com/x",
        run_id="rid_pr",
        out_root=out_root,
        bridge_fn=lambda **k: _minimal_bridge(out_root, k["run_id"]),
        preview_fn=preview_fn,
        final_render_fn=lambda **k: {},
    )
    assert res["ok"] is False
    assert res["failure_stage"] == FAILURE_PREVIEW
    assert "ffmpeg_missing" in res["blocking_reasons"]


def test_ba256_skipped_existing_status_in_result(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    rid = "rid_skip"

    def preview_fn(**kwargs):
        burn_dir = out_root / f"subtitle_burnin_{rid}"
        burn_dir.mkdir(parents=True, exist_ok=True)
        preview = burn_dir / "preview_with_subtitles.mp4"
        preview.write_bytes(b"\0\0\0\x20ftypisom")
        build_dir = out_root / f"real_local_preview_{rid}"
        build_dir.mkdir(parents=True, exist_ok=True)
        (build_dir / "real_local_preview_result.json").write_text("{}", encoding="utf-8")
        return {
            "ok": True,
            "status": "completed",
            "run_id": rid,
            "build_dir": str(build_dir),
            "paths": {"preview_with_subtitles": str(preview)},
            "warnings": [],
            "blocking_reasons": [],
        }

    def final_render_fn(**kwargs):
        final_dir = out_root / f"final_render_{rid}"
        final_dir.mkdir(parents=True, exist_ok=True)
        final_video = final_dir / "final_video.mp4"
        final_video.write_bytes(b"\0\0\0\x20ftypisom")
        return {
            "ok": True,
            "run_id": rid,
            "status": "skipped_existing",
            "paths": {"final_render_dir": str(final_dir), "final_video_path": str(final_video)},
            "warnings": [],
            "blocking_reasons": [],
        }

    res = run_url_to_final_video_smoke(
        url="https://example.com/a",
        run_id=rid,
        out_root=out_root,
        bridge_fn=lambda **k: _minimal_bridge(out_root, rid),
        preview_fn=preview_fn,
        final_render_fn=final_render_fn,
    )
    assert res["ok"] is True
    assert res["status"] == "skipped_existing"
    assert res["schema_version"] == RESULT_SCHEMA


def test_ba256_final_render_locked_failure_stage(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    rid = "rid_fr"

    def preview_fn(**kwargs):
        burn_dir = out_root / f"subtitle_burnin_{rid}"
        burn_dir.mkdir(parents=True, exist_ok=True)
        preview = burn_dir / "preview_with_subtitles.mp4"
        preview.write_bytes(b"\0\0\0\x20ftypisom")
        build_dir = out_root / f"real_local_preview_{rid}"
        build_dir.mkdir(parents=True, exist_ok=True)
        (build_dir / "real_local_preview_result.json").write_text("{}", encoding="utf-8")
        return {
            "ok": True,
            "status": "completed",
            "run_id": rid,
            "build_dir": str(build_dir),
            "paths": {"preview_with_subtitles": str(preview)},
            "warnings": [],
            "blocking_reasons": [],
        }

    def final_render_fn(**kwargs):
        return {
            "ok": False,
            "run_id": rid,
            "status": "locked",
            "blocking_reasons": ["human_approval_missing"],
            "paths": {},
            "warnings": [],
        }

    res = run_url_to_final_video_smoke(
        url="https://example.com/a",
        run_id=rid,
        out_root=out_root,
        bridge_fn=lambda **k: _minimal_bridge(out_root, rid),
        preview_fn=preview_fn,
        final_render_fn=final_render_fn,
    )
    assert res["ok"] is False
    assert res["failure_stage"] == FAILURE_FINAL_RENDER
