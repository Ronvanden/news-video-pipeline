from __future__ import annotations

import json
from pathlib import Path

from scripts.run_ba_25_5_url_to_final_video_smoke import (
    EXIT_BLOCKED,
    EXIT_OK,
    RESULT_FILENAME,
    RESULT_SCHEMA,
    run_url_to_final_video_smoke,
)


def test_ba255_smoke_runner_wires_paths_and_writes_result_json(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()

    # Arrange stubs
    def bridge_fn(**kwargs):
        rid = kwargs["run_id"]
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

    def preview_fn(**kwargs):
        rid = kwargs["run_id"]
        # simulate BA 25.4 output: preview video exists under output/subtitle_burnin_<run_id>/
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
        rid = kwargs["run_id"]
        final_dir = out_root / f"final_render_{rid}"
        final_dir.mkdir(parents=True, exist_ok=True)
        final_video = final_dir / "final_video.mp4"
        final_video.write_bytes(b"\0\0\0\x20ftypisom")
        return {
            "ok": True,
            "run_id": rid,
            "status": "completed",
            "paths": {"final_render_dir": str(final_dir), "final_video_path": str(final_video)},
            "warnings": [],
            "blocking_reasons": [],
        }

    res = run_url_to_final_video_smoke(
        url="https://example.com/a",
        run_id="rid_smoke",
        out_root=out_root,
        duration_minutes=3,
        bridge_fn=bridge_fn,
        preview_fn=preview_fn,
        final_render_fn=final_render_fn,
    )

    assert res["schema_version"] == RESULT_SCHEMA
    assert res["ok"] is True
    assert res["status"] == "completed"
    assert res["exit_code"] == EXIT_OK

    # Result JSON written
    result_json = Path(res["paths"]["result_json"])
    assert result_json.name == RESULT_FILENAME
    assert result_json.is_file()

    # Local preview adapter written for BA 24.x
    lp_dir = out_root / "local_preview_rid_smoke"
    assert (lp_dir / "preview_with_subtitles.mp4").is_file()
    assert (lp_dir / "local_preview_result.json").is_file()
    assert (lp_dir / "human_approval.json").is_file()

    # Final artifact exists
    assert Path(res["paths"]["final_video"]).is_file()


def test_ba255_no_auto_approve_can_return_locked_exit_2(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()

    def bridge_fn(**kwargs):
        rid = kwargs["run_id"]
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

    def preview_fn(**kwargs):
        rid = kwargs["run_id"]
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
        rid = kwargs["run_id"]
        # simulate BA 24.2 gate lock
        return {
            "ok": False,
            "run_id": rid,
            "status": "locked",
            "message": "Human approval missing/not approved.",
            "warnings": ["Human approval missing/not approved."],
            "blocking_reasons": ["human_approval_missing"],
        }

    res = run_url_to_final_video_smoke(
        url="https://example.com/a",
        run_id="rid_lock",
        out_root=out_root,
        duration_minutes=3,
        auto_approve=False,
        bridge_fn=bridge_fn,
        preview_fn=preview_fn,
        final_render_fn=final_render_fn,
    )
    assert res["ok"] is False
    assert res["exit_code"] == EXIT_BLOCKED

