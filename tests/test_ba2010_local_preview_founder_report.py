"""BA 20.10 — Local Preview Founder Report (Markdown + Datei, tolerant)."""

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
    d = tmp_path / f"sub2010_{tag}"
    d.mkdir(parents=True, exist_ok=True)
    srt = d / "cues.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nA.\n\n2\n00:00:02,100 --> 00:00:04,000\nB.\n",
        encoding="utf-8",
    )
    m = d / "subtitle_manifest.json"
    m.write_text(json.dumps({"subtitles_srt_path": str(srt)}), encoding="utf-8")
    return m


def _pass_result(preview_path: str = "/tmp/preview.mp4") -> Dict[str, Any]:
    return {
        "ok": True,
        "run_id": "r1",
        "pipeline_dir": "/out/local_preview_r1",
        "warnings": [],
        "blocking_reasons": [],
        "paths": {
            "preview_with_subtitles": preview_path,
            "clean_video": "/out/clean.mp4",
            "subtitle_manifest": "/out/sub.json",
        },
        "steps": {
            "build_subtitles": {"ok": True, "subtitle_manifest_path": "/out/sub.json", "warnings": []},
            "render_clean": {
                "video_created": True,
                "output_path": "/out/clean.mp4",
                "warnings": [],
            },
            "burnin_preview": {"ok": True, "skipped": False, "output_video_path": preview_path, "warnings": []},
        },
    }


def test_pass_report_contains_verdict_and_open_path(preview_mod):
    md = preview_mod.build_local_preview_founder_report(_pass_result())
    assert "Status: **PASS**" in md
    assert "Preview erzeugt: **ja**" in md
    assert "/tmp/preview.mp4" in md
    assert "Öffne die Preview-Datei und prüfe Bild, Ton, Untertitel-Timing." in md


def test_warning_top_level_warnings(preview_mod):
    r = _pass_result()
    r["warnings"] = ["audio_missing_silent_render"]
    md = preview_mod.build_local_preview_founder_report(r)
    assert "Status: **WARNING**" in md
    assert "audio_missing_silent_render" in md
    assert "Öffne die Preview, prüfe die Warnungen" in md


def test_fail_ok_false(preview_mod):
    r = _pass_result()
    r["ok"] = False
    md = preview_mod.build_local_preview_founder_report(r)
    assert "Status: **FAIL**" in md
    assert "Behebe zuerst die Blocking Reasons" in md


def test_fail_blocking_even_if_ok_true(preview_mod):
    r = _pass_result()
    r["blocking_reasons"] = ["ffmpeg_missing"]
    md = preview_mod.build_local_preview_founder_report(r)
    assert "Status: **FAIL**" in md
    assert "ffmpeg_missing" in md


def test_robust_minimal_and_list_steps(preview_mod):
    md = preview_mod.build_local_preview_founder_report({})
    assert "Status: **FAIL**" in md
    assert "nicht verfügbar" in md

    md2 = preview_mod.build_local_preview_founder_report(
        {
            "ok": True,
            "steps": [{"nur": "unbekannt"}],
            "paths": {},
            "warnings": [],
            "blocking_reasons": [],
        }
    )
    assert "step_0" in md2
    assert "Status: **WARNING**" in md2


def test_write_report_file_and_paths(preview_mod, tmp_path):
    pd = tmp_path / "local_preview_x"
    pd.mkdir()
    result = _pass_result()
    result["pipeline_dir"] = str(pd)
    out = preview_mod.write_local_preview_founder_report(result)
    rp = pd / "local_preview_report.md"
    assert rp.is_file()
    assert out["report_path"] == str(rp.resolve())
    assert out["paths"]["founder_report"] == str(rp.resolve())
    assert "Local Preview Founder Report" in rp.read_text(encoding="utf-8")
    assert "report_markdown" in out and len(out["report_markdown"]) > 50


def test_write_without_pipeline_dir_no_crash(preview_mod):
    out = preview_mod.write_local_preview_founder_report({"ok": True, "pipeline_dir": "", "paths": {}})
    assert "report_markdown" in out
    assert "report_path" not in out
    assert "founder_report" not in (out.get("paths") or {})


def test_write_failure_adds_warning_no_crash(preview_mod, tmp_path, monkeypatch):
    pd = tmp_path / "local_preview_y"
    pd.mkdir()
    result = _pass_result()
    result["pipeline_dir"] = str(pd)

    orig = Path.write_text

    def boom(self: Path, *a: Any, **kw: Any):
        if self.name == "local_preview_report.md":
            raise OSError("denied")
        return orig(self, *a, **kw)

    monkeypatch.setattr(Path, "write_text", boom)
    out = preview_mod.write_local_preview_founder_report(result)
    assert "founder_report_write_failed" in (out.get("warnings") or [])
    assert "report_markdown" in out


