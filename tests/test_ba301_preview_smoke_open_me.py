"""BA 30.1 — OPEN_PREVIEW_SMOKE.md operator report for preview smoke."""

from __future__ import annotations

from pathlib import Path

from app.production_assembly.preview_smoke_auto import (
    _attach_open_preview_smoke_report,
    execute_preview_smoke_auto,
    write_preview_smoke_open_me_report,
)


def test_write_open_me_contains_title_video_and_next_steps(tmp_path: Path):
    summ = {
        "ok": True,
        "run_id": "smoke_test_001",
        "preview_result": {
            "ok": True,
            "output_video_path": str((tmp_path / "local_preview_smoke_test_001.mp4").resolve()),
            "duration_seconds": 23.0,
            "scenes_rendered": 4,
            "used_images_count": 0,
            "used_clips_count": 4,
            "ffmpeg_available": True,
            "blocking_reasons": [],
            "warnings": [],
        },
        "local_preview_render_result_path": str(tmp_path / "local_preview_render_result.json"),
        "production_run_summary_path": str(tmp_path / "first_real_production_run_summary_smoke_test_001.json"),
        "render_input_bundle_path": str(tmp_path / "render_input_bundle_smoke_test_001.json"),
        "production_pack_path": str(tmp_path / "production_pack"),
    }
    p = write_preview_smoke_open_me_report(summ, tmp_path)
    assert p.name == "OPEN_PREVIEW_SMOKE.md"
    text = p.read_text(encoding="utf-8")
    assert "# Preview Smoke Ergebnis" in text
    assert "local_preview_smoke_test_001.mp4" in text
    assert "## Nächste Schritte" in text
    assert "Human Preview Review" in text


def test_execute_sets_open_preview_smoke_report_path(tmp_path: Path):
    out = tmp_path / "output"
    out.mkdir()
    work = out / "w"
    work.mkdir()
    img = work / "scene.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    import json

    am_path = work / "asset_manifest.json"
    am_path.write_text(
        json.dumps(
            {
                "assets": [
                    {
                        "scene_number": 1,
                        "visual_asset_kind": "motion_clip",
                        "selected_asset_path": str(img.resolve()),
                        "visual_prompt_effective": "p",
                    }
                ],
                "production_asset_approval_result": {
                    "approval_status": "approved",
                    "blocking_reasons": [],
                    "warnings": [],
                },
                "visual_cost_summary": {"total_units": 1.0, "by_kind": {}},
            }
        ),
        encoding="utf-8",
    )

    def fake_prev(**kwargs):
        prev_out = Path(kwargs["output_dir"])
        return {
            "ok": True,
            "output_video_path": str((prev_out / "local_preview_rpt.mp4").resolve()),
            "duration_seconds": 10.0,
            "scenes_rendered": 1,
            "used_images_count": 0,
            "used_clips_count": 1,
            "ffmpeg_available": True,
            "blocking_reasons": [],
            "warnings": [],
        }

    summ, code = execute_preview_smoke_auto(
        run_id="rpt",
        output_root=out,
        asset_manifest=am_path,
        run_local_preview_from_bundle_fn=fake_prev,
    )
    assert code == 0
    rp = summ.get("open_preview_smoke_report_path") or ""
    assert rp
    assert Path(rp).is_file()
    assert "Preview Smoke Ergebnis" in Path(rp).read_text(encoding="utf-8")


def test_attach_open_me_nonfatal_on_write_error(tmp_path: Path, monkeypatch):
    def boom(_summary, _out_dir):
        raise OSError("simulated_write_failure")

    monkeypatch.setattr(
        "app.production_assembly.preview_smoke_auto.write_preview_smoke_open_me_report",
        boom,
    )
    summ: dict = {
        "ok": False,
        "run_id": "x",
        "preview_result": None,
        "local_preview_render_result_path": "",
        "production_run_summary_path": "",
        "render_input_bundle_path": "",
        "production_pack_path": "",
    }
    _attach_open_preview_smoke_report(summ, tmp_path)
    assert summ.get("open_preview_smoke_report_path") == ""
    assert summ.get("open_preview_smoke_write_warnings")
    assert "open_preview_smoke_report_failed" in str(summ["open_preview_smoke_write_warnings"])
