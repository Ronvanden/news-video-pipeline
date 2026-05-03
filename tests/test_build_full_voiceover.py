"""BA 20.0 — build_full_voiceover.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from app.prompt_engine.schema import ChapterOutlineItem, ProductionPromptPlan

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "build_full_voiceover.py"


@pytest.fixture(scope="module")
def voice_mod():
    spec = importlib.util.spec_from_file_location("build_full_voiceover", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _minimal_plan(**kwargs) -> ProductionPromptPlan:
    defaults = dict(
        template_type="true_crime",
        tone="ernst",
        hook="Standard-Hook für Tests.",
        chapter_outline=[
            ChapterOutlineItem(title="A", summary="Erstes Kapitel mit genügend Text für den Voiceover-Fallback."),
            ChapterOutlineItem(title="B", summary="Zweites Kapitel füllt die Sprechspur weiter aus."),
        ],
        scene_prompts=["Szene eins.", "Szene zwei."],
        voice_style="calm",
        thumbnail_angle="dramatic",
    )
    defaults.update(kwargs)
    return ProductionPromptPlan(**defaults)


def test_extract_prefers_full_script_json(voice_mod):
    plan = _minimal_plan()
    text, st, _ = voice_mod.extract_narration_text(
        plan,
        full_script_json="Dies ist das volle Skript. Es hat viele Wörter und soll Vorrang haben vor Kapiteln.",
    )
    assert st == "full_script"
    assert "volle Skript" in text
    assert "Erstes Kapitel" not in text


def test_extract_chapter_summaries_when_no_full_script(voice_mod):
    plan = _minimal_plan()
    text, st, warns = voice_mod.extract_narration_text(plan, full_script_json="")
    assert st == "chapter_summaries"
    assert "Erstes Kapitel" in text
    assert "Zweites Kapitel" in text
    assert not any("hook_only" in w for w in warns)


def test_extract_hook_plus_chapters_when_summaries_too_short(voice_mod):
    plan = _minimal_plan(
        chapter_outline=[
            ChapterOutlineItem(title="X", summary="a"),
            ChapterOutlineItem(title="Y", summary="b"),
        ],
        hook="Ausführlicher Hook der als Ergänzung zur dünnen Kapiteltexte dienen soll und lang genug ist.",
    )
    text, st, warns = voice_mod.extract_narration_text(plan, full_script_json="")
    assert st == "hook_plus_chapter_summaries"
    assert "Ausführlicher Hook" in text
    assert any("narration_fallback_hook_plus_chapters" in w for w in warns)


def test_extract_hook_only_then_empty(voice_mod):
    plan = _minimal_plan(hook="Nur der Hook bleibt.", chapter_outline=[], scene_prompts=["s"])
    text, st, warns = voice_mod.extract_narration_text(plan, full_script_json="")
    assert st == "hook_only"
    assert "Hook" in text

    empty = _minimal_plan(hook="", chapter_outline=[], scene_prompts=["s"])
    text2, st2, warns2 = voice_mod.extract_narration_text(empty, full_script_json="")
    assert st2 == "empty"
    assert text2 == ""
    assert any("narration_text_empty" in w for w in warns2)


def test_build_writes_files_and_duration_above_smoke_baseline(voice_mod, tmp_path, monkeypatch):
    long_script = " ".join([f"wort{i}" for i in range(120)])
    plan = _minimal_plan()

    def fake_write(_mp3, dur, _ff):
        assert dur >= 30  # 120 Wörter / 145 wpm * 60 ≈ 49 s
        return True, []

    monkeypatch.setattr(voice_mod, "_write_smoke_mp3_ffmpeg", fake_write)

    meta = voice_mod.build_full_voiceover(
        plan,
        run_id="t20",
        out_root=tmp_path,
        voice_mode="smoke",
        full_script_json=long_script,
        ffmpeg_bin="ffmpeg_mock",
    )
    assert meta["ok"] is True
    assert meta["source_type"] == "full_script"
    assert meta["word_count"] >= 100
    assert meta["estimated_duration_seconds"] > voice_mod.SMOKE_BASELINE_SECONDS
    out = Path(meta["output_dir"])
    assert (out / "narration_script.txt").is_file()
    assert (out / "voice_manifest.json").is_file()
    man = json.loads((out / "voice_manifest.json").read_text(encoding="utf-8"))
    assert man["run_id"] == "t20"
    assert man["voice_mode"] == "smoke"
    assert "blocking_reasons" in man and "warnings" in man


def test_missing_narration_handled_cleanly(voice_mod, tmp_path):
    plan = _minimal_plan(hook="", chapter_outline=[], scene_prompts=["x"])
    meta = voice_mod.build_full_voiceover(
        plan,
        run_id="empty20",
        out_root=tmp_path,
        voice_mode="smoke",
        full_script_json="",
        ffmpeg_bin="",
    )
    assert meta["ok"] is False
    assert "narration_text_empty" in meta["blocking_reasons"]
    man_path = Path(meta["voice_manifest_path"])
    man = json.loads(man_path.read_text(encoding="utf-8"))
    assert man["word_count"] == 0
    assert man["estimated_duration_seconds"] == 0


def test_provider_mode_warns_without_env(voice_mod, tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    plan = _minimal_plan()

    def fake_write(*a, **k):
        return True, []

    monkeypatch.setattr(voice_mod, "_write_smoke_mp3_ffmpeg", fake_write)

    meta = voice_mod.build_full_voiceover(
        plan,
        run_id="pv20",
        out_root=tmp_path,
        voice_mode="provider",
        ffmpeg_bin="x",
    )
    assert meta["voice_mode"] == "provider"
    assert "provider_voice_env_missing_using_smoke_placeholder" in meta["warnings"]


def test_load_plan_json_strips_full_script_before_validate(voice_mod, tmp_path):
    p = tmp_path / "plan.json"
    body = _minimal_plan().model_dump()
    body["full_script"] = "Extra Skript aus Export. " * 15
    p.write_text(json.dumps(body), encoding="utf-8")
    plan, fs = voice_mod.load_plan_from_json_file(p)
    assert fs
    assert "Extra Skript" in fs
    assert plan.hook
