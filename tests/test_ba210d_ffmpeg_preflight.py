"""BA 21.0d — Lokaler FFmpeg-Preflight / Setup-Guard (ohne echte ffmpeg-Aufrufe)."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_PIPELINE = _ROOT / "scripts" / "run_local_preview_pipeline.py"
_MINI_SCRIPT = _ROOT / "scripts" / "run_local_preview_mini_fixture.py"


@pytest.fixture(scope="module")
def pipeline_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_pipeline", _PIPELINE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mini_mod():
    spec = importlib.util.spec_from_file_location("run_local_preview_mini_fixture", _MINI_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod._preflight_pipeline_mod = None
    yield mod
    mod._preflight_pipeline_mod = None


def _fake_proc(out: str, rc: int = 0) -> Any:
    class P:
        returncode = rc
        stdout = out

    return P()


def test_check_local_ffmpeg_tools_both_ok(pipeline_mod):
    def which(name: str) -> Optional[str]:
        return f"/bin/{name}"

    def run(cmd, **_kwargs):
        tool = cmd[0]
        return _fake_proc(f"{tool} version 1.2.3\nother line\n")

    r = pipeline_mod.check_local_ffmpeg_tools(_which=which, _run=run, _timeout_sec=5.0)
    assert r["ok"] is True
    assert r["ffmpeg"]["available"] is True
    assert r["ffprobe"]["available"] is True
    assert "ffmpeg version" in r["ffmpeg"]["version"]
    assert "ffprobe version" in r["ffprobe"]["version"]
    assert r["missing_tools"] == []
    assert r["setup_hint"] == ""


def test_check_missing_ffmpeg(pipeline_mod):
    def which(name: str) -> Optional[str]:
        if name == "ffmpeg":
            return None
        return f"/x/{name}"

    def run(cmd, **_kwargs):
        return _fake_proc(f"{cmd[0]} version 9\n")

    r = pipeline_mod.check_local_ffmpeg_tools(_which=which, _run=run)
    assert r["ok"] is False
    assert "ffmpeg" in r["missing_tools"]
    assert r["ffmpeg"]["available"] is False
    assert r["setup_hint"]


def test_check_missing_ffprobe(pipeline_mod):
    def which(name: str) -> Optional[str]:
        if name == "ffprobe":
            return None
        return f"/x/{name}"

    def run(cmd, **_kwargs):
        return _fake_proc(f"{cmd[0]} version 9\n")

    r = pipeline_mod.check_local_ffmpeg_tools(_which=which, _run=run)
    assert r["ok"] is False
    assert "ffprobe" in r["missing_tools"]


def test_check_subprocess_timeout(pipeline_mod):
    def which(name: str) -> Optional[str]:
        return f"/bin/{name}"

    def run(_cmd, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=_cmd, timeout=5)

    r = pipeline_mod.check_local_ffmpeg_tools(_which=which, _run=run)
    assert r["ok"] is False
    assert any("ffmpeg_version_check_timeout" in w for w in r["warnings"])


def test_check_nonzero_return(pipeline_mod):
    calls: List[str] = []

    def which(name: str) -> Optional[str]:
        return f"/bin/{name}"

    def run(cmd, **_kwargs):
        calls.append(cmd[0])
        return _fake_proc("", rc=1)

    r = pipeline_mod.check_local_ffmpeg_tools(_which=which, _run=run)
    assert r["ok"] is False
    assert "ffmpeg_version_check_failed" in r["warnings"]
    assert "ffprobe_version_check_failed" in r["warnings"]


def test_build_ffmpeg_setup_hint_contains_winget(pipeline_mod):
    h = pipeline_mod.build_ffmpeg_setup_hint(["ffmpeg"])
    assert "winget install Gyan.FFmpeg" in h
    assert "ffmpeg -version" in h
    assert "ffprobe -version" in h


def test_mini_fixture_main_blocks_when_preflight_fails(mini_mod, tmp_path, monkeypatch):
    calls: list[Any] = []

    def fake_smoke(_argv=None):
        calls.append(_argv)
        return 0

    monkeypatch.setattr(mini_mod, "_ffmpeg_preflight_check", lambda: {"ok": False, "missing_tools": ["ffmpeg"]})
    monkeypatch.setattr(mini_mod, "_load_smoke_main", lambda: fake_smoke)
    rc = mini_mod.main(["--out-root", str(tmp_path), "--run-id", "pf1"])
    assert rc == 1
    assert calls == []


def test_mini_fixture_skip_preflight_still_calls_smoke(mini_mod, tmp_path, monkeypatch):
    calls: list[Any] = []

    def fake_smoke(argv=None):
        calls.append(list(argv or []))
        return 0

    monkeypatch.setattr(mini_mod, "_ffmpeg_preflight_check", lambda: {"ok": False})
    monkeypatch.setattr(mini_mod, "_load_smoke_main", lambda: fake_smoke)
    rc = mini_mod.main(["--skip-preflight", "--out-root", str(tmp_path), "--run-id", "pf2"])
    assert rc == 0
    assert len(calls) == 1
    assert "--skip-preflight" not in calls[0]


def test_mini_fixture_preflight_ok_runs_smoke(mini_mod, tmp_path, monkeypatch):
    calls: list[Any] = []

    def fake_smoke(argv=None):
        calls.append(list(argv or []))
        return 0

    monkeypatch.setattr(
        mini_mod,
        "_ffmpeg_preflight_check",
        lambda: {
            "ok": True,
            "ffmpeg": {"available": True, "version": "v", "path": "/f"},
            "ffprobe": {"available": True, "version": "v", "path": "/p"},
            "missing_tools": [],
            "warnings": [],
            "setup_hint": "",
        },
    )
    monkeypatch.setattr(mini_mod, "_load_smoke_main", lambda: fake_smoke)
    rc = mini_mod.main(["--out-root", str(tmp_path), "--run-id", "pf3"])
    assert rc == 0
    assert len(calls) == 1
    assert calls[0][0] == "--timeline-manifest"
