"""BA 21.1 — Preview Quality Checklist (Artefakte, keine ffmpeg-Läufe)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Dict

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_PIPELINE = _ROOT / "scripts" / "run_local_preview_pipeline.py"
_SMOKE = _ROOT / "scripts" / "run_local_preview_smoke.py"


@pytest.fixture(scope="module")
def preview_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_pipeline", _PIPELINE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def smoke_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_smoke", _SMOKE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._pipeline_mod = None
    yield mod
    mod._pipeline_mod = None


def _touch(p: Path, content: bytes = b"x") -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content)
    return str(p.resolve())


def test_quality_pass_all_artifacts(preview_mod, tmp_path):
    pv = tmp_path / "pv.mp4"
    rp = tmp_path / "local_preview_report.md"
    om = tmp_path / "OPEN_ME.md"
    _touch(pv, b"abc")
    _touch(rp, b"# r")
    _touch(om, b"# o")
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": [],
        "blocking_reasons": [],
        "paths": {
            "preview_with_subtitles": str(pv),
            "founder_report": str(rp),
            "open_me": str(om),
        },
        "report_path": str(rp),
        "open_me_path": str(om),
        "steps": {},
    }
    qc = preview_mod.build_local_preview_quality_checklist(r)
    assert qc["status"] == "pass"
    assert {it["id"] for it in qc["items"]} == {
        "preview_video_exists",
        "preview_video_non_empty",
        "founder_report_exists",
        "open_me_exists",
        "blocking_reasons_clear",
        "warnings_present",
    }


def test_quality_warning_when_warnings_present(preview_mod, tmp_path):
    pv = tmp_path / "pv.mp4"
    rp = tmp_path / "r.md"
    om = tmp_path / "OPEN_ME.md"
    _touch(pv, b"ab")
    _touch(rp, b"#")
    _touch(om, b"#")
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": ["some_warn"],
        "blocking_reasons": [],
        "paths": {"preview_with_subtitles": str(pv), "founder_report": str(rp), "open_me": str(om)},
        "report_path": str(rp),
        "open_me_path": str(om),
        "steps": {},
    }
    qc = preview_mod.build_local_preview_quality_checklist(r)
    assert qc["status"] == "warning"
    assert any(it["id"] == "warnings_present" and it["status"] == "warning" for it in qc["items"])


def test_quality_fail_missing_preview(preview_mod, tmp_path):
    rp = tmp_path / "r.md"
    om = tmp_path / "OPEN_ME.md"
    _touch(rp)
    _touch(om)
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": [],
        "blocking_reasons": [],
        "paths": {"preview_with_subtitles": str(tmp_path / "missing.mp4"), "founder_report": str(rp), "open_me": str(om)},
        "report_path": str(rp),
        "open_me_path": str(om),
        "steps": {},
    }
    qc = preview_mod.build_local_preview_quality_checklist(r)
    assert qc["status"] == "fail"
    assert any(it["id"] == "preview_video_exists" and it["status"] == "fail" for it in qc["items"])


def test_quality_fail_preview_zero_bytes(preview_mod, tmp_path):
    pv = tmp_path / "pv.mp4"
    rp = tmp_path / "r.md"
    om = tmp_path / "OPEN_ME.md"
    _touch(pv, b"")
    _touch(rp)
    _touch(om)
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": [],
        "blocking_reasons": [],
        "paths": {"preview_with_subtitles": str(pv), "founder_report": str(rp), "open_me": str(om)},
        "report_path": str(rp),
        "open_me_path": str(om),
        "steps": {},
    }
    qc = preview_mod.build_local_preview_quality_checklist(r)
    assert qc["status"] == "fail"
    assert any(it["id"] == "preview_video_non_empty" and it["status"] == "fail" for it in qc["items"])


def test_quality_fail_real_blocking(preview_mod, tmp_path):
    pv = tmp_path / "pv.mp4"
    rp = tmp_path / "r.md"
    om = tmp_path / "OPEN_ME.md"
    _touch(pv, b"a")
    _touch(rp)
    _touch(om)
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": [],
        "blocking_reasons": ["ffmpeg_missing"],
        "paths": {"preview_with_subtitles": str(pv), "founder_report": str(rp), "open_me": str(om)},
        "report_path": str(rp),
        "open_me_path": str(om),
        "steps": {},
    }
    qc = preview_mod.build_local_preview_quality_checklist(r)
    assert qc["status"] == "fail"
    assert any(it["id"] == "blocking_reasons_clear" and it["status"] == "fail" for it in qc["items"])


def test_quality_non_blocking_blocking_does_not_fail_checklist(preview_mod, tmp_path):
    pv = tmp_path / "pv.mp4"
    rp = tmp_path / "r.md"
    om = tmp_path / "OPEN_ME.md"
    _touch(pv, b"a")
    _touch(rp)
    _touch(om)
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": [],
        "blocking_reasons": ["preview_with_subtitles_already_exists"],
        "paths": {"preview_with_subtitles": str(pv), "founder_report": str(rp), "open_me": str(om)},
        "report_path": str(rp),
        "open_me_path": str(om),
        "steps": {},
    }
    qc = preview_mod.build_local_preview_quality_checklist(r)
    assert qc["status"] == "pass"
    assert any(it["id"] == "blocking_reasons_clear" and it["status"] == "pass" for it in qc["items"])


def test_finalize_writes_quality_checklist(preview_mod, tmp_path):
    tl = tmp_path / "tl.json"
    nar = tmp_path / "n.txt"
    tl.write_text("{}", encoding="utf-8")
    nar.write_text("b", encoding="utf-8")
    sub_m = tmp_path / "sm.json"

    def fake_build(*_a, **_k):
        return {"ok": True, "subtitle_manifest_path": str(sub_m), "warnings": [], "blocking_reasons": []}

    def fake_render(*_a, **kw):
        ov = kw.get("output_video")
        if ov is not None:
            Path(ov).parent.mkdir(parents=True, exist_ok=True)
            Path(ov).write_bytes(b"cv")
        return {"video_created": True, "warnings": [], "blocking_reasons": []}

    def fake_burn(*_a, **_k):
        p = tmp_path / "pv211.mp4"
        p.write_bytes(b"pv")
        return {
            "ok": True,
            "skipped": False,
            "output_video_path": str(p),
            "warnings": [],
            "blocking_reasons": [],
        }

    meta = preview_mod.run_local_preview_pipeline(
        tl,
        nar,
        out_root=tmp_path,
        run_id="ba211fin",
        build_subtitle_pack_fn=fake_build,
        render_final_story_video_fn=fake_render,
        burn_in_subtitles_preview_fn=fake_burn,
    )
    assert isinstance(meta.get("quality_checklist"), dict)
    assert meta["quality_checklist"].get("status") in ("pass", "warning", "fail")
    pdir = Path(meta["pipeline_dir"])
    rep = (pdir / "local_preview_report.md").read_text(encoding="utf-8")
    assert "## Quality Checklist" in rep
    om = (pdir / "OPEN_ME.md").read_text(encoding="utf-8")
    assert "## Quality Checklist" in om


def test_smoke_summary_includes_quality_line(smoke_mod, preview_mod):
    pv = Path("/tmp/pv.mp4")
    r: Dict[str, Any] = {
        "ok": True,
        "warnings": [],
        "blocking_reasons": [],
        "paths": {"preview_with_subtitles": str(pv)},
        "report_path": "/tmp/r.md",
        "open_me_path": "/tmp/o.md",
        "quality_checklist": {"status": "warning"},
    }
    smoke_mod._pipeline_mod = preview_mod
    s = smoke_mod.build_local_preview_smoke_summary(r)
    assert "Quality: WARNING" in s
