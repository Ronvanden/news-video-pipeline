"""BA 20.12 — OPEN_ME.md / Artefakt-Index für lokale Preview-Ordner."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "run_local_preview_pipeline.py"


@pytest.fixture(scope="module")
def preview_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_pipeline", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _min_subtitle_manifest(tmp_path: Path, tag: str) -> Path:
    d = tmp_path / f"sub2012_{tag}"
    d.mkdir(parents=True, exist_ok=True)
    srt = d / "cues.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nA.\n\n2\n00:00:02,100 --> 00:00:04,000\nB.\n",
        encoding="utf-8",
    )
    m = d / "subtitle_manifest.json"
    m.write_text(json.dumps({"subtitles_srt_path": str(srt)}), encoding="utf-8")
    return m


def _base_ok() -> Dict[str, Any]:
    return {
        "ok": True,
        "run_id": "r12",
        "pipeline_dir": "/out/pipe",
        "warnings": [],
        "blocking_reasons": [],
        "report_path": "/out/pipe/local_preview_report.md",
        "paths": {
            "preview_with_subtitles": "/out/pipe/pv.mp4",
            "clean_video": "/out/pipe/cv.mp4",
            "subtitle_manifest": "/out/sub.json",
        },
        "steps": {
            "build_subtitles": {"ok": True, "subtitle_manifest_path": "/out/sub.json", "warnings": []},
            "render_clean": {"video_created": True, "output_path": "/out/pipe/cv.mp4", "warnings": []},
            "burnin_preview": {"ok": True, "skipped": False, "output_video_path": "/out/pipe/pv.mp4", "warnings": []},
        },
    }


def test_open_me_pass_contains_core_sections(preview_mod):
    md = preview_mod.build_local_preview_open_me(_base_ok())
    assert "# Local Preview Package" in md
    assert "Verdict: **PASS**" in md
    assert "Preview Video:" in md
    assert "Founder Report:" in md
    assert "/out/pipe/pv.mp4" in md
    assert "/out/pipe/local_preview_report.md" in md
    assert "Untertitel-Timing" in md


def test_open_me_warning_lists_warnings(preview_mod):
    r = _base_ok()
    r["warnings"] = ["w1"]
    md = preview_mod.build_local_preview_open_me(r)
    assert "Verdict: **WARNING**" in md
    assert "- w1" in md


def test_open_me_fail_blocking(preview_mod):
    r = _base_ok()
    r["ok"] = False
    r["blocking_reasons"] = ["x"]
    md = preview_mod.build_local_preview_open_me(r)
    assert "Verdict: **FAIL**" in md
    assert "- x" in md.split("## Blocking Reasons")[1]


def test_open_me_minimal_dict_no_crash(preview_mod):
    md = preview_mod.build_local_preview_open_me({})
    assert "Verdict: **FAIL**" in md
    assert "nicht verfügbar" in md


def test_write_open_me_creates_file(preview_mod, tmp_path):
    pd = tmp_path / "lp_12"
    pd.mkdir()
    r = _base_ok()
    r["pipeline_dir"] = str(pd)
    out = preview_mod.write_local_preview_open_me(r)
    om = pd / "OPEN_ME.md"
    assert om.is_file()
    assert out["open_me_path"] == str(om.resolve())
    assert out["paths"]["open_me"] == str(om.resolve())
    assert "open_me_markdown" in out


def test_write_open_me_no_pipeline_dir(preview_mod):
    r = _base_ok()
    r["pipeline_dir"] = ""
    out = preview_mod.write_local_preview_open_me(r)
    assert "open_me_markdown" in out
    assert "open_me_path" not in out


def test_write_open_me_oserror_warning(preview_mod, tmp_path, monkeypatch):
    pd = tmp_path / "lp_12b"
    pd.mkdir()
    r = _base_ok()
    r["pipeline_dir"] = str(pd)
    orig = Path.write_text

    def boom(self: Path, *a: Any, **kw: Any):
        if self.name == "OPEN_ME.md":
            raise OSError("nope")
        return orig(self, *a, **kw)

    monkeypatch.setattr(Path, "write_text", boom)
    out = preview_mod.write_local_preview_open_me(r)
    assert "open_me_write_failed" in (out.get("warnings") or [])
    assert "open_me_markdown" in out


def test_finalize_writes_both_artifacts(preview_mod, tmp_path, monkeypatch):
    tl = tmp_path / "tl.json"
    nar = tmp_path / "nar.txt"
    tl.write_text(json.dumps({"estimated_duration_seconds": 4.0}), encoding="utf-8")
    nar.write_text("b", encoding="utf-8")
    sub_m = _min_subtitle_manifest(tmp_path, "fin")
    aud_stub = tmp_path / "a2012fin.wav"
    aud_stub.write_bytes(b"\0")

    def fake_build(*_a, **_k):
        return {
            "ok": True,
            "subtitle_manifest_path": str(sub_m),
            "audio_path": str(aud_stub),
            "warnings": [],
            "blocking_reasons": [],
        }

    def fake_render(*_a, **_k):
        return {"video_created": True, "output_path": str(tmp_path / "c.mp4"), "warnings": [], "blocking_reasons": []}

    def fake_burn(*_a, **_k):
        return {
            "ok": True,
            "skipped": False,
            "output_video_path": str(tmp_path / "pv.mp4"),
            "warnings": [],
            "blocking_reasons": [],
        }

    monkeypatch.setattr(preview_mod, "_probe_media_duration_seconds", lambda p, **kw: (4.0, None))

    meta = preview_mod.run_local_preview_pipeline(
        tl,
        nar,
        out_root=tmp_path,
        run_id="ba2012int",
        build_subtitle_pack_fn=fake_build,
        render_final_story_video_fn=fake_render,
        burn_in_subtitles_preview_fn=fake_burn,
    )
    pdir = Path(meta["pipeline_dir"])
    assert (pdir / "local_preview_report.md").is_file()
    assert (pdir / "OPEN_ME.md").is_file()


def test_smoke_summary_shows_open_me_after_pipeline(tmp_path, preview_mod, monkeypatch):
    """Smoke-Zeile Open-Me nach echtem Pipeline-Modul-Lauf mit Mocks."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("smoke2012", _ROOT / "scripts" / "run_local_preview_smoke.py")
    assert spec and spec.loader
    sm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sm)
    sm._pipeline_mod = None

    tl = tmp_path / "t.json"
    nar = tmp_path / "n.txt"
    tl.write_text(json.dumps({"estimated_duration_seconds": 4.0}), encoding="utf-8")
    nar.write_text("b", encoding="utf-8")
    sub_m = _min_subtitle_manifest(tmp_path, "sm2012")
    aud_stub = tmp_path / "a2012sm.wav"
    aud_stub.write_bytes(b"\0")

    def fake_build(*_a, **_k):
        return {
            "ok": True,
            "subtitle_manifest_path": str(sub_m),
            "audio_path": str(aud_stub),
            "warnings": [],
            "blocking_reasons": [],
        }

    def fake_render(*_a, **kw):
        ov = kw.get("output_video")
        if ov is not None:
            Path(ov).parent.mkdir(parents=True, exist_ok=True)
            Path(ov).write_bytes(b"cv")
        return {"video_created": True, "warnings": [], "blocking_reasons": []}

    def fake_burn(*_a, **_k):
        p = tmp_path / "pv2012.mp4"
        p.write_bytes(b"pv")
        return {
            "ok": True,
            "skipped": False,
            "output_video_path": str(p),
            "warnings": [],
            "blocking_reasons": [],
        }

    monkeypatch.setattr(preview_mod, "_probe_media_duration_seconds", lambda p, **kw: (4.0, None))

    meta = preview_mod.run_local_preview_pipeline(
        tl,
        nar,
        out_root=tmp_path,
        run_id="sm2012",
        build_subtitle_pack_fn=fake_build,
        render_final_story_video_fn=fake_render,
        burn_in_subtitles_preview_fn=fake_burn,
    )
    s = sm.build_local_preview_smoke_summary(meta)
    assert "Open-Me Datei:" in s
    assert "OPEN_ME.md" in s
    assert "Quality:" in s
    assert "Subtitle Quality:" in s
    assert "Sync Guard:" in s
    om_txt = (Path(meta["pipeline_dir"]) / "OPEN_ME.md").read_text(encoding="utf-8")
    assert "## Subtitle Quality" in om_txt
    assert "## Sync Guard" in om_txt
