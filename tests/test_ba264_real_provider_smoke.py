"""BA 26.4 — Real Provider Smoke (dry_run / Live-Gates, max_real_scenes, force_provider)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.production_connectors.real_provider_smoke import run_real_provider_smoke


def _pack(tmp: Path, *, beats: list[dict], name: str = "p.json") -> Path:
    p = tmp / name
    p.write_text(
        json.dumps({"scene_expansion": {"expanded_scene_assets": beats}}),
        encoding="utf-8",
    )
    return p


def test_dry_run_runway_builds_payload(tmp_path: Path):
    beats = [
        {
            "chapter_index": 0,
            "beat_index": 0,
            "visual_prompt": "A calm skyline.",
            "duration_seconds": 6,
        }
    ]
    pack = _pack(tmp_path, beats=beats)
    r = run_real_provider_smoke(
        pack,
        out_root=tmp_path / "o",
        run_id="dr1",
        selected_provider="runway",
        dry_run=True,
        real_provider_enabled=False,
        max_real_scenes=1,
    )
    assert r["ok"] is True
    sc = r["scenes"][0]
    assert sc["dry_run"] is True
    assert sc["real_call_attempted"] is False
    summ = sc.get("dry_run_request_summary") or {}
    assert summ.get("method") == "POST"
    assert "/v1/image_to_video" in str(summ.get("url", ""))
    pt = str(summ["body_fields"].get("promptText") or "")
    assert "A calm skyline." in pt
    assert "[visual_no_text_guard_v26_4]" in pt
    assert summ["body_fields"].get("promptImage") == "<data_uri_omitted_dry_run>"


def test_live_without_real_provider_enabled_blocks(tmp_path: Path):
    pack = _pack(
        tmp_path,
        beats=[
            {
                "chapter_index": 0,
                "beat_index": 0,
                "visual_prompt": "X",
                "duration_seconds": 5,
            }
        ],
    )
    r = run_real_provider_smoke(
        pack,
        out_root=tmp_path / "o",
        run_id="blk1",
        selected_provider="runway",
        dry_run=False,
        real_provider_enabled=False,
        max_real_scenes=1,
        assets_directory=tmp_path / "assets",
    )
    assert r["ok"] is False
    assert r["scenes"][0]["blocking_reasons"] == ["real_provider_not_enabled"]


def test_live_without_api_key_blocks_cleanly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("RUNWAY_API_KEY", raising=False)
    adir = tmp_path / "assets"
    adir.mkdir()
    (adir / "scene_001.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    pack = _pack(
        tmp_path,
        beats=[
            {
                "chapter_index": 0,
                "beat_index": 0,
                "visual_prompt": "Y",
                "duration_seconds": 5,
            }
        ],
    )
    r = run_real_provider_smoke(
        pack,
        out_root=tmp_path / "o",
        run_id="key1",
        selected_provider="runway",
        dry_run=False,
        real_provider_enabled=True,
        max_real_scenes=1,
        assets_directory=adir,
    )
    assert r["ok"] is False
    sc = r["scenes"][0]
    assert "runway_api_key_missing" in sc["blocking_reasons"]
    assert any("missing_env" in w for w in sc["warnings"])
    assert sc["real_call_attempted"] is False


def test_max_real_scenes_limits_attempts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RUNWAY_API_KEY", "k")
    adir = tmp_path / "assets"
    adir.mkdir()
    for i in (1, 2):
        (adir / f"scene_{i:03d}.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    pack = _pack(
        tmp_path,
        beats=[
            {
                "chapter_index": 0,
                "beat_index": 0,
                "visual_prompt": "A",
                "duration_seconds": 5,
            },
            {
                "chapter_index": 0,
                "beat_index": 1,
                "visual_prompt": "B",
                "duration_seconds": 5,
            },
        ],
    )

    def fake_run(**kwargs):
        return {
            "ok": True,
            "status": "completed",
            "output_video_path": str(tmp_path / "clip.mp4"),
            "warnings": [],
            "blocking_reasons": [],
            "metadata": {"task_id": "t1"},
        }

    r = run_real_provider_smoke(
        pack,
        out_root=tmp_path / "o",
        run_id="mx1",
        selected_provider="runway",
        dry_run=False,
        real_provider_enabled=True,
        max_real_scenes=1,
        assets_directory=adir,
        runway_run_fn=fake_run,
    )
    assert r["scenes"][0]["real_call_attempted"] is True
    assert r["scenes"][0]["real_call_succeeded"] is True
    assert r["scenes"][1]["blocking_reasons"] == ["max_real_scenes_reached"]
    assert r["scenes"][1]["real_call_attempted"] is False
    assert r["ok"] is False


def test_force_provider_overrides_local_clip(tmp_path: Path):
    clip = tmp_path / "local.mp4"
    clip.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    pack = _pack(
        tmp_path,
        beats=[
            {
                "chapter_index": 0,
                "beat_index": 0,
                "visual_prompt": "Z",
                "duration_seconds": 5,
                "runway_clip_path": "local.mp4",
            }
        ],
    )
    r = run_real_provider_smoke(
        pack,
        out_root=tmp_path / "o",
        run_id="fr1",
        selected_provider="runway",
        dry_run=True,
        real_provider_enabled=False,
        force_provider=True,
        max_real_scenes=1,
    )
    sc = r["scenes"][0]
    assert sc["local_video_path"] == str(clip.resolve())
    assert sc.get("dry_run_request_summary") is not None
    assert "local_clip_takes_precedence_skip_provider" not in " ".join(sc["warnings"])


def test_local_clip_skips_without_force(tmp_path: Path):
    clip = tmp_path / "local2.mp4"
    clip.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    pack = _pack(
        tmp_path,
        beats=[
            {
                "chapter_index": 0,
                "beat_index": 0,
                "visual_prompt": "Z",
                "runway_clip_path": "local2.mp4",
            }
        ],
        name="p2.json",
    )
    r = run_real_provider_smoke(
        pack,
        out_root=tmp_path / "o",
        run_id="lc1",
        selected_provider="runway",
        dry_run=True,
        real_provider_enabled=False,
        force_provider=False,
        max_real_scenes=1,
    )
    sc = r["scenes"][0]
    assert sc["local_video_path"] == str(clip.resolve())
    assert sc.get("dry_run_request_summary") is None
    assert any("local_clip_takes_precedence" in w for w in sc["warnings"])


def test_invalid_provider_top_level_block(tmp_path: Path):
    pack = _pack(tmp_path, beats=[{"chapter_index": 0, "beat_index": 0, "visual_prompt": "a"}])
    r = run_real_provider_smoke(
        pack,
        out_root=tmp_path / "o",
        run_id="invp",
        selected_provider="openai",
        dry_run=True,
        real_provider_enabled=False,
    )
    assert "invalid_selected_provider" in r["blocking_reasons"]
