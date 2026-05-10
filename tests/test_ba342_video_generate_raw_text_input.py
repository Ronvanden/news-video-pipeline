"""BA 32.42 — Raw Text Input für /founder/dashboard/video/generate (keine Provider-Calls)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.founder_dashboard.ba323_video_generate import execute_dashboard_video_generate


def test_execute_dashboard_video_generate_forwards_raw_text_and_title(tmp_path: Path):
    class _FakeMod:
        def __init__(self):
            self.kw = None

        def run_ba265_url_to_final(self, **kwargs):
            self.kw = dict(kwargs)
            out_dir = Path(str(kwargs.get("out_dir") or "")).resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            # Simuliere erzeugte Artefakte (script/pack/manifest), ohne ffmpeg oder Provider.
            (out_dir / "script.json").write_text(
                json.dumps(
                    {
                        "title": "T",
                        "hook": "H",
                        "chapters": [],
                        "full_script": "x",
                        "sources": ["raw_text"],
                        "warnings": ["raw_text_input_used"],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (out_dir / "scene_plan.json").write_text(json.dumps({"title": "T", "scenes": []}), encoding="utf-8")
            (out_dir / "scene_asset_pack.json").write_text(
                json.dumps({"scene_expansion": {"expanded_scene_assets": []}}), encoding="utf-8"
            )
            gen_dir = out_dir / "generated_assets_x"
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
                "input_mode": "raw_text",
                "url": None,
                "output_dir": str(out_dir),
                "final_video_path": "",
                "script_path": str(out_dir / "script.json"),
                "scene_plan_path": str(out_dir / "scene_plan.json"),
                "scene_asset_pack_path": str(out_dir / "scene_asset_pack.json"),
                "asset_manifest_path": str(mp),
                "warnings": ["raw_text_input_used"],
                "blocking_reasons": [],
            }

    fake = _FakeMod()
    with patch("app.founder_dashboard.ba323_video_generate._load_run_url_to_final_mod", lambda: fake):
        out = execute_dashboard_video_generate(
            url=None,
            raw_text="Ein kurzer Artikeltext für Smoke.",
            title="Smoke Titel",
            output_dir=tmp_path / "out",
            run_id="ba342",
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
    assert out.get("ok") is True
    assert fake.kw is not None
    assert fake.kw.get("raw_text")
    assert fake.kw.get("title") == "Smoke Titel"
    assert fake.kw.get("url") is None


def test_run_url_to_final_raw_text_bypasses_url_extraction(tmp_path: Path):
    # Direkter Test auf run_ba265_url_to_final: extract_text_from_url darf nicht aufgerufen werden.
    import importlib.util

    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "run_url_to_final_mp4.py"
    spec = importlib.util.spec_from_file_location("run_url_to_final_ba342", script)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    with patch.object(m, "extract_text_from_url", side_effect=AssertionError("should_not_extract")):
        # build_script_response_from_extracted_text ist schwergewichtig; stubben.
        with patch.object(
            m,
            "build_script_response_from_extracted_text",
            return_value=(
                "T",
                "H",
                [{"title": "K1", "content": "C"}],
                "FULL",
                ["raw_text"],
                ["raw_text_input_used"],
            ),
        ):
            doc = m.run_ba265_url_to_final(
                url=None,
                raw_text="Text",
                title="",
                script_json_path=None,
                out_dir=tmp_path / "out2",
                max_scenes=1,
                duration_seconds=20,
                asset_dir=None,
                run_id="ba342b",
                motion_mode="static",
                voice_mode="none",
                asset_runner_mode="placeholder",
                max_live_assets=None,
                max_motion_clips=0,
            )
    assert (tmp_path / "out2" / "script.json").is_file()
    assert (tmp_path / "out2" / "scene_plan.json").is_file()
    assert (tmp_path / "out2" / "scene_asset_pack.json").is_file()
    assert "url_extraction_empty_use_script_json" not in " ".join(doc.get("blocking_reasons") or [])

