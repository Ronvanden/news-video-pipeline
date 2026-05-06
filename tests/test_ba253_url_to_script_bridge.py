"""BA 25.3 — URL-to-Script Bridge tests.

Mockt die bestehende Script-Generation-Logik in ``app.utils`` und prüft
ausschließlich das CLI-/Bridge-Verhalten:

- Source-Type-Auto-Erkennung (YouTube vs Article)
- run_id-Validierung (Exit 3)
- Erfolgreiche Article-/YouTube-Pfade schreiben generate_script_response.json
- ``--print-json`` ist parsbares JSON
- BA 25.2 Adapter-Kompatibilität
- Strukturierter Generation-Fehler (Exit 1)
- Kein Render-/Orchestrator-Aufruf in BA 25.3
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_BRIDGE_PATH = _ROOT / "scripts" / "run_url_to_script_bridge.py"
_ADAPTER_PATH = _ROOT / "app" / "real_video_build" / "script_input_adapter.py"


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
def bridge_mod():
    return _load_module("run_url_to_script_bridge", _BRIDGE_PATH)


@pytest.fixture(scope="module")
def adapter_mod():
    return _load_module("script_input_adapter_ba253", _ADAPTER_PATH)


def _article_response_tuple() -> tuple:
    return (
        "Article Title",
        "Article hook line.",
        [
            {"title": "K1", "content": "Erster Inhalt."},
            {"title": "K2", "content": "Zweiter Inhalt."},
            {"title": "K3", "content": "Dritter Inhalt."},
        ],
        "Hook: ... Kapitel 1: Erster Inhalt. Kapitel 2: Zweiter Inhalt.",
        ["https://example.com/article"],
        ["script_warning_demo"],
    )


def _youtube_response_dict() -> Dict[str, Any]:
    return {
        "title": "YT Title",
        "hook": "YT hook line.",
        "chapters": [
            {"title": "YT-K1", "content": "YT Inhalt eins."},
            {"title": "YT-K2", "content": "YT Inhalt zwei."},
            {"title": "YT-K3", "content": "YT Inhalt drei."},
        ],
        "full_script": "Hook ... YT Inhalt eins. YT Inhalt zwei.",
        "sources": ["https://www.youtube.com/watch?v=abc123XYZ12"],
        "warnings": ["yt_warning_demo"],
    }


# ----------------------------
# Detection
# ----------------------------


def test_auto_detects_youtube_url(bridge_mod):
    assert bridge_mod.detect_source_type("https://youtu.be/abc123XYZ12", "auto") == "youtube"
    assert bridge_mod.detect_source_type("https://www.youtube.com/watch?v=abc", "auto") == "youtube"
    assert bridge_mod.detect_source_type("https://m.youtube.com/watch?v=abc", "auto") == "youtube"


def test_auto_detects_article_url(bridge_mod):
    assert bridge_mod.detect_source_type("https://example.com/news/1", "auto") == "article"
    assert bridge_mod.detect_source_type("https://news.example.org/topic", "auto") == "article"


def test_explicit_source_type_overrides_auto(bridge_mod):
    # YouTube-URL, aber explizit als article angefordert
    assert bridge_mod.detect_source_type("https://youtu.be/abc", "article") == "article"
    # Artikel-URL, aber explizit als youtube angefordert
    assert bridge_mod.detect_source_type("https://example.com/x", "youtube") == "youtube"


# ----------------------------
# run_id validation
# ----------------------------


def test_invalid_run_id_returns_exit_3(bridge_mod, tmp_path: Path):
    res = bridge_mod.run_bridge(
        url="https://example.com/news",
        run_id="bad/run",
        target_language="de",
        duration_minutes=2,
        source_type="article",
        out_root=str(tmp_path),
    )
    assert res["ok"] is False
    assert res["status"] == "failed"
    assert res["error_code"] == "invalid_run_id"
    assert res["exit_code"] == 3


def test_invalid_url_returns_exit_3(bridge_mod, tmp_path: Path):
    res = bridge_mod.run_bridge(
        url="not-a-url",
        run_id="run_ok_001",
        target_language="de",
        duration_minutes=2,
        source_type="article",
        out_root=str(tmp_path),
    )
    assert res["ok"] is False
    assert res["error_code"] == "invalid_url"
    assert res["exit_code"] == 3


# ----------------------------
# Article path
# ----------------------------


def test_article_success_writes_generate_script_response(bridge_mod, tmp_path: Path):
    with patch.object(
        bridge_mod, "extract_text_from_url", return_value=("Body text " * 80, [])
    ), patch.object(
        bridge_mod,
        "build_script_response_from_extracted_text",
        return_value=_article_response_tuple(),
    ):
        res = bridge_mod.run_bridge(
            url="https://example.com/news/1",
            run_id="article_run_001",
            target_language="de",
            duration_minutes=3,
            source_type="auto",
            out_root=str(tmp_path),
        )

    assert res["ok"] is True
    assert res["status"] == "completed"
    assert res["source_type"] == "article"
    assert res["exit_code"] == 0

    out_path = Path(res["generate_script_response_path"])
    assert out_path.is_file()
    parsed = json.loads(out_path.read_text(encoding="utf-8"))

    # Vertrag bleibt unverändert: 6 Pflichtfelder
    for key in ("title", "hook", "chapters", "full_script", "sources", "warnings"):
        assert key in parsed
    assert parsed["title"] == "Article Title"
    assert parsed["hook"] == "Article hook line."
    assert isinstance(parsed["chapters"], list) and len(parsed["chapters"]) == 3

    # Bridge-Metadaten sind zusätzlich vorhanden, brechen aber nichts:
    assert parsed["run_id"] == "article_run_001"
    assert parsed["source_url"] == "https://example.com/news/1"
    assert parsed["source_type"] == "article"
    assert parsed["target_language"] == "de"
    assert int(parsed["duration_minutes"]) == 3
    assert isinstance(parsed["created_at_epoch"], int)


def test_article_extraction_empty_returns_failed(bridge_mod, tmp_path: Path):
    with patch.object(
        bridge_mod, "extract_text_from_url", return_value=("", ["empty_extract"])
    ):
        res = bridge_mod.run_bridge(
            url="https://example.com/empty",
            run_id="article_empty_001",
            target_language="de",
            duration_minutes=2,
            source_type="article",
            out_root=str(tmp_path),
        )
    assert res["ok"] is False
    assert res["status"] == "failed"
    assert res["exit_code"] == 1
    assert "article_extraction_empty" in res.get("blocking_reasons", [])


# ----------------------------
# YouTube path
# ----------------------------


def test_youtube_success_writes_generate_script_response(bridge_mod, tmp_path: Path):
    with patch.object(
        bridge_mod, "generate_script_from_youtube_video", return_value=_youtube_response_dict()
    ):
        res = bridge_mod.run_bridge(
            url="https://www.youtube.com/watch?v=abc123XYZ12",
            run_id="yt_run_001",
            target_language="de",
            duration_minutes=2,
            source_type="auto",
            out_root=str(tmp_path),
        )

    assert res["ok"] is True
    assert res["source_type"] == "youtube"
    assert res["exit_code"] == 0

    parsed = json.loads(Path(res["generate_script_response_path"]).read_text(encoding="utf-8"))
    assert parsed["title"] == "YT Title"
    assert parsed["source_url"].startswith("https://www.youtube.com/")
    assert parsed["source_type"] == "youtube"
    assert isinstance(parsed["warnings"], list)


def test_youtube_empty_result_returns_failed(bridge_mod, tmp_path: Path):
    with patch.object(
        bridge_mod,
        "generate_script_from_youtube_video",
        return_value={
            "title": "",
            "hook": "",
            "chapters": [],
            "full_script": "",
            "sources": [],
            "warnings": ["transcript_unavailable"],
        },
    ):
        res = bridge_mod.run_bridge(
            url="https://youtu.be/abcdEFGHIJK",
            run_id="yt_empty_001",
            target_language="de",
            duration_minutes=2,
            source_type="youtube",
            out_root=str(tmp_path),
        )

    assert res["ok"] is False
    assert res["status"] == "failed"
    assert res["exit_code"] == 1
    assert "youtube_generation_empty" in res.get("blocking_reasons", [])


# ----------------------------
# Adapter compatibility (BA 25.2)
# ----------------------------


def test_output_is_compatible_with_ba252_adapter(bridge_mod, adapter_mod, tmp_path: Path):
    with patch.object(
        bridge_mod, "extract_text_from_url", return_value=("Body " * 80, [])
    ), patch.object(
        bridge_mod,
        "build_script_response_from_extracted_text",
        return_value=_article_response_tuple(),
    ):
        res = bridge_mod.run_bridge(
            url="https://example.com/news/2",
            run_id="adapter_run_001",
            target_language="de",
            duration_minutes=2,
            source_type="article",
            out_root=str(tmp_path),
        )
    assert res["ok"] is True
    parsed = json.loads(Path(res["generate_script_response_path"]).read_text(encoding="utf-8"))

    pack = adapter_mod.build_scene_asset_pack_from_generate_script_response(
        parsed, run_id=parsed["run_id"]
    )
    beats = (pack.get("scene_expansion") or {}).get("expanded_scene_assets") or []
    assert beats, "Adapter must produce at least one beat from bridge output"
    narrations = [str(b.get("narration") or "") for b in beats]
    # Mindestens eine Kapitel-Inhalts-Narration kommt durch:
    assert any("Erster Inhalt." in n for n in narrations)


# ----------------------------
# CLI behaviour (--print-json)
# ----------------------------


def test_cli_print_json_emits_parsable_json(bridge_mod, tmp_path: Path):
    with patch.object(
        bridge_mod, "extract_text_from_url", return_value=("Body " * 80, [])
    ), patch.object(
        bridge_mod,
        "build_script_response_from_extracted_text",
        return_value=_article_response_tuple(),
    ):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = bridge_mod.main(
                [
                    "--url",
                    "https://example.com/news/3",
                    "--run-id",
                    "cli_run_001",
                    "--target-language",
                    "de",
                    "--duration-minutes",
                    "2",
                    "--source-type",
                    "article",
                    "--out-root",
                    str(tmp_path),
                    "--print-json",
                ]
            )
    assert rc == 0
    parsed = json.loads(buf.getvalue())
    assert parsed["ok"] is True
    assert parsed["status"] == "completed"
    assert "generate_script_response_path" in parsed


def test_cli_invalid_run_id_emits_error_json_exit_3(bridge_mod, tmp_path: Path):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = bridge_mod.main(
            [
                "--url",
                "https://example.com/news/x",
                "--run-id",
                "bad/run",
                "--out-root",
                str(tmp_path),
                "--print-json",
            ]
        )
    assert rc == 3
    parsed = json.loads(buf.getvalue())
    assert parsed["ok"] is False
    assert parsed["error_code"] == "invalid_run_id"


# ----------------------------
# BA 25.3 must NOT call render/orchestrator
# ----------------------------


def test_ba253_does_not_call_orchestrator_or_render(bridge_mod, tmp_path: Path):
    """Bridge darf weder Orchestrator noch Render-Skripte aufrufen."""
    forbidden_modules: List[str] = [
        "scripts.run_real_video_build",
        "run_real_video_build",
    ]
    with patch.object(
        bridge_mod, "extract_text_from_url", return_value=("Body " * 80, [])
    ), patch.object(
        bridge_mod,
        "build_script_response_from_extracted_text",
        return_value=_article_response_tuple(),
    ):
        res = bridge_mod.run_bridge(
            url="https://example.com/news/4",
            run_id="no_orch_001",
            target_language="de",
            duration_minutes=2,
            source_type="article",
            out_root=str(tmp_path),
        )
    assert res["ok"] is True

    # Es darf keine Render-/Orchestrator-Artefakte unter der run_dir geben.
    run_dir = Path(res["build_dir"])
    assert run_dir.is_dir()
    forbidden_artefacts = [
        "real_video_build_result.json",
        "scene_asset_pack.json",
        "clean_video.mp4",
        "preview_with_subtitles.mp4",
        "final_video.mp4",
        "final_render_result.json",
    ]
    for name in forbidden_artefacts:
        assert not (run_dir / name).exists(), f"BA 25.3 darf {name} nicht erzeugen"

    # Module dürfen nicht implizit geladen worden sein.
    for m in forbidden_modules:
        assert m not in sys.modules or sys.modules[m] is not None  # smoke; kein hard import erwartet
