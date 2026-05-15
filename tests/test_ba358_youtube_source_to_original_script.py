"""BA 32.58 — YouTube-Source → Originalskript → Video (keine echten Provider/YouTube-Calls)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import utils as app_utils
from app.main import app
from app.founder_dashboard.ba323_video_generate import execute_dashboard_video_generate


def _load_run_url_to_final_mod():
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "run_url_to_final_mp4.py"
    spec = importlib.util.spec_from_file_location("run_url_to_final_ba358", script)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_run_ba265_youtube_source_calls_rewrite_helper_not_raw_transcript(tmp_path: Path) -> None:
    m = _load_run_url_to_final_mod()

    def _fake_build(*, source_youtube_url: str, duration_minutes: int, **kwargs):
        assert "youtube.com" in source_youtube_url or "youtu.be" in source_youtube_url
        assert duration_minutes >= 1
        return (
            {
                "title": "Neu generierter Titel",
                "hook": "Eigener Hook",
                "chapters": [{"title": "K1", "content": "Inhalt"}],
                    "full_script": "Komplett neuer Fließtext aus dem Rewrite-Pfad.",
                "sources": ["https://www.youtube.com/watch?v=abc123def45"],
                "warnings": ["youtube_source_rewrite_used", "transcript_used_as_source_material"],
            },
            True,
            ["youtube_source_rewrite_used", "transcript_used_as_source_material"],
            [],
        )

    with patch.object(m, "build_script_dict_from_youtube_source", side_effect=_fake_build):
        with patch.object(m, "extract_text_from_url", side_effect=AssertionError("url_extract_should_not_run")):
            doc = m.run_ba265_url_to_final(
                url="https://example.com/should-not-be-used",
                raw_text="should not win",
                source_youtube_url="https://www.youtube.com/watch?v=abc123def45",
                script_json_path=None,
                out_dir=tmp_path / "yt_out",
                max_scenes=2,
                duration_seconds=120,
                asset_dir=None,
                run_id="ba358yt",
                motion_mode="static",
                voice_mode="none",
                asset_runner_mode="placeholder",
                max_live_assets=None,
                max_motion_clips=0,
            )
    assert doc.get("input_mode") == "youtube_source"
    assert doc.get("transcript_available") is True
    assert doc.get("generated_original_script") is True
    assert "youtube.com" in str(doc.get("source_youtube_url") or "")
    body = json.loads((tmp_path / "yt_out" / "script.json").read_text(encoding="utf-8"))
    # Simuliertes Roh-Transkript (dürfte bei echtem Rewrite nicht 1:1 in full_script landen):
    assert "ZZONLYINORIGINALTRANSCRIPT99" not in (body.get("full_script") or "")
    assert "Rewrite-Pfad" in (body.get("full_script") or "")
    br = " ".join(doc.get("blocking_reasons") or [])
    assert "url_extraction_empty_use_script_json" not in br


def test_run_ba265_youtube_transcript_missing_blocks_without_providers(tmp_path: Path) -> None:
    m = _load_run_url_to_final_mod()

    def _fake_empty(*, source_youtube_url: str, **kwargs):
        return None, False, [], ["youtube_transcript_missing"]

    with patch.object(m, "build_script_dict_from_youtube_source", side_effect=_fake_empty):
        with patch.object(m, "extract_text_from_url", side_effect=AssertionError("no_url_extract")):
            doc = m.run_ba265_url_to_final(
                url=None,
                raw_text=None,
                source_youtube_url="https://www.youtube.com/watch?v=nosuchtranscript",
                script_json_path=None,
                out_dir=tmp_path / "yt_block",
                max_scenes=1,
                duration_seconds=60,
                asset_dir=None,
                run_id="ba358blk",
                motion_mode="static",
                voice_mode="none",
                asset_runner_mode="placeholder",
                max_live_assets=None,
                max_motion_clips=0,
            )
    assert doc.get("ok") is False
    assert "youtube_transcript_missing" in (doc.get("blocking_reasons") or [])
    assert "transcript_missing" in (doc.get("warnings") or [])
    assert "youtube_transcript_unavailable" in (doc.get("warnings") or [])
    assert doc.get("generated_original_script") is False
    assert (tmp_path / "yt_block" / "scene_plan.json").is_file() is False


def test_run_ba265_final_script_wins_over_youtube(tmp_path: Path) -> None:
    m = _load_run_url_to_final_mod()
    called = {"n": 0}

    def _fake_build(**kwargs):
        called["n"] += 1
        raise AssertionError("youtube_should_not_run")

    inline = {
        "title": "Final",
        "hook": "H",
        "chapters": [],
        "full_script": "Nur final script.",
        "sources": [],
        "warnings": [],
    }
    with patch.object(m, "build_script_dict_from_youtube_source", side_effect=_fake_build):
        with patch.object(m, "extract_text_from_url", side_effect=AssertionError("no_extract")):
            doc = m.run_ba265_url_to_final(
                url="https://example.com/x",
                source_youtube_url="https://www.youtube.com/watch?v=abc123def45",
                inline_script=inline,
                script_json_path=None,
                out_dir=tmp_path / "final_wins",
                max_scenes=1,
                duration_seconds=60,
                asset_dir=None,
                run_id="ba358fs",
                motion_mode="static",
                voice_mode="none",
                asset_runner_mode="placeholder",
                max_live_assets=None,
                max_motion_clips=0,
            )
    assert called["n"] == 0
    assert doc.get("input_mode") == "final_script"
    body = json.loads((tmp_path / "final_wins" / "script.json").read_text(encoding="utf-8"))
    assert body.get("full_script") == "Nur final script."


def test_dashboard_youtube_url_conflict_422() -> None:
    client = TestClient(app)
    r = client.post(
        "/founder/dashboard/video/generate",
        json={
            "source_youtube_url": "https://www.youtube.com/watch?v=aaaaaaaaaaa",
            "youtube_url": "https://www.youtube.com/watch?v=bbbbbbbbbbb",
        },
    )
    assert r.status_code == 422


def test_dashboard_url_youtube_watch_auto_routes_to_source_youtube_url() -> None:
    client = TestClient(app)
    captured: dict = {}

    def _fake_execute(**kwargs):
        captured.update(kwargs)
        return {
            "ok": False,
            "run_id": "stub",
            "warnings": [],
            "blocking_reasons": ["stubbed"],
        }

    with patch("app.routes.founder_dashboard.execute_dashboard_video_generate", side_effect=_fake_execute):
        r = client.post(
            "/founder/dashboard/video/generate",
            json={"url": "https://www.youtube.com/watch?v=abc123XYZ12"},
        )

    assert r.status_code == 200
    assert captured.get("url") is None
    assert captured.get("source_youtube_url") == "https://www.youtube.com/watch?v=abc123XYZ12"


def test_dashboard_article_url_remains_article_url() -> None:
    client = TestClient(app)
    captured: dict = {}

    def _fake_execute(**kwargs):
        captured.update(kwargs)
        return {
            "ok": False,
            "run_id": "stub",
            "warnings": [],
            "blocking_reasons": ["stubbed"],
        }

    with patch("app.routes.founder_dashboard.execute_dashboard_video_generate", side_effect=_fake_execute):
        r = client.post(
            "/founder/dashboard/video/generate",
            json={"url": "https://example.com/article"},
        )

    assert r.status_code == 200
    assert captured.get("url") == "https://example.com/article"
    assert captured.get("source_youtube_url") is None


def test_execute_forwards_youtube_and_script_fields(tmp_path: Path) -> None:
    captured: dict = {}

    class _FakeMod:
        def run_ba265_url_to_final(self, **kwargs):
            captured.update(kwargs)
            out_dir = Path(str(kwargs.get("out_dir") or "")).resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "script.json").write_text("{}", encoding="utf-8")
            (out_dir / "scene_plan.json").write_text("{}", encoding="utf-8")
            (out_dir / "scene_asset_pack.json").write_text("{}", encoding="utf-8")
            gen_dir = out_dir / "g"
            gen_dir.mkdir(parents=True, exist_ok=True)
            (gen_dir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            mp = gen_dir / "asset_manifest.json"
            mp.write_text(
                json.dumps(
                    {
                        "asset_count": 1,
                        "generation_mode": "placeholder",
                        "warnings": [],
                        "assets": [{"image_path": "scene_001.png", "generation_mode": "placeholder"}],
                    }
                ),
                encoding="utf-8",
            )
            return {
                "ok": True,
                "input_mode": "youtube_source",
                "source_youtube_url": "https://www.youtube.com/watch?v=x",
                "transcript_available": True,
                "generated_original_script": True,
                "output_dir": str(out_dir),
                "final_video_path": "",
                "script_path": str(out_dir / "script.json"),
                "scene_asset_pack_path": str(out_dir / "scene_asset_pack.json"),
                "asset_manifest_path": str(mp),
                "warnings": [],
                "blocking_reasons": [],
            }

    with patch("app.founder_dashboard.ba323_video_generate._load_run_url_to_final_mod", lambda: _FakeMod()):
        out = execute_dashboard_video_generate(
            url=None,
            raw_text=None,
            script_text=None,
            source_youtube_url="https://www.youtube.com/watch?v=x",
            rewrite_style="news",
            video_template="generic",
            target_language="de",
            output_dir=tmp_path / "ex",
            run_id="e358",
            duration_target_seconds=600,
            max_scenes=2,
            max_live_assets=1,
            motion_clip_every_seconds=60,
            motion_clip_duration_seconds=10,
            max_motion_clips=0,
            allow_live_assets=False,
            allow_live_motion=False,
            voice_mode="none",
            motion_mode="static",
        )
    assert captured.get("source_youtube_url") == "https://www.youtube.com/watch?v=x"
    assert captured.get("rewrite_style") == "news"
    assert captured.get("video_template") == "generic"
    assert captured.get("target_language") == "de"
    assert out.get("input_mode") == "youtube_source"
    assert out.get("generated_original_script") is True


def test_youtube_transcript_missing_adds_clear_warning(tmp_path: Path) -> None:
    m = _load_run_url_to_final_mod()

    def _fake_empty(*, source_youtube_url: str, **kwargs):
        return None, False, ["transcript_missing", "youtube_transcript_unavailable"], ["youtube_transcript_missing"]

    with patch.object(m, "build_script_dict_from_youtube_source", side_effect=_fake_empty):
        with patch.object(m, "extract_text_from_url", side_effect=AssertionError("no_url_extract")):
            doc = m.run_ba265_url_to_final(
                url=None,
                raw_text=None,
                source_youtube_url="https://www.youtube.com/watch?v=nosuchid1234",
                script_json_path=None,
                out_dir=tmp_path / "yt_warn",
                max_scenes=1,
                duration_seconds=60,
                asset_dir=None,
                run_id="ba358warn",
                motion_mode="static",
                voice_mode="none",
                asset_runner_mode="placeholder",
                max_live_assets=None,
                max_motion_clips=0,
            )
    assert doc.get("ok") is False
    assert "youtube_transcript_missing" in (doc.get("blocking_reasons") or [])
    assert "transcript_missing" in (doc.get("warnings") or [])
    assert "youtube_transcript_unavailable" in (doc.get("warnings") or [])


def test_wordcount_warning_counts_chapters_when_full_script_empty() -> None:
    def _fake_generate_script(*args, **kwargs):
        return (
            "Titel",
            "Hook mit mehreren Worten.",
            [
                {"title": "Kapitel 1", "content": "Alpha beta gamma delta."},
                {"title": "Kapitel 2", "content": "Epsilon zeta eta theta."},
            ],
            "",
            "llm",
            "",
        )

    with patch.object(app_utils, "summarize_text", return_value="Zusammenfassung"):
        with patch.object(app_utils, "translate_to_german", return_value="Zusammenfassung"):
            with patch.object(app_utils, "extract_key_points", return_value=["Ein Punkt mit ausreichend Text"]):
                with patch.object(app_utils, "generate_title", return_value="Titel"):
                    with patch.object(app_utils.ScriptGenerator, "generate_script", side_effect=_fake_generate_script):
                        _title, _hook, _chapters, _full_script, _sources, warnings = (
                            app_utils.build_script_response_from_extracted_text(
                                extracted_text="Quelle mit ein bisschen Inhalt.",
                                source_url="https://example.com/article",
                                target_language="de",
                                duration_minutes=1,
                            )
                        )

    wc_warnings = [w for w in warnings if str(w).startswith("Target word count:")]
    assert wc_warnings
    assert "Actual word count: 0" not in wc_warnings[0]
