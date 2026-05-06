"""BA 26.5 — OpenAI Images Adapter V1 (dry-run + controlled live failure)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.production_connectors.openai_images_adapter import generate_openai_image_from_prompt


def test_openai_images_adapter_dry_run_writes_placeholder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    out = tmp_path / "img.png"
    res = generate_openai_image_from_prompt(
        "[visual_no_text_guard_v26_4]\nNo readable text.",
        out,
        dry_run=True,
        size="256x256",
        model="gpt-image-1",
    )
    d = res.to_dict()
    assert d["ok"] is True
    assert d["dry_run"] is True
    assert d["provider"] == "openai_images"
    assert Path(d["output_path"]).is_file()
    assert d["bytes_written"] > 0


def test_openai_images_adapter_live_missing_key_is_controlled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # settings.openai_api_key may be populated from developer env; force empty for deterministic test.
    monkeypatch.setattr("app.config.settings.openai_api_key", "", raising=False)
    out = tmp_path / "img.png"
    res = generate_openai_image_from_prompt(
        "Clean background.\n\n[visual_no_text_guard_v26_4]\nNo readable text.",
        out,
        dry_run=False,
        size="256x256",
        model="gpt-image-1",
    )
    d = res.to_dict()
    assert d["ok"] is False
    assert d["error_code"] == "openai_api_key_missing"
    assert d["dry_run"] is False

