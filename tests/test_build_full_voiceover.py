"""BA 20.0 / BA 20.1 — build_full_voiceover.py."""

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


def test_chunk_narration_splits_long_text(voice_mod):
    block = "wort " * 3000
    chunks = voice_mod.chunk_narration_for_tts(block, 1000)
    assert len(chunks) >= 3
    assert all(len(c) <= 1000 for c in chunks)


def test_chunk_narration_respects_paragraphs(voice_mod):
    p1 = "Absatz eins. " * 80
    p2 = "Absatz zwei. " * 80
    text = p1 + "\n\n" + p2
    chunks = voice_mod.chunk_narration_for_tts(text, 1200)
    assert len(chunks) >= 2


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
    assert meta["provider_used"] == "smoke"
    assert meta["real_tts_generated"] is False
    assert meta["fallback_used"] is False
    assert meta["chunk_count"] == 0
    out = Path(meta["output_dir"])
    assert (out / "narration_script.txt").is_file()
    assert (out / "voice_manifest.json").is_file()
    man = json.loads((out / "voice_manifest.json").read_text(encoding="utf-8"))
    assert man["run_id"] == "t20"
    assert man["voice_mode"] == "smoke"
    assert "provider_used" in man
    assert "chunk_count" in man
    assert "real_tts_generated" in man
    assert "fallback_used" in man
    assert man["provider_used"] == "smoke"
    assert man["chunk_count"] == 0
    assert man["real_tts_generated"] is False
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
    assert man["provider_used"] == "none"


def test_elevenlabs_env_missing_fallback_smoke(voice_mod, tmp_path, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    plan = _minimal_plan()

    def fake_write(*a, **k):
        return True, []

    monkeypatch.setattr(voice_mod, "_write_smoke_mp3_ffmpeg", fake_write)

    meta = voice_mod.build_full_voiceover(
        plan,
        run_id="el20",
        out_root=tmp_path,
        voice_mode="elevenlabs",
        ffmpeg_bin="x",
    )
    assert meta["voice_mode"] == "elevenlabs"
    assert "elevenlabs_env_missing_fallback_smoke" in meta["warnings"]
    assert meta["fallback_used"] is True
    assert meta["provider_used"] == "smoke"
    assert meta["real_tts_generated"] is False


def test_openai_env_missing_fallback_smoke(voice_mod, tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    plan = _minimal_plan()

    def fake_write(*a, **k):
        return True, []

    monkeypatch.setattr(voice_mod, "_write_smoke_mp3_ffmpeg", fake_write)

    meta = voice_mod.build_full_voiceover(
        plan,
        run_id="oa20",
        out_root=tmp_path,
        voice_mode="openai",
        ffmpeg_bin="x",
    )
    assert meta["voice_mode"] == "openai"
    assert "openai_tts_env_missing_fallback_smoke" in meta["warnings"]
    assert meta["fallback_used"] is True
    assert meta["provider_used"] == "smoke"


def test_elevenlabs_mock_post_single_chunk_success(voice_mod, tmp_path, monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-fake")
    plan = _minimal_plan()

    def fake_write(*a, **k):
        return True, []

    monkeypatch.setattr(voice_mod, "_write_smoke_mp3_ffmpeg", fake_write)

    def fake_post(_text, _key, _vid, _body_json):
        return b"ID3fake"

    meta = voice_mod.build_full_voiceover(
        plan,
        run_id="elok2",
        out_root=tmp_path,
        voice_mode="elevenlabs",
        ffmpeg_bin="ffmpeg_mock",
        elevenlabs_post_override=fake_post,
    )
    assert meta["ok"] is True
    assert meta["provider_used"] == "elevenlabs"
    assert meta["real_tts_generated"] is True
    assert meta["fallback_used"] is False
    assert meta["chunk_count"] >= 1


def test_voice_mode_unknown_defaults_smoke(voice_mod, tmp_path, monkeypatch):
    plan = _minimal_plan()

    def fake_write(*a, **k):
        return True, []

    monkeypatch.setattr(voice_mod, "_write_smoke_mp3_ffmpeg", fake_write)

    meta = voice_mod.build_full_voiceover(
        plan,
        run_id="unk",
        out_root=tmp_path,
        voice_mode="legacy_provider",
        ffmpeg_bin="x",
    )
    assert meta["voice_mode"] == "smoke"
    assert "voice_mode_unknown_defaulting_smoke" in meta["warnings"]


def test_load_plan_json_strips_full_script_before_validate(voice_mod, tmp_path):
    p = tmp_path / "plan.json"
    body = _minimal_plan().model_dump()
    body["full_script"] = "Extra Skript aus Export. " * 15
    p.write_text(json.dumps(body), encoding="utf-8")
    plan, fs = voice_mod.load_plan_from_json_file(p)
    assert fs
    assert "Extra Skript" in fs
    assert plan.hook
