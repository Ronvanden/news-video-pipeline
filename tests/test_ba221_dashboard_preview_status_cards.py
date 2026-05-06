"""BA 22.1 — Dashboard Preview Status Cards (Panel + optional local_preview_result.json)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.founder_dashboard.local_preview_panel import (
    build_local_preview_panel_payload,
    build_status_cards_from_saved_result,
)
from app.main import app


def test_status_cards_from_saved_json_full():
    blob = {
        "verdict": "WARNING",
        "quality_checklist": {"status": "warning"},
        "subtitle_quality_check": {"status": "pass", "summary": "ok"},
        "sync_guard": {"status": "warning", "summary": "drift"},
        "warning_classification": {"highest": "CHECK", "summary": "1 CHECK", "items": [{"code": "x", "level": "CHECK"}]},
        "founder_quality_decision": {
            "decision_code": "REVIEW_REQUIRED",
            "top_issue": "timing_review",
            "next_step": "Prüfe Preview.",
        },
    }
    sc = build_status_cards_from_saved_result(blob)
    assert sc["verdict"] == "WARNING"
    assert sc["quality"] == "WARNING"
    assert sc["subtitle_quality"] == "PASS"
    assert sc["sync_guard"] == "WARNING"
    assert sc["warning_level"] == "CHECK"
    assert sc["founder_decision"] == "REVIEW_REQUIRED"
    assert sc["top_issue"] == "timing_review"
    assert sc["next_step"] == "Prüfe Preview."
    assert sc["contract_present"] is True


def test_status_cards_missing_file_all_unknown():
    sc = build_status_cards_from_saved_result(None)
    assert sc["verdict"] == "UNKNOWN"
    assert sc["founder_decision"] == "UNKNOWN"
    assert sc["contract_present"] is False
    assert "contract_file_missing" in sc["top_issue"]


def test_panel_reads_local_preview_result_json(tmp_path: Path):
    run_dir = tmp_path / "local_preview_with_json"
    run_dir.mkdir(parents=True)
    snap = {
        "snapshot_version": "local_preview_dashboard_snapshot_v1",
        "verdict": "PASS",
        "quality_checklist": {"status": "pass"},
        "subtitle_quality_check": {"status": "pass", "summary": ""},
        "sync_guard": {"status": "pass", "summary": ""},
        "warning_classification": {"highest": "INFO", "summary": ""},
        "founder_quality_decision": {"decision_code": "GO_PREVIEW", "top_issue": "", "next_step": "Öffne Preview."},
    }
    (run_dir / "local_preview_result.json").write_text(json.dumps(snap), encoding="utf-8")

    payload = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=5)
    assert payload["panel_version"] == "ba22_local_preview_panel_v3"
    assert payload["latest_status_cards"]["verdict"] == "PASS"
    assert payload["latest_status_cards"]["founder_decision"] == "GO_PREVIEW"
    r0 = payload["runs"][0]
    assert r0["status_cards"]["quality"] == "PASS"


def test_panel_fallback_result_json_alt_name(tmp_path: Path):
    run_dir = tmp_path / "local_preview_alt"
    run_dir.mkdir(parents=True)
    (run_dir / "result.json").write_text(
        json.dumps(
            {
                "verdict": "FAIL",
                "quality_checklist": {"status": "fail"},
                "subtitle_quality_check": {"status": "fail", "summary": ""},
                "sync_guard": {"status": "fail", "summary": ""},
                "warning_classification": {"highest": "BLOCKING", "summary": ""},
                "founder_quality_decision": {
                    "decision_code": "BLOCK",
                    "top_issue": "blocking",
                    "next_step": "Fixen.",
                },
            }
        ),
        encoding="utf-8",
    )
    p = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=5)
    assert p["runs"][0]["status_cards"]["verdict"] == "FAIL"
    assert p["runs"][0]["status_cards"]["warning_level"] == "BLOCKING"


def test_corrupt_json_yields_unknown(tmp_path: Path):
    d = tmp_path / "local_preview_badjson"
    d.mkdir(parents=True)
    (d / "local_preview_result.json").write_text("{not json", encoding="utf-8")
    p = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=5)
    assert p["runs"][0]["status_cards"]["verdict"] == "UNKNOWN"


def test_dashboard_html_contains_status_labels():
    client = TestClient(app)
    r = client.get("/founder/dashboard")
    assert r.status_code == 200
    text = r.text
    assert "Local Preview" in text
    assert "Verdict" in text
    assert "Quality" in text
    assert "Founder decision" in text
    assert "lp-latest-cards" in text


def test_pipeline_writes_local_preview_result_json(tmp_path, monkeypatch):
    import importlib.util

    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "run_local_preview_pipeline.py"
    spec = importlib.util.spec_from_file_location("run_local_preview_pipeline_ba221", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    tl = tmp_path / "tl221.json"
    nar = tmp_path / "n221.txt"
    tl.write_text(json.dumps({"estimated_duration_seconds": 4.0}), encoding="utf-8")
    nar.write_text("n", encoding="utf-8")

    sub_d = tmp_path / "sub221"
    sub_d.mkdir(parents=True)
    srt = sub_d / "cues.srt"
    srt.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nA.\n\n2\n00:00:02,100 --> 00:00:04,000\nB.\n",
        encoding="utf-8",
    )
    sub_m = sub_d / "subtitle_manifest.json"
    sub_m.write_text(json.dumps({"subtitles_srt_path": str(srt)}), encoding="utf-8")
    aud_stub = tmp_path / "a221.wav"
    aud_stub.write_bytes(b"\0")

    def fake_build(*_a, **_k):
        return {
            "ok": True,
            "subtitle_manifest_path": str(sub_m),
            "audio_path": str(aud_stub),
            "warnings": [],
            "blocking_reasons": [],
        }

    def fake_render(*_a, **kw):
        ov = kw.get("output_video")
        if ov is not None:
            Path(ov).parent.mkdir(parents=True, exist_ok=True)
            Path(ov).write_bytes(b"cv")
        return {"video_created": True, "warnings": [], "blocking_reasons": []}

    def fake_burn(*_a, **_k):
        outp = tmp_path / "pv221.mp4"
        outp.write_bytes(b"pv")
        return {
            "ok": True,
            "skipped": False,
            "output_video_path": str(outp),
            "warnings": [],
            "blocking_reasons": [],
        }

    monkeypatch.setattr(mod, "_probe_media_duration_seconds", lambda p, **kw: (4.0, None))

    meta = mod.run_local_preview_pipeline(
        tl,
        nar,
        out_root=tmp_path,
        run_id="ba221rid",
        build_subtitle_pack_fn=fake_build,
        render_final_story_video_fn=fake_render,
        burn_in_subtitles_preview_fn=fake_burn,
    )
    piped = Path(meta["pipeline_dir"])
    jf = piped / "local_preview_result.json"
    assert jf.is_file()
    data = json.loads(jf.read_text(encoding="utf-8"))
    assert data.get("snapshot_version") == "local_preview_dashboard_snapshot_v1"
    assert "verdict" in data
    sc = build_status_cards_from_saved_result(data)
    assert sc["contract_present"] is True


def test_panel_route_ok():
    client = TestClient(app)
    res = client.get("/founder/dashboard/local-preview/panel")
    assert res.status_code == 200
    assert "panel_version" in res.json()
