from __future__ import annotations

import json
from pathlib import Path

from scripts.run_ba_25_5_url_to_final_video_smoke import (
    EXIT_BLOCKED,
    EXIT_INVALID_INPUT,
    EXIT_OK,
    RESULT_FILENAME,
    RESULT_SCHEMA,
    main,
    run_url_to_final_video_smoke,
)


def test_ba255_smoke_runner_wires_paths_and_writes_result_json(tmp_path: Path):
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
        pack = build_dir / "scene_asset_pack.json"
        pack.write_text("{}", encoding="utf-8")
        (build_dir / "real_local_preview_result.json").write_text("{}", encoding="utf-8")
        return {
            "ok": True,
            "status": "completed",
            "run_id": rid,
            "build_dir": str(build_dir),
            "paths": {
                "preview_with_subtitles": str(preview),
                "scene_asset_pack": str(pack),
            },
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
    assert res["auto_approved"] is True
    assert res["source_url"] == "https://example.com/a"
    assert res["generate_script_response_path"]
    assert res["scene_asset_pack_path"]
    assert res["final_video_path"]

    result_json = Path(res["paths"]["result_json"])
    assert result_json.name == RESULT_FILENAME
    assert result_json.is_file()
    assert (result_json.parent / "URL_TO_FINAL_VIDEO_OPEN_ME.md").is_file()

    lp_dir = out_root / "local_preview_rid_smoke"
    assert (lp_dir / "preview_with_subtitles.mp4").is_file()
    assert (lp_dir / "local_preview_result.json").is_file()
    assert (lp_dir / "human_approval.json").is_file()
    hap = json.loads((lp_dir / "human_approval.json").read_text(encoding="utf-8"))
    assert hap.get("auto_approved") is True
    assert hap.get("smoke_dev_flow") is True

    assert Path(res["paths"]["final_video"]).is_file()


def test_ba255_no_auto_approve_skips_final_render_and_writes_no_approval(tmp_path: Path):
    out_root = tmp_path / "output"
    out_root.mkdir()
    final_calls = []

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
        final_calls.append(kwargs)
        raise AssertionError("final render must not run without auto-approve")

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
    assert final_calls == []
    assert res["ok"] is False
    assert res["exit_code"] == EXIT_BLOCKED
    assert res["auto_approved"] is False
    assert "human_approval_required_before_final_render" in res["blocking_reasons"]
    assert res["failure_stage"] == "human_approval_gate"
    assert res["human_approval_path"] == ""
    assert "Human approval required before final render" in res["next_step"]

    lp_dir = out_root / "local_preview_rid_lock"
    assert not (lp_dir / "human_approval.json").is_file()


def test_ba255_main_print_json_invalid_run_id_is_parseable_json(tmp_path: Path, capsys):
    code = main(
        [
            "--url",
            "https://example.com",
            "--run-id",
            "bad/run",
            "--out-dir",
            str(tmp_path / "out"),
            "--print-json",
        ]
    )
    assert code == EXIT_INVALID_INPUT
    raw = capsys.readouterr().out.strip()
    obj = json.loads(raw)
    assert obj["ok"] is False
    assert obj["failure_stage"] == "input_validation"
    assert "schema_version" in obj
