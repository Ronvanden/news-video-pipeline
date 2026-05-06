"""BA 21.0 — Mini E2E Fixture / Real Operator Smoke (Dateien & Shortcut, kein ffmpeg)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE = _ROOT / "fixtures" / "local_preview_mini"
_MINI_SCRIPT = _ROOT / "scripts" / "run_local_preview_mini_fixture.py"


@pytest.fixture(scope="module")
def mini_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_mini_fixture", _MINI_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fixture_files_exist():
    assert (_FIXTURE / "mini_timeline_manifest.json").is_file()
    assert (_FIXTURE / "mini_narration.txt").is_file()
    assert (_FIXTURE / "README.md").is_file()
    assert (_FIXTURE / "assets" / "scene_001.png").is_file()
    assert (_FIXTURE / "assets" / "scene_002.png").is_file()
    assert (_FIXTURE / "assets" / "scene_003.png").is_file()


def test_mini_timeline_is_valid_json_with_expected_shape():
    raw = (_FIXTURE / "mini_timeline_manifest.json").read_text(encoding="utf-8")
    assert "C:\\" not in raw
    assert '"assets_directory": "fixtures/local_preview_mini/assets"' in raw
    data = json.loads(raw)
    assert data.get("audio_path") == ""
    assert data.get("assets_directory") == "fixtures/local_preview_mini/assets"
    scenes = data.get("scenes")
    assert isinstance(scenes, list) and len(scenes) == 3
    for sc in scenes:
        assert "image_path" in sc and "duration_seconds" in sc


def test_mini_narration_not_empty():
    body = (_FIXTURE / "mini_narration.txt").read_text(encoding="utf-8")
    assert len(body.strip()) > 80
    assert "Mini-Preview" in body or "Preview" in body


def test_readme_contains_smoke_open_me_and_powershell():
    md = (_FIXTURE / "README.md").read_text(encoding="utf-8")
    assert "run_local_preview_smoke.py" in md
    assert "OPEN_ME.md" in md
    assert "PowerShell" in md
    assert "local_preview_" in md


def test_build_mini_fixture_argv_no_script_name(mini_mod, tmp_path):
    argv = mini_mod.build_mini_fixture_argv(
        out_root=tmp_path / "out",
        run_id="rid210",
        print_json=True,
        motion_mode="static",
        subtitle_style="classic",
    )
    assert "run_local_preview_smoke.py" not in argv
    assert argv[0] == "--timeline-manifest"
    assert str(mini_mod._TIMELINE) in argv
    assert str(mini_mod._NARRATION) in argv
    assert "--print-json" in argv
    assert "--subtitle-style" in argv and "classic" in argv
    assert "mini_timeline_manifest.json" in " ".join(argv)
    assert "mini_narration.txt" in " ".join(argv)
    assert "rid210" in argv


def test_shortcut_main_delegates_without_real_smoke(monkeypatch, mini_mod, tmp_path):
    calls: list[list[str] | None] = []

    def fake_main(a=None):
        calls.append(a)
        return 0

    monkeypatch.setattr(
        mini_mod,
        "_ffmpeg_preflight_check",
        lambda: {
            "ok": True,
            "ffmpeg": {"available": True, "version": "x", "path": "/f"},
            "ffprobe": {"available": True, "version": "y", "path": "/p"},
            "missing_tools": [],
            "warnings": [],
            "setup_hint": "",
        },
    )
    monkeypatch.setattr(mini_mod, "_load_smoke_main", lambda: fake_main)
    rc = mini_mod.main(["--out-root", str(tmp_path), "--run-id", "deleg210"])
    assert rc == 0
    assert len(calls) == 1
    assert calls[0] is not None
    assert "run_local_preview_smoke.py" not in calls[0]
    assert calls[0][0] == "--timeline-manifest"
    assert "--run-id" in calls[0]
    i = calls[0].index("--run-id")
    assert calls[0][i + 1] == "deleg210"


def test_mini_fixture_module_importable():
    spec = importlib.util.spec_from_file_location("mini2", _MINI_SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert callable(m.main)
    assert callable(m.build_mini_fixture_argv)
