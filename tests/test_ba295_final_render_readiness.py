"""BA 29.5 — Final render readiness gate."""

from __future__ import annotations

from app.production_assembly.final_render_readiness import build_final_render_readiness_result


def _ps(**kwargs):
    base = {
        "run_id": "r",
        "local_preview_render_result": {
            "ok": True,
            "output_video_path": "/tmp/preview.mp4",
        },
        "human_preview_review_result": {
            "review_status": "pending",
            "approved_for_final_render": False,
        },
    }
    base.update(kwargs)
    return base


def test_pending_human_needs_review():
    r = build_final_render_readiness_result(
        production_summary=_ps(),
        final_render_dry_run={"ok": True},
        local_preview_render_result={"ok": True, "output_video_path": "/x.mp4"},
    )
    assert r["readiness_status"] == "needs_review"
    assert r["ok"] is False


def test_rejected_blocked():
    r = build_final_render_readiness_result(
        production_summary=_ps(
            human_preview_review_result={"review_status": "rejected", "approved_for_final_render": False},
        ),
        final_render_dry_run={"ok": True},
        local_preview_render_result={"ok": True, "output_video_path": "/x.mp4"},
    )
    assert r["readiness_status"] == "blocked"


def test_approved_and_technical_ready():
    r = build_final_render_readiness_result(
        production_summary=_ps(
            human_preview_review_result={"review_status": "approved", "approved_for_final_render": True},
        ),
        final_render_dry_run={"ok": True},
        local_preview_render_result={"ok": True, "output_video_path": "/x.mp4"},
    )
    assert r["readiness_status"] == "ready"
    assert r["ok"] is True


def test_preview_missing_needs_review():
    r = build_final_render_readiness_result(
        production_summary=_ps(
            human_preview_review_result={"review_status": "approved", "approved_for_final_render": True},
        ),
        final_render_dry_run={"ok": True},
        local_preview_render_result={"ok": False, "output_video_path": ""},
    )
    assert r["technical_ready"] is False
    assert r["readiness_status"] == "needs_review"
