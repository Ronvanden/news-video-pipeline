"""BA 21.0e — Idempotente Preview bei bereits vorhandener preview_with_subtitles.mp4."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_PIPELINE = _ROOT / "scripts" / "run_local_preview_pipeline.py"
_BURN = _ROOT / "scripts" / "burn_in_subtitles_preview.py"


@pytest.fixture(scope="module")
def preview_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_pipeline", _PIPELINE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def burn_mod():
    spec = importlib.util.spec_from_file_location("burn_in_subtitles_preview", _BURN)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_sanitize_strips_preview_already_exists(preview_mod):
    assert preview_mod.sanitize_local_preview_blocking_reasons(
        ["preview_with_subtitles_already_exists", "ffmpeg_missing"]
    ) == ["ffmpeg_missing"]


def test_verdict_warning_not_fail_when_only_non_blocking_blocking_and_preview_ok(preview_mod):
    r: Dict[str, Any] = {
        "ok": True,
        "blocking_reasons": ["preview_with_subtitles_already_exists"],
        "warnings": ["preview_with_subtitles_already_exists", "other_warn"],
        "paths": {"preview_with_subtitles": "/p/preview_with_subtitles.mp4", "clean_video": "/c.mp4"},
        "steps": {
            "build_subtitles": {"ok": True, "subtitle_manifest_path": "/m.json", "warnings": []},
            "render_clean": {"video_created": True, "output_path": "/c.mp4", "warnings": []},
            "burnin_preview": {
                "ok": True,
                "skipped": False,
                "output_video_path": "/p/preview_with_subtitles.mp4",
                "warnings": ["preview_with_subtitles_already_exists"],
            },
        },
    }
    assert preview_mod.compute_local_preview_verdict(r) == "WARNING"


def test_founder_report_blocking_section_empty_after_sanitize(preview_mod):
    r: Dict[str, Any] = {
        "ok": True,
        "run_id": "e2e",
        "pipeline_dir": "/out/lp",
        "blocking_reasons": ["preview_with_subtitles_already_exists"],
        "warnings": ["preview_with_subtitles_already_exists"],
        "paths": {"preview_with_subtitles": "/out/pv.mp4", "clean_video": "/out/cv.mp4"},
        "steps": {
            "burnin_preview": {
                "ok": True,
                "skipped": False,
                "output_video_path": "/out/pv.mp4",
                "warnings": ["preview_with_subtitles_already_exists"],
            },
        },
    }
    md = preview_mod.build_local_preview_founder_report(r)
    assert "Status: **WARNING**" in md
    br_part = md.split("## Blocking Reasons", 1)[1].split("## Next Step", 1)[0]
    assert "preview_with_subtitles_already_exists" not in br_part
    assert "*keine*" in br_part or "*(keine)*" in br_part


def test_open_me_blocking_section_empty_after_sanitize(preview_mod):
    r: Dict[str, Any] = {
        "ok": True,
        "run_id": "e2e",
        "pipeline_dir": "/out/lp",
        "blocking_reasons": ["preview_with_subtitles_already_exists"],
        "warnings": ["w"],
        "paths": {"preview_with_subtitles": "/out/pv.mp4"},
        "steps": {},
    }
    md = preview_mod.build_local_preview_open_me(r)
    br_part = md.split("## Blocking Reasons", 1)[1].split("## Next Step", 1)[0]
    assert "preview_with_subtitles_already_exists" not in br_part
    assert "Keine" in br_part


def test_burn_reuses_existing_preview_without_blocking(burn_mod, tmp_path):
    out_root = tmp_path / "out"
    rid = "idem210e"
    out_dir = out_root / f"subtitle_burnin_{rid}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_mp4 = out_dir / "preview_with_subtitles.mp4"
    out_mp4.write_bytes(b"fake-mp4")

    inv = tmp_path / "clean.mp4"
    inv.write_bytes(b"x")
    man = tmp_path / "sub.json"
    man.write_text(
        json.dumps(
            {
                "subtitle_style": "classic",
                "subtitles_srt_path": str((tmp_path / "sub.srt").resolve()),
            }
        ),
        encoding="utf-8",
    )
    srt = tmp_path / "sub.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHello\n",
        encoding="utf-8",
    )

    def which(_: str) -> str:
        return str(tmp_path / "ffmpeg")

    def run(_cmd, **_kwargs):
        raise AssertionError("ffmpeg should not run when preview already exists")

    meta = burn_mod.burn_in_subtitles_preview(
        inv,
        man,
        out_root=out_root,
        run_id=rid,
        force=False,
        subprocess_run=run,
        shutil_which=which,
    )
    assert meta["ok"] is True
    assert "preview_with_subtitles_already_exists" in meta["warnings"]
    assert "preview_with_subtitles_already_exists" not in (meta.get("blocking_reasons") or [])


def test_pipeline_fake_burn_idempotent_no_blocking_in_result(preview_mod, tmp_path):
    tl = tmp_path / "tl.json"
    nar = tmp_path / "n.txt"
    tl.write_text("{}", encoding="utf-8")
    nar.write_text("body", encoding="utf-8")
    sub_m = tmp_path / "sub_manifest.json"

    def fake_build(*_a, **_k):
        return {"ok": True, "subtitle_manifest_path": str(sub_m), "warnings": [], "blocking_reasons": []}

    def fake_render(*_a, **_k):
        return {"video_created": True, "warnings": [], "blocking_reasons": []}

    def fake_burn(*_a, **_k):
        pv = tmp_path / "pv.mp4"
        pv.write_bytes(b"p")
        return {
            "ok": True,
            "skipped": False,
            "output_video_path": str(pv),
            "warnings": ["preview_with_subtitles_already_exists"],
            "blocking_reasons": [],
        }

    meta = preview_mod.run_local_preview_pipeline(
        tl,
        nar,
        out_root=tmp_path,
        run_id="idem_pipe",
        build_subtitle_pack_fn=fake_build,
        render_final_story_video_fn=fake_render,
        burn_in_subtitles_preview_fn=fake_burn,
    )
    assert meta["ok"] is True
    assert "preview_with_subtitles_already_exists" in meta["warnings"]
    assert "preview_with_subtitles_already_exists" not in meta.get("blocking_reasons", [])