def test_run_pipeline_writes_report_file(preview_mod, tmp_path):
    tl = tmp_path / "tl.json"
    nar = tmp_path / "nar.txt"
    tl.write_text("{}", encoding="utf-8")
    nar.write_text("body", encoding="utf-8")
    sub_m = _min_subtitle_manifest(tmp_path, "wr")

    def fake_build(*_a, **_k):
        return {"ok": True, "subtitle_manifest_path": str(sub_m), "warnings": [], "blocking_reasons": []}

    def fake_render(*_a, **kw):
        ov = kw.get("output_video")
        if ov is not None:
            Path(ov).parent.mkdir(parents=True, exist_ok=True)
            Path(ov).write_bytes(b"cv")
        return {"video_created": True, "output_path": str(ov) if ov else "", "warnings": [], "blocking_reasons": []}

    def fake_burn(*_a, **_k):
        p = tmp_path / "pv.mp4"
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
        run_id="wr2010",
        build_subtitle_pack_fn=fake_build,
        render_final_story_video_fn=fake_render,
        burn_in_subtitles_preview_fn=fake_burn,
    )
    pdir = Path(meta["pipeline_dir"])
    assert (pdir / "local_preview_report.md").is_file()
    assert (pdir / "OPEN_ME.md").is_file()
    rep_txt = (pdir / "local_preview_report.md").read_text(encoding="utf-8")
    assert "## Quality Checklist" in rep_txt
    assert "## Subtitle Quality" in rep_txt
    assert meta.get("report_path")
    assert meta.get("open_me_path")
    assert "report_markdown" in meta
    assert "open_me_markdown" in meta
    assert "Local Preview Package" in (pdir / "OPEN_ME.md").read_text(encoding="utf-8")


def test_main_json_excludes_report_markdown_but_has_report_path(preview_mod, tmp_path, capsys, monkeypatch):
    import sys

    tl = tmp_path / "t.json"
    nar = tmp_path / "n.txt"
    tl.write_text("{}", encoding="utf-8")
    nar.write_text("z", encoding="utf-8")
    sub_m = _min_subtitle_manifest(tmp_path, "cli")

    def fake_build(*_a, **_k):
        return {"ok": True, "subtitle_manifest_path": str(sub_m), "warnings": [], "blocking_reasons": []}

    def fake_render(*_a, **_k):
        return {"video_created": True, "warnings": [], "blocking_reasons": []}

    def fake_burn(*_a, **_k):
        return {
            "ok": True,
            "skipped": False,
            "output_video_path": str(tmp_path / "o.mp4"),
            "warnings": [],
            "blocking_reasons": [],
        }

    real_run = preview_mod.run_local_preview_pipeline

    def wrapped(timeline_manifest, narration_script, **kw):
        return real_run(
            timeline_manifest,
            narration_script,
            build_subtitle_pack_fn=fake_build,
            render_final_story_video_fn=fake_render,
            burn_in_subtitles_preview_fn=fake_burn,
            **kw,
        )

    monkeypatch.setattr(preview_mod, "run_local_preview_pipeline", wrapped)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--timeline-manifest",
            str(tl),
            "--narration-script",
            str(nar),
            "--out-root",
            str(tmp_path),
            "--run-id",
            "cli2010",
        ],
    )
    preview_mod.main()
    out = capsys.readouterr().out
    parsed = json.loads(out.strip())
    assert "report_markdown" not in parsed
    assert parsed.get("report_path")


def test_main_print_report_stdout(preview_mod, tmp_path, capsys, monkeypatch):
    import sys

    tl = tmp_path / "t2.json"
    nar = tmp_path / "n2.txt"
    tl.write_text("{}", encoding="utf-8")
    nar.write_text("z", encoding="utf-8")
    sub_m = _min_subtitle_manifest(tmp_path, "pr")

    def fake_build(*_a, **_k):
        return {"ok": True, "subtitle_manifest_path": str(sub_m), "warnings": [], "blocking_reasons": []}

    def fake_render(*_a, **_k):
        return {"video_created": True, "warnings": [], "blocking_reasons": []}

    def fake_burn(*_a, **_k):
        return {
            "ok": True,
            "skipped": False,
            "output_video_path": str(tmp_path / "o2.mp4"),
            "warnings": [],
            "blocking_reasons": [],
        }

    real_run = preview_mod.run_local_preview_pipeline

    def wrapped(timeline_manifest, narration_script, **kw):
        return real_run(
            timeline_manifest,
            narration_script,
            build_subtitle_pack_fn=fake_build,
            render_final_story_video_fn=fake_render,
            burn_in_subtitles_preview_fn=fake_burn,
            **kw,
        )

    monkeypatch.setattr(preview_mod, "run_local_preview_pipeline", wrapped)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "x",
            "--timeline-manifest",
            str(tl),
            "--narration-script",
            str(nar),
            "--out-root",
            str(tmp_path),
            "--run-id",
            "pr2010",
            "--print-report",
        ],
    )
    preview_mod.main()
    full = capsys.readouterr().out
    assert "\n---\n" in full
    head, _, tail = full.partition("\n---\n")
    json.loads(head.strip())
    assert "# Local Preview Founder Report" in tail
