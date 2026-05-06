"""BA 27.3 — Continuity display tests (strings + README + dashboard)."""

from __future__ import annotations

import json
from pathlib import Path

from app.real_video_build.production_pack import write_production_pack_readme
from app.visual_plan.continuity_display import (
    build_continuity_display_block,
    build_continuity_display_line,
)


def test_display_line_prepared():
    a = {"continuity_provider_preparation_status": "prepared", "reference_asset_ids": ["r1"], "continuity_strength": "high"}
    s = build_continuity_display_line(a)
    assert "Kontinuität: vorbereitet" in s
    assert "Referenzen: 1" in s
    assert "Stärke: hoch" in s


def test_display_line_missing():
    a = {"continuity_provider_preparation_status": "missing_reference", "reference_asset_ids": ["r1"]}
    s = build_continuity_display_line(a)
    assert "Referenz fehlt" in s


def test_display_line_none():
    a = {"scene_number": 1}
    assert build_continuity_display_line(a) == "Kontinuität: keine"


def test_hint_truncated():
    long = "x" * 300
    a = {"continuity_provider_preparation_status": "prepared", "reference_asset_ids": ["r1"], "continuity_prompt_hint": long}
    b = build_continuity_display_block(a)
    assert b["continuity_hint_short"].endswith("…")
    assert len(b["continuity_hint_short"]) <= 140


def test_display_block_counts_refs():
    a = {"continuity_provider_preparation_status": "prepared", "reference_asset_ids": ["a", "b"]}
    b = build_continuity_display_block(a)
    assert b["continuity_reference_count"] == 2


def test_readme_includes_continuity_section(tmp_path: Path):
    pack = tmp_path / "pack"
    summary = {
        "run_id": "r",
        "ready_for_render": False,
        "render_readiness_status": "needs_review",
        "approval_status": "needs_review",
        "blocking_reasons": [],
        "warnings": [],
        "continuity_wiring_summary": {"prepared_count": 2, "missing_reference_count": 1, "needs_review_count": 0, "none_count": 3},
    }
    p = write_production_pack_readme(pack_dir=pack, summary=summary)
    txt = p.read_text(encoding="utf-8")
    assert "## Kontinuität" in txt
    assert "vorbereitet" in txt


def test_dashboard_html_contains_continuity_string():
    html = Path("app/founder_dashboard/html.py").read_text(encoding="utf-8")
    assert "Kontinuität:" in html

