"""BA 29.6 — Safe final render execution (dry-run / gated)."""

from __future__ import annotations

import json
from pathlib import Path

from app.production_assembly.final_render_execution import build_final_render_execution_result


def test_dry_run_does_not_execute(tmp_path: Path):
    ps = {
        "final_render_readiness_result": {"readiness_status": "ready"},
        "local_preview_video_path": str(tmp_path / "in.mp4"),
    }
    (tmp_path / "in.mp4").write_bytes(b"x")
    r = build_final_render_execution_result(
        production_summary=ps,
        output_dir=tmp_path / "out",
        execute=False,
        _which=lambda x: "/ffmpeg",
        _run=lambda *a, **k: None,
    )
    assert r["executed"] is False
    assert r["ok"] is True
    assert r.get("ffmpeg_command_preview")


def test_not_ready_blocks_execute(tmp_path: Path):
    ps = {"final_render_readiness_result": {"readiness_status": "blocked"}}
    r = build_final_render_execution_result(production_summary=ps, output_dir=tmp_path / "o", execute=True)
    assert r["ok"] is False
    assert r["executed"] is False


def test_safe_final_render_cli_dry(tmp_path: Path, monkeypatch):
    import importlib.util
    import sys

    root = Path(__file__).resolve().parents[1]
    p = root / "scripts" / "run_safe_final_render.py"
    spec = importlib.util.spec_from_file_location("run_safe_final_render", p)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    inp = tmp_path / "in.mp4"
    inp.write_bytes(b"v")
    summ = tmp_path / "ps.json"
    summ.write_text(
        json.dumps(
            {
                "final_render_readiness_result": {"readiness_status": "ready"},
                "local_preview_video_path": str(inp),
            }
        ),
        encoding="utf-8",
    )
    outd = tmp_path / "finalout"
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_safe_final_render.py", "--production-summary", str(summ), "--output-dir", str(outd)],
    )
    assert mod.main() == 0
    assert (outd / "final_render_execution_result.json").is_file()
