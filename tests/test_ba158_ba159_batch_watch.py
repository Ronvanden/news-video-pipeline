"""BA 15.8–15.9 — Batch URL Engine + Watch Approval (Kernfälle)."""

from unittest.mock import MagicMock, patch

from app.manual_url_story.batch_engine import parse_urls_file_lines, run_batch_url_demo
from app.manual_url_story.schema import UrlQualityGateResult
from app.manual_url_story.watch_approval import (
    load_watch_items_from_json,
    run_watch_approval_scan,
)


def test_parse_urls_file_skips_comments_and_blank():
    text = "# intro\n\nhttps://a.example/x\n\nhttps://b.example/y\n"
    assert parse_urls_file_lines(text) == ["https://a.example/x", "https://b.example/y"]


@patch("app.manual_url_story.batch_engine._get_manual_url_rewrite_phase")
def test_batch_ranking_strong_before_weak(mock_get):
    def _side_effect(req):
        url = req.manual_source_url or ""
        if "weak" in url:
            gate = UrlQualityGateResult(
                url_quality_status="weak",
                hook_potential_score=25,
                narrative_density_score=40,
                emotional_weight_score=10,
                recommended_mode="documentary",
            )
        else:
            gate = UrlQualityGateResult(
                url_quality_status="strong",
                hook_potential_score=82,
                narrative_density_score=70,
                emotional_weight_score=20,
                recommended_mode="mystery",
            )
        o = MagicMock()
        o.script_title = "Titel"
        o.effective_title = ""
        o.full_script_preview = "Zusammenfassung " * 8
        o.effective_source_summary = ""
        return o, gate

    mock_get.return_value = _side_effect

    result = run_batch_url_demo(
        ["https://strong.example/a", "https://weak.example/b"],
        top_n=2,
    )
    assert result.ranked_urls[0] == "https://strong.example/a"
    assert result.top_candidates[0] == "https://strong.example/a"
    assert result.items[0].hook_potential_score == 82


@patch("app.manual_url_story.batch_engine._get_manual_url_rewrite_phase")
def test_batch_blocked_urls_list(mock_get):
    gate = UrlQualityGateResult(
        url_quality_status="blocked",
        hook_potential_score=0,
        narrative_density_score=0,
        emotional_weight_score=0,
        blocking_reasons=["x"],
    )
    o = MagicMock(
        script_title="",
        effective_title="",
        full_script_preview="",
        effective_source_summary="",
    )
    mock_get.return_value = lambda _req: (o, gate)

    result = run_batch_url_demo(["https://blocked.example/z"])
    assert result.blocked_urls == ["https://blocked.example/z"]
    assert result.top_candidates == []


@patch("app.manual_url_story.watch_approval.extract_text_from_url")
def test_watch_approval_queue_and_duplicate(mock_ext):
    mock_ext.return_value = ("Wort " * 120, [])
    raw = {
        "sources": [
            {
                "kind": "feed_stub",
                "label": "Quelle A",
                "urls": [
                    "https://news.example/item?utm=1",
                    "https://news.example/item?utm=2",
                ],
            }
        ]
    }
    items = load_watch_items_from_json(raw)
    assert len(items) == 2

    result = run_watch_approval_scan(items)
    assert len(result.detected_items) == 2
    assert mock_ext.call_count == 1
    skips = [x for x in result.detected_items if x.recommended_action == "skip"]
    assert skips


@patch("app.manual_url_story.watch_approval.extract_text_from_url")
def test_watch_load_items_flat(mock_ext):
    mock_ext.return_value = ("Inhalt " * 80, [])
    items = load_watch_items_from_json(
        {"items": [{"url": "https://a.example/x", "label": "A"}]}
    )
    assert len(items) == 1
    r = run_watch_approval_scan(items)
    assert len(r.detected_items) == 1
