"""BA 20.8 — Production Output Bundle Validator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "validate_production_output_bundle.py"


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _touch(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x")
    return str(path.resolve())


def _run(*args: str):
    cp = subprocess.run([sys.executable, str(_SCRIPT), *args], capture_output=True, text=True)
    body = json.loads(cp.stdout)
    return cp.returncode, body


def test_complete_bundle_pass(tmp_path):
    clean = _touch(tmp_path / "clean.mp4")
    burn = _touch(tmp_path / "burn.mp4")
    srt = _touch(tmp_path / "subtitles.srt")
    ass = _touch(tmp_path / "subtitles.ass")

    rm = _write_json(tmp_path / "render.json", {
        "clean_video_path": clean,
        "subtitle_burnin_video_path": burn,
        "subtitle_sidecar_srt_path": srt,
        "subtitle_sidecar_ass_path": ass,
        "subtitle_delivery_mode": "both",
        "subtitle_style": "typewriter",
        "renderer_used": "ass_typewriter",
    })
    sm = _write_json(tmp_path / "subtitle.json", {"subtitle_style": "typewriter", "subtitles_srt_path": srt})
    bm = _write_json(tmp_path / "burnin.json", {
        "subtitle_burnin_video_path": burn,
        "clean_input_video_path": clean,
        "subtitle_delivery_mode": "burn_in",
        "subtitle_style": "typewriter",
        "renderer_used": "ass_typewriter",
        "ass_subtitle_path": ass,
        "clean_video_required": True,
    })
    code, out = _run("--render-manifest", str(rm), "--subtitle-manifest", str(sm), "--burnin-manifest", str(bm))
    assert code == 0
    assert out["ok"] is True
    assert out["status"] == "pass"


def test_missing_burnin_video_blocking(tmp_path):
    clean = _touch(tmp_path / "clean.mp4")
    rm = _write_json(tmp_path / "render.json", {
        "clean_video_path": clean,
        "subtitle_burnin_video_path": str(tmp_path / "missing.mp4"),
        "subtitle_delivery_mode": "burn_in",
        "subtitle_style": "classic",
    })
    code, out = _run("--render-manifest", str(rm))
    assert code == 1
    assert out["ok"] is False
    assert "subtitle_burnin_video_missing" in out["blocking_reasons"]


def test_typewriter_with_ass_pass(tmp_path):
    clean = _touch(tmp_path / "clean.mp4")
    burn = _touch(tmp_path / "burn.mp4")
    ass = _touch(tmp_path / "type.ass")
    rm = _write_json(tmp_path / "render.json", {
        "clean_video_path": clean,
        "subtitle_burnin_video_path": burn,
        "subtitle_delivery_mode": "burn_in",
        "subtitle_style": "typewriter",
        "renderer_used": "ass_typewriter",
        "subtitle_sidecar_ass_path": ass,
    })
    code, out = _run("--render-manifest", str(rm))
    assert code == 0
    assert out["status"] == "warning"  # fehlende optionale Manifeste ohne strict
    assert "typewriter_ass_subtitle_missing" not in out["warnings"]


def test_typewriter_missing_ass_warning_or_strict_fail(tmp_path):
    clean = _touch(tmp_path / "clean.mp4")
    burn = _touch(tmp_path / "burn.mp4")
    rm = _write_json(tmp_path / "render.json", {
        "clean_video_path": clean,
        "subtitle_burnin_video_path": burn,
        "subtitle_delivery_mode": "burn_in",
        "subtitle_style": "typewriter",
        "renderer_used": "ass_typewriter",
        "subtitle_sidecar_ass_path": str(tmp_path / "missing.ass"),
    })
    code, out = _run("--render-manifest", str(rm))
    assert code == 0
    assert "typewriter_ass_subtitle_missing" in out["warnings"]

    code_s, out_s = _run("--render-manifest", str(rm), "--strict")
    assert code_s == 1
    assert "typewriter_ass_subtitle_missing" in out_s["blocking_reasons"]


def test_subtitle_style_none_pass_without_burnin(tmp_path):
    clean = _touch(tmp_path / "clean.mp4")
    rm = _write_json(tmp_path / "render.json", {
        "clean_video_path": clean,
        "subtitle_delivery_mode": "none",
        "subtitle_style": "none",
        "renderer_used": "none",
    })
    code, out = _run("--render-manifest", str(rm))
    assert code == 0
    assert out["ok"] is True


def test_missing_optional_manifest_non_strict_warning(tmp_path):
    rm = _write_json(tmp_path / "render.json", {"subtitle_delivery_mode": "none", "subtitle_style": "none"})
    code, out = _run("--render-manifest", str(rm))
    assert code == 0
    assert out["status"] == "warning"
    assert "manifest_missing:subtitle" in out["warnings"]


def test_missing_optional_manifest_strict_fail(tmp_path):
    rm = _write_json(tmp_path / "render.json", {"subtitle_delivery_mode": "none", "subtitle_style": "none"})
    code, out = _run("--render-manifest", str(rm), "--strict")
    assert code == 1
    assert out["status"] == "fail"
    assert "manifest_missing:subtitle" in out["blocking_reasons"]


def test_output_json_written(tmp_path):
    clean = _touch(tmp_path / "clean.mp4")
    rm = _write_json(tmp_path / "render.json", {
        "clean_video_path": clean,
        "subtitle_delivery_mode": "none",
        "subtitle_style": "none",
    })
    out_json = tmp_path / "validator_result.json"
    code, out = _run("--render-manifest", str(rm), "--output-json", str(out_json))
    assert code == 0
    assert out_json.is_file()
    disk = json.loads(out_json.read_text(encoding="utf-8"))
    assert disk["ok"] == out["ok"]
