from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

from app import utils


_ROOT = Path(__file__).resolve().parents[1]
_BA265 = _ROOT / "scripts" / "run_url_to_final_mp4.py"


def _load_ba265_module():
    spec = importlib.util.spec_from_file_location("run_url_to_final_mp4_length_t", _BA265)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_120_seconds_maps_to_elevenlabs_calibrated_target_words():
    ba265 = _load_ba265_module()
    audit = ba265._duration_scaling_audit(
        target_seconds=120,
        script_word_count=256,
        scene_count=5,
        voice_duration_seconds=118.0,
        final_video_duration_seconds=119.0,
    )
    assert audit["target_word_count"] == 256
    assert audit["scene_count"] == 5
    assert audit["estimated_voice_wpm"] == 130.169


def test_duration_audit_warns_when_target_is_overshot():
    ba265 = _load_ba265_module()
    audit = ba265._duration_scaling_audit(
        target_seconds=120,
        script_word_count=317,
        scene_count=5,
        voice_duration_seconds=148.75,
        final_video_duration_seconds=149.04,
    )
    warnings = ba265._duration_scaling_warnings(audit)
    assert audit["duration_ratio"] == 1.242
    assert audit["estimated_voice_wpm"] == 127.866
    assert "target_duration_overshot" in warnings
    assert "voice_longer_than_target_duration" in warnings


def test_duration_audit_prefers_full_script_without_chapter_duplication():
    ba265 = _load_ba265_module()
    script = {
        "hook": "Hook words should not duplicate.",
        "chapters": [{"title": "Kapitel", "content": "Short chapter."}],
        "full_script": "one two three four five",
    }
    assert ba265._script_text_for_duration_audit(script) == "one two three four five"


def test_voiceover_prefers_full_script_when_chapter_rows_are_shorter():
    ba265 = _load_ba265_module()
    script = {
        "full_script": " ".join([f"word{i}" for i in range(40)]),
    }
    scene_rows = [{"narration": "short row narration"}]
    text, source = ba265._collect_voiceover_text_from_script(script, scene_rows)
    assert source == "full_script"
    assert text == script["full_script"]


def test_script_generation_prompt_contains_duration_and_length_direction():
    source = inspect.getsource(utils.ScriptGenerator._generate_with_openai)
    assert "Zielwortanzahl: {target_word_count}" in source
    assert "Mindestwortanzahl: {min_word_count}" in source
    assert "Die Zielwortanzahl ist verbindlich" in source
    assert "Kein Telegrammstil" in source
    assert "vorhandenes Material ausfuehrlicher paraphrasieren" in source


def test_expansion_pass_uses_dynamic_word_band_for_short_targets():
    source = inspect.getsource(utils.ScriptGenerator._expand_llm_script_with_openai)
    assert "target_min_words = max(1, int(min_word_count))" in source
    assert "target_word_count <= 400" in source
    assert "desired_new_words" in source
    assert "nahe {target_word_count} Woerter" in source


def test_short_script_gets_precise_duration_warnings(monkeypatch):
    def fake_generate_script(self, title, key_points, duration_minutes, source_word_count=0, **kwargs):
        del self, key_points, duration_minutes, source_word_count, kwargs
        return (
            title,
            "Kurzer Hook.",
            [{"title": "Kapitel 1", "content": "Kurz."}],
            "Kurzes Skript.",
            "llm",
            "LLM expansion still below target",
        )

    monkeypatch.setattr(utils, "summarize_text", lambda text, sentences_count=20: text)
    monkeypatch.setattr(utils, "translate_to_german", lambda text: text)
    monkeypatch.setattr(utils, "extract_key_points", lambda text: ["Punkt eins", "Punkt zwei"])
    monkeypatch.setattr(utils, "generate_title", lambda text: "Testtitel")
    monkeypatch.setattr(utils.ScriptGenerator, "generate_script", fake_generate_script)

    _title, _hook, _chapters, _full_script, _sources, warnings = (
        utils.build_script_response_from_extracted_text(
            extracted_text="Ausreichend Quellmaterial fuer einen Test.",
            source_url="https://example.com/source",
            target_language="de",
            duration_minutes=2,
            extraction_warnings=[],
            video_template="generic",
        )
    )

    assert "Target word count: 256, Actual word count: 2" in warnings
    assert "script_below_target_after_expansion" in warnings
    assert "duration_target_unreachable_due_to_short_script" in warnings
