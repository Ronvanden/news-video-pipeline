"""BA 32.73 — Visual Reference Layer V1 (no live API in CI)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

from app.production_connectors.visual_reference_layer import (
    build_visual_reference_brief_v1,
    run_visual_reference_image_v1,
)


def test_brief_builder_required_fields_and_prompt_structure() -> None:
    brief = build_visual_reference_brief_v1(
        title="Test Title",
        hook_or_summary="Kurzfassung zum Thema.",
        video_template="generic",
        target_platform="youtube",
    )
    assert brief["visual_reference_version"] == "ba32_73_v1"
    for k in (
        "title",
        "topic_or_summary",
        "visual_style",
        "subject_lock",
        "subject_lock_reason",
        "master_reference_prompt",
        "negative_prompt",
        "thumbnail_direction",
        "scene_style_lock",
        "provider_handoff_notes",
        "warnings",
    ):
        assert k in brief

    p = str(brief["master_reference_prompt"])
    # prompt must contain style/light/camera cues + thumbnail space hint
    assert "Lighting" in p
    assert "Camera" in p
    assert "negative space" in p.lower()
    assert "16:9" in p
    assert "do NOT render text".lower() in p.lower()

    neg = str(brief["negative_prompt"]).lower()
    assert "watermark" in neg
    assert "logo" in neg
    assert "text" in neg


def test_subject_lock_male_inference_from_german_title() -> None:
    brief = build_visual_reference_brief_v1(
        title="Der Mann, der spurlos verschwand",
        hook_or_summary="Eine investigative Geschichte über ein mysteriöses Verschwinden.",
    )
    assert brief.get("subject_lock") == "adult_man"
    p = str(brief.get("master_reference_prompt") or "").lower()
    assert "adult man" in p
    neg = str(brief.get("negative_prompt") or "").lower()
    assert "female main character" in neg


def test_subject_lock_neutral_when_no_gender_tokens() -> None:
    brief = build_visual_reference_brief_v1(
        title="Das Rätsel im Hafen",
        hook_or_summary="Ein dokumentarischer Blick auf eine ungewöhnliche Spurensuche.",
    )
    assert brief.get("subject_lock") == "neutral"
    p = str(brief.get("master_reference_prompt") or "").lower()
    assert "gender-neutral" in p


def test_cli_requires_confirm_exit_3(capsys) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "run_visual_reference_smoke.py"
    spec = importlib.util.spec_from_file_location("run_visual_reference_smoke_ba3273", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with patch.object(sys, "argv", ["run_visual_reference_smoke.py", "--title", "t", "--summary", "s"]):
        rc = mod.main()
    assert rc == 3
    out = capsys.readouterr().out
    j = json.loads(out)
    assert j.get("blocking_reason") == "confirm_live_openai_image_required"


def test_run_visual_reference_writes_report_and_sanitizes_warnings(tmp_path: Path) -> None:
    class _FakeGen:
        ok = True
        provider = "openai_images"
        dry_run = True
        model = "gpt-image-2"
        size = "1024x1024"
        prompt_used = "x"
        output_path = str(tmp_path / "master_reference.png")
        bytes_written = 8
        warnings = ["ok", "Bearer sk-THIS-MUST-NOT-LEAK"]
        error_code = ""
        error_message = ""

    (tmp_path / "master_reference.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    with patch(
        "app.production_connectors.visual_reference_layer.generate_openai_image_from_prompt",
        return_value=_FakeGen(),
    ):
        out = run_visual_reference_image_v1(
            output_dir=tmp_path,
            title="t",
            summary="s",
            model=None,
            size="",
            timeout_seconds=1.0,
            dry_run=True,
        )
    assert out["visual_reference_version"] == "ba32_73_v1"
    assert out["model"] == "gpt-image-2"
    assert out["size"] == "1024x1024"
    assert Path(out["output_path"]).is_file()
    rp = Path(out["result_path"])
    assert rp.is_file()
    txt = rp.read_text(encoding="utf-8")
    assert "sk-" not in txt
    assert "Bearer" not in txt
    assert "visual_reference_warning_sanitized" in (out.get("warnings") or [])


def test_no_auto_fallback_model_default_gpt_image_2(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENAI_IMAGE_MODEL", raising=False)

    class _FakeGen:
        ok = False
        provider = "openai_images"
        dry_run = False
        model = "gpt-image-2"
        size = "1024x1024"
        prompt_used = "x"
        output_path = str(tmp_path / "master_reference.png")
        bytes_written = 0
        warnings = ["openai_api_key_missing"]
        error_code = "openai_api_key_missing"
        error_message = "missing"

    with patch(
        "app.production_connectors.visual_reference_layer.generate_openai_image_from_prompt",
        return_value=_FakeGen(),
    ):
        out = run_visual_reference_image_v1(
            output_dir=tmp_path,
            title="t",
            summary="s",
            model=None,
            size="1024x1024",
            timeout_seconds=1.0,
            dry_run=False,
        )
    assert out["model"] == "gpt-image-2"
    # We do not switch models automatically; warning remains controlled.
    assert any("openai_api_key_missing" in str(w) for w in (out.get("warnings") or []))

