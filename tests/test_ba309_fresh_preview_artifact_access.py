"""BA 30.9 — sichere read-only Fresh-Preview-Artefakt-Datei-Route."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.founder_dashboard.fresh_preview_artifact_access import resolve_fresh_preview_artifact_path
from app.founder_dashboard.html import get_founder_dashboard_html
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_resolve_under_fresh_topic_preview(tmp_path: Path):
    root = tmp_path / "output"
    run = root / "fresh_topic_preview" / "run_a"
    run.mkdir(parents=True)
    fp = run / "script.json"
    fp.write_text('{"x":1}', encoding="utf-8")
    p_ok, reason = resolve_fresh_preview_artifact_path(root, str(fp.resolve()))
    assert reason == "ok"
    assert p_ok == fp.resolve()


def test_resolve_render_input_bundle_at_output_root(tmp_path: Path):
    root = tmp_path / "output"
    root.mkdir(parents=True)
    fp = root / "render_input_bundle_run_x.json"
    fp.write_text("{}", encoding="utf-8")
    p_ok, reason = resolve_fresh_preview_artifact_path(root, str(fp.resolve()))
    assert reason == "ok"
    assert p_ok == fp.resolve()


def test_resolve_motion_manifests_at_output_root(tmp_path: Path):
    root = tmp_path / "output"
    root.mkdir(parents=True)
    tl = root / "motion_timeline_manifest_run_x.json"
    cl = root / "motion_clip_manifest_run_x.json"
    tl.write_text("{}", encoding="utf-8")
    cl.write_text("{}", encoding="utf-8")
    assert resolve_fresh_preview_artifact_path(root, str(tl.resolve()))[1] == "ok"
    assert resolve_fresh_preview_artifact_path(root, str(cl.resolve()))[1] == "ok"


def test_resolve_local_preview_result_under_work(tmp_path: Path):
    root = tmp_path / "output"
    lp = root / ".preview_smoke_work" / "run_x" / "local_preview" / "local_preview_render_result.json"
    lp.parent.mkdir(parents=True)
    lp.write_text("{}", encoding="utf-8")
    p_ok, reason = resolve_fresh_preview_artifact_path(root, str(lp.resolve()))
    assert reason == "ok"
    assert p_ok == lp.resolve()


def test_resolve_preview_smoke_summary_at_output_root(tmp_path: Path):
    root = tmp_path / "output"
    root.mkdir(parents=True)
    fp = root / "preview_smoke_auto_summary_run_a.json"
    fp.write_text("{}", encoding="utf-8")
    p_ok, reason = resolve_fresh_preview_artifact_path(root, str(fp.resolve()))
    assert reason == "ok"
    assert p_ok == fp.resolve()


def test_resolve_open_preview_smoke_under_preview_work(tmp_path: Path):
    root = tmp_path / "output"
    md = root / ".preview_smoke_work" / "run_a" / "OPEN_PREVIEW_SMOKE.md"
    md.parent.mkdir(parents=True)
    md.write_text("# ok\n", encoding="utf-8")
    p_ok, reason = resolve_fresh_preview_artifact_path(root, str(md.resolve()))
    assert reason == "ok"
    assert p_ok == md.resolve()


def test_traversal_relative_string_escapes_output_blocked(tmp_path: Path):
    root = tmp_path / "output"
    root.mkdir(parents=True)
    evil = tmp_path / "evil.json"
    evil.write_text("{}", encoding="utf-8")
    run = root / "fresh_topic_preview" / "run_a"
    run.mkdir(parents=True)
    rel_req = "fresh_topic_preview/run_a/../../../evil.json"
    p_ok, reason = resolve_fresh_preview_artifact_path(root, rel_req)
    assert p_ok is None
    assert reason == "forbidden"


def test_outside_output_blocked(tmp_path: Path):
    outside = tmp_path / "other.json"
    outside.write_text("{}", encoding="utf-8")
    out_root = tmp_path / "output"
    out_root.mkdir(parents=True)
    p_ok, reason = resolve_fresh_preview_artifact_path(out_root, str(outside.resolve()))
    assert p_ok is None
    assert reason == "forbidden"


def test_missing_file_404(client: TestClient, tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.routes.founder_dashboard.default_local_preview_out_root",
        lambda: tmp_path / "output",
    )
    root = tmp_path / "output"
    root.mkdir(parents=True)
    missing = root / "fresh_topic_preview" / "run_a" / "script.json"
    r = client.get("/founder/dashboard/fresh-preview/file", params={"path": str(missing.resolve())})
    assert r.status_code == 404


def test_bad_extension_forbidden(client: TestClient, tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.routes.founder_dashboard.default_local_preview_out_root",
        lambda: tmp_path / "output",
    )
    run = tmp_path / "output" / "fresh_topic_preview" / "run_a"
    run.mkdir(parents=True)
    bad = run / "clip.mp4"
    bad.write_bytes(b"x")
    r = client.get("/founder/dashboard/fresh-preview/file", params={"path": str(bad.resolve())})
    assert r.status_code == 403


def test_directory_forbidden(client: TestClient, tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.routes.founder_dashboard.default_local_preview_out_root",
        lambda: tmp_path / "output",
    )
    d = tmp_path / "output" / "fresh_topic_preview" / "run_a"
    d.mkdir(parents=True)
    r = client.get("/founder/dashboard/fresh-preview/file", params={"path": str(d.resolve())})
    assert r.status_code == 403


def test_file_too_large_413(client: TestClient, tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.routes.founder_dashboard.default_local_preview_out_root",
        lambda: tmp_path / "output",
    )
    run = tmp_path / "output" / "fresh_topic_preview" / "run_a"
    run.mkdir(parents=True)
    huge = run / "big.json"
    huge.write_text("x" * (1024 * 1024 + 1), encoding="utf-8")
    r = client.get("/founder/dashboard/fresh-preview/file", params={"path": str(huge.resolve())})
    assert r.status_code == 413


def test_endpoint_returns_json(client: TestClient, tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "app.routes.founder_dashboard.default_local_preview_out_root",
        lambda: tmp_path / "output",
    )
    run = tmp_path / "output" / "fresh_topic_preview" / "run_x"
    run.mkdir(parents=True)
    fp = run / "script.json"
    fp.write_text('{"title":"T"}', encoding="utf-8")
    r = client.get("/founder/dashboard/fresh-preview/file", params={"path": str(fp.resolve())})
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("application/json")
    assert json.loads(r.text)["title"] == "T"


def test_dashboard_html_contains_open_marker():
    html = get_founder_dashboard_html()
    assert "Öffnen" in html
    assert "fp-open-artifact" in html
    assert "/founder/dashboard/fresh-preview/file" in html
