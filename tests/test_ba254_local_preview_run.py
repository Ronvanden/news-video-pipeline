"""BA 25.4 — Real Local Preview Run tests.

Verdrahtet:
  generate_script_response.json
    → BA 25.2 Adapter → scene_asset_pack.json
    → BA 25.1 Orchestrator (mockt) → preview_with_subtitles.mp4 + real_video_build_result.json

Tests sind offline-tauglich: der Orchestrator-Aufruf wird stets über
``orchestrator_fn`` injiziert und schreibt nur Stub-Artefakte (kein ffmpeg, kein TTS).
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Dict, List

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_RUNNER_PATH = _ROOT / "scripts" / "run_ba_25_4_local_preview.py"
_ORCH_PATH = _ROOT / "scripts" / "run_real_video_build.py"


def _load_module(name: str, path: Path):
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def runner_mod():
    return _load_module("run_ba_25_4_local_preview", _RUNNER_PATH)


@pytest.fixture(scope="module")
def orch_mod():
    return _load_module("run_real_video_build_for_test_254", _ORCH_PATH)


def _generate_script_response_dict() -> Dict[str, Any]:
    return {
        "title": "Test Title",
        "hook": "Eine kurze Hook-Zeile für BA 25.4.",
        "chapters": [
            {"title": "Kapitel 1", "content": "Erster Inhalt mit klarer Aussage."},
            {"title": "Kapitel 2", "content": "Zweiter Inhalt mit weiteren Fakten."},
            {"title": "Kapitel 3", "content": "Dritter Inhalt schließt die Story."},
        ],
        "full_script": "Hook: ... Kapitel 1: Erster Inhalt. Kapitel 2: Zweiter Inhalt.",
        "sources": ["https://example.com/article"],
        "warnings": ["script_warning_demo"],
    }


def _write_script_json(tmp_path: Path, data: Dict[str, Any]) -> Path:
    p = tmp_path / "generate_script_response.json"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _make_fake_orchestrator(tmp_root: Path, *, status: str = "completed",
                            blocking: List[str] | None = None,
                            warnings: List[str] | None = None,
                            with_preview: bool = True):
    """Liefert eine ``orchestrator_fn``, die das BA-25.1-Result-Schema simuliert."""

    def fake(**kwargs: Any) -> Dict[str, Any]:
        rid = kwargs["run_id"]
        out_root = Path(kwargs["out_root"]).resolve()
        build_dir = out_root / f"real_build_{rid}"
        build_dir.mkdir(parents=True, exist_ok=True)
        clean_video = build_dir / "clean_video.mp4"
        clean_video.write_bytes(b"clean")

        burnin_dir = out_root / f"subtitle_burnin_{rid}"
        burnin_dir.mkdir(parents=True, exist_ok=True)
        preview_path = burnin_dir / "preview_with_subtitles.mp4"
        if with_preview:
            preview_path.write_bytes(b"preview")

        sub_dir = out_root / f"subtitles_{rid}"
        sub_dir.mkdir(parents=True, exist_ok=True)
        srt = sub_dir / "subtitles.srt"
        srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nA.\n", encoding="utf-8")
        sub_man = sub_dir / "subtitle_manifest.json"
        sub_man.write_text(json.dumps({"subtitles_srt_path": str(srt)}), encoding="utf-8")

        voice_dir = out_root / f"full_voice_{rid}"
        voice_dir.mkdir(parents=True, exist_ok=True)
        narration = voice_dir / "narration_script.txt"
        narration.write_text("body", encoding="utf-8")
        mp3 = voice_dir / "full_voiceover.mp3"
        mp3.write_bytes(b"\x00\x01")

        result_payload = {
            "schema_version": "real_video_build_result_v1",
            "run_id": rid,
            "ok": status == "completed",
            "status": status,
            "build_dir": str(build_dir),
            "scene_asset_pack": str(kwargs["scene_asset_pack"]),
            "metadata": {
                "asset_mode": kwargs.get("asset_mode"),
                "voice_mode": kwargs.get("voice_mode"),
                "motion_mode": kwargs.get("motion_mode"),
                "subtitle_style": kwargs.get("subtitle_style"),
                "subtitle_mode": kwargs.get("subtitle_mode"),
                "force": bool(kwargs.get("force", False)),
            },
            "steps": [],
            "paths": {
                "scene_asset_pack": str(kwargs["scene_asset_pack"]),
                "asset_manifest": "",
                "timeline_manifest": "",
                "voiceover_audio": str(mp3),
                "narration_script": str(narration),
                "clean_video": str(clean_video),
                "subtitle_manifest": str(sub_man),
                "subtitle_file": str(srt),
                "preview_with_subtitles": str(preview_path) if with_preview else "",
                "local_preview_dir": "",
                "final_render_dir": "",
                "final_video": "",
            },
            "warnings": list(warnings or []),
            "blocking_reasons": list(blocking or []),
            "next_step": "",
            "created_at_epoch": 1700000000,
        }
        # Mirror real orchestrator persistence
        (build_dir / "real_video_build_result.json").write_text(
            json.dumps(result_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return result_payload

    return fake


# ----------------------------
# Smoke / happy path
# ----------------------------


def test_happy_path_writes_pack_and_aggregate(runner_mod, tmp_path: Path):
    script_json = _write_script_json(tmp_path, _generate_script_response_dict())

    result = runner_mod.run_real_local_preview(
        script_json_path=script_json,
        run_id="ba254_happy",
        out_root=tmp_path,
        orchestrator_fn=_make_fake_orchestrator(tmp_path),
    )

    assert result["schema_version"] == "real_local_preview_result_v1"
    assert result["status"] == "completed"
    assert result["ok"] is True
    assert result["exit_code"] == 0
    assert result["blocking_reasons"] == []

    paths = result["paths"]
    assert paths["script_json"] == str(script_json.resolve())
    assert Path(paths["scene_asset_pack"]).is_file()
    assert paths["preview_with_subtitles"].endswith("preview_with_subtitles.mp4")
    assert Path(paths["real_video_build_result"]).is_file()
    assert paths["local_preview_dir"].endswith("real_local_preview_ba254_happy")

    # Aggregate result file persisted
    agg_file = Path(result["build_dir"]) / "real_local_preview_result.json"
    assert agg_file.is_file()
    parsed = json.loads(agg_file.read_text(encoding="utf-8"))
    assert parsed["status"] == "completed"
    assert parsed["paths"]["scene_asset_pack"].endswith("scene_asset_pack.json")

    # OPEN_ME written by default
    assert Path(paths["open_me"]).is_file()


def test_pack_actually_uses_ba252_adapter(runner_mod, tmp_path: Path):
    """Beats müssen echte Narration aus den Kapiteln tragen (BA 25.2 Vertrag)."""
    script_json = _write_script_json(tmp_path, _generate_script_response_dict())
    result = runner_mod.run_real_local_preview(
        script_json_path=script_json,
        run_id="ba254_adapter",
        out_root=tmp_path,
        orchestrator_fn=_make_fake_orchestrator(tmp_path),
    )
    assert result["ok"] is True
    pack = json.loads(Path(result["paths"]["scene_asset_pack"]).read_text(encoding="utf-8"))
    beats = (pack.get("scene_expansion") or {}).get("expanded_scene_assets") or []
    narrations = [str(b.get("narration") or "") for b in beats]
    assert any("Erster Inhalt" in n for n in narrations)
    assert any("Zweiter Inhalt" in n for n in narrations)


# ----------------------------
# Validation
# ----------------------------


def test_invalid_run_id_returns_blocked_exit_3(runner_mod, tmp_path: Path):
    script_json = _write_script_json(tmp_path, _generate_script_response_dict())
    result = runner_mod.run_real_local_preview(
        script_json_path=script_json,
        run_id="../bad",
        out_root=tmp_path,
    )
    assert result["status"] == "blocked"
    assert result["ok"] is False
    assert result["exit_code"] == 3
    assert "invalid_run_id" in result["blocking_reasons"]


def test_missing_script_json_returns_blocked_exit_3(runner_mod, tmp_path: Path):
    missing = tmp_path / "nope.json"
    result = runner_mod.run_real_local_preview(
        script_json_path=missing,
        run_id="ba254_missing",
        out_root=tmp_path,
    )
    assert result["status"] == "blocked"
    assert result["exit_code"] == 3
    assert "script_json_missing" in result["blocking_reasons"]


def test_invalid_script_json_returns_blocked(runner_mod, tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("not-json", encoding="utf-8")
    result = runner_mod.run_real_local_preview(
        script_json_path=bad,
        run_id="ba254_badjson",
        out_root=tmp_path,
    )
    assert result["status"] == "blocked"
    assert "script_json_invalid" in result["blocking_reasons"]


def test_unusable_script_returns_failed(runner_mod, tmp_path: Path):
    """Wenn Adapter aus dem Input keine Szenen ableiten kann."""
    # Looks like GenerateScriptResponse aufgrund hook-Key, aber chapters/full_script leer.
    empty = {
        "title": "",
        "hook": "",
        "chapters": [],
        "full_script": "",
        "sources": [],
        "warnings": [],
    }
    script_json = _write_script_json(tmp_path, empty)
    result = runner_mod.run_real_local_preview(
        script_json_path=script_json,
        run_id="ba254_empty",
        out_root=tmp_path,
    )
    assert result["ok"] is False
    assert result["status"] in ("blocked", "failed")
    assert "generate_script_response_unusable" in result["blocking_reasons"]


# ----------------------------
# Orchestrator status propagation
# ----------------------------


def test_orchestrator_blocked_propagates(runner_mod, tmp_path: Path):
    script_json = _write_script_json(tmp_path, _generate_script_response_dict())
    fake = _make_fake_orchestrator(
        tmp_path,
        status="blocked",
        blocking=["ffmpeg_missing"],
        with_preview=False,
    )
    result = runner_mod.run_real_local_preview(
        script_json_path=script_json,
        run_id="ba254_block",
        out_root=tmp_path,
        orchestrator_fn=fake,
    )
    assert result["status"] == "blocked"
    assert result["exit_code"] == 2
    assert "ffmpeg_missing" in result["blocking_reasons"]


def test_orchestrator_failed_propagates(runner_mod, tmp_path: Path):
    script_json = _write_script_json(tmp_path, _generate_script_response_dict())
    fake = _make_fake_orchestrator(
        tmp_path,
        status="failed",
        blocking=["clean_render_failed"],
        with_preview=False,
    )
    result = runner_mod.run_real_local_preview(
        script_json_path=script_json,
        run_id="ba254_fail",
        out_root=tmp_path,
        orchestrator_fn=fake,
    )
    assert result["status"] == "failed"
    assert result["exit_code"] == 1
    assert "clean_render_failed" in result["blocking_reasons"]


def test_completed_without_preview_downgrades_to_blocked(runner_mod, tmp_path: Path):
    script_json = _write_script_json(tmp_path, _generate_script_response_dict())
    fake = _make_fake_orchestrator(tmp_path, status="completed", with_preview=False)
    result = runner_mod.run_real_local_preview(
        script_json_path=script_json,
        run_id="ba254_nopreview",
        out_root=tmp_path,
        orchestrator_fn=fake,
    )
    assert result["status"] == "blocked"
    assert "preview_with_subtitles_missing" in result["blocking_reasons"]


# ----------------------------
# Contract preservation
# ----------------------------


def test_does_not_modify_generate_script_response_contract(runner_mod, tmp_path: Path):
    """Original generate_script_response.json darf nicht verändert werden."""
    src_data = _generate_script_response_dict()
    script_json = _write_script_json(tmp_path, src_data)
    before = script_json.read_text(encoding="utf-8")
    result = runner_mod.run_real_local_preview(
        script_json_path=script_json,
        run_id="ba254_contract",
        out_root=tmp_path,
        orchestrator_fn=_make_fake_orchestrator(tmp_path),
    )
    assert result["ok"] is True
    after = script_json.read_text(encoding="utf-8")
    assert before == after


def test_real_video_build_result_schema_preserved(runner_mod, tmp_path: Path):
    """Aggregat darf den BA-25.1-Vertrag nicht überschreiben."""
    script_json = _write_script_json(tmp_path, _generate_script_response_dict())
    result = runner_mod.run_real_local_preview(
        script_json_path=script_json,
        run_id="ba254_schema",
        out_root=tmp_path,
        orchestrator_fn=_make_fake_orchestrator(tmp_path),
    )
    rb = result["real_build_result"]
    assert rb["schema_version"] == "real_video_build_result_v1"
    assert "paths" in rb and "preview_with_subtitles" in rb["paths"]


# ----------------------------
# CLI surface
# ----------------------------


def test_cli_print_json_emits_parsable_json(runner_mod, tmp_path: Path, monkeypatch):
    script_json = _write_script_json(tmp_path, _generate_script_response_dict())
    fake = _make_fake_orchestrator(tmp_path)

    original = runner_mod.run_real_local_preview

    def patched(**kwargs):
        kwargs.setdefault("orchestrator_fn", fake)
        return original(**kwargs)

    monkeypatch.setattr(runner_mod, "run_real_local_preview", patched)

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = runner_mod.main(
            [
                "--script-json",
                str(script_json),
                "--run-id",
                "ba254_cli",
                "--out-root",
                str(tmp_path),
                "--print-json",
            ]
        )
    assert rc == 0
    parsed = json.loads(buf.getvalue())
    assert parsed["status"] == "completed"
    assert parsed["paths"]["scene_asset_pack"].endswith("scene_asset_pack.json")


def test_cli_invalid_run_id_returns_exit_3(runner_mod, tmp_path: Path):
    script_json = _write_script_json(tmp_path, _generate_script_response_dict())
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = runner_mod.main(
            [
                "--script-json",
                str(script_json),
                "--run-id",
                "../bad",
                "--out-root",
                str(tmp_path),
                "--print-json",
            ]
        )
    assert rc == 3
    parsed = json.loads(buf.getvalue())
    assert parsed["ok"] is False
    assert "invalid_run_id" in parsed["blocking_reasons"]


def test_cli_no_open_me_skips_open_me_file(runner_mod, tmp_path: Path, monkeypatch):
    script_json = _write_script_json(tmp_path, _generate_script_response_dict())
    fake = _make_fake_orchestrator(tmp_path)

    original = runner_mod.run_real_local_preview

    def patched(**kwargs):
        kwargs.setdefault("orchestrator_fn", fake)
        return original(**kwargs)

    monkeypatch.setattr(runner_mod, "run_real_local_preview", patched)

    rc = runner_mod.main(
        [
            "--script-json",
            str(script_json),
            "--run-id",
            "ba254_noopen",
            "--out-root",
            str(tmp_path),
            "--no-open-me",
        ]
    )
    assert rc == 0
    open_me = tmp_path / "real_local_preview_ba254_noopen" / "REAL_LOCAL_PREVIEW_OPEN_ME.md"
    assert not open_me.exists()


# ----------------------------
# Anti-regression: BA 25.4 must use existing wiring, not duplicate
# ----------------------------


def test_ba254_imports_ba252_adapter_module(runner_mod):
    assert hasattr(runner_mod, "build_scene_asset_pack_from_generate_script_response")
    assert hasattr(runner_mod, "build_scene_asset_pack_from_story_pack")
    assert hasattr(runner_mod, "write_scene_asset_pack")


def test_ba254_default_orchestrator_loads_run_real_video_build(runner_mod):
    """Default-Orchestrator muss auf scripts/run_real_video_build.py zeigen."""
    assert runner_mod._REAL_BUILD_SCRIPT.name == "run_real_video_build.py"
    assert runner_mod._REAL_BUILD_SCRIPT.is_file()
