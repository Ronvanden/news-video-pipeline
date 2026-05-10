"""BA 32.74 — Thumbnail Candidates V1 (no live API in CI)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

from app.production_connectors.thumbnail_candidates import (
    build_thumbnail_candidate_briefs_v1,
    run_thumbnail_candidates_v1,
)
from app.production_connectors.visual_reference_layer import build_visual_reference_brief_v1


def test_candidate_builder_generates_three_variants_and_caps_count() -> None:
    vr = build_visual_reference_brief_v1(
        title="Der Mann, der spurlos verschwand",
        hook_or_summary="Kurze Zusammenfassung.",
    )
    out = build_thumbnail_candidate_briefs_v1(
        visual_reference_brief=vr,
        title="Der Mann, der spurlos verschwand",
        summary="Kurze Zusammenfassung.",
        count=99,
        target_platform="youtube",
    )
    assert out["thumbnail_candidates_version"] == "ba32_74_v1"
    assert out["subject_lock"] == "adult_man"
    cands = out["candidates"]
    assert len(cands) == 3
    ids = [c["candidate_id"] for c in cands]
    assert ids == ["thumb_a", "thumb_b", "thumb_c"]

    for c in cands:
        p = str(c["prompt"]).lower()
        assert "negative space" in p
        assert "do not render text" in p
        assert "typography" in p
        assert "16:9" in p
        assert c["subject_lock"] == "adult_man"
        neg = str(c["negative_prompt"]).lower()
        assert "female main character" in neg


def test_builder_default_count_and_max_3() -> None:
    out0 = build_thumbnail_candidate_briefs_v1(title="t", summary="s", count=0)
    assert len(out0["candidates"]) == 3
    out1 = build_thumbnail_candidate_briefs_v1(title="t", summary="s", count=1)
    assert len(out1["candidates"]) == 1
    out2 = build_thumbnail_candidate_briefs_v1(title="t", summary="s", count=2)
    assert len(out2["candidates"]) == 2


def test_cli_requires_confirm_exit_3(capsys) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "run_thumbnail_candidates_smoke.py"
    spec = importlib.util.spec_from_file_location("run_thumb_candidates_smoke_ba3274", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with patch.object(sys, "argv", ["run_thumbnail_candidates_smoke.py", "--title", "t", "--summary", "s"]):
        rc = mod.main()
    assert rc == 3
    out = capsys.readouterr().out
    j = json.loads(out)
    assert j.get("blocking_reason") == "confirm_live_openai_image_required"


def test_run_thumbnail_candidates_writes_report_and_sanitizes_warnings(tmp_path: Path) -> None:
    class _FakeGen:
        ok = True
        provider = "openai_images"
        dry_run = True
        model = "gpt-image-2"
        size = "1024x1024"
        prompt_used = "x"
        bytes_written = 8
        warnings = ["ok", "Bearer sk-THIS-MUST-NOT-LEAK"]
        error_code = ""
        error_message = ""

        def __init__(self, out_path: Path):
            self.output_path = str(out_path)

    def _fake_generate(prompt, output_path, **_kw):
        p = Path(output_path)
        p.write_bytes(b"\x89PNG\r\n\x1a\n")
        return _FakeGen(p)

    with patch(
        "app.production_connectors.thumbnail_candidates.generate_openai_image_from_prompt",
        side_effect=_fake_generate,
    ):
        out = run_thumbnail_candidates_v1(
            output_dir=tmp_path,
            title="t",
            summary="s",
            count=3,
            model=None,
            size="",
            timeout_seconds=1.0,
            dry_run=True,
        )
    assert out["thumbnail_candidates_version"] == "ba32_74_v1"
    assert out["model"] == "gpt-image-2"
    assert out["size"] == "1024x1024"
    assert out["generated_count"] == 3
    assert out["failed_count"] == 0
    rp = Path(out["result_path"])
    assert rp.is_file()
    txt = rp.read_text(encoding="utf-8")
    assert "sk-" not in txt
    assert "Bearer" not in txt
    assert "thumbnail_candidates_warning_sanitized" in (out.get("warnings") or [])
    paths = out["candidate_paths"]
    assert Path(paths["thumb_a"]).is_file()
    assert Path(paths["thumb_b"]).is_file()
    assert Path(paths["thumb_c"]).is_file()


def test_default_model_is_gpt_image_2_and_no_auto_fallback(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENAI_IMAGE_MODEL", raising=False)

    class _FakeGen:
        ok = False
        provider = "openai_images"
        dry_run = False
        model = "gpt-image-2"
        size = "1024x1024"
        prompt_used = "x"
        output_path = str(tmp_path / "thumbnail_candidate_thumb_a.png")
        bytes_written = 0
        warnings = ["openai_api_key_missing"]
        error_code = "openai_api_key_missing"
        error_message = "missing"

    with patch(
        "app.production_connectors.thumbnail_candidates.generate_openai_image_from_prompt",
        return_value=_FakeGen(),
    ):
        out = run_thumbnail_candidates_v1(
            output_dir=tmp_path,
            title="t",
            summary="s",
            count=1,
            model=None,
            size="1024x1024",
            timeout_seconds=1.0,
            dry_run=False,
        )
    assert out["model"] == "gpt-image-2"
    assert out["generated_count"] == 0
    assert out["failed_count"] == 1
    assert any("openai_api_key_missing" in str(w) for w in (out.get("warnings") or []))

