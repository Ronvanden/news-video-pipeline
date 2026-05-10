"""BA 32.77 — Thumbnail Pack Export (read/display only, no providers)."""

from __future__ import annotations

import json
from pathlib import Path

from app.founder_dashboard.ba323_video_generate import build_open_me_video_result_html
from app.production_connectors.thumbnail_pack_export import (
    discover_thumbnail_batch_overlay_reports,
    load_thumbnail_pack_v1,
    normalize_thumbnail_pack_from_batch_report,
    pick_best_batch_overlay_report,
)


def test_normalize_extracts_recommended_and_variants(tmp_path: Path) -> None:
    raw = {
        "ok": True,
        "thumbnail_batch_overlay_version": "ba32_76_v1",
        "generated_count": 2,
        "outputs": [
            {
                "output_id": "batch_01",
                "score": 70,
                "style_preset": "impact_youtube",
                "text_lines": ["A", "B"],
                "output_path": str(tmp_path / "t1.png"),
            },
            {
                "output_id": "batch_02",
                "score": 55,
                "style_preset": "urgent_mystery",
                "text_lines": ["X"],
                "output_path": str(tmp_path / "t2.png"),
            },
        ],
        "recommended_thumbnail": {
            "output_id": "batch_01",
            "score": 70,
            "style_preset": "impact_youtube",
            "text_lines": ["A", "B"],
            "output_path": str(tmp_path / "t1.png"),
        },
    }
    rp = tmp_path / "thumbnail_batch_overlay_result.json"
    pack = normalize_thumbnail_pack_from_batch_report(raw, result_path=rp)
    assert pack["thumbnail_pack_status"] == "ready"
    assert pack["thumbnail_recommended_path"] == str(tmp_path / "t1.png")
    assert pack["thumbnail_recommended_score"] == 70
    assert pack["thumbnail_recommended_style_preset"] == "impact_youtube"
    assert pack["thumbnail_recommended_text_lines"] == ["A", "B"]
    assert pack["thumbnail_top_score"] == 70
    assert pack["thumbnail_generated_count"] == 2
    assert len(pack["thumbnail_variants"]) == 2
    assert pack["thumbnail_pack_result_path"] == str(rp.resolve())
    assert pack["thumbnail_pack_path"] == str(rp.parent.resolve())


def test_load_missing_report(tmp_path: Path) -> None:
    pack = load_thumbnail_pack_v1(output_dir=tmp_path)
    assert pack["thumbnail_pack_status"] == "missing_report"
    assert pack["thumbnail_variants"] == []


def test_load_from_disk_nested(tmp_path: Path) -> None:
    sub = tmp_path / "nested" / "pack"
    sub.mkdir(parents=True)
    img = sub / "thumbnail_batch_01.png"
    img.write_bytes(b"x")
    raw = {
        "ok": True,
        "thumbnail_batch_overlay_version": "ba32_76_v1",
        "generated_count": 1,
        "outputs": [
            {
                "output_id": "batch_01",
                "score": 80,
                "style_preset": "impact_youtube",
                "text_lines": ["EINS"],
                "output_path": str(img.resolve()),
            }
        ],
        "recommended_thumbnail": {
            "output_id": "batch_01",
            "score": 80,
            "style_preset": "impact_youtube",
            "text_lines": ["EINS"],
            "output_path": str(img.resolve()),
        },
    }
    jp = sub / "thumbnail_batch_overlay_result.json"
    jp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    pack = load_thumbnail_pack_v1(output_dir=tmp_path)
    assert pack["thumbnail_pack_status"] == "ready"
    assert pack["thumbnail_top_score"] == 80
    assert pack["thumbnail_pack_result_path"] == str(jp.resolve())


def test_pick_best_prefers_ok_and_count(tmp_path: Path) -> None:
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text(
        json.dumps({"ok": False, "generated_count": 0, "outputs": []}, ensure_ascii=False),
        encoding="utf-8",
    )
    b.write_text(
        json.dumps(
            {
                "ok": True,
                "generated_count": 2,
                "outputs": [
                    {"output_id": "x", "score": 1, "style_preset": "x", "text_lines": [], "output_path": "p"},
                    {"output_id": "y", "score": 2, "style_preset": "y", "text_lines": [], "output_path": "q"},
                ],
                "recommended_thumbnail": {
                    "output_id": "y",
                    "score": 2,
                    "style_preset": "y",
                    "text_lines": [],
                    "output_path": "q",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    chosen = pick_best_batch_overlay_report([a, b])
    assert chosen == b


def test_discover_deduplicates(tmp_path: Path) -> None:
    p = tmp_path / "thumbnail_batch_overlay_result.json"
    p.write_text("{}", encoding="utf-8")
    found = discover_thumbnail_batch_overlay_reports(tmp_path)
    assert len(found) == 1


def test_open_me_contains_thumbnail_pack_section(tmp_path: Path) -> None:
    rec = tmp_path / "out.png"
    rec.write_bytes(b"x")
    html = build_open_me_video_result_html(
        {
            "ok": True,
            "run_id": "r1",
            "warnings": [],
            "blocking_reasons": [],
            "thumbnail_pack": normalize_thumbnail_pack_from_batch_report(
                {
                    "ok": True,
                    "generated_count": 1,
                    "outputs": [
                        {
                            "output_id": "batch_01",
                            "score": 90,
                            "style_preset": "impact_youtube",
                            "text_lines": ["Hallo"],
                            "output_path": str(rec),
                        }
                    ],
                    "recommended_thumbnail": {
                        "output_id": "batch_01",
                        "score": 90,
                        "style_preset": "impact_youtube",
                        "text_lines": ["Hallo"],
                        "output_path": str(rec),
                    },
                },
                result_path=tmp_path / "thumbnail_batch_overlay_result.json",
            ),
        }
    )
    assert "Thumbnail Pack (BA 32.77)" in html
    assert "Alle Varianten" in html
    assert "Empfohlene Variante" in html
    assert "batch_01" in html
    assert "heuristisch" in html
