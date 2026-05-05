"""BA 22.2 — sichere Preview-Datei-Route + Panel file_urls + Dashboard-Texte."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.founder_dashboard.local_preview_panel import (
    LOCAL_PREVIEW_ALLOWED_FILENAMES,
    build_file_urls_for_run,
    build_local_preview_file_url,
    build_local_preview_panel_payload,
    local_preview_safe_resolve_file,
    validate_local_preview_run_id,
)
from app.main import app


def _patch_out_root(monkeypatch, tmp: Path) -> None:
    import app.routes.founder_dashboard as fd

    monkeypatch.setattr(fd, "default_local_preview_out_root", lambda: tmp)


def test_validate_run_id_rejects_traversal():
    assert validate_local_preview_run_id("ok-run_1") is True
    assert validate_local_preview_run_id("../x") is False
    assert validate_local_preview_run_id("a/b") is False


def test_safe_resolve_whitelist_and_resolve(tmp_path: Path):
    d = tmp_path / "local_preview_safe1"
    d.mkdir(parents=True)
    (d / "preview_with_subtitles.mp4").write_bytes(b"x")
    p = local_preview_safe_resolve_file(tmp_path, "safe1", "preview_with_subtitles.mp4")
    assert p is not None and p.is_file()
    assert local_preview_safe_resolve_file(tmp_path, "safe1", "evil.txt") is None
    assert local_preview_safe_resolve_file(tmp_path, "../x", "preview_with_subtitles.mp4") is None


def test_safe_resolve_rejects_symlink_file(tmp_path: Path):
    d = tmp_path / "local_preview_symrun"
    d.mkdir(parents=True)
    outside = tmp_path / "outside_secret.txt"
    outside.write_text("secret", encoding="utf-8")
    link = d / "preview_with_subtitles.mp4"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Symlinks not supported or insufficient privileges")
    assert local_preview_safe_resolve_file(tmp_path, "symrun", "preview_with_subtitles.mp4") is None


def test_build_file_urls_priority(tmp_path: Path):
    d = tmp_path / "local_preview_prio"
    d.mkdir(parents=True)
    (d / "clean_video.mp4").write_bytes(b"a")
    urls = build_file_urls_for_run(d, "prio")
    assert urls["preview_url"] == build_local_preview_file_url("prio", "clean_video.mp4")
    (d / "preview_with_subtitles.mp4").write_bytes(b"b")
    urls2 = build_file_urls_for_run(d, "prio")
    assert "preview_with_subtitles.mp4" in urls2["preview_url"]


def test_panel_payload_file_urls(tmp_path: Path):
    d = tmp_path / "local_preview_purls"
    d.mkdir(parents=True)
    (d / "OPEN_ME.md").write_text("# hi", encoding="utf-8")
    (d / "local_preview_result.json").write_text("{}", encoding="utf-8")
    p = build_local_preview_panel_payload(out_root=tmp_path, runs_limit=5)
    assert p["panel_version"] == "ba22_local_preview_panel_v3"
    u = p["runs"][0]["file_urls"]
    assert u["open_me_url"].endswith("/OPEN_ME.md")
    assert u["result_json_url"].endswith("/local_preview_result.json")
    assert p["latest_file_urls"]["open_me_url"] == u["open_me_url"]


def test_file_route_serves_mp4(tmp_path: Path, monkeypatch):
    _patch_out_root(monkeypatch, tmp_path)
    d = tmp_path / "local_preview_vid1"
    d.mkdir(parents=True)
    (d / "preview_with_subtitles.mp4").write_bytes(b"\0\x00\x00\x20ftypisom")

    client = TestClient(app)
    r = client.get("/founder/dashboard/local-preview/file/vid1/preview_with_subtitles.mp4")
    assert r.status_code == 200
    assert "video" in (r.headers.get("content-type") or "").lower()
    assert len(r.content) > 0


def test_file_route_serves_markdown(tmp_path: Path, monkeypatch):
    _patch_out_root(monkeypatch, tmp_path)
    d = tmp_path / "local_preview_md1"
    d.mkdir(parents=True)
    (d / "OPEN_ME.md").write_text("# t", encoding="utf-8")

    client = TestClient(app)
    r = client.get("/founder/dashboard/local-preview/file/md1/OPEN_ME.md")
    assert r.status_code == 200
    assert r.text == "# t"


def test_file_route_404_missing(tmp_path: Path, monkeypatch):
    _patch_out_root(monkeypatch, tmp_path)
    d = tmp_path / "local_preview_miss"
    d.mkdir(parents=True)
    client = TestClient(app)
    r = client.get("/founder/dashboard/local-preview/file/miss/preview_with_subtitles.mp4")
    assert r.status_code == 404


def test_file_route_404_bad_filename(tmp_path: Path, monkeypatch):
    _patch_out_root(monkeypatch, tmp_path)
    d = tmp_path / "local_preview_badfn"
    d.mkdir(parents=True)
    (d / "secret.txt").write_text("x", encoding="utf-8")
    client = TestClient(app)
    r = client.get("/founder/dashboard/local-preview/file/badfn/secret.txt")
    assert r.status_code == 404


def test_dashboard_html_has_preview_strings():
    client = TestClient(app)
    r = client.get("/founder/dashboard")
    assert r.status_code == 200
    t = r.text
    assert "Preview öffnen" in t
    assert "Report öffnen" in t
    assert "OPEN_ME öffnen" in t
    assert "lp-preview-video-wrap" in t


def test_dashboard_js_no_broken_innerhtml_class_muted():
    """Escapierte Anführungszeichen in innerHTML-Strings brachen JS (Unexpected identifier 'muted')."""
    client = TestClient(app)
    t = client.get("/founder/dashboard").text
    assert 'innerHTML = "<p class="' not in t
    assert "v.muted = true" in t
    assert "v.controls = true" in t


def test_config_lists_file_route():
    client = TestClient(app)
    j = client.get("/founder/dashboard/config").json()
    rel = j.get("local_preview_file_relative") or {}
    assert "/founder/dashboard/local-preview/file/" in rel.get("path", "")


def test_allowed_filenames_covers_contract():
    assert "local_preview_result.json" in LOCAL_PREVIEW_ALLOWED_FILENAMES
